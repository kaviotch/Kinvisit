#!/usr/bin/env python3
"""
Generates the binary assets the site links to:

  site/assets/og-report.png            1200x630 share card, the report artifact
  site/assets/favicon.png              96x96
  site/assets/apple-touch-icon.png     180x180
  site/assets/kinvisit-sample-report.pdf

Headless Chrome does the rendering, so the PDF and the share card use the same
type and colour as the site itself.

    python3 gen_assets.py
"""

import os
import subprocess
import sys

from PIL import Image, ImageDraw

import build
import content as KC

C_POINTS = KC.CONSENT_POINTS
C_HI = KC.CONSENT_HI

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site", "assets")
WORK = os.path.join(HERE, "_render")

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CANVAS = "#FCFBF9"
INK = "#14140F"
INK_SOFT = "#4B4B46"
INK_FAINT = "#71706D"
LINE = "#E4E3E0"
LINE_STRONG = "#C9C8C4"
ACCENT = "#1E4D52"
PANEL = "#14140F"

WITHDRAWN = "#8A4034"
SUBSTITUTED = "#3F5F3A"

# The same three self-hosted faces the site uses, so a shared report and a
# downloaded PDF look like they came from the same company.
FONT_DIR = os.path.join(HERE, "site", "assets", "fonts")
FONT_CSS = """
  @font-face { font-family:'Geist'; font-weight:400 500; font-display:block;
               src:url('file://%s/geist-latin.woff2') format('woff2'); }
  @font-face { font-family:'Geist Mono'; font-weight:400; font-display:block;
               src:url('file://%s/geist-mono-latin.woff2') format('woff2'); }
  @font-face { font-family:'Literata'; font-weight:400 500; font-display:block;
               src:url('file://%s/literata-latin.woff2') format('woff2'); }
  :root { --serif:'Literata',Georgia,serif;
          --sans:'Geist',sans-serif;
          --mono:'Geist Mono',monospace; }
""" % (FONT_DIR, FONT_DIR, FONT_DIR)




# --------------------------------------------------------------- wordmark
#
# One mark, drawn once, used on the report letterhead, in the site header, on
# the favicon and on the share card. The report has to read as issued by an
# institution rather than typed by whoever happened to be in the room, and a
# name set in the body font is not a mark.
#
# The letterforms are Geist outlines converted to a path, not live text. A
# wordmark set as <text> falls back to whatever face the machine has, which is
# exactly the failure a mark exists to prevent, and the report is printed and
# opened as a PDF on machines that have never heard of Geist.
#
# The device is a rule under "Kin", drawn to the exact advance width of those
# three letters: the half of the name that is the promise. Nothing else.

def _wordmark_path(word="Kinvisit", size=46.0):
    """Geist outlines for one word, as a single path in a y-down space."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform
    from fontTools.ttLib import TTFont

    font = TTFont(os.path.join(OUT, "fonts", "geist-latin.woff2"))
    upem = font["head"].unitsPerEm
    scale = size / upem
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    pen = SVGPathPen(glyphs)
    x = 0.0
    marks = {}
    for i, ch in enumerate(word):
        name = cmap[ord(ch)]
        # y is flipped: font space counts up from the baseline, SVG counts down.
        glyphs[name].draw(TransformPen(pen, Transform(scale, 0, 0, -scale, x * scale, 0)))
        x += hmtx[name][0]
        marks[i + 1] = x * scale
    return pen.getCommands(), marks, x * scale


def wordmark_svg(colour="currentColor", size=46.0, rule_after=3, label="Kinvisit"):
    d, marks, width = _wordmark_path(size=size)
    rule_w = marks[rule_after]
    rule_y = round(size * 0.20, 2)
    rule_h = max(2.0, round(size * 0.065, 2))
    height = round(size * 0.20 + rule_y + rule_h, 2)
    return (
        f'<svg class="mark" viewBox="0 {-size} {round(width, 2)} {round(size + rule_y + rule_h, 2)}" '
        f'width="{round(width, 2)}" height="{round(size + rule_y + rule_h, 2)}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}">'
        f'<path fill="{colour}" d="{d}"/>'
        f'<rect x="0" y="{rule_y}" width="{round(rule_w, 2)}" height="{rule_h}" fill="{colour}"/>'
        f'</svg>'
    )


def build_wordmark():
    """Write the mark once, so the site, the report and the icons share it."""
    svg = wordmark_svg(colour="#14140F")
    dst = os.path.join(OUT, "wordmark.svg")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg + "\n")
    print("wordmark.svg", os.path.getsize(dst), "bytes")
    return svg


def chrome(args):
    if not os.path.exists(CHROME):
        sys.exit("Google Chrome not found. Install it, or render these assets elsewhere.")
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--virtual-time-budget=6000", "--force-device-scale-factor=1"] + args,
        check=True, capture_output=True,
    )


# ------------------------------------------------------------------- og card


def og_card():
    v = build.VISITS[3]
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{FONT_CSS}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ width:1200px; height:630px; background:{CANVAS}; font-family:var(--sans);
          color:{INK}; display:flex; padding:56px 60px; gap:52px; align-items:center; }}
  .left {{ width:452px; flex:none; }}
  .brand {{ font-family:var(--sans); font-size:20px; font-weight:500;
            letter-spacing:-.01em; margin-bottom:40px; }}
  .brand i {{ display:none; }}
  h1 {{ font-family:var(--sans); font-size:52px; line-height:1.0; font-weight:400;
        letter-spacing:-.03em; margin-bottom:24px; }}
  p {{ font-size:21px; line-height:1.5; color:{INK_SOFT}; }}
  .strip {{ margin-top:40px; padding-top:24px; border-top:1px solid {LINE};
            font-family:var(--mono); font-size:13px; letter-spacing:.1em;
            text-transform:uppercase; color:{INK_FAINT}; }}
  .card {{ flex:1; background:#fff; border-top:2px solid {INK}; border-radius:2px;
           overflow:hidden; box-shadow:0 18px 40px -28px rgba(20,20,15,.35); }}
  .head {{ display:flex; justify-content:space-between; padding:16px 24px;
           border-bottom:1px solid {LINE}; font-family:var(--mono); font-size:13px;
           letter-spacing:.1em; text-transform:uppercase; color:{INK_FAINT}; }}
  .row {{ display:grid; grid-template-columns:118px 1fr; gap:14px; padding:16px 24px;
          border-bottom:1px solid {LINE}; align-items:baseline; }}
  dt {{ font-family:var(--mono); font-size:12.5px; letter-spacing:.1em;
        text-transform:uppercase; color:{INK_FAINT}; }}
  dd {{ font-size:19px; font-family:var(--serif); color:{INK}; }}
  .em {{ color:{WITHDRAWN}; }}
  .foot {{ padding:17px 24px; font-family:var(--serif); color:{INK_SOFT}; font-size:17px; }}
</style></head><body>
  <div class="left">
    <div class="brand"><i></i>Kinvisit</div>
    <h1>A photo of a prescription is not a medical record.</h1>
    <p>Someone sits in the consultation, writes down what the doctor actually said, and sends it to you the same day.</p>
    <div class="strip">Delhi NCR &middot; From &#8377;3,200 a month</div>
  </div>
  <div class="card">
    <div class="head"><span>Consultation report</span><span>#04</span></div>
    <dl>
      <div class="row"><dt>Visit</dt><dd>{v['short']} &middot; Orthopaedics OPD</dd></div>
      <div class="row"><dt>Medication</dt><dd class="em">Oral anti-inflammatory withdrawn</dd></div>
      <div class="row"><dt>Why</dt><dd>eGFR 58, April renal panel</dd></div>
      <div class="row"><dt>Substituted</dt><dd>Diclofenac gel, twice daily</dd></div>
    </dl>
    <div class="foot">The surgeon had no access to the April panel. The record did.</div>
  </div>
</body></html>"""
    src = os.path.join(WORK, "og.html")
    open(src, "w", encoding="utf-8").write(html)
    dst = os.path.join(OUT, "og-report.png")
    chrome([f"--screenshot={dst}", "--window-size=1200,630", "file://" + src])
    Image.open(dst).convert("RGB").save(dst, optimize=True)
    print("og-report.png", os.path.getsize(dst), "bytes")


# -------------------------------------------------------------------- icons


def icons():
    """The mark's K with its rule, on ink. Rendered from the same outlines as
    the wordmark, so the tab, the letterhead and the header are one thing at
    three sizes rather than three drawings that resemble each other."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.misc.transform import Transform
    from fontTools.ttLib import TTFont

    font = TTFont(os.path.join(OUT, "fonts", "geist-latin.woff2"))
    upem = font["head"].unitsPerEm
    glyphs = font.getGlyphSet()
    name = font.getBestCmap()[ord("K")]
    pen = SVGPathPen(glyphs)
    glyphs[name].draw(TransformPen(pen, Transform(1.0 / upem, 0, 0, -1.0 / upem, 0, 0)))
    d = pen.getCommands()
    adv = font["hmtx"][name][0] / upem

    def svg(size, bg, fg):
        # 0.52 of the box for the letter, the rule under it at the letter's
        # own width, the whole thing optically centred.
        k = size * 0.46
        x = (size - adv * k) / 2
        y = size * 0.60
        rh = max(2.0, size * 0.055)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
                f'viewBox="0 0 {size} {size}">'
                f'<rect width="{size}" height="{size}" rx="{size * 0.22:.1f}" fill="{bg}"/>'
                f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.2f})">'
                f'<path fill="{fg}" d="{d}"/></g>'
                f'<rect x="{x:.2f}" y="{y + size * 0.09:.2f}" width="{adv * k:.2f}" '
                f'height="{rh:.2f}" fill="{fg}"/>'
                f'</svg>')

    # The SVG favicon is the one modern browsers use; the PNGs are the fallback.
    with open(os.path.join(OUT, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg(64, INK, CANVAS))
    print("favicon.svg", os.path.getsize(os.path.join(OUT, "favicon.svg")), "bytes")

    for size, path in ((96, "favicon.png"), (180, "apple-touch-icon.png")):
        src = os.path.join(WORK, f"icon-{size}.svg")
        open(src, "w", encoding="utf-8").write(svg(size, INK, CANVAS))
        dst = os.path.join(OUT, path)
        chrome([f"--screenshot={dst}", f"--window-size={size},{size}",
                "--default-background-color=00000000", "file://" + src])
        print(path, os.path.getsize(dst), "bytes")


# ---------------------------------------------------------------------- pdf


def sample_pdf():
    def visit_html(v):
        asked = "".join(
            f"<div class='qa'><p class='q'>{q}</p><p class='a'>{a}</p></div>"
            for q, a in v["asked"]
        )
        instr = "".join(f"<li>{i}</li>" for i in v["instructions"])
        meds = "".join(
            f"<tr><td class='m'>{n}</td><td class='s {s}'>{l}</td><td>{w}</td></tr>"
            for n, s, l, w in v["meds"]
        )
        tests = "".join(f"<li>{t}</li>" for t in v["tests"])
        flags = "".join(
            f"<li class='{s}'>{t} <em>({'open' if s == 'open' else 'resolved'})</em></li>"
            for t, s in v["unresolved"]
        )
        return f"""
<section class="visit">
  <div class="vhead">
    <h2>Visit {v['n']} &middot; {v['dept']}</h2>
    <span>{v['date']}</span>
  </div>
  <table class="kv">
    <tr><th>Seen at</th><td>{v['where']}</td></tr>
    <tr><th>Clinician</th><td>{v['doctor']}</td></tr>
  </table>

  <h3>What the family asked, and what came back</h3>
  {asked}

  <h3>Instructions, as given</h3>
  <ul>{instr}</ul>

  <h3>Medication</h3>
  <table class="meds">
    <thead><tr><th>Medicine</th><th>Change</th><th>Reason recorded</th></tr></thead>
    <tbody>{meds}</tbody>
  </table>
  <p class="recon"><strong>Reconciliation.</strong> {v['recon']}</p>

  <h3>Tests</h3>
  <ul>{tests}</ul>

  <h3>Unresolved</h3>
  <ul class="flags">{flags}</ul>

  <h3>Next visit</h3>
  <p>{v['nxt']}</p>
</section>"""

    head = "".join(f"<th>Visit {i + 1}<br><span>{build.VISITS[i]['short']}</span></th>"
                   for i in range(4))
    rows = ""
    for name, cells, marks in build.MED_TABLE:
        mark_at = {i: cls for cls, i in marks}
        tds = "".join(
            f"<td class='{mark_at.get(i, '')}'>{c if c else '&middot;'}</td>"
            for i, c in enumerate(cells)
        )
        rows += f"<tr><th>{name}</th>{tds}</tr>"

    html = f"""<!doctype html><html lang="en-IN"><head><meta charset="utf-8">
<title>Kinvisit sample consultation report</title><style>
{FONT_CSS}
  @page {{ size:A4; margin:16mm 15mm 18mm; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:var(--serif); font-size:10.5pt; line-height:1.5; color:{INK};
          margin:0; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  .watermark {{ position:fixed; top:44%; left:0; right:0; text-align:center;
                font-family:var(--serif); font-size:58pt; color:rgba(20,20,15,.06);
                transform:rotate(-24deg); letter-spacing:.04em; z-index:0; }}
  .sheet {{ position:relative; z-index:1; }}
  header.doc {{ border-bottom:2px solid {INK}; padding-bottom:14px; margin-bottom:22px; }}
  .brand {{ font-family:var(--sans); font-size:20pt; font-weight:500; letter-spacing:-.02em; }}
  .sub {{ font-family:var(--mono); font-size:7.5pt; letter-spacing:.14em;
          text-transform:uppercase; color:{INK_FAINT}; margin-top:5px; }}
  .banner {{ border:1px dashed {INK}; background:{CANVAS}; color:{INK};
             padding:9px 13px; font-size:9pt; margin:16px 0 24px; border-radius:6px; }}
  h2 {{ font-family:var(--serif); font-size:15pt; font-weight:500; margin:0; letter-spacing:-.01em; }}
  h3 {{ font-family:var(--mono); font-size:7.5pt; letter-spacing:.14em; text-transform:uppercase;
        color:{INK_FAINT}; font-weight:500; margin:16px 0 6px; }}
  p {{ margin:0 0 7px; }}
  ul {{ margin:0 0 7px; padding-left:17px; }}
  li {{ margin-bottom:3px; }}
  .visit {{ page-break-inside:avoid; break-inside:avoid; border:1px solid {LINE};
            border-radius:8px; padding:16px 18px; margin-bottom:16px; background:#fff; }}
  .vhead {{ display:flex; justify-content:space-between; align-items:baseline;
            border-bottom:1px solid {LINE}; padding-bottom:9px; margin-bottom:4px; }}
  .vhead span {{ font-family:var(--mono); font-size:8.5pt; color:{INK_FAINT}; }}
  table {{ width:100%; border-collapse:collapse; font-size:9.5pt; }}
  table.kv th {{ text-align:left; width:88px; font-family:var(--mono); font-size:7.5pt;
                 letter-spacing:.1em; text-transform:uppercase; color:{INK_FAINT};
                 font-weight:500; padding:5px 0; vertical-align:top; }}
  table.kv td {{ padding:5px 0; }}
  table.meds th {{ text-align:left; font-family:var(--mono); font-size:7.5pt;
                   letter-spacing:.1em; text-transform:uppercase; color:{INK_FAINT};
                   font-weight:500; border-bottom:1px solid {LINE}; padding:6px 8px 6px 0; }}
  table.meds td {{ padding:6px 8px 6px 0; border-bottom:1px solid {LINE}; vertical-align:top; }}
  table.meds td.m {{ font-weight:600; width:33%; }}
  table.meds td.s {{ width:17%; font-family:var(--mono); font-size:8pt; }}
  td.s.new, td.s.up {{ color:{SUBSTITUTED}; }}
  td.s.stop {{ color:{WITHDRAWN}; }}
  td.s.same {{ color:{INK_FAINT}; }}
  .qa {{ margin-bottom:9px; }}
  .q {{ font-weight:600; margin-bottom:2px; }}
  .a {{ color:{INK_SOFT}; margin:0; }}
  .recon {{ background:#F4F1EB; border-radius:2px; padding:9px 11px; font-size:9.5pt; }}
  ul.flags li.open {{ color:{INK_SOFT}; }}
  ul.flags li.resolved {{ color:{INK_SOFT}; }}
  ul.flags em {{ font-family:var(--mono); font-size:8pt; font-style:normal; }}
  .matrix {{ page-break-before:always; }}
  table.mx {{ margin-top:10px; }}
  table.mx th {{ text-align:left; font-family:var(--mono); font-size:7.5pt; letter-spacing:.08em;
                 text-transform:uppercase; color:{INK_FAINT}; font-weight:500;
                 border-bottom:1px solid {LINE}; padding:7px 8px; background:#F2ECE1; }}
  table.mx th span {{ letter-spacing:0; }}
  table.mx tbody th {{ background:none; text-transform:none; font-size:9.5pt; color:{INK};
                       font-weight:600; letter-spacing:0; font-family:var(--sans); }}
  table.mx td {{ padding:7px 8px; border-bottom:1px solid {LINE};
                 font-family:var(--mono); font-size:8.5pt; color:{INK_SOFT}; }}
  table.mx td.hit {{ color:{WITHDRAWN}; }}
  table.mx td.newly {{ color:{INK}; }}
  footer.doc {{ margin-top:22px; padding-top:12px; border-top:1px solid {LINE};
                font-size:8pt; color:{INK_FAINT}; }}
</style></head><body>
<div class="watermark">Sample. Not a real patient.</div>
<div class="sheet">
  <header class="doc">
    <div class="brand">Kinvisit</div>
    <div class="sub">Consultation record &middot; Delhi NCR &middot; prepared for the family</div>
  </header>

  <div class="banner"><strong>Sample. Not a real patient.</strong> Every name, date, dose, and
    result on this document is illustrative. It shows the format a Kinvisit family receives after
    each attended consultation.</div>

  {"".join(visit_html(v) for v in build.VISITS)}

  <section class="matrix">
    <h2>Medication history across all four visits</h2>
    <p style="margin-top:6px;color:{INK_SOFT}">Nobody holds this table today. Not the
      cardiologist, not the nephrologist, not the family. It is built one visit at a time, and it
      is what made the fourth visit safe.</p>
    <table class="mx">
      <thead><tr><th>Medicine</th>{head}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </section>

  <footer class="doc">
    Kinvisit is not a medical provider. Our companions document and clarify. They do not diagnose,
    prescribe, or advise. Every clinical decision on this record was made by the treating doctor.
    <br>{build.EMAIL} &middot; {build.PHONE_DISPLAY} &middot; kinvisit.in
  </footer>
</div>
</body></html>"""

    src = os.path.join(WORK, "sample-report.html")
    open(src, "w", encoding="utf-8").write(html)
    dst = os.path.join(OUT, "kinvisit-sample-report.pdf")
    chrome(["--no-pdf-header-footer", f"--print-to-pdf={dst}", "file://" + src])
    print("kinvisit-sample-report.pdf", os.path.getsize(dst), "bytes")


# ------------------------------------------------------------- consent kit


def consent_pdf():
    """M16. One page, English and Hindi, for a family to read to a parent."""
    def rows(pairs, lang=""):
        attr = f' lang="{lang}"' if lang else ""
        return "".join(
            f'<tr><th{attr}>{h}</th><td{attr}>{b}</td></tr>' for h, b in pairs
        )

    html = f"""<!doctype html><html lang="en-IN"><head><meta charset="utf-8">
<title>Kinvisit consent</title><style>
{FONT_CSS}
  @page {{ size:A4; margin:15mm 15mm 16mm; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:var(--sans); font-size:10pt; line-height:1.5; color:{INK}; margin:0;
          -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  header {{ border-bottom:2px solid {INK}; padding-bottom:12px; margin-bottom:16px; }}
  .brand {{ font-family:var(--sans); font-size:19pt; font-weight:500; letter-spacing:-.02em; }}
  .sub {{ font-family:var(--mono); font-size:7pt; letter-spacing:.14em; text-transform:uppercase;
          color:{INK_FAINT}; margin-top:4px; }}
  .draft {{ border:1px dashed {INK}; background:{CANVAS}; color:{INK}; padding:8px 12px;
            font-size:8.5pt; border-radius:6px; margin-bottom:16px; }}
  h2 {{ font-family:var(--serif); font-size:13pt; font-weight:600; margin:18px 0 8px; }}
  p.intro {{ margin:0 0 12px; color:{INK_SOFT}; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ text-align:left; width:33%; vertical-align:top; padding:7px 12px 7px 0;
        border-bottom:1px solid {LINE}; font-size:9.5pt; font-weight:650; }}
  td {{ vertical-align:top; padding:7px 0; border-bottom:1px solid {LINE}; color:{INK_SOFT}; }}
  .sign {{ margin-top:20px; padding-top:14px; border-top:2px solid {INK}; display:flex; gap:24px; }}
  .sign div {{ flex:1; }}
  .rule {{ height:1px; background:{LINE_STRONG}; margin:26px 0 6px; }}
  .cap {{ font-family:var(--mono); font-size:7pt; letter-spacing:.1em; text-transform:uppercase;
          color:{INK_FAINT}; }}
  footer {{ margin-top:18px; padding-top:10px; border-top:1px solid {LINE};
            font-size:7.5pt; color:{INK_FAINT}; }}
</style></head><body>
  <header>
    <div class="brand">Kinvisit</div>
    <div class="sub">What we ask your parent to agree to &middot; consent, one page</div>
  </header>

  <div class="draft"><strong>Draft.</strong> This document has not yet been reviewed by a lawyer,
    and the Hindi translation has not yet been checked by a native speaker. Do not use it to take
    consent from anyone until both are done.</div>

  <p class="intro">Read this to the person whose consultation it is. They decide, not the family
    member who is paying.</p>

  <table>{rows(C_POINTS)}</table>

  <div class="rule"></div>
  <p class="cap">The same page in Hindi</p>
  <table>{rows(C_HI, lang="hi")}</table>

  <div class="sign">
    <div><p class="cap">Patient name and signature</p><p>&nbsp;</p><p>&nbsp;</p></div>
    <div><p class="cap">Date</p><p>&nbsp;</p><p>&nbsp;</p></div>
    <div><p class="cap">Taken by</p><p>&nbsp;</p><p>&nbsp;</p></div>
  </div>

  <footer>
    Kinvisit is not a medical provider. Our companions document and clarify. They do not diagnose,
    prescribe, or advise. Consent can be withdrawn at any time by telling the companion or calling
    the number below, without anyone else's permission.
    <br>{build.EMAIL} &middot; {build.PHONE_DISPLAY} &middot; kinvisit.in
  </footer>
</body></html>"""

    src = os.path.join(WORK, "consent.html")
    open(src, "w", encoding="utf-8").write(html)
    dst = os.path.join(OUT, "kinvisit-consent.pdf")
    chrome(["--no-pdf-header-footer", f"--print-to-pdf={dst}", "file://" + src])
    print("kinvisit-consent.pdf", os.path.getsize(dst), "bytes")


if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    build_wordmark()
    og_card()
    icons()
    sample_pdf()
    consent_pdf()
