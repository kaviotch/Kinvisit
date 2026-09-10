#!/usr/bin/env python3
"""
Build every web variant of the photographs from the masters in photos/.

Four pictures, and each one earns its place by showing something the copy can
only assert: the person who actually attends, the report as a physical object,
the room the buyer is dreading, and the handwritten question list that nobody
else in the category has.

    python3 gen_photos.py      # only when a master changes

Each master produces a WebP and a JPEG at two widths. WebP first in the
<picture>, JPEG as the fallback, and both are served from this origin, so the
CSP stays at img-src 'self' and no picture is a request to anyone else.
Dimensions are written into build.py's PHOTOS table so every <img> carries
width and height and nothing on the page jumps while a picture loads.
"""

import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "photos")
OUT = os.path.join(HERE, "site", "assets", "photos")

# name, widths to emit, and the focal crop as (left, top, right, bottom) in
# fractions of the master. A crop is here only where the master carries
# something that does not earn its space on the page.
# Widths are what the picture is actually displayed at, doubled for a retina
# screen. Shipping a 1920px file into a 560px slot is the commonest way a page
# gets heavy without looking any better.
PLAN = [
    ("report-on-desk",     [380, 760], None),
    ("opd-corridor",       [340, 680], None),
    ("questions-notebook", [380, 760], None),
    # The founder, for the square slot in the bio on /about. The crop is the
    # top square of the frame: it keeps the token board over his shoulder,
    # which is the half of the picture that says where he is.
    ("founder-portrait",   [220, 440], (0.0, 0.0, 1.0, 0.8217)),
]

QUALITY_JPEG = 80
QUALITY_WEBP = 74


def main():
    if not os.path.isdir(SRC):
        print("photos/ is missing. The masters live there.")
        return 1
    os.makedirs(OUT, exist_ok=True)

    manifest = {}
    worst = 0        # what one viewer on a retina screen actually downloads
    for name, widths, crop in PLAN:
        master = os.path.join(SRC, name + ".jpg")
        if not os.path.exists(master):
            print(f"missing master: photos/{name}.jpg")
            return 1
        im = Image.open(master).convert("RGB")
        if crop:
            w, h = im.size
            im = im.crop((int(crop[0] * w), int(crop[1] * h),
                          int(crop[2] * w), int(crop[3] * h)))
            # A portrait slot is square, and a one-pixel discrepancy from
            # rounding is enough to make the declared height a lie.
            if name.endswith("-portrait"):
                side = min(im.size)
                left = (im.width - side) // 2
                top = (im.height - side) // 2
                im = im.crop((left, top, left + side, top + side))

        # The first width is the one the markup declares, so the browser knows
        # the aspect ratio before a byte of image arrives.
        base_w = widths[0]
        base_h = round(im.height * base_w / im.width)
        manifest[name] = {"width": base_w, "height": base_h}

        for w in widths:
            h = round(im.height * w / im.width)
            resized = im.resize((w, h), Image.LANCZOS)
            suffix = "" if w == widths[0] else f"@{len(widths)}x"
            for ext, kw in (("webp", dict(quality=QUALITY_WEBP, method=6)),
                            ("jpg", dict(quality=QUALITY_JPEG, optimize=True,
                                         progressive=True))):
                path = os.path.join(OUT, f"{name}{suffix}.{ext}")
                resized.save(path, **kw)
                size = os.path.getsize(path)
                if ext == "webp" and w == widths[-1]:
                    worst += size
                print(f"  {os.path.basename(path):32} {w}x{h:<5} {size // 1024:>4}KB")

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    # The number that matters is not every file on disk, it is what one
    # viewer pays. A retina screen takes the widest WebP of each picture, and
    # nobody takes the JPEG unless their browser cannot read WebP.
    print(f"\n{worst / 1024:.0f}KB is what a retina viewer downloads "
          f"across {len(PLAN)} pictures")
    if worst > 500 * 1024:
        print("over budget: more than 500KB of photographs on one page load")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
