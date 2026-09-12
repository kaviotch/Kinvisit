#!/usr/bin/env python3
"""Copy and markup checks. Run after build.py. Exits non-zero on any failure."""

import glob
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")

BANNED_WORDS = [
    "seamless", "holistic", "cutting-edge", "leverage", "peace of mind",
    "loved ones", "journey", "empower", "trusted", "compassionate", "caring",
]

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

fails = []
notes = []


def visible_text(src):
    """Everything a reader actually sees, with entities resolved."""
    s = re.sub(r"<(script|style)\b[\s\S]*?</\1>", " ", src, flags=re.I)
    s = re.sub(r"<!--[\s\S]*?-->", " ", s)
    # attribute values that are read by humans
    attrs = " ".join(re.findall(r'(?:alt|title|content|placeholder|aria-label)="([^"]*)"', s))
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(s + " " + attrs)


def check_tags(path, src):
    body = re.sub(r"<(script|style)\b[\s\S]*?</\1>", "", src, flags=re.I)
    body = re.sub(r"<!--[\s\S]*?-->", "", body)
    body = re.sub(r"<!doctype[^>]*>", "", body, flags=re.I)
    stack = []
    for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*?)(/?)>", body):
        closing, tag, attrs, self_close = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if tag in VOID or self_close:
            continue
        if closing:
            if not stack:
                fails.append(f"{path}: stray </{tag}>")
                return
            if stack[-1] != tag:
                fails.append(f"{path}: </{tag}> closes <{stack[-1]}>")
                return
            stack.pop()
        else:
            stack.append(tag)
    if stack:
        fails.append(f"{path}: unclosed {stack}")


def check_ids(path, src):
    ids = set(re.findall(r'\bid="([^"]+)"', src))
    for ref in re.findall(r'href="#([^"]+)"', src):
        if ref and ref not in ids:
            fails.append(f"{path}: href=#{ref} has no matching id")
    for ref in re.findall(r'aria-(?:labelledby|controls|describedby)="([^"]+)"', src):
        for token in ref.split():
            if token not in ids:
                fails.append(f"{path}: aria reference '{token}' has no matching id")
    for ref in re.findall(r'\bfor="([^"]+)"', src):
        if ref not in ids:
            fails.append(f"{path}: label for='{ref}' has no matching input id")


def check_headings(path, src):
    levels = [int(m) for m in re.findall(r"<h([1-6])\b", src)]
    h1 = levels.count(1)
    if h1 != 1:
        fails.append(f"{path}: {h1} h1 elements, expected exactly 1")
    prev = 0
    for lv in levels:
        if prev and lv > prev + 1:
            fails.append(f"{path}: heading jumps from h{prev} to h{lv}")
        prev = lv


def check_meta(path, src):
    for pattern, label in [
        (r"<title>[^<]{10,}</title>", "title"),
        (r'<meta name="description" content="[^"]{50,}"', "meta description"),
        (r'<link rel="canonical"', "canonical"),
        (r'<meta property="og:image"', "og:image"),
        (r'<html lang="en-IN">', "lang=en-IN"),
        (r'class="skip"', "skip link"),
    ]:
        if not re.search(pattern, src):
            fails.append(f"{path}: missing {label}")


def check_links(path, src):
    internal = set(re.findall(r'href="(/[^"#?]*)"', src))
    for href in internal:
        if href.startswith("/assets/"):
            target = os.path.join(OUT, href.lstrip("/"))
        elif href == "/":
            target = os.path.join(OUT, "index.html")
        else:
            target = os.path.join(OUT, href.strip("/") + ".html")
        if not os.path.exists(target):
            fails.append(f"{path}: link {href} points at nothing ({os.path.basename(target)})")


def check_repo_wide():
    """Part J. No emoji in any file, including comments."""
    emoji = re.compile(r"[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\uFE0F\u2B00-\u2BFF]")
    allow = {"\u2190", "\u2192", "\u2191", "\u2193", "\u2194", "\u2212", "\u2022"}
    for path in sorted(glob.glob(os.path.join(HERE, "**", "*.*"), recursive=True)):
        if "/_render/" in path or "/node_modules/" in path or path.endswith((".png", ".pdf", ".ico")):
            continue
        if not path.endswith((".py", ".js", ".json", ".css", ".html", ".md", ".toml", ".txt")):
            continue
        try:
            body = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for m in emoji.finditer(body):
            if m.group(0) in allow:
                continue
            fails.append(f"{os.path.relpath(path, HERE)}: emoji {m.group(0)!r} at offset {m.start()}")


def check_analytics_privacy():
    """No health free text may reach an analytics provider. The free-text field
    names are the things that must never appear inside a track() call."""
    banned = ["wb-note", "note.value", "what-to-raise", "sh-text", "text.value",
              "raise", "question", "symptom"]
    for path in sorted(glob.glob(os.path.join(HERE, "site", "assets", "js", "*.js"))):
        body = open(path, encoding="utf-8").read()
        for m in re.finditer(r"KV\.track\(([\s\S]{0,320}?)\);", body):
            call = m.group(1)
            for b in banned:
                if b in call:
                    fails.append(f"{os.path.basename(path)}: track() call may carry free text "
                                 f"({b}): {call.strip()[:110]}")


def check_tokens():
    """The design system is only real if it is enforced. tokens.css is the one
    place a colour, a font size, or a font family may be defined."""
    css_dir = os.path.join(OUT, "assets")
    tokens = open(os.path.join(css_dir, "tokens.css"), encoding="utf-8").read()

    declared = set(re.findall(r"(--[a-z0-9-]+):", tokens))
    notes.append(f"tokens: {len(declared)} custom properties declared")

    palette = re.findall(
        r"--(?:paper|paper-deep|warm|sand|ink|accent|accent-ink|withdrawn|substituted|"
        r"on-accent):\s*(#[0-9A-Fa-f]{6})", tokens)
    if len(set(palette)) > 10:
        fails.append(f"tokens.css declares {len(set(palette))} literal colours, the system "
                     f"allows 10: {sorted(set(palette))}")

    styles = open(os.path.join(css_dir, "styles.css"), encoding="utf-8").read()
    # Comments go, except the one marker that grants an exemption, which has
    # to survive so the check below can see it.
    body = re.sub(r"/\*[\s\S]*?\*/",
                  lambda m: "/*decorative-glyph-exempt*/"
                  if "decorative-glyph-exempt" in m.group(0) else "",
                  styles)

    for m in re.finditer(r"#[0-9A-Fa-f]{3,8}\b", body):
        fails.append(f"styles.css: hardcoded colour {m.group(0)} outside tokens.css")

    # rgb()/hsl() literals are allowed only as an alpha of the two palette
    # anchors, which is how ink-on-paper and paper-on-ink are expressed.
    def _triple(name):
        m = re.search(r"--" + name + r":\s*#([0-9A-Fa-f]{6})", tokens)
        if not m:
            return None
        h = m.group(1)
        return " ".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))

    # Read from tokens.css rather than written here, so changing the palette
    # cannot leave a stale literal behind that this check still permits.
    anchors = [t for t in (_triple("ink"), _triple("paper")) if t]
    for m in re.finditer(r"(?:rgb|hsl)a?\(([^)]*)\)", body):
        val = re.sub(r"\s+", " ", m.group(1)).strip()
        if not any(val.startswith(a + " /") for a in anchors):
            fails.append(f"styles.css: colour literal rgb({val}) is not an alpha of "
                         f"ink or paper ({' or '.join(anchors)})")

    # Figtree is variable 300 to 900. Four weights are used and no others:
    # 300 light, 400 reading, 600 labels, 800 headlines and figures.
    for m in re.finditer(r"font-weight:\s*(\d+)", body):
        if m.group(1) not in ("300", "400", "600", "800"):
            fails.append(f"styles.css: font-weight {m.group(1)}, the system uses "
                         f"300, 400, 600 and 800")

    # @font-face has to name the family it is defining. Every other rule in
    # the file must reach the family through a token.
    without_faces = re.sub(r"@font-face\s*\{[^}]*\}", "", body)
    for m in re.finditer(r"font-family:\s*([^;]+);", without_faces):
        val = m.group(1)
        if "var(--font-" in val:
            continue
        fails.append(f"styles.css: font-family {val.strip()} is not a token")

    # ink-40 is 2.97:1 on paper. It is a rule colour. Using it for text is the
    # easiest way to fail AA without noticing.
    for m in re.finditer(r"(?:^|[;{\s])(?:color|fill):\s*var\(--ink-40\)", body):
        fails.append("styles.css: --ink-40 used as a text colour, it is 2.97:1 and rules only")
    paper_triple = _triple("paper") or "255 255 255"
    for m in re.finditer(r"(?:^|[;{\s])(?:color|fill):\s*rgb\("
                         + re.escape(paper_triple) + r" / 0\.(\d+)\)", body):
        if int(m.group(1).ljust(2, "0")) < 55:
            near = body[max(0, m.start() - 200):m.start()]
            if "decorative-glyph-exempt" in near:
                continue
            fails.append(f"styles.css: paper at 0.{m.group(1)} on ink is under 4.5:1")

    banned_fonts = ["Inter", "Roboto", "Arial", "BlinkMacSystemFont", "-apple-system", "Segoe UI"]
    for f in banned_fonts:
        if f in styles or f in tokens:
            fails.append(f"font stack contains a forbidden family: {f}")


def check_staffing_claims():
    """A4. Nothing may promise a clinician we have not hired. Every mention of
    the nursing lead has to sit next to a qualifier saying the role is open."""
    forbidden = [
        "nursing-trained companion",
        "is nursing or paramedic trained",
    ]
    qualifiers = ["once that role is filled", "is hired", "we hire", "not hired", "will meet",
                  "will be", "will review", "not filled", "until our nursing lead", "we have not"]
    for f in sorted(f for f in glob.glob(os.path.join(OUT, "*.html"))
                    if not os.path.basename(f).startswith("_")):
        page = os.path.basename(f)
        text = visible_text(open(f, encoding="utf-8").read())
        low = text.lower()
        for phrase in forbidden:
            if phrase in low:
                fails.append(f"{page}: promises a clinician we have not hired: '{phrase}'")
        for m in re.finditer(r"our nursing lead", low):
            window = low[max(0, m.start() - 220):m.end() + 260]
            if not any(qq in window for qq in qualifiers):
                fails.append(f"{page}: 'our nursing lead' with no open-role qualifier near "
                             f"'{text[max(0, m.start() - 60):m.end() + 60].strip()}'")


def check_price_consistency():
    """Every price on the homepage must match the pricing page exactly."""
    price = re.compile(r"&#8377;([\d,]+)")
    home = set(price.findall(open(os.path.join(OUT, "index.html"), encoding="utf-8").read()))
    pricing = set(price.findall(open(os.path.join(OUT, "pricing.html"), encoding="utf-8").read()))
    orphans = home - pricing
    if orphans:
        fails.append(f"index.html: price(s) {sorted(orphans)} do not appear on pricing.html")


def check_js_budget():
    """Homepage JavaScript, everything it can pull in, under 60KB gzipped."""
    import gzip
    total = 0
    names = ["site.js"]
    home = open(os.path.join(OUT, "index.html"), encoding="utf-8").read()
    mechs = set(re.findall(r'data-mech="([a-z-]+)"', home))
    alias = {"via": "share", "ctxbar": "share", "currency": "pricing", "overseas": "pricing"}
    files = {os.path.join(OUT, "assets", "site.js")}
    for m in mechs:
        files.add(os.path.join(OUT, "assets", "js", alias.get(m, m) + ".js"))
    for f in sorted(files):
        if not os.path.exists(f):
            fails.append(f"index.html: mechanism script missing: {os.path.basename(f)}")
            continue
        total += len(gzip.compress(open(f, "rb").read()))
        names.append(os.path.basename(f))
    notes.append(f"homepage JS: {total / 1024:.1f}KB gzipped across {len(files)} files")
    if total > 60 * 1024:
        fails.append(f"homepage JS budget exceeded: {total / 1024:.1f}KB gzipped, limit 60KB")



def _srgb(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    r, g, b = (_srgb(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ratio(fg, bg):
    a, b = _lum(fg), _lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def check_contrast():
    """Every text colour, measured against every surface it is set on.

    The site alternates between four grounds, so a value is only safe if it
    clears the floor on the darkest of them. Body text is held to 7:1 rather
    than 4.5:1: this audience includes cataracts and a phone held up in Delhi
    daylight. Computed from the hex values, so darkening a token by a shade
    cannot quietly drop a pair under the floor.

    --accent is deliberately not in the text list. It is a fill, and what is
    checked for it is the label that sits on top of it.
    """
    tokens = open(os.path.join(OUT, "assets", "tokens.css"), encoding="utf-8").read()

    def colour(name):
        """A token may be a hex value or an alpha of ink over a surface."""
        m = re.search(r"--" + name + r":\s*#([0-9A-Fa-f]{6})", tokens)
        if m:
            h = m.group(1)
            return ("hex", tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
        m = re.search(r"--" + name + r":\s*rgb\(([\d ]+) / ([0-9.]+)\)", tokens)
        if m:
            base = tuple(int(v) for v in m.group(1).split())
            return ("alpha", (base, float(m.group(2))))
        fails.append(f"tokens.css: --{name} is neither a hex value nor an alpha")
        return None

    surfaces = {}
    for name in ("paper", "paper-deep", "warm", "sand"):
        c = colour(name)
        if c and c[0] == "hex":
            surfaces[name] = c[1]
    if not surfaces:
        return

    def resolve(tok, bg):
        kind, val = tok
        if kind == "hex":
            return val
        base, a = val
        return tuple(base[i] * a + bg[i] * (1 - a) for i in range(3))

    pairs = []
    for name in ("ink", "ink-90", "ink-70", "ink-55", "accent-ink",
                 "withdrawn", "substituted"):
        tok = colour(name)
        if not tok:
            continue
        for sname, s_rgb in surfaces.items():
            pairs.append((f"--{name} on {sname}", resolve(tok, s_rgb), s_rgb, 7.0))

    # Fills carry a label rather than being one.
    accent, on_accent = colour("accent"), colour("on-accent")
    ink = colour("ink")
    if accent and on_accent:
        pairs.append(("--on-accent on --accent", on_accent[1], accent[1], 4.5))
    if ink and on_accent:
        pairs.append(("--on-accent on --ink", on_accent[1], ink[1], 4.5))

    # The three lit values exist only for the ink ground, so they are measured
    # against it and against nothing else. A value derived to read on paper is
    # around 2:1 here, which is the mistake they were added to stop.
    if ink:
        for name in ("withdrawn-lit", "substituted-lit", "accent-lit"):
            tok = colour(name)
            if tok:
                pairs.append((f"--{name} on --ink", tok[1], ink[1], 7.0))

    worst = None
    for label, fg, bg, need in pairs:
        r = _ratio(fg, bg)
        if worst is None or r < worst[1]:
            worst = (label, r)
        if r < need:
            fails.append(f"contrast: {label} is {r:.2f}:1, this site holds it to {need}:1")
    if worst:
        notes.append(f"contrast: {len(pairs)} pairs measured, tightest {worst[0]} "
                     f"at {worst[1]:.2f}:1")

ALLOWED_ORIGINS = {
    "https://kinvisit.in",      # our own canonical
    "https://plausible.io",     # cookieless analytics, named in the cookie policy
    "https://schema.org",       # structured-data vocabulary, not a request
    "https://wa.me",            # the WhatsApp deep link
}


def check_third_parties():
    """No embed, pixel, font host, tag manager, or chat widget may appear
    without a decision. The cookie policy states there are none; this is what
    keeps that sentence true. Adding an origin here means adding it to
    /cookies and to the CSP in netlify.toml as well."""
    for f in sorted(f for f in glob.glob(os.path.join(OUT, "*.html"))
                    if not os.path.basename(f).startswith("_")):
        src = open(f, encoding="utf-8").read()
        page = os.path.basename(f)
        for tag in re.findall(r"<(?:iframe|embed|object)\b[^>]*>", src, re.I):
            fails.append(f"{page}: third-party embed, and /cookies says there are none: {tag[:80]}")
        for origin in set(re.findall(r'(?:src|href|action)="(https?://[a-z0-9.-]+)', src, re.I)):
            if origin not in ALLOWED_ORIGINS:
                fails.append(f"{page}: outside origin {origin} is not in the cookie policy")

    # Supabase is reached by fetch from the portal pages, so it is declared in
    # connect-src rather than as a tag. It must still be named in the policy.
    policy = open(os.path.join(HERE, "netlify.toml"), encoding="utf-8").read()
    cookies = open(os.path.join(OUT, "cookies.html"), encoding="utf-8").read()
    if "supabase.co" in policy and "database behind the portal" not in cookies:
        fails.append("cookies.html: the CSP allows supabase.co but the policy does not mention it")


def check_verification_claims():
    """The site may not claim a companion has been police verified unless
    companions.json records the date. This is the one claim on the site that
    is both checkable and worth lying about, so it is checked."""
    import json
    path = os.path.join(HERE, "content", "companions.json")
    roster = json.load(open(path, encoding="utf-8"))["companions"]
    anyone_verified = any(c.get("policeVerified") for c in roster)
    if anyone_verified:
        return
    for f in sorted(f for f in glob.glob(os.path.join(OUT, "*.html"))
                    if not os.path.basename(f).startswith("_")):
        text = visible_text(open(f, encoding="utf-8").read()).lower()
        for m in re.finditer(r"police (?:verification|verified)", text):
            window = text[max(0, m.start() - 200):m.end() + 200]
            # "will meet before their first booking" is a promise, not a claim.
            if "will meet" in window or "before their first booking" in window:
                continue
            fails.append(f"{os.path.basename(f)}: claims police verification, but no companion in "
                         f"companions.json records a date for it")


REQUIRED_LEGAL = ["privacy.html", "terms.html", "refunds.html", "cookies.html", "consent.html"]


def check_legal_pages():
    """The pages an Indian online seller has to be able to point at, and the
    consent tick that the DPDP Act asks for on anything that collects
    personal data."""
    for name in REQUIRED_LEGAL:
        if not os.path.exists(os.path.join(OUT, name)):
            fails.append(f"missing legal page: {name}")

    home = open(os.path.join(OUT, "index.html"), encoding="utf-8").read()
    for href in ("/privacy", "/terms", "/refunds", "/cookies"):
        if f'href="{href}"' not in home:
            fails.append(f"index.html: no link to {href}, it has to be reachable from every page")

    # Every form that collects personal data needs a real tick, not small print.
    for f in sorted(f for f in glob.glob(os.path.join(OUT, "*.html"))
                    if not os.path.basename(f).startswith("_")):
        src = open(f, encoding="utf-8").read()
        for form in re.findall(r"<form\b[\s\S]*?</form>", src):
            if 'data-netlify="true"' not in form:
                continue
            if 'name="consent"' not in form or 'type="checkbox"' not in form:
                name = re.search(r'name="([^"]+)"', form)
                fails.append(f"{os.path.basename(f)}: form {name.group(1) if name else '?'} "
                             f"collects data with no consent checkbox")
            elif 'required' not in form.split('name="consent"')[1][:200]:
                fails.append(f"{os.path.basename(f)}: the consent checkbox is not required")



def check_photographs():
    """Photographs are the one asset here that is not generated from the
    tokens, so they get their own rules: every one carries alt text that is
    not the caption repeated, declares its own width and height so nothing on
    the page jumps while it loads, and comes from this origin."""
    import json
    manifest_path = os.path.join(OUT, "assets", "photos", "manifest.json")
    if not os.path.exists(manifest_path):
        fails.append("site/assets/photos/manifest.json is missing. Run gen_photos.py.")
        return
    manifest = json.load(open(manifest_path, encoding="utf-8"))

    seen = 0
    for f in sorted(f for f in glob.glob(os.path.join(OUT, "*.html"))
                    if not os.path.basename(f).startswith("_")):
        page = os.path.basename(f)
        src = open(f, encoding="utf-8").read()
        for img in re.findall(r"<img\b[^>]*>", src):
            if "/assets/photos/" not in img:
                continue
            seen += 1
            if not re.search(r'\bwidth="\d+"', img) or not re.search(r'\bheight="\d+"', img):
                fails.append(f"{page}: a photograph has no width and height, so the page will "
                             f"jump when it loads")
            alt = re.search(r'alt="([^"]*)"', img)
            if not alt or len(alt.group(1)) < 30:
                fails.append(f"{page}: a photograph's alt text is missing or too short to "
                             f"describe the picture")
        # A caption that repeats the alt text is read out twice.
        for fig in re.findall(r"<figure[\s\S]*?</figure>", src):
            alt = re.search(r'alt="([^"]*)"', fig)
            cap = re.search(r"<figcaption>([\s\S]*?)</figcaption>", fig)
            if alt and cap and alt.group(1).strip().lower() == cap.group(1).strip().lower():
                fails.append(f"{page}: a caption repeats its alt text word for word")

    # Every variant the markup can ask for has to exist.
    for name in manifest:
        for variant in (f"{name}.webp", f"{name}.jpg", f"{name}@2x.webp", f"{name}@2x.jpg"):
            if not os.path.exists(os.path.join(OUT, "assets", "photos", variant)):
                fails.append(f"photos: {variant} is missing. Run gen_photos.py.")

    notes.append(f"photographs: {seen} on the site, {len(manifest)} masters")


def check_one_mark():
    """One wordmark, drawn once. A second icon drawn somewhere else is how a
    company ends up with two marks that nearly match."""
    mark = os.path.join(OUT, "assets", "wordmark.svg")
    if not os.path.exists(mark):
        fails.append("assets/wordmark.svg is missing. Run gen_assets.py.")
        return
    body = open(mark, encoding="utf-8").read()
    if "<text" in body:
        fails.append("wordmark.svg contains live text. It must be outlines, or it falls back "
                     "to whatever face the reader's machine has.")
    build_src = open(os.path.join(HERE, "build.py"), encoding="utf-8").read()
    if re.search(r'favicon\.svg", "w"', build_src):
        fails.append("build.py writes a second favicon. gen_assets.py owns the mark.")



# Words that tell a family a clinician will be in the room with their parent.
QUALIFIED_ATTENDANT = [
    r"a (?:specialist|nurse|clinician|doctor) (?:attends|will attend|comes)",
    r"(?:specialist|nurse|clinician|clinically qualified)[a-z ]{0,20}(?:attends|attending|"
    r"in the room|at every visit|accompanies)",
    r"our (?:specialists|nurses|clinicians) attend",
    r"qualified companion(?:s)? attend",
    r"(?:nursing|paramedic) qualified companion at every visit",
]


def check_attendant_claims():
    """The site may not describe the person who attends as clinically
    qualified unless companions.json records one.

    This is the claim with the most riding on it. A family choosing whether a
    stranger sits in their parent's consultation is deciding on the strength
    of what that person is, and a false answer is a misleading advertisement
    under the Consumer Protection Act, 2019 as well as a broken promise. The
    switch is clinicallyQualified in content/companions.json: set it true when
    the certificate is on file and this check stops objecting on its own."""
    import json
    roster = json.load(open(os.path.join(HERE, "content", "companions.json"),
                            encoding="utf-8"))["companions"]
    if any(c.get("clinicallyQualified") for c in roster):
        notes.append("attendant: a clinically qualified companion is on the roster")
        return
    notes.append("attendant: no clinically qualified companion on the roster, "
                 "so qualified-attendant copy is blocked")

    for f in sorted(f for f in glob.glob(os.path.join(OUT, "*.html"))
                    if not os.path.basename(f).startswith("_")):
        text = visible_text(open(f, encoding="utf-8").read()).lower()
        for pattern in QUALIFIED_ATTENDANT:
            for m in re.finditer(pattern, text):
                window = text[max(0, m.start() - 200):m.end() + 200]
                # Future tense is a promise, not a claim about today.
                if any(q in window for q in ("will meet", "will be", "we hire", "every companion "
                                             "we hire", "once that role is filled", "not yet",
                                             "have not hired", "is the first hire")):
                    continue
                fails.append(
                    f"{os.path.basename(f)}: says a qualified person attends, but no companion "
                    f"in companions.json has clinicallyQualified set: "
                    f"'{text[max(0, m.start() - 50):m.end() + 50].strip()}'")


def main():
    # Files beginning with an underscore are working documents: the temporary
    # pages the suites write, and design previews that are not part of the
    # site yet. They are not held to the site's rules until they are.
    files = sorted(f for f in glob.glob(os.path.join(OUT, "*.html"))
                   if not os.path.basename(f).startswith("_"))
    if not files:
        print("no html built")
        return 1

    for f in files:
        path = os.path.basename(f)
        src = open(f, encoding="utf-8").read()
        text = visible_text(src)

        for ch, name in [("—", "em dash"), ("–", "en dash")]:
            if ch in text:
                context = [t for t in re.findall(r"[^.!?]*" + ch + r"[^.!?]*", text)][:3]
                fails.append(f"{path}: {name} in copy -> {context}")

        for word in BANNED_WORDS:
            for m in re.finditer(r"\b" + re.escape(word) + r"\b", text, re.I):
                fails.append(f"{path}: banned word '{m.group(0)}' near '{text[max(0,m.start()-40):m.end()+40].strip()}'")

        check_tags(path, src)
        check_ids(path, src)
        check_headings(path, src)
        check_meta(path, src)
        check_links(path, src)

        imgs = re.findall(r"<img\b[^>]*>", src)
        for img in imgs:
            if 'alt="' not in img:
                fails.append(f"{path}: <img> without alt")

        notes.append(f"{path}: {len(text.split())} words")

    check_repo_wide()
    check_tokens()
    check_contrast()
    check_third_parties()
    check_verification_claims()
    check_attendant_claims()
    check_legal_pages()
    check_photographs()
    check_one_mark()
    check_analytics_privacy()
    check_staffing_claims()
    check_price_consistency()
    check_js_budget()

    print("\n".join(notes))
    print()
    if fails:
        print(f"{len(fails)} PROBLEM(S)")
        for f in fails:
            print("  -", f)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
