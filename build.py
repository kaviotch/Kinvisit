#!/usr/bin/env python3
"""
Kinvisit static site builder.

Writes plain .html files into site/. No framework, no client-side router.
Every page is real HTML at a real path and reads correctly with JavaScript off.

    python3 build.py
"""

import json
import os
import re

import content as C
import mechanisms as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")

# ---------------------------------------------------------------- constants

# A1. Canonical URLs must name the domain that actually serves the bytes.
# Netlify sets URL to the site's primary address and CONTEXT to production,
# deploy-preview, or branch-deploy, so a preview build canonicalises to itself
# and tells crawlers to stay away instead of pointing at a domain it is not.
CONTEXT = os.environ.get("CONTEXT", "local")
IS_PRODUCTION = CONTEXT in ("production", "local")
SITE = (os.environ.get("KINVISIT_SITE_URL")
        or os.environ.get("URL")
        or "https://kinvisit.in").rstrip("/")
WA_NUMBER = "918920428806"
WA_TEXT = "Hi%2C%20I%27d%20like%20to%20book%20a%20Kinvisit%20visit%20for%20my%20parent%20in%20Delhi."
WA_LINK = f"https://wa.me/{WA_NUMBER}?text={WA_TEXT}"
PHONE_DISPLAY = "+91 89204 28806"
PHONE_HREF = "+918920428806"
EMAIL = "hello@kinvisit.in"

NAV = [
    ("/record", "The record"),
    ("/pricing", "Pricing"),
    ("/conversations", "Conversations"),
    ("/about", "Who comes"),
    ("/faq", "FAQ"),
]

DISCLAIMER = (
    "Kinvisit is not a medical provider. Our companions document and clarify. "
    "They do not diagnose, prescribe, or advise."
)

# ------------------------------------------------------- verified figures
#
# Every number that appears on this site is listed here with the primary
# source it was checked against. If a figure is not in this block, it does
# not go on the site.
#
# LASI  = Longitudinal Ageing Study in India, Wave 1 (2017-18),
#         n = 31,464 adults aged 60 and above.
#         Morbidity distribution: no morbidity 37.6%, single 30.3%,
#         multimorbidity 32.1%  ->  62.4% have at least one condition,
#         and 32.1 / 62.4 = 51.4% of those have two or more.
#         Source: "The burden of disease-specific multimorbidity among older
#         adults in India and its states: evidence from LASI",
#         BMC Geriatrics, 2023.
#         Living arrangements (60+, n = 30,370): alone 5.1%, spouse and/or
#         others 19.5%, spouse and children 43.5%, children and others 26.7%,
#         others only 5.1%.  Households containing no adult child:
#         5.1 + 19.5 + 5.1 = 29.7%.
#         Source: "Living arrangement of Indian elderly: a predominant
#         predictor of their level of life satisfaction", BMC Geriatrics, 2023.
#
# UNFPA = India Ageing Report 2023. 60+ population 149 million in 2022,
#         projected 347 million by 2050. Share of population 10.5% (2022)
#         rising to 20.8% (2050).

# ---------------------------------------------------------------- the record
#
# One illustrative patient, four visits, twelve weeks apart. Not a real
# patient. Doctors are recorded by role, never by name.

VISITS = [
    dict(
        n=1,
        date="12 March 2026",
        short="12 Mar",
        dept="Endocrinology",
        where="Multi-specialty OPD, South Delhi",
        doctor="Consultant endocrinologist. Name recorded in your copy.",
        asked=[
            ("Her right hand has been swelling since January. Has it ever been mentioned?",
             "No note of it in the file. Doctor examined it, said to keep watching it, ordered no test."),
            ("Are the morning sugars high enough to change anything?",
             "Yes. Metformin doubled from today."),
        ],
        instructions=[
            "Metformin to 1000mg twice daily, from tomorrow morning.",
            "Fasting sugar log to be brought to every visit.",
            "Return in four weeks. Sooner if the swelling spreads above the wrist.",
        ],
        meds=[
            ("Metformin 500mg BD to 1000mg BD", "up", "Increased", "Fasting sugars high through February. HbA1c 8.4%."),
            ("Atorvastatin 10mg OD", "same", "Unchanged", "Continued."),
        ],
        recon="Checked against 3 standing medicines. No interaction flagged.",
        tests=["None ordered."],
        unresolved=[("Right-hand swelling. Doctor advised monitoring. No test ordered.", "open")],
        nxt="09 April 2026 &middot; nephrology referral",
        callout=None,
    ),
    dict(
        n=2,
        date="09 April 2026",
        short="09 Apr",
        dept="Nephrology",
        where="Multi-specialty OPD, South Delhi",
        doctor="Consultant nephrologist. Name recorded in your copy.",
        asked=[
            ("The swelling did not settle. Is this the kidneys?",
             "Renal panel ordered on the spot and read in the room. eGFR 58, which is mild impairment."),
            ("Does the diabetes medicine need to change because of this?",
             "Not yet. Doctor said review Metformin only if eGFR falls below 45."),
        ],
        instructions=[
            "Start Telmisartan 40mg once daily.",
            "Salt restriction discussed.",
            "Repeat renal panel in eight weeks.",
        ],
        meds=[
            ("Telmisartan 40mg OD", "new", "Started", "For blood pressure and renal protection."),
            ("Metformin 1000mg BD", "same", "Held", "Held at current dose. Review point set at eGFR 45."),
        ],
        recon="Checked against 4 standing medicines. Metformin flagged for review if eGFR falls below 45.",
        tests=["Renal function panel. Result: eGFR 58 mL/min/1.73m2, creatinine 1.1 mg/dL."],
        unresolved=[
            ("Swelling now unresolved across two visits.", "open"),
            ("eGFR 58. Recheck due by 04 June.", "open"),
        ],
        nxt="14 May 2026 &middot; endocrinology review",
        callout=None,
    ),
    dict(
        n=3,
        date="14 May 2026",
        short="14 May",
        dept="Endocrinology",
        where="Multi-specialty OPD, South Delhi",
        doctor="Consultant endocrinologist. Name recorded in your copy.",
        asked=[
            ("Does the endocrinologist know about the kidney result?",
             "No. The referral was not on their screen. The companion produced the April report and it was read into this consultation."),
            ("Is a second diabetes medicine safe with the kidney result?",
             "Doctor kept the starting dose low for that reason."),
        ],
        instructions=[
            "Add Glimepiride 1mg once daily, before breakfast.",
            "Watch for low sugar in the late morning.",
            "Bring the repeat renal panel to the next visit.",
        ],
        meds=[
            ("Glimepiride 1mg OD", "new", "Started", "HbA1c improved to 7.6% but still above target."),
        ],
        recon=("Checked against 5 standing medicines. Low-sugar risk noted for Glimepiride alongside "
               "reduced renal clearance. Dose held at 1mg."),
        tests=["None ordered."],
        unresolved=[("Renal panel recheck now two weeks overdue.", "open")],
        nxt="11 June 2026 &middot; orthopaedics",
        callout="The endocrinologist did not know about the April referral. The record did.",
    ),
    dict(
        n=4,
        date="11 June 2026",
        short="11 Jun",
        dept="Orthopaedics",
        where="Multi-specialty OPD, South Delhi",
        doctor="Consultant orthopaedic surgeon. Name recorded in your copy.",
        asked=[
            ("Six weeks of right knee pain. What is the plan?",
             "A course of oral anti-inflammatories was proposed at the start of the consultation."),
            ("She had a kidney result in April. Does that change the plan?",
             "Yes. The companion produced the eGFR 58 result. The oral drug was withdrawn and a topical gel prescribed instead."),
        ],
        instructions=[
            "Do not start the oral anti-inflammatory.",
            "Apply diclofenac gel twice daily to the right knee.",
            "Repeat renal panel booked for 24 June.",
        ],
        meds=[
            ("Diclofenac 50mg BD, oral", "stop", "Withdrawn", "Withdrawn on renal grounds. eGFR 58 recorded in April."),
            ("Diclofenac gel, topical BD", "new", "Substituted", "Local action, minimal renal load."),
        ],
        recon=("Companion produced the eGFR 58 result from the April nephrology visit. "
               "Oral anti-inflammatory withdrawn on renal grounds and a topical substituted."),
        tests=["Renal function panel ordered. Booked for 24 June."],
        unresolved=[("eGFR recheck ordered and booked for 24 June.", "resolved")],
        nxt="09 July 2026 &middot; nephrology, with the June panel carried",
        callout="The surgeon had no access to the April renal panel. The record did.",
    ),
]

# M14. The desk's three pickers. Departments are the specialty list already
# offered on /book, so a companion sees the same words a family typed. The
# hospitals are content/hospitals.json, grouped by the areas declared in it,
# so the desk and the coverage checker can never drift apart. The questions
# are the ones a companion is there to ask when nobody in the family can.

DESK_DEPARTMENTS = [
    "Cardiology", "Dermatology", "Endocrinology", "ENT", "Gastroenterology",
    "General medicine", "General surgery", "Geriatrics", "Gynaecology",
    "Nephrology", "Neurology", "Oncology", "Ophthalmology", "Orthopaedics",
    "Psychiatry", "Pulmonology", "Rheumatology", "Urology",
]

DESK_QUESTIONS = [
    ("Medicines", [
        "Does this new medicine interact with anything she is already taking?",
        "Should any medicine she is on now be stopped or reduced?",
        "Is this dose safe given her kidney and liver results?",
        "What do we do if a dose is missed?",
        "How long is she meant to stay on this?",
    ]),
    ("The symptom we came about", [
        "This has been going on since last month. Is there a note of it in the file?",
        "Could this be a side effect of something she is already taking?",
        "What would make this urgent enough to come back sooner?",
    ]),
    ("Tests", [
        "What is this test looking for, and when do we get the result?",
        "Who reads the result to us, and how?",
        "Is there an earlier test that should be repeated today?",
    ]),
    ("The other doctors", [
        "Does her other specialist know about this change?",
        "Should we bring the last report from the other department?",
        "Which doctor is holding the whole picture?",
    ]),
    ("Before we leave", [
        "When is the next visit, and with whom?",
        "What should we watch for at home before then?",
        "Who do we call if something changes at night?",
    ]),
]


MED_TABLE = [
    ("Metformin",         ["1000mg BD", "1000mg BD", "1000mg BD", "1000mg BD"], []),
    ("Atorvastatin",      ["10mg OD", "10mg OD", "10mg OD", "10mg OD"], []),
    ("Telmisartan",       ["", "40mg OD", "40mg OD", "40mg OD"], [("newly", 1)]),
    ("Glimepiride",       ["", "", "1mg OD", "1mg OD"], [("newly", 2)]),
    ("Diclofenac, oral",  ["", "", "", "Withdrawn"], [("hit", 3)]),
    ("Diclofenac, gel",   ["", "", "", "Applied BD"], [("subbed", 3)]),
]

# ------------------------------------------------------------------ chrome


# F3. The whole stylesheet is inlined. It is 11KB gzipped, so a separate file
# would cost a round trip on a high latency mobile connection to save less than
# it costs, and inlining removes every render-blocking request from the page.
# The font is preloaded and swaps in, so nothing on the critical path is remote.

def _minify_css(text):
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{};,])\s*", r"\1", text)
    return text.replace(";}", "}").strip()


def _read(*parts):
    with open(os.path.join(OUT, "assets", *parts), encoding="utf-8") as f:
        return f.read()


# tokens.css must come first: it defines every value styles.css consumes.
CSS = _minify_css(_read("tokens.css") + "\n" + _read("styles.css"))



# ---------------------------------------------------------------- photographs
#
# Four pictures, each doing something the copy cannot. The alt text describes
# what is in the frame for someone who cannot see it, and never repeats the
# caption sitting next to it, which a screen reader would then read twice.

with open(os.path.join(OUT, "assets", "photos", "manifest.json"), encoding="utf-8") as _f:
    PHOTO_SIZES = json.load(_f)

PHOTOS = {
    "founder-opd": (
        "Kunal Jain sitting in a hospital outpatient waiting area, writing in a notebook. "
        "Other people wait in the rows behind him."),
    "report-on-desk": (
        "A printed Kinvisit consultation record lying on a wooden desk beside reading glasses "
        "and a pen. The visible sections are the questions asked, the instructions given, and "
        "the medication table."),
    "opd-corridor": (
        "A Delhi outpatient department at capacity. Every seat in the waiting rows is taken, a "
        "queue stands along the corridor, and an overhead board lists token numbers against "
        "consultation room numbers."),
    "questions-notebook": (
        "A notebook page headed with a department and a date, listing ten numbered questions to "
        "put to the doctor, with a checklist of documents to carry and a note of the visit's "
        "main goal."),
}


def photo(name, caption=None, cls="", loading="lazy"):
    """One picture, WebP first with a JPEG behind it, both from this origin.

    width and height are always written out. Without them the page reflows when
    each picture arrives, and on a slow connection that is the reader losing
    their place in the middle of a sentence."""
    alt = PHOTOS[name]
    size = PHOTO_SIZES[name]
    fig_cls = f"shot {cls}".strip()
    cap = f'<figcaption>{caption}</figcaption>' if caption else ""
    return f"""<figure class="{fig_cls}">
  <picture>
    <source type="image/webp" srcset="/assets/photos/{name}.webp 1x, /assets/photos/{name}@2x.webp 2x">
    <img src="/assets/photos/{name}.jpg"
         srcset="/assets/photos/{name}.jpg 1x, /assets/photos/{name}@2x.jpg 2x"
         width="{size['width']}" height="{size['height']}"
         loading="{loading}" decoding="async" alt="{alt}">
  </picture>
  {cap}
</figure>"""



def _read_mark():
    with open(os.path.join(OUT, "assets", "wordmark.svg"), encoding="utf-8") as f:
        return f.read().strip()


# Inlined rather than linked: it is 2.8KB, it appears on every page, and a
# separate request for a logo is a request that can fail and leave the header
# empty. currentColor lets one file serve the ink header and the paper footer.
WORDMARK = _read_mark().replace('fill="#14140F"', 'fill="currentColor"')


def wa_icon():
    return (
        '<svg class="wa-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
        '<path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.5.1-.6.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.5s-.5-1.3-.7-1.7-.4-.4-.5-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4 5 5 0 0 0 3 .6 2.6 2.6 0 0 0 1.7-1.2 2.1 2.1 0 0 0 .1-1.2z"/>'
        "</svg>"
    )


def nav(current):
    def link(href, label):
        mark = ' aria-current="page"' if href == current else ""
        return f'<a href="{href}"{mark}>{label}</a>'

    links = "".join(link(href, label) for href, label in NAV)
    menu_links = "".join(f'<a href="{href}">{label}</a>' for href, label in NAV)
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="nav">
  <div class="nav-in">
    <a class="brand" href="/">{WORDMARK}</a>
    <nav class="nav-links" aria-label="Primary">{links}</nav>
    <div class="nav-cta">
      <a class="nav-login" href="/portal">Sign in</a>
      <a class="btn btn-ghost btn-sm" href="{WA_LINK}" rel="noopener">{wa_icon()}WhatsApp</a>
      <a class="btn btn-primary btn-sm" href="/book">Book a visit</a>
    </div>
    <button class="burger" id="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="menu"><span></span></button>
  </div>
</header>
<div class="menu" id="menu" hidden>
  {menu_links}
  <a href="/portal">Sign in to the portal</a>
  <a href="/book">Book a visit</a>
  <div class="menu-foot">
    <a href="{WA_LINK}" rel="noopener">WhatsApp {PHONE_DISPLAY}</a>
    <a href="mailto:{EMAIL}">{EMAIL}</a>
  </div>
</div>"""


def footer():
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <div class="foot-brand">{WORDMARK}</div>
        <p style="max-width:34ch">Someone sits in your parent's consultation, writes down what was said, and sends it to you the same day.</p>
        <p><a href="{WA_LINK}" rel="noopener">WhatsApp {PHONE_DISPLAY}</a><br>
           <a href="mailto:{EMAIL}">{EMAIL}</a><br>
           Delhi NCR</p>
      </div>
      <div>
        <h2>The service</h2>
        <div class="foot-links">
          <a href="/record">The record</a>
          <a href="/pricing">Pricing</a>
          <a href="/hospitals">Where we go</a>
          <a href="/conversations">Difficult conversations</a>
          <a href="/book">Book a visit</a>
        </div>
      </div>
      <div>
        <h2>The company</h2>
        <div class="foot-links">
          <a href="/about">Who comes</a>
          <a href="/faq">FAQ</a>
          <a href="/promise">The same-day promise</a>
          <a href="/consent">Your parent's consent</a>
          <a href="/proof">Research and market</a>
          <a href="/portal">Sign in to the portal</a>
        </div>
      </div>
    </div>
    <div class="foot-bottom">
      <p class="disclaimer">{DISCLAIMER}</p>
      {business_block(compact=True)}
      <div class="foot-legal">
        <a href="/privacy">Privacy</a>
        <a href="/terms">Terms</a>
        <a href="/refunds">Cancellation and refunds</a>
        <a href="/cookies">Cookies</a>
      </div>
      <p>&copy; 2026 Kinvisit</p>
    </div>
  </div>
</footer>
<a class="fab" href="{WA_LINK}" rel="noopener">{wa_icon()}WhatsApp us</a>"""



def business_block(compact=False):
    """The seller's identity. The Consumer Protection (E-Commerce) Rules 2020
    require a legal name, a principal geographic address, and a named contact
    for grievances to be displayed. content/business.json ships empty and this
    renders nothing until it is filled, because an invented address on a legal
    page is worse than a missing one."""
    b = C.BUSINESS
    if not b.get("published"):
        return ""
    a = b["registeredAddress"]
    where = ", ".join(x for x in [a["line1"], a["line2"], a["city"], a["state"], a["pin"]] if x)
    g = b["grievanceOfficer"]
    rows = [("Registered name", M.esc(b["legalName"]) +
             (f' ({M.esc(b["entityType"])})' if b.get("entityType") else ""))]
    if where:
        rows.append(("Registered address", M.esc(where)))
    if b.get("udyamNumber"):
        rows.append(("Udyam registration", M.esc(b["udyamNumber"])))
    if b.get("gstin"):
        rows.append(("GSTIN", M.esc(b["gstin"])))
    if g.get("name"):
        contact = M.esc(g["name"])
        if g.get("email"):
            contact += f' &middot; <a href="mailto:{M.esc(g["email"])}">{M.esc(g["email"])}</a>'
        if g.get("phone"):
            contact += " &middot; " + M.esc(g["phone"])
        rows.append(("Grievance officer", contact))
    cells = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
    cls = "biz biz-compact" if compact else "biz"
    return f'<dl class="{cls}">{cells}</dl>'



# ------------------------------------------------------------------ hero rail
#
# Every hero on this site sets its headline to 15ch and its lede to 42ch, on
# purpose: that is what makes them readable. The cost is a third of the page
# left empty to the right of every opening, on eighteen pages.
#
# The rail fills it with the thing a reader actually wants at the top of a
# page, which is orientation: what this page is, in four lines they can take
# in without reading the prose. It is never decoration. If a page has nothing
# true to put here, it gets no rail.

def hero_rail(items, label="At a glance", shot=None, caption=None, stamp=None):
    """The rail, and optionally the photograph that sits above it.

    The rail alone left a column of empty paper down the right of every
    opening. A picture fills it with the thing the page is about, and the
    stamp is the kind of mark that ends up on real hospital paperwork."""
    rows = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in items)
    pic = ""
    if shot:
        mark = f'<span class="stamp">{stamp}</span>' if stamp else ""
        cap = f'<figcaption>{caption}</figcaption>' if caption else ""
        # The picture is a column beside the text, not a block inside the
        # band. Beside it, it stretches to whatever height the text is, so
        # neither a long opening nor a short one leaves a hole.
        pic = (f'<figure class="hero-shot">'
               f'<span class="rail-frame">{photo_img(shot)}{mark}</span>{cap}</figure>')
    return (f'{pic}<aside class="hero-rail" aria-label="{label}">'
            f'<dl>{rows}</dl></aside>')


def photo_img(name):
    """Just the picture element, for places that supply their own frame."""
    alt = PHOTOS[name]
    size = PHOTO_SIZES[name]
    return (f'<picture>'
            f'<source type="image/webp" srcset="/assets/photos/{name}.webp 1x,'
            f' /assets/photos/{name}@2x.webp 2x">'
            f'<img src="/assets/photos/{name}.jpg"'
            f' srcset="/assets/photos/{name}.jpg 1x, /assets/photos/{name}@2x.jpg 2x"'
            f' width="{size["width"]}" height="{size["height"]}"'
            f' loading="lazy" decoding="async" alt="{alt}">'
            f'</picture>')


def _with_rail(body, rail):
    """Put the rail in the hero without every page having to know how.

    The heroes are all one shape, so the wrap becomes a two column grid and
    the rail is appended inside it. Done here rather than in eighteen places
    so the structure cannot drift page by page."""
    if not rail:
        return body
    m = re.search(r'(<section class="hero">\s*\n  <div class="wrap)([^"]*)(">)', body)
    if not m:
        return body
    # The wrap's own closing tag is the first one at its indent level. A hero
    # can hold a second wrap after it (/record does), and closing on the last
    # one would pull that into the grid.
    close = body.index("\n  </div>", m.end())
    inner = body[m.end():close]
    return (body[:m.start()] + m.group(1) + " hero-grid" + m.group(3)
            + '\n    <div class="hero-main' + m.group(2) + '">'
            + inner + "\n    </div>\n    " + rail + body[close:])


def page(path, title, desc, body, current=None, noindex=False, jsonld=None, og_type="website",
         scripts=(), analytics=True, chrome=True, rail=None):
    """Write one real HTML file at a real path."""
    body = _with_rail(body, rail)
    canonical = SITE + ("" if path == "/" else path)
    fname = "index.html" if path == "/" else path.strip("/") + ".html"
    if noindex or not IS_PRODUCTION:
        robots = '<meta name="robots" content="noindex,follow">\n  '
    else:
        robots = ""
    ld = f'\n<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    # A page behind a login does not tell an analytics provider that it was
    # opened. Plausible is cookieless and takes no free text, but the fact of
    # a family reading their medical record is itself the sensitive part.
    plausible = ('\n  <script defer data-domain="kinvisit.in" '
                 'src="https://plausible.io/js/script.tagged-events.js"></script>') if analytics else ""
    # defer scripts run in document order, so the library is always ready
    # before site.js boots a mechanism that needs it.
    pre = "".join(f'<script src="{src}" defer></script>\n' for src in scripts)
    slug = "home" if path == "/" else path.strip("/")
    # A page with no site chrome gets no marketing bar either. Asking someone
    # to book a visit on the page where they sign in to read a medical record
    # is the wrong voice in the wrong place.
    ctxbar = ("" if (not chrome or slug in ("book", "privacy", "terms", "404", "thanks"))
              else M.context_bar(SITE))

    html = f"""<!doctype html>
<html lang="en-IN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {robots}<title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canonical}">

  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Kinvisit">
  <meta property="og:locale" content="en_IN">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE}/assets/og-report.png">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="A Kinvisit consultation report showing an oral anti-inflammatory withdrawn because of a kidney result from a previous visit.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{SITE}/assets/og-report.png">

  <meta name="theme-color" content="#FCFBF9">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/assets/favicon.png" sizes="96x96">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">

  <link rel="preload" href="/assets/fonts/figtree.woff2" as="font" type="font/woff2" crossorigin>
  <style>{CSS}</style>

{plausible}{ld}
</head>
<body data-page="{slug}">
{M.share_banner() if chrome else ""}
{nav(current) if chrome else portal_bar()}
<main id="main">
{body}
</main>
{footer() if chrome else portal_foot()}
{ctxbar}
{pre}<script src="/assets/site.js" defer></script>
</body>
</html>
"""
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(html)
    return fname


# ------------------------------------------------------------ render parts


def med_pill(name, state, label):
    semantic = {"Withdrawn": " med-withdrawn", "Substituted": " med-substituted"}
    return (f'<span class="pill {state}{semantic.get(label, "")}">'
            f'<span class="tag">{label}</span><span class="dose">{name}</span></span>')



def visit_ref(v):
    """A reference a family can quote back at us on the phone.

    Derived from the visit rather than stored, so it cannot drift from the
    record it names: year, day and month, department, and the visit number.
    A document that cannot be cited is a web page."""
    day, month, year = v["date"].split()
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    mm = months.index(month) + 1
    dept = "".join(ch for ch in v["dept"].upper() if ch.isalpha())[:4]
    return f"KV/{year}/{mm:02d}{int(day):02d}/{dept}/{v['n']:02d}"


def render_visit(v):
    """One consultation report, rendered the way the family receives it."""
    asked = "".join(
        f'<div class="qa"><p class="q">{q}</p><p class="a">{a}</p></div>'
        for q, a in v["asked"]
    )
    instructions = "".join(f"<li>{i}</li>" for i in v["instructions"])
    pills = "".join(med_pill(n, s, l) for n, s, l, _ in v["meds"])
    why = "".join(
        f'<p class="fine" style="margin-top:8px"><strong>{n.split(",")[0]}:</strong> {w}</p>'
        for n, s, l, w in v["meds"]
    )
    tests = "".join(f"<li>{t}</li>" for t in v["tests"])
    flags = "".join(
        f'<div class="flag {s}"><span class="d" aria-hidden="true"></span><span>{t}</span></div>'
        for t, s in v["unresolved"]
    )
    callout = (
        f'<div class="vp-callout">{v["callout"]}</div>' if v.get("callout") else ""
    )

    return f"""<article class="visit-panel" id="visit-{v['n']}" aria-labelledby="visit-{v['n']}-h">
  <div class="vp-letterhead">
    <div class="vp-mark">{WORDMARK}</div>
    <dl class="vp-ref">
      <div><dt>Document</dt><dd>Consultation record</dd></div>
      <div><dt>Reference</dt><dd>{visit_ref(v)}</dd></div>
      <div><dt>Issued</dt><dd>{v['date']}</dd></div>
    </dl>
  </div>
  <div class="vp-head">
    <h2 id="visit-{v['n']}-h">Visit {v['n']}. {v['dept']}</h2>
    <span class="date">{v['date']}</span>
  </div>
  <div class="vp-field">
    <h3>Seen at</h3>
    {M.annotation_markup("Seen at", f"{v['n']}-seen-at")}
    <p>{v['where']}<br>{v['doctor']}</p>
  </div>
  <div class="vp-field">
    <h3>What the family asked, and what came back</h3>
    {M.annotation_markup("What the family asked, and what came back", f"{v['n']}-what-the-family-asked-and-what-came-back")}
    {asked}
  </div>
  <div class="vp-field">
    <h3>Instructions, as given</h3>
    {M.annotation_markup("Instructions, as given", f"{v['n']}-instructions-as-given")}
    <ul class="list plain">{instructions}</ul>
  </div>
  <div class="vp-field">
    <h3>Medication</h3>
    {M.annotation_markup("Medication", f"{v['n']}-medication")}
    <div class="pill-row">{pills}</div>
    {why}
    <p class="fine" style="margin-top:12px"><strong>Reconciliation.</strong> {v['recon']}</p>
  </div>
  <div class="vp-field">
    <h3>Tests</h3>
    {M.annotation_markup("Tests", f"{v['n']}-tests")}
    <ul class="list plain">{tests}</ul>
  </div>
  <div class="vp-field">
    <h3>Unresolved</h3>
    {M.annotation_markup("Unresolved", f"{v['n']}-unresolved")}
    {flags}
  </div>
  <div class="vp-field">
    <h3>Next visit</h3>
    {M.annotation_markup("Next visit", f"{v['n']}-next-visit")}
    <p>{v['nxt']}</p>
  </div>
  {callout}
  <div class="vp-sign">
    <div class="vp-sign-line">
      <span class="vp-sign-name">Signed by the attending companion</span>
      <span class="vp-sign-role">Name recorded in your copy</span>
    </div>
    <p class="vp-sign-note">Kinvisit does not diagnose, prescribe, or advise. Every clinical
      decision on this record was made by the treating doctor.</p>
  </div>
</article>"""


EMPTY_CELL = '<span aria-hidden="true">&middot;</span><span class="vh">not prescribed</span>'


def render_med_table():
    head = "".join(
        f'<th scope="col">Visit {i + 1}<br>{VISITS[i]["short"]}</th>' for i in range(4)
    )
    rows = ""
    for name, cells, marks in MED_TABLE:
        mark_at = {i: cls for cls, i in marks}
        tds = ""
        for i, cell in enumerate(cells):
            cls = mark_at.get(i, "") if cell else "none"
            label = f'Visit {i + 1} &middot; {VISITS[i]["short"]}'
            attr = f' class="{cls}"' if cls else ""
            tds += (f'<td{attr} data-v="{label}">'
                    f'{cell if cell else EMPTY_CELL}</td>')
        rows += f'<tr><th scope="row">{name}</th>{tds}</tr>'
    return f"""<div class="table-scroll" tabindex="0" role="region" aria-label="Medication history across four visits">
  <table class="med">
    <caption class="vh">Medicines recorded at each of four consultations</caption>
    <thead><tr><th scope="col">Medicine</th>{head}</tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
<p class="scroll-hint fine">Scroll the table sideways to see all four visits.</p>"""


def visit_tabs():
    tabs = "".join(
        f'<a class="visit-tab" href="#visit-{v["n"]}">'
        f'<span class="vn">Visit {v["n"]}</span>'
        f'<span class="vd">{v["short"]}</span>'
        f'<span class="vs">{v["dept"]}</span></a>'
        for v in VISITS
    )
    return f'<div class="visits" id="visitTabs">{tabs}</div>'


# ------------------------------------------------------------ shared blocks

FAQ_ITEMS = [
    ("What if my parent does not want a stranger in the room?",
     "The companion is introduced as your family's representative, not a stranger, and waits outside "
     "if your parent asks. Most parents settle by the second visit."),
    ("What if the doctor will not engage with the companion?",
     "Companions document and clarify. They never advise, and they never argue. The room stays "
     "entirely in the doctor's control, which is why doctors rarely object."),
    ("Who actually turns up?",
     "One named companion, and the same one at every visit. They are not clinically qualified "
     "today, because we have not hired our nursing lead yet and we will not describe a standard "
     "we cannot staff. Who they are, the standard every companion will meet before their first "
     "booking, and the roster as it grows are all on the "
     "<a href=\"/about\">who comes page</a>."),
    ("What language does the companion speak?",
     "Hindi and English. If your parent is more comfortable in another language, tell us when you "
     "book and we will match where we can."),
    ("What if the appointment runs four hours?",
     "The visit is a flat rate however long the hospital takes. There is no hourly extension charge, "
     "because hospital queues are not your fault."),
    ("Can I be on a call during the consultation?",
     "If the doctor permits it, yes. Many do not, which is exactly why the written record exists. "
     "Ask us when you book."),
    ("My parent's doctor is at a small clinic, not a large hospital. Does that work?",
     "Yes. We accompany at any hospital, clinic, or diagnostic centre in Delhi NCR."),
    ("I live abroad. How do I pay and how do I reach you?",
     "You can pay by international card or UPI. We answer on WhatsApp, and we schedule calls to your "
     "timezone, not ours. Tell us where you are and we will work around it."),
    ("Is our medical data safe?",
     "The record is held under Digital Personal Data Protection Act 2023 safeguards and shared only "
     "with the family that pays for it. We take no commission from hospitals or labs, so there is "
     "nobody else to share it with. Our <a href=\"/privacy\">privacy policy</a> sets out what we "
     "hold and how you delete it."),
    ("What if the report does not arrive?",
     "You know within a day, and that visit is not billed. The deliverable is countable on purpose."),
    ("Which cities do you cover?",
     "Delhi NCR today. Hyderabad is the second city once the Delhi book is proven."),
    ("Can I cancel anytime?",
     "Yes. Month to month, no lock-in and no exit fee."),
]


def faq_block(items):
    out = '<div class="faq">'
    for q, a in items:
        out += f"""<details>
  <summary>{q}</summary>
  <div class="ans">{a}</div>
</details>"""
    return out + "</div>"


def faq_jsonld(items):
    import json
    entries = [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)},
        }
        for q, a in items
    ]
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entries})


SCOPE_BLOCK = """<div class="two-col">
  <div class="does yes">
    <h3>Does</h3>
    <ul class="list yes">
      <li>Arrives with your questions written down and asks them</li>
      <li>Records instructions and dosages exactly as given</li>
      <li>Reconciles the new prescription against every standing medicine</li>
      <li>Flags what is unresolved and carries it to the next visit</li>
      <li>Carries prior reports and results to the next doctor</li>
    </ul>
  </div>
  <div class="does no">
    <h3>Does not</h3>
    <ul class="list no">
      <li>Give medical advice or a second opinion</li>
      <li>Change or suggest a dose</li>
      <li>Overrule or argue with the treating doctor</li>
      <li>Consent to procedures on the family's behalf</li>
      <li>Share the record with anyone but the paying family</li>
    </ul>
  </div>
</div>"""

PLANS_BLOCK = f"""<div class="plans">
  <div class="plan">
    <span class="per">Per month</span>
    <span class="amt">&#8377;2,500</span>
    <ul>
      <li>One attended consultation</li>
      <li>Written report the same day</li>
      <li>Medicines tracked and reconciled</li>
      <li>Health record maintained across visits</li>
    </ul>
    <a class="btn btn-ghost btn-block" href="/book">Request a visit</a>
  </div>
  <div class="plan feature">
    <span class="flag-lbl">Most families</span>
    <span class="per">Per month</span>
    <span class="amt">&#8377;4,500</span>
    <ul>
      <li>Two attended consultations</li>
      <li>Diagnostics and labs accompanied</li>
      <li>Priority scheduling</li>
      <li>Everything in the lower plan</li>
    </ul>
    <a class="btn btn-primary btn-block" href="/book">Request a visit</a>
  </div>
  <div class="plan">
    <span class="per">Per extra visit</span>
    <span class="amt">&#8377;1,800</span>
    <ul>
      <li>Any visit beyond the plan</li>
      <li>Flat rate, however long the hospital takes</li>
      <li>No hourly extension charge</li>
      <li>No plan required to book one</li>
    </ul>
    <a class="btn btn-ghost btn-block" href="/book">Request a visit</a>
  </div>
</div>"""

GUARANTEE_BLOCK = """<div class="guarantee">
  <p><strong>If the report does not reach you the same day, that visit is not billed.</strong></p>
  <p>The deliverable is countable on purpose.</p>
</div>"""

ATTENDANT_BLOCK = """<div class="prose">
  <h2>An attendant costs less. Here is what the difference buys.</h2>
  <p>An informal attendant gets your parent to the hospital and home again. That is a transport and
     mobility job, and around &#8377;1,500 a visit is a fair price for it.</p>
  <p><strong>Kinvisit does a different job.</strong></p>
  <p>The companion sits inside the consultation rather than waiting outside it. They arrive with
     your questions written down. They reconcile the new prescription against every medicine your
     parent already takes, which is where the real risk sits. And they leave behind a dated written
     record the next doctor can read.</p>
  <p>Every companion we hire will be nursing or paramedic qualified. The companion attending
     today is not, which is why that reconciliation is a written
     comparison against the standing list rather than a clinical opinion, and why
     <a href="/about">we say so on the page about who comes</a>.</p>
  <p>If your parent needs a lift, hire an attendant. If nobody in your family knows what the last
     four doctors actually said, that is the job we do.</p>
</div>"""

AFTER_BLOCK = """<div class="prose">
  <h2>The report is not the end of the visit.</h2>
</div>
<div class="grid g2" style="margin-top:26px">
  <div class="card">
    <h3>Something needs attention now</h3>
    <p style="color:var(--ink-soft);font-size:.96rem;margin:0">The companion raises it with the
      hospital's own staff there and then, and calls you from the corridor. We do not wait for the
      report.</p>
  </div>
  <div class="card">
    <h3>The new prescription conflicts</h3>
    <p style="color:var(--ink-soft);font-size:.96rem;margin:0">We flag it in writing, tell you
      exactly what to ask, and tell you which doctor to ask.</p>
  </div>
  <div class="card">
    <h3>Something is left unresolved</h3>
    <p style="color:var(--ink-soft);font-size:.96rem;margin:0">It is carried into the question list
      for the next appointment automatically. Nothing gets dropped between specialists.</p>
  </div>
  <div class="card">
    <h3>You have a question afterwards</h3>
    <p style="color:var(--ink-soft);font-size:.96rem;margin:0">Call us about any report for as long
      as you are with us. There is no per-question charge.</p>
  </div>
</div>
<p class="prose" style="margin-top:24px;color:var(--ink-soft)"><strong>What we do not do:</strong>
  diagnose, prescribe, change a dose, or give a second opinion. We make sure nothing said in that
  room disappears.</p>"""

HOSPITAL_OPTIONS = "".join(
    f'<option value="{h["name"]}"></option>' for h in C.HOSPITALS["hospitals"]
)


def _person(x, y, cls="body"):
    return (f'<circle class="{cls}" cx="{x}" cy="{y}" r="9"/>'
            f'<path class="{cls}" d="M{x-17} {y+30}a17 17 0 0 1 34 0z"/>')


# The consultation room, drawn rather than described. Two SVGs rather than one
# scaled down, because a 760 wide diagram shrunk to a phone makes 4px labels.
ROOM_SVG = f"""<svg class="room-figure room-wide" viewBox="0 0 760 250" role="img"
  aria-label="A solid box containing the doctor and your parent, and a separate dashed box containing the family who pays. The line between them is broken.">
  <rect class="solid"  x="1"   y="34" width="330" height="200"/>
  <rect class="dashed" x="471" y="34" width="288" height="200"/>
  <text class="lbl"     x="14"  y="22">The consultation room &#183; 8 minutes</text>
  <text class="lbl lbl-out" x="484" y="22">Another city &#183; another country</text>
  {_person(110, 118)}<text class="lbl" x="110" y="182" text-anchor="middle">Doctor</text>
  {_person(232, 118)}<text class="lbl" x="232" y="182" text-anchor="middle">Your parent</text>
  {_person(615, 118, "body-out")}<text class="lbl lbl-out" x="615" y="182" text-anchor="middle">The family who pays</text>
  <text class="lbl" x="401" y="126" text-anchor="middle">Nothing leaves</text>
  <line class="gap-line" x1="339" y1="152" x2="379" y2="152"/>
  <line class="gap-line" x1="423" y1="152" x2="463" y2="152"/>
</svg>
<svg class="room-figure room-tall" viewBox="0 0 340 470" role="img"
  aria-label="A solid box containing the doctor and your parent, and a separate dashed box containing the family who pays. The line between them is broken.">
  <rect class="solid"  x="1" y="26"  width="338" height="196"/>
  <rect class="dashed" x="1" y="308" width="338" height="152"/>
  <text class="lbl"     x="14" y="16">The consultation room &#183; 8 minutes</text>
  <text class="lbl lbl-out" x="14" y="298">Another city &#183; another country</text>
  {_person(96, 104)}<text class="lbl" x="96" y="170" text-anchor="middle">Doctor</text>
  {_person(240, 104)}<text class="lbl" x="240" y="170" text-anchor="middle">Your parent</text>
  {_person(170, 378, "body-out")}<text class="lbl lbl-out" x="170" y="442" text-anchor="middle">The family who pays</text>
  <text class="lbl" x="170" y="262" text-anchor="middle">Nothing leaves</text>
  <line class="gap-line" x1="170" y1="230" x2="170" y2="248"/>
  <line class="gap-line" x1="170" y1="276" x2="170" y2="294"/>
</svg>"""


PERSON_SVG = ('<svg class="glyph" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
              '<circle cx="12" cy="7" r="4"/><path d="M2.6 22a9.4 9.4 0 0 1 18.8 0z"/></svg>')

# C1. Today's reality first, framed as the offer. The standard we are building
# toward comes second and is written in the future tense, because writing it in
# the present tense and then disclosing that nobody has been hired reads as a
# bait and switch, which is what the previous ordering did.

_TODAY_BODY = "".join(f"<p>{para}</p>" for para in C.TODAY_BODY)
_TODAY_PRACTICAL = "".join(f"<li>{i}</li>" for i in C.TODAY_PRACTICAL)
_FUTURE_STANDARD = "".join(f"<li>{i}</li>" for i in C.FUTURE_STANDARD)

def who_block(photo=True, roster=True):
    return f"""<div class="prose">
  <p class="eyebrow">Who comes</p>
  <h2>{C.TODAY_HEADING}</h2>
  <div class="lede">{_TODAY_BODY}</div>
</div>

<div class="two-col" style="margin-top:26px">
  <div class="does yes">
    <h3>What that means for you today</h3>
    <ul class="list yes">{_TODAY_PRACTICAL}</ul>
  </div>
  <div class="does no future">
    <h3>{C.FUTURE_STANDARD_HEADING}</h3>
    <ul class="list plain">{_FUTURE_STANDARD}</ul>
    <p class="fine" style="margin-top:12px">Written in the future tense on purpose. None of these
      people are hired yet.</p>
  </div>
</div>

<div style="margin-top:26px">{M.roster(photo=photo) if roster else
    '<p class="prose"><a class="btn btn-ghost" href="/about">See who attends today, and what they are qualified as</a></p>'}</div>

<p class="prose fine" style="margin-top:20px">{C.TRUST_COMMITMENT}</p>"""


def cta_block():
    return f"""<section class="panel">
  <div class="wrap">
    <div class="prose">
      <h2>Start with one visit.</h2>
      <p class="lede">Delhi NCR today. Tell us the appointment and we will call you back the same
        working day.</p>
      <div class="btn-row" style="margin-top:26px">
        <a class="btn btn-dark" href="/book">Book the next appointment</a>
        <a class="btn btn-outline-light" href="{WA_LINK}" rel="noopener">{wa_icon()}WhatsApp us</a>
      </div>
    </div>
  </div>
</section>"""


# ------------------------------------------------------------------- pages


def build_home():
    v4 = VISITS[3]

    body = f"""<section class="hero">
  <div class="wrap">
    <p class="eyebrow" data-load>For families across the distance</p>
    <h1 data-load>A photo of a prescription is not a medical record.</h1>
    <p class="lede" data-load>Kinvisit attends your parent's hospital consultation in Delhi NCR,
      writes down what was actually said, and sends you the report the same day.</p>
    <div class="btn-row" data-load>
      <a class="btn btn-primary" href="/record">See the report you would receive</a>
    </div>
    <p class="trust" data-load>
      <span>{C.ATTENDS_SHORT}</span>
      <span>Same-day written report</span>
      <span>Delhi NCR</span>
      <span>From <b>{M.rupees(3200)} a month</b></span>
    </p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="compare rv" data-reveal="compare">
      <div>
        <p class="cmp-label">What you get today</p>
        <div class="wa-card">
          <div class="wa-bubble">
            <div class="wa-photo" role="img" aria-label="A blurred photograph of a prescription slip, too indistinct to read"></div>
            <p class="wa-meta">IMG_4821 &middot; 9:42 PM</p>
          </div>
          <p class="wa-quote">&ldquo;Doctor said it's fine.&rdquo; Forwarded from Mum. Blurry, and
            three weeks late.</p>
        </div>
      </div>
      <div class="arrow-link" aria-hidden="true">
        <span class="bar"></span>
        <span class="txt">&#8595;</span>
        <span class="bar"></span>
      </div>
      <div>
        <p class="cmp-label">What Kinvisit sends</p>
        <div class="report-card">
          <div class="report-head"><span>Kinvisit &middot; Consultation report</span><span class="n">#04</span></div>
          <dl style="margin:0">
            <div class="report-row"><dt>Visit</dt><dd>11 June &middot; Orthopaedics OPD</dd></div>
            <div class="report-row"><dt>Medication</dt><dd><span class="em">Oral anti-inflammatory withdrawn</span></dd></div>
            <div class="report-row"><dt>Why</dt><dd>eGFR 58 recorded at the April renal panel</dd></div>
            <div class="report-row"><dt>Substituted</dt><dd>Diclofenac gel, twice daily</dd></div>
            <div class="report-row"><dt>Next visit</dt><dd>09 July &middot; reports carried</dd></div>
          </dl>
          <div class="report-foot">The surgeon had no access to the April renal panel. The record did.</div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="slow">
  <div class="wrap">
    <div class="figure-split">
      <div class="prose">
        <p class="eyebrow">The problem</p>
        <h2>The room is where care happens. Nobody is there for you.</h2>
      </div>
      {photo("opd-corridor", caption="An outpatient department in Delhi NCR on an ordinary "
           "morning. Your parent is somewhere in this, holding the file.")}
    </div>

    <div class="stats stats-2">
      <div class="stat rv">
        <span class="num">62%</span>
        <p>of Indians over 60 live with at least one diagnosed chronic condition, and more than
          half of those have two or more.<sup>1</sup></p>
      </div>
      <div class="stat rv">
        <span class="num">30%</span>
        <p>live in a household with no adult child in it. There is nobody younger in the
          room.<sup>2</sup></p>
      </div>
    </div>

    <div class="room rv" data-reveal="room">
      {ROOM_SVG}
      <p class="fine">Every clinical decision is made in the solid box. The
        person who pays for it stands in the dashed one.</p>
    </div>

    <div class="prose">
      <p class="lede" style="color:var(--ink)">The problem is not access to doctors. It is that an
        eight minute consultation leaves behind nothing anyone can use afterwards.</p>
      <p class="fine" style="margin-top:26px">
        <sup>1</sup> Longitudinal Ageing Study in India, Wave 1, 2017-18, n = 31,464 adults aged 60
        and above. 37.6% reported no chronic condition, 30.3% one, and 32.1% two or more.
        <br>
        <sup>2</sup> Same survey, living-arrangement analysis, n = 30,370. 5.1% live alone, 19.5%
        with a spouse and no children present, and 5.1% with others only. Both figures come from
        peer-reviewed analyses of LASI published in BMC Geriatrics, 2023, and are set out with
        their derivations on our <a href="/proof">research page</a>.
      </p>
    </div>
  </div>
</section>

{M.gap_calculator()}

{M.ledger_band()}

<section id="report" class="slow report-stage">
  <div class="wrap wrap-wide">
    <div class="figure-split">
      <div class="prose">
        <p class="eyebrow">What you actually receive</p>
        <h2>One visit. Every word of it, written down.</h2>
        <p class="lede">This is the whole deliverable, not a summary of it. Read it before you
          decide anything else about us.</p>
      </div>
      {photo("report-on-desk", caption="The report as it arrives: a printed sheet a family can "
           "carry into the next consultation.", cls="shot-object")}
    </div>
    <div class="prose">
      <p style="margin-top:18px;color:var(--ink-soft)">Three steps, every time. The companion
        arrives with your written questions, sits through the consultation and records what is
        said, then reconciles the new prescription against every standing medicine before the
        report reaches you the same day. They document and clarify. They never advise, and they
        never argue with your parent's doctor.</p>
    </div>

    <p class="sample-note" style="margin-top:26px">Sample record. Illustrative, not a real patient.</p>

    {M.annotation_toggle()}

    <div class="rv" data-reveal="report">{render_visit(v4)}</div>

    <div class="btn-row">
      <a class="btn btn-ghost" href="/assets/kinvisit-sample-report.pdf" download>Download this report as a PDF</a>
      <a class="btn btn-ghost" href="/record">See all four visits</a>
    </div>

    <div class="prose" style="margin-top:52px">
      <h3>The same four visits, as one medication history</h3>
      <p style="color:var(--ink-soft)">Each visit adds one dated row. This is what the fourth
        doctor was shown.</p>
    </div>
    <div class="rv" data-reveal="table">
      {render_med_table()}
    </div>
    <p class="prose fine" style="margin-top:14px">Nobody holds this table today. Not the
      cardiologist, not the nephrologist, not the family. It is built one visit at a time.</p>

    <div class="prose" style="margin-top:34px">{M.share_block(SITE)}</div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Scope</p>
      <h2>What the companion does, and does not, do.</h2>
    </div>
    <div style="margin-top:26px">{SCOPE_BLOCK}</div>
  </div>
</section>

<section class="sunk">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">After the room</p>
      <h2>The report is not the end of the visit.</h2>
      <p class="lede">Pick the thing you are actually worried about.</p>
    </div>
    <div style="margin-top:26px">{M.escalation()}</div>
  </div>
</section>

<section id="who">
  <div class="wrap">
    {who_block(photo=False, roster=False)}
  </div>
</section>

{M.compounding_scrubber()}

<section id="pricing" class="tight">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Pricing</p>
      <h2>You are buying the file, not the errand.</h2>
      <p class="lede">A single visit gets you one transcript. The monthly plan maintains the
        record, which is the thing that catches what a single room cannot.</p>
    </div>
    <div style="margin-top:26px">{GUARANTEE_BLOCK}</div>
    <div class="price-strip">
      <div><span class="ps-n">{M.rupees(2200)}</span><span class="ps-l">one visit, one report</span></div>
      <div class="ps-feature"><span class="ps-n">{M.rupees(3200)}</span><span class="ps-l">a month, with the file maintained</span></div>
      <div><span class="ps-n">{M.rupees(5400)}</span><span class="ps-l">a month, two visits</span></div>
    </div>
    <p class="fine" style="margin-top:14px">No setup fee, no lock-in, and no commission from
      hospitals or labs. <a href="/pricing">Full pricing, and what happens if we miss</a>.</p>
    <div style="margin-top:52px">{ATTENDANT_BLOCK}</div>
  </div>
</section>

<section class="panel slow">
  <div class="wrap">
    <div class="quote">
      <blockquote>&ldquo;My grandmother saw a doctor twice a month for years. The only report we
        ever got was: the doctor said it's fine.&rdquo;</blockquote>
      <cite>Kunal Jain, Founder &middot; <a href="/about">Read the full story</a></cite>
    </div>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">FAQ</p>
      <h2>What families ask first.</h2>
    </div>
    <div class="prose">{faq_block(FAQ_ITEMS[:6])}</div>
    <p class="prose" style="margin-top:20px"><a href="/faq">All twelve questions</a>, or
      <a href="/conversations">the three conversations families find hardest</a>.</p>
  </div>
</section>

{cta_block()}"""

    import json as _json

    jsonld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Kinvisit",
        "description": ("A trained companion attends a parent's hospital consultation in Delhi NCR "
                        "and sends the family a written report the same day."),
        "url": SITE,
        "telephone": PHONE_HREF,
        "email": EMAIL,
        "areaServed": {"@type": "AdministrativeArea", "name": "Delhi NCR, India"},
        "address": {"@type": "PostalAddress", "addressRegion": "Delhi NCR", "addressCountry": "IN"},
        "founder": {"@type": "Person", "name": "Kunal Jain"},
        "makesOffer": [
            {
                "@type": "Offer",
                "name": p["name"],
                "price": str(p["price"]),
                "priceCurrency": "INR",
                "description": p["summary"],
                "itemOffered": {"@type": "Service", "name": p["name"],
                                "serviceType": "Hospital consultation accompaniment and written record"},
            }
            for p in C.PLANS
        ],
    })

    page(
        "/",
        "Kinvisit | A trained companion at your parent's hospital visit, Delhi NCR",
        "Kinvisit attends your parent's hospital consultation in Delhi NCR and sends you a written "
        "report the same day. From ₹3,200 a month, or ₹2,200 for a single visit.",
        body,
        current=None,
        jsonld=jsonld,
        rail=hero_rail(shot="opd-corridor",
        caption="An outpatient department in Delhi NCR on an ordinary morning.",
        stamp="Thursday 10:40 &middot; Room 5",
        items=[
            ("Where", "Delhi NCR, 26 hospitals listed"),
            ("Who attends", C.ATTENDS_RAIL),
            ("You receive", "A written record before midnight"),
            ("From", f"{M.rupees(3200)} a month, no lock-in"),
        ]),
    )


def build_record():
    panels = "".join(render_visit(v) for v in VISITS)
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">The record</p>
    <h1>One year. Four specialists. One chart.</h1>
    <p class="lede">Click through a sample patient's visits. Watch what the record catches that no
      single doctor could.</p>
    <p class="sample-note" style="margin-top:22px">Sample record. Illustrative, not a real patient.</p>
  </div>
  <div class="wrap prose hero-pair">
    {photo("questions-notebook", caption="What the family sent, written out the night before. "
           "The companion does not invent questions in the room.", cls="shot-tall",
           loading="eager")}
    {photo("report-on-desk", caption="What came back, the same evening.", cls="shot-tall")}
  </div>
</section>

<section class="slow report-stage">
  <div class="wrap wrap-wide">
    {M.annotation_toggle()}
    {visit_tabs()}
    {panels}
    <div class="btn-row" style="margin-top:24px">
      <a class="btn btn-ghost" href="/assets/kinvisit-sample-report.pdf" download>Download the sample report as a PDF</a>
      <a class="btn btn-primary" href="/book">Book the next appointment</a>
    </div>
    <div class="prose" style="margin-top:30px">{M.share_block(SITE)}</div>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <h2>The same four visits, as one medication history</h2>
      <p class="lede">This is the object the fourth doctor was shown.</p>
    </div>
    <div style="margin-top:22px">{render_med_table()}</div>
    <p class="prose fine" style="margin-top:14px">Nobody holds this table today. Not the
      cardiologist, not the nephrologist, not the family. It is built one visit at a time.</p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Scope</p>
      <h2>What the companion does, and does not, do.</h2>
    </div>
    <div style="margin-top:26px">{SCOPE_BLOCK}</div>
  </div>
</section>

{cta_block()}"""
    page(
        "/record",
        "The report you would receive | Kinvisit",
        "A full sample Kinvisit consultation report across four visits, including the medication "
        "history that caught an unsafe prescription. Illustrative, not a real patient.",
        body,
        current="/record",
        rail=hero_rail(shot="report-on-desk",
        caption="The report as it arrives, on the family's own table.",
        items=[
            ("This sample", "Four visits across one year"),
            ("Specialists", "Endocrinology, nephrology, orthopaedics"),
            ("What it caught", "An oral anti-inflammatory withdrawn"),
            ("Read next", '<a href="/pricing">What it costs</a>'),
        ]),
    )


def build_pricing():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Pricing</p>
    <h1>You are buying the file, not the errand.</h1>
    <p class="lede">We sell two different things. Attendance, which is a person in a room for one
      afternoon. And the record, which is a maintained file that outlives any single visit. They
      are priced differently because they are worth different amounts.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    {GUARANTEE_BLOCK}
    {M.plans_block()}
    {M.currency_note()}
    <p class="fine" style="margin-top:16px">Plans are month to month, with no setup fee, no
      lock-in, and no exit fee. You are not charged until we have confirmed the visit with you by
      phone.</p>
    {M.overseas_toggle()}
  </div>
</section>

{M.overseas_tier()}

<section class="sunk slow">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Why the single visit costs more per visit</p>
      <h2>The expensive way to buy is the one that builds nothing.</h2>
      <p>A single visit gives you a transcript of one room. It is genuinely useful, and for one
        doctor seen twice a year it may be all you need.</p>
      <p>What it does not do is carry anything forward. Nobody reconciles next month's
        prescription against this month's. Nobody notices that the question you asked in April was
        never answered. The next doctor starts from your parent's memory, which is where this
        problem began.</p>
      <p>So the single visit is priced as the standalone product it is, and the plans are priced
        as the thing that compounds. We would rather be honest about that than sell you a cheap
        entry plan that quietly does less.</p>
      <p><a href="/#compounding">See what twelve visits build</a>.</p>
    </div>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">The awkward questions</p>
      <h2>What happens when something goes wrong.</h2>
      <p class="lede">Every one of these is a reason not to buy, so every one of them is answered
        here rather than in an email after you have paid.</p>
    </div>
    <div style="margin-top:26px">{M.policies_block()}</div>
    <p class="prose" style="margin-top:22px"><a href="/promise">Every time we have missed the
      same-day promise, with the cause and what we changed</a>.</p>
  </div>
</section>

<section class="sunk">
  <div class="wrap">
    {ATTENDANT_BLOCK}
  </div>
</section>

<section>
  <div class="wrap">
    <div class="prose">
      <h2>What the fee does not buy</h2>
      <p class="lede">Worth saying plainly, because the boundary is the product.</p>
    </div>
    <div style="margin-top:26px">{SCOPE_BLOCK}</div>
  </div>
</section>

{cta_block()}"""

    import json as _json
    offers = _json.dumps({
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "Kinvisit hospital consultation accompaniment",
        "serviceType": "Hospital consultation accompaniment and written record",
        "provider": {"@type": "Organization", "name": "Kinvisit", "url": SITE},
        "areaServed": {"@type": "AdministrativeArea", "name": "Delhi NCR, India"},
        "offers": [
            {"@type": "Offer", "name": p["name"], "price": str(p["price"]),
             "priceCurrency": "INR", "description": p["summary"],
             "url": SITE + "/pricing"}
            for p in C.PLANS
        ],
    })

    page(
        "/pricing",
        "Pricing | Kinvisit",
        "A single Kinvisit visit is ₹2,200. The maintained record is ₹3,200 a month for one "
        "consultation or ₹5,400 for two. If the report does not reach you the same day, that "
        "visit is not billed.",
        body,
        current="/pricing",
        jsonld=offers,
        rail=hero_rail([
            ("Billing", "Month to month, no setup fee"),
            ("Lock-in", "None. Cancel any time"),
            ("If we miss", '<a href="/promise">That visit is not billed</a>'),
            ("Charged", "Only after we confirm by phone"),
        ]),
    )



def dpdp_consent(field_id, what):
    """The notice and the tick the DPDP Act, 2023 asks for.

    The Act wants consent that is free, specific, informed and unambiguous,
    given by a clear affirmative action, alongside a notice saying what is
    collected, what for, how to take it back, and how to complain. A line of
    small print saying "by submitting you agree" is none of those things, so
    this is a real checkbox and the notice is above it in words a family can
    read."""
    g = C.BUSINESS.get("grievanceOfficer", {})
    officer = g.get("email") or EMAIL
    return f"""<div class="consent-notice">
        <p class="consent-head">Before you send this</p>
        <ul>
          <li><strong>What we collect.</strong> {what}</li>
          <li><strong>What we do with it.</strong> Call you to confirm the appointment, attend it,
            and write the report. Nothing else. We do not advertise to you, profile you, or share
            it with any hospital, laboratory, pharmacy, or insurer.</li>
          <li><strong>Taking it back.</strong> Write to
            <a href="mailto:{EMAIL}">{EMAIL}</a> at any time and we delete it. Withdrawing is as
            easy as giving it.</li>
          <li><strong>If we get it wrong.</strong> Our grievance officer is at
            <a href="mailto:{officer}">{officer}</a>, and you can escalate to the Data Protection
            Board of India.</li>
        </ul>
      </div>

      <div class="field field-check">
        <label class="check" for="{field_id}">
          <input id="{field_id}" name="consent" type="checkbox" value="yes" required>
          <span>I have read the above and I agree that Kinvisit may hold and use this
            information to arrange the visit. I have read the
            <a href="/privacy">privacy policy</a> and the <a href="/terms">terms</a>.
            <span class="req" aria-hidden="true">*</span></span>
        </label>
        <span class="err" role="alert" id="{field_id}-err"></span>
      </div>"""


def build_book():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Request a visit</p>
    <h1>Tell us about the appointment.</h1>
    <p class="lede">We confirm every visit by phone before a companion is assigned. You are not
      charged until that call.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <div class="pathway">
        <p class="eyebrow">The fast way</p>
        <h2>Four taps, and we write the message for you.</h2>
        <p style="color:var(--ink-soft)">Most families do this on WhatsApp. Answer three questions
          and you arrive in WhatsApp with the whole thing composed.</p>
        {M.wa_builder(WA_NUMBER)}
        <noscript>
          <p><a class="btn btn-primary" href="{WA_LINK}" rel="noopener">{wa_icon()}Message us on WhatsApp</a></p>
        </noscript>
      </div>
    </div>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <div class="or-rule"><span>or use the form</span></div>

    <form class="form" name="visit-request" method="POST" action="/thanks"
          data-netlify="true" netlify-honeypot="company-website"
          data-validate data-event="Booking Submitted">
      <input type="hidden" name="form-name" value="visit-request">
      <p class="hp"><label>Do not fill this in <input class="hp-input" name="company-website" tabindex="-1" autocomplete="off" aria-hidden="true"></label></p>

      <p class="form-lede">Three things now. Everything else on the next screen, or on the phone.</p>

      <div class="field">
        <label for="your-name">Your name <span class="req" aria-hidden="true">*</span></label>
        <input id="your-name" name="your-name" type="text" autocomplete="name" required>
        <span class="err" role="alert" id="your-name-err"></span>
      </div>

      <div class="field">
        <label for="phone">Your phone or WhatsApp number <span class="req" aria-hidden="true">*</span></label>
        <span class="hint" id="phone-hint">Include the country code, for example +44 or +1.</span>
        <input id="phone" name="phone" type="tel" autocomplete="tel" aria-describedby="phone-hint" required>
        <span class="err" role="alert" id="phone-err"></span>
      </div>

      <div class="field">
        <label for="hospital">Which hospital or clinic? <span class="req" aria-hidden="true">*</span></label>
        <span class="hint" id="hospital-hint">Any hospital, clinic, or diagnostic centre in Delhi
          NCR. Type it however you say it.</span>
        <input id="hospital" name="hospital" type="text" list="hospital-list"
          aria-describedby="hospital-hint" autocomplete="off" required>
        <span class="err" role="alert" id="hospital-err"></span>
        <datalist id="hospital-list">{HOSPITAL_OPTIONS}</datalist>
      </div>

      <div class="field">
        <label for="email">Your email <span class="req" aria-hidden="true">*</span></label>
        <span class="hint" id="email-hint">Your confirmation arrives here within minutes, and so
          does every written report afterwards.</span>
        <input id="email" name="email" type="email" autocomplete="email"
               aria-describedby="email-hint" required>
        <span class="err" role="alert" id="email-err"></span>
      </div>

      {dpdp_consent("consent-visit", "Your name, your phone number, your email, and the hospital. "
                    "Nothing about the patient's health on this form.")}

      <button class="btn btn-primary btn-block" type="submit">Request this visit</button>
    </form>

    <div class="form-note" style="margin-top:30px">
      <p style="margin:0"><strong>We confirm every visit by phone before a companion is assigned.
        You are not charged until that call.</strong></p>
    </div>
  </div>
</section>

<section class="sunk">
  <div class="wrap prose">
    <p class="eyebrow">When we will call</p>
    <h2>At a reasonable hour. Yours, not ours.</h2>
    {M.callback_clock()}
  </div>
</section>

<section>
  <div class="wrap prose">
    {M.consent_block()}
    <div class="btn-row" style="margin-top:22px">
      <a class="btn btn-ghost" href="/consent">Read the consent we ask for</a>
      <a class="btn btn-ghost" href="/assets/kinvisit-consent.pdf" download>Download it as a PDF</a>
    </div>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <p>Prefer to talk first? <a href="{WA_LINK}" rel="noopener">WhatsApp {PHONE_DISPLAY}</a> or call
      <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a>.</p>
  </div>
</section>"""
    page(
        "/book",
        "Request a visit | Kinvisit",
        "Tell us about your parent's next hospital appointment in Delhi NCR. Three fields, or four "
        "taps on WhatsApp. We confirm every visit by phone before a companion is assigned.",
        body,
        current=None,
    )


def build_thanks():
    """A2. The second screen. The lead is already captured, so everything here
    is optional and abandoning it costs nothing."""
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Request received</p>
    <h1>We have it. You can stop here.</h1>
    <p class="lede">Everything below is optional. It makes the first call shorter, and it means
      the companion arrives already knowing what you want raised. If you would rather tell us on
      the phone, close this page.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <form class="form" name="visit-details" method="POST" action="/details-saved"
          data-netlify="true" netlify-honeypot="company-website" data-event="Booking Details Added">
      <input type="hidden" name="form-name" value="visit-details">
      <p class="hp"><label>Do not fill this in <input class="hp-input" name="company-website" tabindex="-1" autocomplete="off" aria-hidden="true"></label></p>

      <div class="field">
        <label for="d-phone">The phone number you just gave us</label>
        <span class="hint" id="d-phone-hint">So we can match this to your request.</span>
        <input id="d-phone" name="phone" type="tel" autocomplete="tel" aria-describedby="d-phone-hint">
      </div>

      <div class="field">
        <label for="d-city">Where do you live?</label>
        <span class="hint" id="d-city-hint">So we call you at a reasonable hour, not ours.</span>
        <input id="d-city" name="your-city" type="text" autocomplete="address-level2" aria-describedby="d-city-hint">
      </div>

      <div class="field">
        <label for="d-patient">Your parent's name</label>
        <input id="d-patient" name="patient-name" type="text">
      </div>

      <div class="field">
        <label for="d-age">Your parent's age</label>
        <input id="d-age" name="patient-age" type="number" min="1" max="120" inputmode="numeric">
      </div>

      <div class="field">
        <label for="d-specialty">Department or specialty, if known</label>
        <input id="d-specialty" name="specialty" type="text" list="specialty-list" autocomplete="off">
        <datalist id="specialty-list">
          <option value="Cardiology"></option>
          <option value="Endocrinology"></option>
          <option value="Nephrology"></option>
          <option value="Neurology"></option>
          <option value="Oncology"></option>
          <option value="Ophthalmology"></option>
          <option value="Orthopaedics"></option>
          <option value="Pulmonology"></option>
          <option value="Rheumatology"></option>
          <option value="General medicine"></option>
        </datalist>
      </div>

      <div class="field">
        <label for="d-date">Appointment date and time, if already booked</label>
        <input id="d-date" name="appt-datetime" type="datetime-local">
      </div>

      <div class="check">
        <input id="d-notbooked" name="not-booked-yet" type="checkbox" value="yes">
        <label for="d-notbooked">Not booked yet. Help me pick a slot.</label>
      </div>

      <div class="field">
        <label for="d-raise">What should the companion raise in the room?</label>
        <span class="hint" id="d-raise-hint">For example: her hand has been swelling for months and
          we do not know if it has ever been mentioned.</span>
        <textarea id="d-raise" name="what-to-raise" rows="5" aria-describedby="d-raise-hint"></textarea>
      </div>

      {dpdp_consent("consent-details", "The patient's name and age, the hospital and department, "
                    "the appointment time, and anything you write about their health in the box "
                    "above. This is health data and we treat it as such. If the visit does not go "
                    "ahead we delete all of it after 90 days.")}

      <button class="btn btn-primary btn-block" type="submit">Add these details</button>
    </form>
  </div>
</section>

<section class="sunk">
  <div class="wrap prose">
    <h2>What happens next</h2>
    <div class="steps" style="margin-top:22px">
      <div class="step">
        <p class="n">01</p>
        <h3>We read it today</h3>
        <p>If you gave us an email, a confirmation is on its way. If it has not arrived in ten
          minutes, check spam, then WhatsApp us.</p>
        <p class="when">Within minutes</p>
      </div>
      <div class="step">
        <p class="n">02</p>
        <h3>We call you</h3>
        <p>Within one working day, at an hour that works where you live. We confirm the
          appointment, the hospital, and what you want raised in the room.</p>
        <p class="when">Within one working day</p>
      </div>
      <div class="step">
        <p class="n">03</p>
        <h3>Then a companion is assigned</h3>
        <p>Not before. You are not charged until the confirming call, and if the report does not
          reach you on the day of the visit, that visit is not billed.</p>
        <p class="when">After the call</p>
      </div>
    </div>

    <div class="btn-row" style="margin-top:30px">
      <a class="btn btn-primary" href="{WA_LINK}" rel="noopener">{wa_icon()}Message us now instead</a>
      <a class="btn btn-ghost" href="/record">See the report you will receive</a>
    </div>
  </div>
</section>"""
    page(
        "/thanks",
        "Request received | Kinvisit",
        "Your visit request has reached Kinvisit. We call you back within one working day.",
        body,
        noindex=True,
    )


def build_details_saved():
    """The second screen's confirmation. Posting the details form back to
    /thanks would re-render the same empty form, which reads as a failure."""
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Saved</p>
    <h1>Got it. That is everything we need before the call.</h1>
    <p class="lede">Your companion will have read all of this before the appointment, so the call
      is about confirming the slot rather than repeating yourself.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <div class="form-note">
      <p style="margin:0"><strong>We call within one working day, at an hour that works where you
        live. You are not charged until that call.</strong></p>
    </div>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-primary" href="{WA_LINK}" rel="noopener">{wa_icon()}Message us now instead</a>
      <a class="btn btn-ghost" href="/record">See the report you will receive</a>
    </div>
    <p style="margin-top:26px">Remembered something else? <a href="/thanks">Add more details</a>,
      or just tell us on the call.</p>
  </div>
</section>"""
    page(
        "/details-saved",
        "Details saved | Kinvisit",
        "Your appointment details have reached Kinvisit. We call you back within one working day.",
        body,
        noindex=True,
    )


def build_hospitals():
    areas = ["South Delhi", "Central Delhi", "West Delhi", "East Delhi", "Gurugram", "Noida",
             "Greater Noida", "Ghaziabad", "Faridabad"]
    chips = "".join(f'<span class="area">{a}</span>' for a in areas)
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Where we go</p>
    <h1>Any hospital your parent already trusts.</h1>
    <p class="lede">We do not run a clinic and we have no arrangement with any hospital, which means
      no hospital pays us and no hospital influences what goes in your report. We meet your parent
      at the OPD they already attend, anywhere in Delhi NCR.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <h2>Areas we cover today</h2>
      <p style="color:var(--ink-soft)">Government hospital, private chain, standalone clinic, or
        diagnostic centre. If it is in Delhi NCR, we attend.</p>
    </div>
    <div style="margin-top:20px">{M.hospital_checker()}</div>
    <p class="fine" style="margin-top:18px">Outside these areas, ask us anyway. If we cannot reach
      it, we will say so on the call rather than take the booking.</p>
  </div>
</section>

<section class="sunk">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Independence</p>
      <h2>No commission. No referrals. No conflicts.</h2>
      <p>Every bundled eldercare provider has commercial relationships with hospitals, labs, and
        pharmacies. Those relationships have to be paid for somewhere, and they are paid for inside
        the advice you receive.</p>
      <p>Kinvisit takes no commission from any hospital, lab, or pharmacy. We are paid by the family
        and by nobody else. That is the whole reason the report can say an oral drug should be
        withdrawn, or that a test was never ordered.</p>
      <p>It also means we will never recommend a hospital. We go where your parent already goes.</p>
    </div>
  </div>
</section>

{cta_block()}"""
    page(
        "/hospitals",
        "Where we go | Kinvisit",
        "Kinvisit accompanies at any hospital, clinic, or diagnostic centre across Delhi NCR. We "
        "take no commission from any hospital or lab, so no hospital influences your report.",
        body,
        current="/hospitals",
        rail=hero_rail([
            ("Listed", "26 hospitals across Delhi NCR"),
            ("Areas", "South, Central, West, East and North Delhi"),
            ("Also", "Gurugram, Noida, Ghaziabad, Faridabad"),
            ("Not listed", "Ask. We go to clinics too"),
        ]),
    )


def build_about():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">About</p>
    <h1>Built from one family's blind spot.</h1>
  </div>
</section>

<section class="slow">
  <div class="wrap">
    <div class="prose">
      <div class="bio">
        <div class="bio-photo has-photo">
          <picture>
            <source type="image/webp" srcset="/assets/photos/founder-portrait.webp 1x, /assets/photos/founder-portrait@2x.webp 2x">
            <img src="/assets/photos/founder-portrait.jpg"
                 srcset="/assets/photos/founder-portrait.jpg 1x, /assets/photos/founder-portrait@2x.jpg 2x"
                 width="200" height="200" loading="lazy" decoding="async"
                 alt="Kunal Jain in a hospital outpatient department, with an overhead board listing token numbers against OPD room numbers behind him">
          </picture>
        </div>
        <div>
          <h2 style="margin-bottom:.2em">Kunal Jain</h2>
          <p class="fine" style="margin-bottom:1.2em">Founder &middot; Delhi NCR</p>
          <p>My grandmother was diabetic, lived in another city, and saw a doctor once or twice a
            month for years. The report back was always the same sentence: the doctor said it's
            fine.</p>
          <p>Swelling in her hand worsened month over month across a year of appointments. Nobody
            outside the room ever knew whether it had been raised. Not because anyone was
            careless, but because an eight minute consultation produces no record, and the person
            paying for the care is a thousand miles away.</p>
          <p>I am not clinical, and Kinvisit is not built on the idea that I should be. The first
            hire is a nursing lead who owns the visit protocol, the question checklist, the report
            format, and companion training. Until that person is in place, I attend every visit
            myself.</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="sunk">
  <div class="wrap">
    {who_block(photo=False)}
  </div>
</section>

<section>
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Scope</p>
      <h2>The boundary we will not move.</h2>
      <p class="lede">A companion who advises is a liability to your parent and to their doctor.
        This list is not marketing. It is the operating rule.</p>
    </div>
    <div style="margin-top:26px">{SCOPE_BLOCK}</div>
  </div>
</section>

<section class="sunk">
  <div class="wrap">
    <div class="prose">
      <h2>Talk to us before you book</h2>
      <p class="lede">Most families want a conversation first. That is the right instinct.</p>
      <div class="grid g2" style="margin-top:26px">
        <div class="card">
          <h3>WhatsApp</h3>
          <p style="margin:0"><a href="{WA_LINK}" rel="noopener">{PHONE_DISPLAY}</a><br>
            <span class="fine">Fastest. We answer to your timezone.</span></p>
        </div>
        <div class="card">
          <h3>Email</h3>
          <p style="margin:0"><a href="mailto:{EMAIL}">{EMAIL}</a><br>
            <span class="fine">We reply within one working day.</span></p>
        </div>
      </div>
      <p class="fine" style="margin-top:20px">Kinvisit is registered as a micro enterprise under
        Udyam. Company details are available on request.</p>
    </div>
  </div>
</section>

{cta_block()}"""
    page(
        "/about",
        "About Kinvisit | Who sits in the room with your parent",
        "Kinvisit was built after a year of appointments produced one sentence: the doctor said "
        "it's fine. Who our companions are, what they are trained on, and where we honestly stand "
        "today.",
        body,
        current="/about",
        rail=hero_rail(shot="questions-notebook",
        caption="What a family sends us, the night before.",
        items=[
            ("Attending today", "One named companion, not clinically qualified"),
            ("Clinically qualified", "Not yet. The nursing lead is the first hire"),
            ("Languages", "Hindi, English"),
            ("Named on this page", "Every companion, as they join"),
        ]),
    )


def build_faq():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">FAQ</p>
    <h1>What families ask first.</h1>
    <p class="lede">If your question is not here, ask it on WhatsApp. We answer to your timezone.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">{faq_block(FAQ_ITEMS)}</div>
    <div class="prose btn-row" style="margin-top:30px">
      <a class="btn btn-primary" href="/book">Book the next appointment</a>
      <a class="btn btn-ghost" href="{WA_LINK}" rel="noopener">{wa_icon()}Ask on WhatsApp</a>
    </div>
  </div>
</section>"""
    page(
        "/faq",
        "Questions families ask | Kinvisit",
        "Language, timings, doctor cooperation, data safety, cancellation, and paying from abroad. "
        "Twelve straight answers about how a Kinvisit visit works.",
        body,
        current="/faq",
        jsonld=faq_jsonld(FAQ_ITEMS),
        rail=hero_rail([
            ("Still unsure", "Message us and ask"),
            ("WhatsApp", PHONE_DISPLAY),
            ("Email", f'<a href="mailto:{EMAIL}">{EMAIL}</a>'),
            ("Read next", '<a href="/record">The report you would receive</a>'),
        ]),
    )


def build_proof():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">For investors and accelerators</p>
    <h1>Research, market, and where we honestly stand.</h1>
    <p class="lede">This page is not written for families. It is the evidence base behind the
      product, including the parts that do not flatter us.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <h2>1. The market</h2>
      <p>India had 149 million people aged 60 and above in 2022. That is projected to reach 347
        million by 2050, taking the 60-plus share of the population from 10.5% to 20.8%.</p>
      <p class="fine">Source: India Ageing Report 2023, UNFPA India and the International Institute
        for Population Sciences.</p>

      <h2 style="margin-top:2em">2. The consultation-record gap</h2>
      <p>Among adults aged 60 and above in India (LASI Wave 1, 2017-18, n = 31,464), 37.6% reported
        no chronic condition, 30.3% reported one, and 32.1% reported two or more. So 62.4% live with
        at least one diagnosed chronic condition, and 51.4% of those carry two or more.</p>
      <p>Two or more conditions means two or more specialists. Indian outpatient care produces no
        chart that travels between them. The patient's own memory is the integration layer.</p>
      <p>On living arrangements (n = 30,370): 5.1% live alone, 19.5% live with a spouse and no
        children present, and 5.1% live with others only. 29.7% of households containing someone
        aged 60 or above therefore contain no adult child.</p>
      <p class="fine">Sources: "The burden of disease-specific multimorbidity among older adults in
        India and its states: evidence from LASI", BMC Geriatrics, 2023. "Living arrangement of
        Indian elderly: a predominant predictor of their level of life satisfaction", BMC
        Geriatrics, 2023. Both are peer-reviewed analyses of the Longitudinal Ageing Study in India,
        Wave 1.</p>
      <p class="fine">Figures we could not verify against a primary source have been removed from
        this site rather than estimated.</p>
    </div>

    <div class="prose" style="margin-top:2.6em">
      <h2>3. Competitive landscape</h2>
      <p>Drawn to be useful rather than flattering. The informal attendant is the real incumbent and
        is listed as a serious column, because that is what families actually compare us against.</p>
    </div>
    <div class="cmp-table-scroll" style="margin-top:18px">
      <table class="cmp">
        <colgroup><col><col><col class="us-col"><col><col></colgroup>
        <thead>
          <tr>
            <th scope="col">&nbsp;</th>
            <th scope="col">Informal attendant</th>
            <th scope="col" class="us">Kinvisit</th>
            <th scope="col">Bundled membership</th>
            <th scope="col">Home nursing</th>
          </tr>
        </thead>
        <tbody>
          <tr><th scope="row">Clinically trained</th><td class="n">No</td><td class="y">Yes</td><td class="n">No</td><td class="y">Yes</td></tr>
          <tr><th scope="row">Sold as a standalone service</th><td class="y">Yes</td><td class="y">Yes</td><td class="n">No</td><td class="n">No</td></tr>
          <tr><th scope="row">Produces a written record</th><td class="n">No</td><td class="y">Yes</td><td class="n">Rarely</td><td class="n">Shift notes only</td></tr>
          <tr><th scope="row">Reconciles medications</th><td class="n">No</td><td class="y">Yes</td><td class="n">No</td><td class="y">In-home only</td></tr>
          <tr><th scope="row">Record persists across visits</th><td class="n">No</td><td class="y">Yes</td><td class="n">No</td><td class="n">No</td></tr>
          <tr><th scope="row">Takes commission from hospitals</th><td class="n">Sometimes</td><td class="y">Never</td><td class="n">Usually</td><td class="n">Usually</td></tr>
        </tbody>
      </table>
    </div>
    <p class="scroll-hint fine">Scroll the table sideways to see every column.</p>
    <p class="prose fine" style="margin-top:14px">Home nursing is not competing for escort-and-report
      work. It is included because it is the nearest clinically staffed alternative, not because it
      is a substitute.</p>

    <div class="prose" style="margin-top:2.6em">
      <h2>4. Pricing against incumbents</h2>
      <p>Two escorted consultations a month, annualised.</p>
      <ul class="list yes">
        <li>Informal attendant, roughly &#8377;1,500 a visit: about &#8377;36,000 a year, untrained, no record</li>
        <li>Kinvisit two-visit plan at &#8377;4,500 a month: &#8377;54,000 a year</li>
        <li>Published bundled membership tier: up to &#8377;1,65,000 a year</li>
      </ul>
      <p class="fine"><strong>Caveat, stated plainly.</strong> A bundled membership at
        &#8377;1,65,000 buys thirty other service lines, most of which Kinvisit does not provide.
        It is not a like-for-like comparison and should not be read as one. The honest comparison is
        the attendant column, where we cost more and deliver a different job. That argument is made
        in full on the <a href="/pricing">pricing page</a>.</p>
    </div>

    <div class="prose" style="margin-top:2.6em">
      <h2>5. Where we are</h2>
      <p>Pre-revenue. Research complete. No pilot yet, no paying customer, no letter of intent. We
        publish our stage rather than imply a further one.</p>
    </div>
    <div class="prose" style="margin-top:22px">{M.ledger_full()}</div>
    <p class="prose fine" style="margin-top:14px">Every miss against the same-day promise is
      published with its cause on <a href="/promise">the promise log</a>.</p>
    <div class="track">
      <div class="on">Idea</div>
      <div class="on">Research</div>
      <div>Pilot</div>
      <div>Revenue</div>
      <div>Scale</div>
    </div>

    <div class="prose" style="margin-top:2.6em">
      <h2>6. What funding buys</h2>
      <ul class="list yes">
        <li>A nursing lead, full time. Owns the visit protocol, question checklist, report format,
          and companion training, and co-signs every report</li>
        <li>The first cohort of companions, hired, verified, and certified on the 40 hour protocol</li>
        <li>A paid pilot across Delhi NCR, priced at the published rates, to produce the first real
          retention and report-turnaround data</li>
        <li>The record system itself, which is the asset that compounds and the reason this is not
          a staffing business</li>
      </ul>
    </div>

    <div class="prose" style="margin-top:2.6em">
      <p><a href="mailto:{EMAIL}">{EMAIL}</a> &middot; <a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a></p>
    </div>
  </div>
</section>"""
    page(
        "/proof",
        "Research and market | Kinvisit",
        "The evidence base behind Kinvisit: ageing and multimorbidity data from LASI and UNFPA, an "
        "honest competitive comparison, current stage, and what funding buys.",
        body,
        rail=hero_rail([
            ("Figures", "Every one sourced, or not published"),
            ("Sources", "LASI Wave 1, UNFPA India, BMC Geriatrics"),
            ("Visit counts", "Zero until they are real"),
            ("Read next", '<a href="/promise">What we publish when we fail</a>'),
        ]),
    )


def build_privacy():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Privacy</p>
    <h1>What we hold, and how you delete it.</h1>
    <p class="lede">Kinvisit processes personal and health data under the Digital Personal Data
      Protection Act, 2023. This page says exactly what that means in practice.</p>
    <p class="fine">Last updated 6 September 2026.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <h2>Who we are</h2>
      <p>Kinvisit is the data fiduciary for the information described here. You can reach our
        grievance officer at <a href="mailto:{EMAIL}">{EMAIL}</a> or {PHONE_DISPLAY}.</p>

      <h2>What we collect</h2>
      <ul class="list yes">
        <li><strong>From you, the paying family member.</strong> Name, phone or WhatsApp number,
          email address, city of residence, and your relationship to the patient.</li>
        <li><strong>About the patient.</strong> Name, age, the hospital and department attended,
          appointment times, current medicines, prescriptions issued, test results shown in the
          room, instructions given by the treating doctor, and the questions you asked us to
          raise.</li>
        <li><strong>From the website.</strong> Aggregate page-view counts through Plausible
          Analytics, which sets no cookies and does not collect personal data or build a profile
          of you.</li>
      </ul>

      <h2>Why we collect it</h2>
      <p>To attend the consultation, write the report, reconcile medicines against the standing
        list, carry unresolved items into the next visit, and bill you. We do not use your data for
        advertising and we do not profile you.</p>

      <h2>Consent</h2>
      <p>We take written consent from the patient, or from a family member entitled to give it on
        their behalf, before the first visit. Consent can be withdrawn at any time by writing to
        {EMAIL}, and withdrawal stops all future visits and processing.</p>

      <h2>Who can see it</h2>
      <ul class="list yes">
        <li>The assigned companion, for the visit they attend</li>
        <li>Our nursing lead, who will review and co-sign every report once that role is filled. It is not filled today, so one person at Kinvisit sees your parent's record</li>
        <li>The paying family member named on the account</li>
      </ul>
      <p>Nobody else. We take no commission from any hospital, laboratory, pharmacy, insurer, or
        diagnostic chain, and we do not sell, rent, or share your data with any of them. We have no
        commercial reason to, and no arrangement that would allow it.</p>

      <h2>Where it is stored</h2>
      <p>Records are stored encrypted at rest on servers located in India. Access is restricted by
        role and every access is logged. Companions carry no patient data on personal devices
        outside the visit.</p>

      <h2>How long we keep it</h2>
      <p>Health records are retained for as long as you hold an account with us, and for three years
        after your last visit, so that a returning family does not lose the history that makes the
        record useful. Billing records are kept for eight years as required by Indian tax law.
        Enquiry and booking-form submissions that do not become visits are deleted after 90
        days, which is what the form itself promises at the point you fill it in.</p>

      <h2>Your rights</h2>
      <ul class="list yes">
        <li>Ask us for a copy of everything we hold about you or the patient</li>
        <li>Ask us to correct anything inaccurate</li>
        <li>Ask us to erase the record, which we do within thirty days except where tax law requires
          us to keep billing entries</li>
        <li>Nominate someone to exercise these rights if the patient cannot</li>
        <li>Raise a grievance with us, and escalate to the Data Protection Board of India if we do
          not resolve it</li>
      </ul>
      <p>Write to <a href="mailto:{EMAIL}">{EMAIL}</a> for any of the above. We respond within seven
        working days.</p>

      <h2>Breach</h2>
      <p>If a breach affects your data we will notify you and the Data Protection Board of India as
        required by the Act, describing what happened and what we are doing about it.</p>

      <h2>Changes</h2>
      <p>If this policy changes materially, we tell every active family by email before the change
        takes effect.</p>
    </div>
  </div>
</section>"""
    page(
        "/privacy",
        "Privacy policy | Kinvisit",
        "What Kinvisit collects, where it is stored, who can see it, how long we keep it, and how "
        "you delete it. Written against the Digital Personal Data Protection Act, 2023.",
        body,
        rail=hero_rail([
            ("Under", "The Digital Personal Data Protection Act, 2023"),
            ("Cookies", '<a href="/cookies">None. No banner either</a>'),
            ("Deletion", "Within 30 days of asking"),
            ("Grievances", f'<a href="mailto:{EMAIL}">{EMAIL}</a>'),
        ]),
    )


def build_terms():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Terms</p>
    <h1>Terms of service.</h1>
    <p class="fine">Last updated 6 September 2026.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap">
    <div class="prose">
      <h2>1. Kinvisit is not a healthcare provider</h2>
      <p>Kinvisit does not provide medical care, medical advice, diagnosis, treatment, or a second
        opinion, and accepts no clinical liability. We are not a hospital, a clinic, a nursing
        agency, a diagnostic service, or an emergency service.</p>
      <p>Our companions attend a consultation, ask the questions you gave us, record what the
        treating doctor says, and reconcile the prescription against the medicines already on file.
        Every clinical decision remains the treating doctor's. Nothing in a Kinvisit report is a
        medical instruction, and nothing in it should be acted on in place of speaking to the
        treating doctor.</p>
      <p>In a medical emergency, call your local emergency number or go to the nearest hospital. Do
        not contact Kinvisit first.</p>

      <h2>2. What we agree to do</h2>
      <ul class="list yes">
        <li>Send a companion to the confirmed appointment</li>
        <li>Raise the questions you supplied, so far as the treating doctor permits</li>
        <li>Record instructions and dosages as they are given</li>
        <li>Reconcile the new prescription against the standing medicine list on file</li>
        <li>Deliver a written report on the day of the visit</li>
      </ul>

      <h2>3. What you agree to do</h2>
      <ul class="list yes">
        <li>Give accurate information about the patient, their medicines, and the appointment</li>
        <li>Obtain the patient's agreement to a companion attending, or confirm you are entitled to
          give it on their behalf</li>
        <li>Tell us of changes to the appointment as soon as you know</li>
      </ul>

      <h2>4. The report guarantee</h2>
      <p>If the written report does not reach you on the day of the visit, that visit is not billed.
        This is the only service-level promise we make, and we make it because it is countable.</p>

      <h2>5. Fees, cancellation, and refunds</h2>
      <p>Plans are month to month with no setup fee, no lock-in, and no exit fee. Prices are as
        published on the <a href="/pricing">pricing page</a>. You are not charged until we confirm a
        visit with you by phone.</p>
      <p>Cancel a visit more than four hours before the appointment and it is not billed. Inside
        four hours, or if the companion has already reached the hospital, the visit is billed in
        full. If the hospital cancels or reschedules, nothing is billed.</p>
      <p>Cancel a plan at any time. The plan runs to the end of the paid month and does not renew.</p>

      <h2>6. Limits of the companion's role</h2>
      <p>A companion will not diagnose, prescribe, change or suggest a dose, overrule or argue with
        the treating doctor, administer medication, perform a clinical procedure, or consent to any
        procedure on the family's behalf. A companion may leave the room at any time if the doctor
        or the patient asks.</p>

      <h2>7. Records and confidentiality</h2>
      <p>The record belongs to the patient and the paying family. We share it with nobody else. Our
        handling of it is set out in the <a href="/privacy">privacy policy</a>. We take no
        commission from any hospital, laboratory, or pharmacy.</p>

      <h2>8. Liability</h2>
      <p>Nothing in these terms excludes liability that cannot be excluded under Indian law,
        including liability for death or personal injury caused by our negligence, or for fraud.
        Subject to that, our total liability for any claim arising out of the service is limited to
        the fees you paid us in the three months before the claim.</p>
      <p>We are not liable for the acts, omissions, or clinical decisions of any hospital, doctor,
        laboratory, or pharmacy.</p>

      <h2>9. Governing law</h2>
      <p>These terms are governed by the laws of India, and the courts at Delhi have exclusive
        jurisdiction.</p>

      <h2>10. Contact</h2>
      <p><a href="mailto:{EMAIL}">{EMAIL}</a> &middot; {PHONE_DISPLAY}</p>
    </div>
  </div>
</section>"""
    page(
        "/terms",
        "Terms of service | Kinvisit",
        "Kinvisit is not a healthcare provider, does not give medical advice, and accepts no "
        "clinical liability. What we agree to do, what you agree to do, fees, cancellation, and "
        "the report guarantee.",
        body,
        rail=hero_rail([
            ("We are not", "A healthcare provider"),
            ("Clinical decisions", "The treating doctor's, always"),
            ("Emergencies", "Call your local number, not us"),
            ("Fees", '<a href="/refunds">Cancellation and refunds</a>'),
        ]),
    )



def build_refunds():
    """Cancellation and refunds, as its own page.

    The substance is already in clause 5 of the terms. It is repeated here
    because every Indian payment gateway requires a standalone, linkable
    cancellation and refund policy before it will process a rupee, and because
    a buyer looking for it should not have to read a contract to find it. The
    two must not drift: if one changes, change both."""

    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Cancellation and refunds</p>
    <h1>When you are charged, and when you are not.</h1>
    <p class="lede">Short version: you are never charged before we confirm a visit with you by
      phone, and if the report does not reach you on the day, that visit is not billed.</p>
    <p class="fine">Last updated 10 September 2026.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <h2>Before anything is charged</h2>
    <p>Sending the booking form or a WhatsApp message costs nothing and commits you to nothing.
      We call you, confirm the appointment, and only then is a visit billable. If we never
      reach you, you are never charged.</p>

    <h2>Cancelling a visit</h2>
    <ul class="list yes">
      <li><strong>More than four hours before the appointment.</strong> Not billed. Nothing to
        refund, because nothing is taken.</li>
      <li><strong>Inside four hours, or once the companion has reached the hospital.</strong>
        Billed in full. The companion has already travelled and given up the slot.</li>
      <li><strong>The hospital cancels or reschedules.</strong> Not billed, however late.</li>
      <li><strong>The patient is unwell and cannot attend.</strong> Not billed. Tell us when you
        can; we do not ask for proof.</li>
    </ul>

    <h2>When we refund</h2>
    <ul class="list yes">
      <li><strong>The report does not reach you on the day of the visit.</strong> That visit is
        not billed, and if it has already been charged it is refunded in full. This is the
        <a href="/promise">same-day promise</a>, and every miss is published.</li>
      <li><strong>No companion attended.</strong> Refunded in full.</li>
      <li><strong>You were charged twice, or charged for a visit that did not happen.</strong>
        Refunded in full.</li>
    </ul>

    <h2>How a refund reaches you</h2>
    <p>To the same method you paid with. We start it within three working days of agreeing it,
      and your bank or card issuer typically takes a further five to seven working days. We do
      not issue credit notes or wallet balances in place of money, unless you ask for one.</p>

    <h2>Cancelling a plan</h2>
    <p>Plans are month to month. There is no setup fee, no lock-in, and no exit fee. Cancel at
      any time and the plan runs to the end of the month you have paid for and does not renew.
      We do not refund part of a month that has already run, because the visits in it were
      available to you.</p>

    <h2>If you disagree with a charge</h2>
    <p>Write to <a href="mailto:{EMAIL}">{EMAIL}</a> or call {PHONE_DISPLAY}. We reply within
      three working days. If we cannot settle it between us, nothing here stops you taking it to
      a consumer forum; these terms do not remove any right you have under the Consumer
      Protection Act, 2019.</p>

    <div style="margin-top:var(--s-4)">{business_block()}</div>

    <p class="fine" style="margin-top:var(--s-4)">This page and clause 5 of the
      <a href="/terms">terms of service</a> say the same thing. If they ever disagree, the terms
      govern and we have made a mistake here that we want to know about.</p>
  </div>
</section>"""

    page(
        "/refunds",
        "Cancellation and refunds | Kinvisit",
        "When a Kinvisit visit is billed and when it is not, what we refund, and how long a "
        "refund takes to reach you. Month to month, no lock-in, no exit fee.",
        body,
        rail=hero_rail([
            ("Charged", "Only after we confirm by phone"),
            ("Cancel free", "More than four hours before"),
            ("Refund starts", "Within three working days"),
            ("Your rights", "The Consumer Protection Act, 2019 still applies"),
        ]),
    )


def build_cookies():
    """The cookie policy, whose main finding is that there is nothing to consent to.

    Worth stating plainly rather than shipping a banner nobody needs. A consent
    banner for storage that is exempt from consent trains people to click
    through the ones that are not."""

    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Cookies</p>
    <h1>This site sets no cookies.</h1>
    <p class="lede">Not strictly necessary ones, not analytics ones, not advertising ones. There
      is no consent banner here because there is nothing to consent to.</p>
    <p class="fine">Last updated 10 September 2026.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <h2>How we count visitors instead</h2>
    <p>We use Plausible Analytics, which counts page views without cookies, without a device
      fingerprint, and without following you to any other site. It records the page, the country,
      and the kind of device, all in aggregate. It cannot tell us who you are, and we cannot ask
      it. Nothing you type into a form or into the portal is ever sent to it, and no page you
      have to sign in to is measured at all.</p>

    <h2>What is stored on your device</h2>
    <p>Two things, both kept in your browser rather than sent anywhere, and both what the law
      calls strictly necessary: storage without which the thing you asked for cannot work.</p>
    <ul class="list yes">
      <li><strong>Your sign-in, if you use the portal.</strong> Kept so that opening a second page
        does not ask for your password again. Signing out removes it.</li>
      <li><strong>A companion's half-finished consultation.</strong> The report desk keeps the
        record being typed in that browser, so a phone that locks or loses signal in an OPD does
        not lose the visit. It is a working draft on one device and it is not your record.</li>
    </ul>
    <p>Clearing your browser data removes both. Neither is readable by any other website, and
      neither reaches us except when you sign in or file a visit deliberately.</p>

    <h2>Third parties</h2>
    <p>There are none to speak of. No advertising network, no social media pixel, no embedded
      video, no chat widget, no font service, no tag manager. Type faces are served from this
      site rather than from a font host. The only outside services this site touches are
      Plausible, which counts pages, and the database behind the portal, which holds your
      records and is reached only when you sign in.</p>

    <h2>If this changes</h2>
    <p>If we ever add something that does set a cookie, this page changes first, and a consent
      banner appears before the cookie does. Write to <a href="mailto:{EMAIL}">{EMAIL}</a> if you
      think we have missed something. The full picture of what we hold is in the
      <a href="/privacy">privacy policy</a>.</p>
  </div>
</section>"""

    page(
        "/cookies",
        "Cookie policy | Kinvisit",
        "Kinvisit sets no cookies. Analytics are cookieless, the only device storage is your "
        "sign-in and a companion's working draft, and there are no third-party trackers.",
        body,
        rail=hero_rail([
            ("Cookies set", "None, of any kind"),
            ("Analytics", "Plausible. Cookieless, no profile"),
            ("On your device", "Your sign-in, and a companion's draft"),
            ("Third parties", "No pixel, no embed, no tag manager"),
        ]),
    )


def build_404():
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">404</p>
    <h1>That page is not here.</h1>
    <p class="lede">The link may be old, or we may have moved it. These are the pages worth
      your time.</p>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-primary" href="/record">See the report you would receive</a>
      <a class="btn btn-ghost" href="/">Back to the homepage</a>
    </div>
    <p style="margin-top:26px">Or just <a href="{WA_LINK}" rel="noopener">WhatsApp us</a>.</p>
  </div>
</section>"""
    page("/404", "Page not found | Kinvisit",
         "That link does not lead anywhere on the Kinvisit site. The sample report, pricing, and "
         "the booking form are all one click away.", body, noindex=True)


def build_conversations():
    """M11. Also the strongest organic-search asset the business has. Someone
    typing 'how do I tell my mother I want someone at her doctor appointment'
    is a perfect-fit buyer with no commercial intent yet."""
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">The difficult conversations</p>
    <h1>Three conversations that decide whether any of this happens.</h1>
    <p class="lede">Being convinced is not the hard part. Telling your mother a stranger will sit
      in her consultation is the hard part. Here is what to say, written out, so you can copy it
      or say it in your own words.</p>
    <p class="fine">Nothing on this page requires you to buy anything. If the scripts are all you
      take from this site, they still work.</p>
  </div>
</section>

<section class="slow">
  <div class="wrap prose conv-wrap">
    {M.conversations()}
  </div>
</section>

<section class="sunk">
  <div class="wrap prose">
    <h2>If the conversation goes well</h2>
    <p class="lede">The next thing to show them is the report, not the price.</p>
    <div class="btn-row" style="margin-top:20px">
      <a class="btn btn-primary" href="/record">See the report you would receive</a>
    </div>
    <div style="margin-top:28px">{M.share_block(SITE)}</div>
  </div>
</section>"""
    page(
        "/conversations",
        "How to tell your parent, your sibling, and the doctor | Kinvisit",
        "Word-for-word scripts for the three conversations families find hardest: telling your "
        "parent someone will be in the room, telling your sibling it is worth paying for, and "
        "telling the doctor who this person is.",
        body,
        current="/conversations",
        rail=hero_rail([
            ("Scripts", "Three, word for word"),
            ("For", "Your parent, your sibling, the doctor"),
            ("Costs", "Nothing. Take them and go"),
            ("Read next", '<a href="/record">The report itself</a>'),
        ]),
    )


def build_promise():
    """M14. The guarantee as a public record rather than a claim."""
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">The same-day promise</p>
    <h1>If the report does not reach you the same day, that visit is not billed.</h1>
    <p class="lede">Same day means before midnight India time on the day of the consultation. Not
      the next morning. Not within 24 hours.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <h2>Every time we have missed it</h2>
    <p style="color:var(--ink-soft)">Anyone can publish a failure. What makes it worth reading is
      the cause and what changed because of it, so both are on every entry.</p>
    <div style="margin-top:24px">{M.promise_log()}</div>
  </div>
</section>

<section class="sunk">
  <div class="wrap prose">
    <h2>Why we publish this</h2>
    <p>A company with no track record has two options. It can make claims, which cost nothing and
      are worth nothing. Or it can publish the record it does have, including the parts that look
      bad, which is expensive to fake.</p>
    <p>Nine out of nine is a marketing number. Eight out of nine with the failure named is
      evidence. We would rather be the second thing.</p>
    <p>If a number anywhere on this site is wrong, tell us and we will correct it publicly.
      <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
  </div>
</section>"""
    page(
        "/promise",
        "The same-day promise, and every time we have missed it | Kinvisit",
        "If a Kinvisit report does not reach you before midnight India time on the day of the "
        "consultation, that visit is not billed. Every miss is published here with its cause.",
        body,
        rail=hero_rail([
            ("The promise", "Same day, or that visit is not billed"),
            ("Same day means", "Before midnight India time"),
            ("Every miss", "Published on this page with its cause"),
            ("Found an error", f'<a href="mailto:{EMAIL}">Tell us and we correct it</a>'),
        ]),
    )


def build_consent():
    """M16. Consent is the parent's, not the buyer's. Must be reviewed by a
    lawyer and by a native Hindi speaker before it is used for real consent."""
    hi = "".join(
        f'<div class="con-row"><h3 lang="hi">{h}</h3><p lang="hi">{b}</p></div>'
        for h, b in C.CONSENT_HI
    )
    body = f"""<section class="hero">
  <div class="wrap prose">
    <p class="eyebrow">Consent</p>
    <h1>Your parent has to agree to this.</h1>
    <p class="lede">You are the one paying. They are the one whose medical information is being
      written down. Those are different people, and the second one decides.</p>
  </div>
</section>

<section class="tight">
  <div class="wrap prose">
    <p>{C.CONSENT_INTRO}</p>
    <h2>What we ask them, exactly</h2>
    <div class="consent" style="margin-top:26px">{"".join(
        f'<div class="con-row"><h3>{t}</h3><p>{b}</p></div>' for t, b in C.CONSENT_POINTS
    )}</div>

    <div class="honest" style="margin-top:26px">
      <h3>Withdrawal is theirs, not yours</h3>
      <p>{C.CONSENT_WITHDRAWAL}</p>
      <p>Some families find that line uncomfortable. We publish it because it is the correct
        position, and because a consent your parent cannot withdraw is not a consent.</p>
    </div>

    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-primary" href="/assets/kinvisit-consent.pdf" download>Download the one page, English and Hindi</a>
      <a class="btn btn-ghost" href="/privacy">How we handle the record</a>
    </div>
  </div>
</section>

<section class="sunk">
  <div class="wrap prose">
    <h2 lang="hi">यह क्या है</h2>
    <p>The same page in Hindi, written to be read aloud to a parent.</p>
    <div class="consent" style="margin-top:22px">{hi}</div>
    <p class="fine" style="margin-top:18px">This translation is a draft. It is being checked by a
      native Hindi speaker and by a lawyer before it is used to take consent from anyone. The
      English text above is the operative version until that check is done.</p>
  </div>
</section>"""
    page(
        "/consent",
        "The consent we ask your parent for | Kinvisit",
        "What Kinvisit asks your parent to agree to before the first visit, what gets written "
        "down, who receives it, how long it is kept, and how they withdraw at any time without "
        "your permission.",
        body,
        rail=hero_rail([
            ("Whose consent", "Your parent's, not the payer's"),
            ("Withdrawn", "At any time, without anyone's permission"),
            ("Reviewed", "Not yet. This needs a lawyer before use"),
            ("In Hindi", "Draft. Needs a native speaker"),
        ]),
    )


LLMS_TXT = f"""# Kinvisit

> Kinvisit sends a trained companion into an elderly parent's hospital
> consultation in Delhi NCR and sends the family a written report the same day.
> It is built for adult children living away from their parents.

## What it is

A person attends the consultation with your parent, asks the questions the
family wrote down in advance, records the doctor's instructions and dosages
exactly as given, reconciles the new prescription against every medicine the
patient already takes, and sends the family a written report before midnight
India time on the day of the visit. Across visits those reports become a
maintained file: a medication history, a list of unresolved questions carried
forward, and a record no single hospital holds.

## What it is not

Kinvisit is not a medical provider. Companions do not diagnose, prescribe,
change a dose, give a second opinion, argue with the treating doctor, or
consent to procedures. Kinvisit is not an emergency service, not a home nursing
service, and not a hospital. It takes no commission from any hospital,
laboratory, or pharmacy.

## Where

Delhi NCR only: Delhi, Gurugram, Noida, Greater Noida, Ghaziabad, Faridabad.
Any hospital, clinic, or diagnostic centre in that area. No other city today.

## What it costs

Single visit, one report, no file maintained: {M.rupees(2200).replace('&#8377;', 'INR ')}.
The record, one consultation a month with the file maintained: {M.rupees(3200).replace('&#8377;', 'INR ')} per month.
The record, two consultations a month: {M.rupees(5400).replace('&#8377;', 'INR ')} per month.
Additional visit on a plan: {M.rupees(1600).replace('&#8377;', 'INR ')}.
If the report does not arrive the same day, that visit is not billed.

## Current stage, stated honestly

Pre-revenue. Sole proprietorship, one founder, no staff yet. The founder,
Kunal Jain, attends every visit personally and is not clinically qualified.
The nursing lead who will own the visit protocol and co-sign reports has not
been hired. The sample report published on the site is illustrative, not a real
patient. Any performance number on the site is published with its source.

## Useful pages

- {{SITE}}/record        a full sample consultation report, four visits
- {{SITE}}/conversations how to tell your parent, your sibling, and the doctor
- {{SITE}}/pricing       prices, cancellation, no-show and refund policy
- {{SITE}}/promise       every time the same-day promise has been missed
- {{SITE}}/consent       what the parent is asked to agree to, English and Hindi
- {{SITE}}/proof         market research, sources, and competitive position
- {{SITE}}/about         who attends today and the standard being built toward

## Contact

WhatsApp and phone {{PHONE_DISPLAY}}. Email {{EMAIL}}.
"""


# ------------------------------------------------------------ static extras



def desk_field(key, label, placeholder, kind="text"):
    return (f'<label><span class="dk-lab">{label}</span>'
            f'<input type="{kind}" id="dk-f-{key}" placeholder="{placeholder}"></label>')



def hospitals_by_area():
    """content/hospitals.json in the order the file declares its areas, so the
    desk lists the same coverage the checker on /hospitals claims."""
    out = []
    for area in C.HOSPITALS["areas"]:
        names = [h["name"] for h in C.HOSPITALS["hospitals"] if h["area"] == area]
        if names:
            out.append((area, sorted(names)))
    return out



def desk_choice(key, label, groups, other_label):
    """A picker a companion can read straight down, with a way out at the
    bottom. Every list here is short enough to scroll and long enough that
    the escape hatch is the exception, not the habit."""
    opts = '<option value="">Choose one</option>'
    for group, items in groups:
        inner = "".join(f'<option value="{M.esc(i)}">{i}</option>' for i in items)
        opts += f'<optgroup label="{M.esc(group)}">{inner}</optgroup>' if group else inner
    opts += f'<option value="__other">{other_label}</option>'
    return f"""<label><span class="dk-lab">{label}</span>
              <select id="dk-f-{key}">{opts}</select></label>
            <label class="dk-other" id="dk-o-{key}" hidden>
              <span class="dk-lab">{other_label}</span>
              <input type="text" id="dk-f-{key}-other"></label>"""


def desk_question_bank():
    opts = '<option value="">Add one of the questions we always ask</option>'
    for group, items in DESK_QUESTIONS:
        inner = "".join(f'<option value="{M.esc(q)}">{q}</option>' for q in items)
        opts += f'<optgroup label="{M.esc(group)}">{inner}</optgroup>'
    return f"""<label class="dk-bank"><span class="dk-lab">From the standard list</span>
      <select id="dk-f-qbank">{opts}</select></label>"""


def desk_set(legend, key, add_label):
    """One repeatable section. The rows themselves are written by desk.js,
    because a row only exists once a companion has something to put in it."""
    return f"""<fieldset class="dk-set">
    <legend>{legend} <span class="dk-count" id="dk-c-{key}"></span></legend>
    <div class="dk-rows" id="dk-r-{key}"></div>
    <button type="button" class="dk-add" data-add="{key}">{add_label}</button>
  </fieldset>"""



def portal_bar():
    """The signed-in header. One way back to the site, one way out."""
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="pt-bar">
  <div class="pt-bar-in">
    <a class="brand" href="/">{WORDMARK}</a>
    <div class="pt-who">
      <span class="pt-name" id="pt-name"></span>
      <button type="button" class="btn btn-ghost btn-sm pt-out" id="pt-signout" hidden>Sign out</button>
    </div>
  </div>
</header>"""


def portal_foot():
    return f"""<footer class="site-foot pt-foot">
  <div class="wrap">
    <p class="fine">Kinvisit is not a medical provider. Our companions document and clarify.
      They do not diagnose, prescribe, or advise. Every clinical decision on these records was
      made by the treating doctor.</p>
    <p class="fine"><a href="/">The Kinvisit site</a> &middot;
      <a href="mailto:{EMAIL}">{EMAIL}</a> &middot; {PHONE_DISPLAY} &middot;
      <a href="/privacy">Privacy</a></p>
  </div>
</footer>"""


def gate(kind, waiting, denied):
    """Every signed-in page opens in the waiting state and stays there until a
    session and a role have both been confirmed. The redirect that follows a
    failure is a courtesy, not the security boundary: the boundary is row level
    security in Postgres, which returns nothing to a caller who is not entitled
    to it however they reached the page."""
    return f"""<div class="pt-gate" data-gate="{kind}">
  <p class="pt-waiting">{waiting}</p>
  <p class="pt-denied" hidden>{denied} <a href="/portal">Go to the sign-in page</a>.</p>
  <noscript><p>The portal needs JavaScript to check your sign-in. Message us on
    {PHONE_DISPLAY} and we will send your record another way.</p></noscript>
</div>"""



def build_config():
    """The portal's connection details, written from the environment at build
    time so no key is committed. The anon key is a public value by design: it
    identifies the project and grants nothing on its own, because every table
    is behind row level security. The service-role key must never appear
    here, or in any file under site/."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if "service_role" in key:
        raise SystemExit("SUPABASE_ANON_KEY looks like a service-role key. Refusing to publish it.")
    body = (
        "/* Written by build.py from the environment. Do not edit. */\n"
        # The portal pages carry a CSP with no 'unsafe-inline', so the class
        # that tells the stylesheet a script ran cannot be set from the head
        # the usual way. It is set here instead, in the first file the portal
        # loads. Until it runs, html has no .js and the two rules that depend
        # on it hold: the desk says it needs a script, and the sign-in board
        # stays down rather than sitting there showing dashes.
        "document.documentElement.className += ' js';\n"
        "window.KV_CONFIG = {\n"
        f"  supabaseUrl: {url!r},\n".replace("'", '"') +
        f"  supabaseAnonKey: {key!r}\n".replace("'", '"') +
        "};\n"
    )
    with open(os.path.join(OUT, "assets", "js", "config.js"), "w", encoding="utf-8") as f:
        f.write(body)
    if not (url and key):
        print("  note: SUPABASE_URL / SUPABASE_ANON_KEY unset, the portal will say so")



PORTAL_SCRIPTS = ("/assets/js/config.js", "/assets/js/vendor/supabase.js",
                  "/assets/js/report.js", "/assets/js/portal.js")

# The sign-in page alone gets the counter. It is loaded ahead of portal.js so
# that its listeners exist before the auth module announces anything, and it
# is not loaded on the two signed-in pages, which have no forms to dress.
SIGNIN_SCRIPTS = ("/assets/js/config.js", "/assets/js/vendor/supabase.js",
                  "/assets/js/report.js", "/assets/js/portal-ui.js",
                  "/assets/js/portal.js")


def login_form(kind, counter, title, blurb, cta):
    """One counter. The number is wayfinding rather than a fact about the
    business, so it is hidden from a screen reader, which is told which form
    it is in by the heading instead.

    Two controls here start hidden and are revealed by portal-ui.js: a button
    that unmasks the password, and the Caps Lock warning. Neither can do
    anything without a script, and a control that does nothing is worse than
    no control, so with scripts unreachable the form is exactly the plain
    pair of fields it always was."""
    return f"""<form class="pt-form" data-login="{kind}" data-counter="{counter}" novalidate>
        <p class="pt-num" aria-hidden="true"><span>Counter</span><b>{counter}</b></p>
        <h2>{title}</h2>
        <p class="pt-blurb">{blurb}</p>
        <div class="field">
          <label for="{kind}-email">Email</label>
          <input id="{kind}-email" name="email" type="email" autocomplete="username"
                 required spellcheck="false">
        </div>
        <div class="field pt-field-pw">
          <label for="{kind}-password">Password</label>
          <div class="pt-pw">
            <input id="{kind}-password" name="password" type="password"
                   autocomplete="current-password" required>
            <button type="button" class="pt-peek" data-pt-peek hidden
                    aria-controls="{kind}-password" aria-pressed="false">Show</button>
          </div>
        </div>
        <p class="pt-caps" data-pt-caps role="status" hidden>Caps Lock is on.</p>
        <p class="pt-error" id="{kind}-error" role="alert" hidden></p>
        <button type="submit" class="btn btn-primary" id="{kind}-submit">{cta}</button>
      </form>"""


def build_portal():
    """Two doors, side by side, because a family and a companion arrive here
    for different reasons and should not have to work out which half of the
    page is theirs. Both submit to the same Supabase project; what separates
    them is the role on the account, checked after the password.

    The page is dressed as the thing the rest of the site keeps quoting: an
    OPD reception, with a board overhead. The board is aria-hidden, and every
    field on it either reflects a real state (the wall clock, the transport
    the page was served over, which form has focus, whether a request is in
    flight) or repeats a sentence that is already in the page and already
    announced. It invents nothing: there is no queue length, no waiting time
    and no token number, because we would have to make all three up."""

    board = """<div class="pt-strip" data-pt-board aria-hidden="true">
  <div class="pt-strip-in">
    <span class="pt-seg"><span class="pt-lab">Counter</span><b class="pt-val" data-pt="counter">--</b></span>
    <span class="pt-seg pt-seg-grow"><span class="pt-lab">Status</span><b class="pt-val" data-pt="status">Reception</b></span>
    <span class="pt-seg"><span class="pt-lab">Link</span><b class="pt-val" data-pt="link">--</b></span>
    <span class="pt-seg"><span class="pt-lab">Time</span><b class="pt-val pt-clock" data-pt="clock"><span data-pt-hh>--</span><i>:</i><span data-pt-mm>--</span></b></span>
  </div>
</div>"""

    body = f"""{board}
<section class="tight">
  <div class="wrap dk-head pt-head">
    <div class="pt-intro">
      <p class="eyebrow">Kinvisit portal</p>
      <h1>Sign in</h1>
      <p class="lede">Accounts are issued by Kinvisit. There is no sign-up form here: if you
        are a family we set your account up when the first visit was booked, and if you are a
        companion it was set up when you joined.</p>

      <p class="form-note pt-unconfigured" id="pt-unconfigured" hidden><strong>The portal is not
        connected yet.</strong> The build has no Supabase project configured, so neither door
        will open. Set SUPABASE_URL and SUPABASE_ANON_KEY and deploy again.</p>
    </div>

    <aside class="pt-help">
      <h2>If you cannot get in</h2>
      <p>Forgotten your password, or never received an invitation? Message us and we will sort
        it out. We cannot read your password, so we reset it rather than tell you what it was.</p>
      <p class="pt-help-line"><a href="tel:{PHONE_HREF}">{PHONE_DISPLAY}</a></p>
      <p class="pt-help-line"><a href="mailto:{EMAIL}">{EMAIL}</a></p>
    </aside>

    <div class="pt-doors">
      {login_form("family", "01", "Families", "Every consultation a companion has attended, and what was said at each one.", "Sign in to your records")}
      {login_form("companion", "02", "Companions", "Open the report desk to write up a consultation, and see the visits you have attended.", "Sign in to the desk")}
    </div>
  </div>
</section>"""

    page(
        "/portal",
        "Sign in | Kinvisit portal",
        "The sign-in page for Kinvisit families and companions. Accounts are issued by "
        "Kinvisit; there is no public sign-up.",
        body,
        noindex=True,
        scripts=SIGNIN_SCRIPTS,
        analytics=False,
        chrome=False,
    )


def build_records():
    """What a family signed in to see: every visit, newest first, and the
    same report the desk produced on the day."""

    body = f"""<section class="tight">
  <div class="wrap dk-head">
    {gate("family", "Checking your sign-in.", "You are signed out, or this is a companion account.")}

    <template id="kv-mark">{WORDMARK}</template>
    <div class="pt-body" hidden>
      <p class="eyebrow">Your records</p>
      <h1 id="rc-title">Consultations</h1>
      <p class="lede" style="max-width:62ch" id="rc-lede">Every consultation a Kinvisit
        companion has attended, with what was asked, what the doctor said, and what changed.</p>

      <div class="rc-counts" id="rc-counts"></div>

      <div class="rc-split" data-mech="records">
        <div class="rc-list" id="rc-list"></div>
        <div class="rc-detail">
          <div class="dk-sheetwrap"><article class="dk-sheet" id="dk-sheet"
               tabindex="-1" aria-live="polite" aria-label="The selected consultation report"></article></div>
          <div class="dk-actions" style="margin-top:var(--s-3)">
            <button type="button" class="btn btn-ghost btn-sm" id="rc-print">Print or save as PDF</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>"""

    page(
        "/records",
        "Your records | Kinvisit portal",
        "The consultation records Kinvisit has written for your family, readable only when "
        "you are signed in to your own account.",
        body,
        noindex=True,
        scripts=PORTAL_SCRIPTS,
        analytics=False,
        chrome=False,
    )


def build_desk():
    """M14. The tool a companion opens in the hospital corridor.

    This is the one page on the site that cannot work without JavaScript. It
    is a staff tool rather than a page of the site: there is no reading it,
    only using it, so with the script unreachable it says so plainly instead
    of presenting a form that would generate nothing. It is noindex, it is not
    in sitemap.xml, and nothing typed into it is sent to Kinvisit or to
    analytics. The record lives in the companion's own browser and leaves it
    only when they press send inside WhatsApp."""

    body = f"""<section class="tight">
  <div class="wrap dk-head">
    {gate("companion", "Checking your sign-in.", "You are signed out, or this is a family account.")}

    <template id="kv-mark">{WORDMARK}</template>
    <div class="pt-body" hidden>
    <p class="eyebrow">For companions</p>
    <h1>Report desk</h1>
    <p class="dk-tally" id="dk-tally"></p>
    <p class="lede" style="max-width:{'62ch'}">Type the consultation in as it happens. The
      report the family receives builds itself alongside, with the WhatsApp message ready to
      send before you leave the building.</p>

    <p class="dk-nojs form-note"><strong>This page needs JavaScript.</strong> Everything it
      does happens inside your browser, so with scripts unavailable there is nothing to show.
      Turn scripts on for kinvisit.in, or message the office on {PHONE_DISPLAY} and dictate
      the visit instead.</p>

    <div class="dk-shell" data-mech="desk"
         data-email="{EMAIL}"
         data-phone="{PHONE_DISPLAY}"
         data-disclaimer="Kinvisit is not a medical provider. Our companions document and clarify. They do not diagnose, prescribe, or advise. Every clinical decision on this record was made by the treating doctor.">

      <div class="dk-record">
        <fieldset class="dk-set">
          <legend>The visit</legend>
          <label class="dk-patient"><span class="dk-lab">Which patient is this visit for</span>
            <select id="dk-f-patient-id">
              <option value="">Sign in to load your patients</option>
            </select></label>
          <div class="dk-grid">
            {desk_field("patient", "Name as it should appear on the report", "Full name as on the file")}
            {desk_field("date", "Date of consultation", "", kind="date")}
            {desk_choice("dept", "Department", [("", DESK_DEPARTMENTS)], "Another department")}
            {desk_choice("where", "Hospital", hospitals_by_area(), "Another hospital")}
            {desk_field("doctor", "Doctor", "Consultant endocrinologist")}
            {desk_field("companion", "Companion", "Who attended")}
          </div>
        </fieldset>

        <fieldset class="dk-set">
          <legend>What the family asked <span class="dk-count" id="dk-c-asked"></span></legend>
          {desk_question_bank()}
          <div class="dk-rows" id="dk-r-asked"></div>
          <button type="button" class="dk-add" data-add="asked">Add a question of your own</button>
        </fieldset>
        {desk_set("What the doctor instructed", "instructions", "Add an instruction")}

        <fieldset class="dk-set">
          <legend>Medicines changed today <span class="dk-count" id="dk-c-meds"></span></legend>
          <div class="dk-rows" id="dk-r-meds"></div>
          <button type="button" class="dk-add" data-add="meds">Add a medicine</button>
          <label style="margin-top:var(--s-3);display:block">
            <span class="dk-lab">Reconciliation note</span>
            <textarea id="dk-f-recon" placeholder="Checked against 3 standing medicines. No interaction flagged."></textarea>
          </label>
        </fieldset>

        {desk_set("Tests", "tests", "Add a test or result")}
        {desk_set("Left unresolved", "flags", "Add a flag")}

        <fieldset class="dk-set">
          <legend>Next visit</legend>
          <label><span class="dk-lab">When and where</span>
            <input type="text" id="dk-f-next" placeholder="09 April 2026, nephrology referral"></label>
        </fieldset>
      </div>

      <div class="dk-out">
        <div class="dk-tabs" role="tablist" aria-label="What to send">
          <button type="button" class="dk-tab" role="tab" id="dk-tab-report"
                  aria-selected="true" aria-controls="dk-pane-report">Report</button>
          <button type="button" class="dk-tab" role="tab" id="dk-tab-wa"
                  aria-selected="false" aria-controls="dk-pane-wa">WhatsApp text</button>
        </div>

        <div class="dk-actions">
          <button type="button" class="btn btn-primary btn-sm" id="dk-save">File this visit</button>
          <button type="button" class="btn btn-ghost btn-sm" id="dk-new">New record</button>
          <button type="button" class="btn btn-ghost btn-sm" id="dk-print">Print or save as PDF</button>
          <button type="button" class="btn btn-ghost btn-sm" id="dk-copy" hidden>Copy message</button>
          <a class="btn btn-ghost btn-sm" id="dk-wa-send" href="#" rel="noopener" hidden>{wa_icon()}Send on WhatsApp</a>
          <span class="dk-state" id="dk-state" role="status"></span>
        </div>

        <div id="dk-pane-report" role="tabpanel" aria-labelledby="dk-tab-report">
          <div class="dk-sheetwrap"><article class="dk-sheet" id="dk-sheet"></article></div>
        </div>

        <div id="dk-pane-wa" role="tabpanel" aria-labelledby="dk-tab-wa" hidden>
          <pre class="dk-msg" id="dk-wa"></pre>
        </div>
      </div>
    </div>
    </div>
  </div>
</section>

<section class="tight dk-saved">
  <div class="wrap">
    <div class="pt-body" hidden>
      <h2>Visits you have filed</h2>
      <p style="max-width:62ch" id="dk-filed-note">Every consultation you have written up,
        newest first. Filing a record puts it in the family's portal straight away.</p>
      <div class="dk-saved-list" id="dk-saved-list"></div>
    </div>
  </div>
</section>"""

    page(
        "/desk",
        "Report desk | Kinvisit portal",
        "The tool a Kinvisit companion uses to write up a consultation and send the family "
        "their report before leaving the hospital. Signed-in companions only.",
        body,
        noindex=True,
        scripts=PORTAL_SCRIPTS,
        analytics=False,
        chrome=False,
    )


def build_static():
    with open(os.path.join(OUT, "_redirects"), "w") as f:
        f.write(
            "# Clean paths. Netlify serves /pricing from pricing.html automatically,\n"
            "# so no SPA catch-all is needed and every route is real HTML.\n"
            "/index.html      /             301!\n"
            "/home            /             301\n"
            "/contact         /about        301\n"
            "# Old hash routes from the previous build, for anything already shared.\n"
            "/#/record        /record        301\n"
            "/#/pricing       /pricing       301\n"
            "/#/book          /book          301\n"
            "/#/about         /about         301\n"
            "/#/faq           /faq           301\n"
            "/#/hospitals     /hospitals     301\n"
        )

    # A1. A preview deploy must never invite crawlers to a domain it is not.
    if IS_PRODUCTION:
        robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
    else:
        robots = f"# {CONTEXT} deploy. Not the production domain.\nUser-agent: *\nDisallow: /\n"
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(robots)

    # F2. Assistants increasingly answer "who can go to my mother's appointment
    # in Delhi" before a search engine does. This is the plain-text brief.
    with open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8") as f:
        f.write(LLMS_TXT)

    urls = ["/", "/record", "/pricing", "/conversations", "/book", "/hospitals", "/about",
            "/faq", "/promise", "/consent", "/proof", "/privacy", "/terms", "/refunds",
            "/cookies"]
    entries = "".join(
        f"<url><loc>{SITE}{'' if u == '/' else u}</loc>"
        f"<priority>{'1.0' if u == '/' else '0.7'}</priority></url>"
        for u in urls
    )
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + entries + "</urlset>\n"
        )

    # The favicon is the wordmark's K, drawn from the same outlines by
    # gen_assets.py. build.py used to draw a second, different icon here; two
    # marks for one company is how a brand stops being one.


def main():
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    build_home()
    build_record()
    build_pricing()
    build_book()
    build_thanks()
    build_details_saved()
    build_hospitals()
    build_about()
    build_faq()
    build_conversations()
    build_promise()
    build_consent()
    build_proof()
    build_privacy()
    build_terms()
    build_refunds()
    build_cookies()
    build_404()
    build_config()
    build_portal()
    build_records()
    build_desk()
    build_static()
    print("built ->", OUT)


if __name__ == "__main__":
    main()
