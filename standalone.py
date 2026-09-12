#!/usr/bin/env python3
"""
One file a companion can be given directly.

/desk is the real thing and this is built from it, never edited by hand: run
build.py first, then this. It inlines the stylesheet's fonts, both scripts,
and drops the marketing nav and footer, because from a file:// URL those links
go nowhere and a staff tool has no use for them. The result opens by double
clicking, needs no server and no network, and works on a phone that has been
handed the file. Nothing in it reports anywhere.

    python3 build.py && python3 standalone.py

Every record still lives in the browser that opened the file, so two
companions with the same file do not see each other's records. That is the
same limit /desk has, stated here so nobody is surprised by it.
"""

import base64
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
DST = os.path.join(HERE, "kinvisit-report-desk.html")

FONTS = {
    "/assets/fonts/geist-latin.woff2": "geist-latin.woff2",
    "/assets/fonts/geist-mono-latin.woff2": "geist-mono-latin.woff2",
    "/assets/fonts/literata-latin.woff2": "literata-latin.woff2",
}


def read(*parts):
    with open(os.path.join(OUT, *parts), encoding="utf-8") as f:
        return f.read()


def main():
    src_path = os.path.join(OUT, "desk.html")
    if not os.path.exists(src_path):
        print("site/desk.html is missing. Run build.py first.")
        return 1
    html = read("desk.html")

    # 1. The fonts travel with the file. Without this the page falls back to a
    #    system stack and stops looking like a Kinvisit document.
    for href, name in FONTS.items():
        with open(os.path.join(OUT, "assets", "fonts", name), "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        html = html.replace(href, "data:font/woff2;base64," + b64)

    # 2. Every script, in the order the page loads them. The Supabase library
    #    is deliberately left out: with no project configured this file cannot
    #    reach a database, portal.js sees that and opens the desk in local
    #    mode, and 110KB of client goes unshipped.
    parts = [
        "/* No project configured. portal.js opens the desk in local mode. */\n"
        # The same line build.py writes into config.js. Without it the
        # stylesheet still believes no script ran and the desk shows the
        # notice saying it needs one, on top of a desk that works.
        "document.documentElement.className += ' js';\n"
        "window.KV_CONFIG = { supabaseUrl: '', supabaseAnonKey: '' };",
        read("assets", "js", "report.js"),
        read("assets", "js", "portal.js"),
        read("assets", "site.js"),
        read("assets", "js", "desk.js"),
    ]
    html = re.sub(r'<script src="/assets/js/[^"]*" defer></script>\s*', "", html)
    html = html.replace(
        '<script src="/assets/site.js" defer></script>',
        "<script>\n" + "\n".join(parts) + "\n</script>",
    )

    # 3. The site chrome goes. Every link in it is a path this file cannot
    #    resolve, and a dead nav on a working tool reads as a broken page.
    html = re.sub(r'<a class="skip".*?</a>\s*', "", html, flags=re.S)
    html = re.sub(r"<header class=\"nav\">.*?</header>\s*", "", html, flags=re.S)
    html = re.sub(r"<header class=\"pt-bar\">.*?</header>\s*", "", html, flags=re.S)
    # The sign-in gate has nothing to check in a file with no project behind
    # it, and its only link points at a page this file cannot reach.
    html = re.sub(r'<div class="pt-gate".*?</div>\s*(?=(?:<template[^>]*>.*?</template>\s*)?'
                  r'<div class="pt-body")',
                  "", html, flags=re.S)
    html = re.sub(r"<div class=\"menu\" id=\"menu\" hidden>.*?</div>\s*(?=<main)", "", html, flags=re.S)
    html = re.sub(r"<footer class=\"site-foot[^\"]*\">.*?</footer>\s*", "", html, flags=re.S)
    html = re.sub(r'<div class="via-banner".*?</div>\s*(?=<main|<header|<div class="menu")',
                  "", html, flags=re.S)

    # 4. Nothing here should be crawled or measured.
    html = html.replace('<script defer data-domain="kinvisit.in" '
                        'src="https://plausible.io/js/script.tagged-events.js"></script>', "")
    html = re.sub(r'<link rel="canonical"[^>]*>', "", html)
    html = re.sub(r'<link rel="icon"[^>]*>|<link rel="apple-touch-icon"[^>]*>', "", html)
    html = re.sub(r'<link rel="preload"[^>]*>', "", html)

    with open(DST, "w", encoding="utf-8") as f:
        f.write(html)

    remaining = sorted(set(re.findall(r'(?:src|href)="(/[^"]*)"', html)))
    print("wrote", os.path.relpath(DST, HERE), f"{os.path.getsize(DST) / 1024:.0f}KB")
    if remaining:
        print("still points at the server:", remaining)
        return 1
    print("no remaining server paths. Opens on its own.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
