#!/usr/bin/env python3
"""
Every mechanism must have a complete, usable state with JavaScript off.

Chrome's headless screenshot path needs scripting, and its scripting-disabled
mode produces no DOM dump, so the honest test is to make the scripts
unreachable and load the pages normally. From the page's point of view that is
identical to a reader with JavaScript disabled or a script that failed to load.

    python3 preview.py &      then      python3 test_nojs.py
"""

import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
ASSETS = os.path.join(OUT, "assets")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = "http://localhost:8899"

# (page, description, must appear, must not appear)
CASES = [
    ("index.html", "M1 full year table renders", [
        r'class="cs-table"', r'Latanoprost', r'Visit 12',
    ], []),
    ("index.html", "M1 counter shows the finished year", [
        r'Visit 12\. Five specialists\. Ten medicines recorded\. Two withdrawn\.',
    ], []),
    ("index.html", "M1 scrubber controls are hidden", [r'class="cs-controls" hidden'], []),
    ("index.html", "M2 gap calculator stays hidden", [r'data-mech="gap" hidden'], []),
    ("index.html", "M6 all seven annotations readable", [
        r'Why this section is here',
    ], [r'class="annot" hidden']),
    ("index.html", "M13 all four branches readable", [
        r'id="esc-conflict"', r'id="esc-doctor"', r'id="esc-emergency"', r'id="esc-disagree"',
        r'11:51', r'not a clinician on duty',
    ], []),
    ("index.html", "M15 context bar hidden", [r'data-mech="ctxbar" hidden'], []),
    ("index.html", "statistics are real numbers", [r'>62%<', r'>30%<'], [r'>0%<']),
    ("index.html", "the whole argument is present", [
        r'A photo of a prescription is not a medical record',
        r'Oral anti-inflammatory withdrawn',
        r'Right now, one named companion attends every visit',
        r'is not clinically qualified',
    ], []),

    ("book.html", "M7 builder collapsed, WhatsApp link offered", [
        r'class="wb-inner" hidden', r'<noscript>[\s\S]{0,400}?wa\.me',
    ], []),
    ("book.html", "M8 clock replaced by a static promise", [
        r'<noscript><p class="cc-static">', r'6pm and 9pm in your local time',
    ], [r'class="cc-live">']),
    ("book.html", "the form still works", [
        r'<form class="form" name="visit-request"', r'action="/thanks"',
    ], []),

    ("hospitals.html", "M12 falls back to the area list", [
        r'class="hc-static"', r'South Delhi', r'Faridabad',
    ], []),

    ("pricing.html", "B2 all three prices readable", [
        r'2,200', r'3,200', r'5,400', r'1,600',
    ], []),
    ("pricing.html", "B4 policies readable", [
        r'your next visit is free', r'More than four hours before',
    ], []),
    ("pricing.html", "M9 overseas tier not hidden behind a dead button", [
        r'data-mech="overseas" hidden', r'Kinvisit Abroad', r'twenty minute call',
    ], []),

    # M15. With no script the portal cannot check a sign-in, so it must not
    # imply that it has. The signed-in pages ship their body hidden in the
    # HTML itself, not merely hidden by script, and they carry no record.
    ("portal.html", "M15 sign-in needs a script to work", [
        r'data-login="family"', r'data-login="companion"',
    ], []),
    ("records.html", "M15 body ships hidden and holds no record", [
        r'class="pt-body" hidden',
    ], [r'Sushila', r'Metformin', r'eGFR']),
    ("desk.html", "M15 desk body ships hidden", [
        r'class="pt-body" hidden',
    ], []),
    # M14 is the one mechanism that cannot degrade into a usable state: a
    # report generator with no script generates nothing. So the desk hides
    # itself and says why, rather than showing a form that does nothing.
    ("desk.html", "M14 desk states plainly that it needs a script", [
        r'This page needs JavaScript',
    ], []),
    ("record.html", "all four visits readable", [
        r'id="visit-1"', r'id="visit-2"', r'id="visit-3"', r'id="visit-4"',
    ], []),

    ("conversations.html", "every script readable", [
        r'They just write', r'Chachu can go', r'I am here on behalf of the family',
    ], []),
]


def fetch(page):
    return subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=6000",
         "--window-size=1200,3000", "--dump-dom", f"{BASE}/{page}"],
        capture_output=True, text=True, timeout=90,
    ).stdout


def main():
    hidden = os.path.join(HERE, "_nojs_hidden")
    os.makedirs(hidden, exist_ok=True)
    shutil.move(os.path.join(ASSETS, "js"), os.path.join(hidden, "js"))
    shutil.move(os.path.join(ASSETS, "site.js"), os.path.join(hidden, "site.js"))

    failed = total = 0
    try:
        cache = {}
        for page, name, must, must_not in CASES:
            if page not in cache:
                cache[page] = fetch(page)
            dom = cache[page]
            total += 1
            missing = [p for p in must if not re.search(p, dom)]
            present = [p for p in must_not if re.search(p, dom)]
            if missing or present:
                failed += 1
                print(f"  FAIL {page}: {name}")
                for m in missing:
                    print(f"         missing: {m}")
                for p in present:
                    print(f"         should not be there: {p}")
            else:
                print(f"  ok   {page}: {name}")

            if "js" in dom and re.search(r'class="js"', dom):
                print(f"  WARN {page}: page still marked as scripted")
    finally:
        shutil.move(os.path.join(hidden, "js"), os.path.join(ASSETS, "js"))
        shutil.move(os.path.join(hidden, "site.js"), os.path.join(ASSETS, "site.js"))
        os.rmdir(hidden)

    print(f"\n{total - failed}/{total} passed with JavaScript unavailable")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
