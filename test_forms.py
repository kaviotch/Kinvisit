#!/usr/bin/env python3
"""
Drives both forms in a real browser and checks what actually arrived.

The preview server records every submission to _submissions.log in the same
shape Netlify would deliver it, so these assertions cover the whole path:
client-side validation, the POST, the redirect, and the landing page.

    python3 preview.py &      then      python3 test_forms.py
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
LOG = os.path.join(HERE, "_submissions.log")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = "http://localhost:8899"

fails = []


def check(name, ok, detail=""):
    print(("  ok   " if ok else "  FAIL ") + name + (f"  {detail}" if not ok and detail else ""))
    if not ok:
        fails.append(name)


def drive(page, script, height=4000):
    src = open(os.path.join(OUT, page), encoding="utf-8").read()
    harness = "<script>setTimeout(function(){\n" + script + "\n}, 2200);</script>"
    tmp = "_t_form_" + page
    open(os.path.join(OUT, tmp), "w", encoding="utf-8").write(
        src.replace("</body>", harness + "</body>")
    )
    try:
        return subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=20000",
             f"--window-size=1200,{height}", "--dump-dom", f"{BASE}/{tmp}"],
            capture_output=True, text=True, timeout=90,
        ).stdout
    finally:
        os.remove(os.path.join(OUT, tmp))


def entries():
    if not os.path.exists(LOG):
        return []
    with open(LOG, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def h1_of(dom):
    m = re.search(r"<h1>(.*?)</h1>", dom, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def main():
    if os.path.exists(LOG):
        os.remove(LOG)

    # ------------------------------------------------ validation must block
    print("\n=== client-side validation ===")
    dom = drive("book.html", """
      var f = document.querySelector('form[name=visit-request]');
      f.querySelector('button[type=submit]').click();
    """)
    check("empty submit does not leave the page", "Tell us about the appointment" in h1_of(dom),
          f"landed on '{h1_of(dom)}'")
    check("empty submit posts nothing", len(entries()) == 0, f"{len(entries())} recorded")
    check("invalid fields are marked", 'class="field invalid"' in dom)
    check("an error message is shown", "This one we do need" in dom)

    dom = drive("book.html", """
      var f = document.querySelector('form[name=visit-request]');
      f.querySelector('#your-name').value = 'Anita Rao';
      f.querySelector('#phone').value = '+971 50 123 4567';
      f.querySelector('#hospital').value = 'Medanta, Gurugram';
      f.querySelector('#email').value = 'not-an-email';
      f.querySelector('button[type=submit]').click();
    """)
    check("a bad email blocks the submit", "Tell us about the appointment" in h1_of(dom))
    check("the email error is specific", "does not look complete" in dom)
    check("still nothing posted", len(entries()) == 0)

    dom = drive("book.html", """
      var f = document.querySelector('form[name=visit-request]');
      f.querySelector('#your-name').value = 'Anita Rao';
      f.querySelector('#phone').value = '+971 50 123 4567';
      f.querySelector('#hospital').value = 'Medanta, Gurugram';
      f.querySelector('#email').value = 'anita@example.com';
      f.querySelector('button[type=submit]').click();
    """)
    check("an unticked consent box blocks the submit",
          "Tell us about the appointment" in h1_of(dom), f"landed on '{h1_of(dom)}'")
    check("and says why", "cannot arrange the visit" in dom)
    check("nothing posted without consent", len(entries()) == 0)

    # ------------------------------------------------------ the happy path
    print("\n=== booking form ===")
    dom = drive("book.html", """
      var f = document.querySelector('form[name=visit-request]');
      f.querySelector('#your-name').value = 'Anita Rao';
      f.querySelector('#phone').value = '+971 50 123 4567';
      f.querySelector('#hospital').value = 'Medanta, Gurugram';
      f.querySelector('#email').value = 'anita@example.com';
      f.querySelector('#consent-visit').checked = true;
      f.querySelector('button[type=submit]').click();
    """)
    check("lands on the confirmation", "We have it" in h1_of(dom), f"landed on '{h1_of(dom)}'")
    check("no server error page", "Unsupported method" not in dom and "Error response" not in dom)

    got = entries()
    check("exactly one submission recorded", len(got) == 1, f"{len(got)} recorded")
    if got:
        e = got[-1]
        check("form name is visit-request", e["form"] == "visit-request", e["form"])
        check("not flagged as spam", e["spam"] is False)
        check("name arrived", e["fields"].get("your-name") == "Anita Rao")
        check("phone arrived with country code", e["fields"].get("phone") == "+971 50 123 4567")
        check("hospital arrived", e["fields"].get("hospital") == "Medanta, Gurugram")
        check("email arrived", e["fields"].get("email") == "anita@example.com")
        check("honeypot not submitted as content", "company-website" not in e["fields"])

    # -------------------------------------------------- the second screen
    print("\n=== details form ===")
    dom = drive("thanks.html", """
      var f = document.querySelector('form[name=visit-details]');
      f.querySelector('#d-phone').value = '+971 50 123 4567';
      f.querySelector('#d-city').value = 'Dubai';
      f.querySelector('#d-patient').value = 'Mum';
      f.querySelector('#d-raise').value = 'her hand has been swelling for months';
      f.querySelector('#consent-details').checked = true;
      f.querySelector('button[type=submit]').click();
    """, height=6000)
    check("lands on its own confirmation", "That is everything we need" in h1_of(dom),
          f"landed on '{h1_of(dom)}'")
    check("does not land back on the empty form", "You can stop here" not in h1_of(dom))

    got = entries()
    check("details recorded", len(got) == 2 and got[-1]["form"] == "visit-details")
    if len(got) == 2:
        check("city arrived", got[-1]["fields"].get("your-city") == "Dubai")
        check("what to raise arrived",
              got[-1]["fields"].get("what-to-raise") == "her hand has been swelling for months")

    # --------------------------------------------------------- the honeypot
    print("\n=== spam trap ===")
    drive("book.html", """
      var f = document.querySelector('form[name=visit-request]');
      f.querySelector('#your-name').value = 'bot';
      f.querySelector('#phone').value = '+10000000';
      f.querySelector('#hospital').value = 'x';
      f.querySelector('#email').value = 'bot@spam.example';
      f.querySelector('#consent-visit').checked = true;
      f.querySelector('[name=company-website]').value = 'http://spam.example';
      f.querySelector('button[type=submit]').click();
    """)
    got = entries()
    check("honeypot submission is flagged", len(got) == 3 and got[-1]["spam"] is True)

    print(f"\n{'all form checks passed' if not fails else str(len(fails)) + ' FAILED'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
