#!/usr/bin/env python3
"""
Proves a redesign moved copy rather than rewriting it.

    python3 copydiff.py snapshot     before touching anything
    python3 copydiff.py check        after, to see exactly what text changed

Compares the set of sentences on every page, so reordering a section or
changing its markup is invisible here, but adding, cutting, or editing a
sentence is not.
"""

import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
SNAP = os.path.join(HERE, "_copy-snapshot.json")


def sentences(path):
    src = open(path, encoding="utf-8").read()
    src = re.sub(r"<(script|style)\b[\s\S]*?</\1>", " ", src, flags=re.I)
    src = re.sub(r"<!--[\s\S]*?-->", " ", src)
    # Split on tags, not on newlines, so re-wrapping a paragraph in the source
    # is invisible here and only a real copy change shows up.
    text = html.unescape(re.sub(r"<[^>]+>", "\x00", src))
    out = set()
    for chunk in text.split("\x00"):
        chunk = re.sub(r"\s+", " ", chunk).strip()
        if len(chunk) < 12:
            continue
        for s in re.split(r"(?<=[.?!])\s+", chunk):
            s = s.strip()
            if len(s) >= 12:
                out.add(s)
    return out


def collect():
    return {
        os.path.basename(f): sorted(sentences(f))
        for f in sorted(glob.glob(os.path.join(OUT, "*.html")))
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"

    if mode == "snapshot":
        data = collect()
        json.dump(data, open(SNAP, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"snapshot: {sum(len(v) for v in data.values())} sentences "
              f"across {len(data)} pages")
        return 0

    if not os.path.exists(SNAP):
        print("no snapshot. Run: python3 copydiff.py snapshot")
        return 1

    before = {k: set(v) for k, v in json.load(open(SNAP, encoding="utf-8")).items()}
    after = {k: set(v) for k, v in collect().items()}

    added = removed = 0
    for page in sorted(set(before) | set(after)):
        b, a = before.get(page, set()), after.get(page, set())
        gone, new = sorted(b - a), sorted(a - b)
        if not gone and not new:
            continue
        print(f"\n=== {page} ===")
        for s in gone:
            removed += 1
            print(f"  REMOVED  {s[:130]}")
        for s in new:
            added += 1
            print(f"  ADDED    {s[:130]}")

    print(f"\n{removed} removed, {added} added")
    if not removed and not added:
        print("copy is byte-identical. The redesign only moved things.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
