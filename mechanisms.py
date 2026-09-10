#!/usr/bin/env python3
"""
Kinvisit interactive mechanisms, rendered server side.

Every mechanism here renders a complete, readable, usable state in plain HTML.
JavaScript only ever upgrades what is already there. Each root element carries
data-mech, which is the only thing the client loader looks for, so a mechanism
whose script fails to load simply stays in its static state.
"""

import html
import json

import content as C


# ------------------------------------------------------------------ helpers


def rupees(n):
    """Indian digit grouping. 3200 -> 3,200. 165000 -> 1,65,000."""
    s = str(int(n))
    if len(s) <= 3:
        return "&#8377;" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return "&#8377;" + ",".join(parts) + "," + tail


def esc(s):
    return html.escape(str(s), quote=True)


def data_json(el_id, obj):
    """Inline JSON for a mechanism, so no mechanism costs a network round trip."""
    payload = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/json" id="{el_id}">{payload}</script>'


# =========================================================== M4. TRUST LEDGER


def _ledger_rows():
    L = C.LEDGER
    rows = [
        (L["visitsAttended"], "visits attended"),
        (L["reportsDelivered"], "reports delivered"),
        (L["deliveredSameDay"], "delivered same day"),
        (L["deliveredLate"], "delivered late, and not billed"),
        (L["hospitalsVisited"], "hospitals visited"),
    ]
    out = ""
    for value, label in rows:
        out += (f'<div class="lg-row"><span class="lg-n">{value}</span>'
                f'<span class="lg-l">{label}</span></div>')
    if L.get("medianHoursToReport"):
        h = L["medianHoursToReport"]
        hours, mins = int(h), round((h - int(h)) * 60)
        out += (f'<div class="lg-row"><span class="lg-n lg-time">{hours}h {mins:02d}m</span>'
                f'<span class="lg-l">median time from consultation to report</span></div>')
    return out


def ledger_band():
    """Homepage band. Renders nothing at all until the numbers are real."""
    L = C.LEDGER
    if not L.get("published"):
        return ""
    return f"""<section class="sunk" id="ledger">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">The record so far</p>
      <h2>Since {esc(_date(L['since']))}</h2>
    </div>
    <div class="ledger" style="margin-top:24px">{_ledger_rows()}</div>
    <p class="fine" style="margin-top:16px">Updated by hand. Last updated
      {esc(_date(L['lastUpdated']))}. If a number here is wrong, tell us and we will correct it
      publicly. <a href="/promise">Every time we have missed the same-day promise</a>.</p>
  </div>
</section>"""


def _date(iso):
    if not iso:
        return "not started"
    months = ["January", "February", "March", "April", "May", "June", "July", "August",
              "September", "October", "November", "December"]
    y, m, d = iso.split("-")
    return f"{int(d)} {months[int(m) - 1]} {y}"


def ledger_full():
    """The /proof version, with the incidents listed."""
    L = C.LEDGER
    if not L.get("published"):
        return ("""<div class="honest">
  <h3>The ledger is not published yet</h3>
  <p>We have not attended enough visits to publish a count that means anything. The moment we
     have, this page will carry the totals, including every report we deliver late. We would
     rather show nothing than show a number we cannot stand behind.</p>
</div>""")
    return f"""<div class="ledger">{_ledger_rows()}</div>
<p class="fine" style="margin-top:14px">Since {esc(_date(L['since']))}. Updated by hand, last on
  {esc(_date(L['lastUpdated']))}.</p>"""


# ============================================================ M14. PROMISE LOG


def promise_log():
    L = C.LEDGER
    incidents = [i for i in L.get("lateIncidents", []) if not i.get("_comment")]
    if not L.get("published"):
        body = """<div class="honest">
  <h3>Nothing to log yet</h3>
  <p>We have not attended enough visits for this log to mean anything. When we miss the promise
     for the first time, it will appear here with the cause and with what we changed because of
     it. That is the whole point of the page.</p>
</div>"""
    elif not incidents:
        body = """<p class="lede">We have not missed it yet. When we do, it will appear here.</p>"""
    else:
        body = ""
        for i in incidents:
            body += f"""<article class="incident">
  <h3>{esc(_date(i['date']))}</h3>
  <p>{esc(i['reason'])}</p>
  <dl class="incident-meta">
    <div><dt>Hospital</dt><dd>{esc(i.get('hospital', 'Withheld'))}</dd></div>
    <div><dt>Billed</dt><dd>{'No' if not i.get('billed') else 'Yes'}</dd></div>
    <div><dt>Cause</dt><dd>{esc(i.get('cause', 'Not recorded'))}</dd></div>
    <div><dt>What we changed</dt><dd>{esc(i.get('changeMade', 'Nothing yet'))}</dd></div>
  </dl>
</article>"""
    return body


# ============================================================== M5. ROSTER


def roster(compact=False, photo=True):
    """photo=False on a page that already shows the same face higher up. One
    person's portrait twice on one page reads as padding, not as proof."""
    people = C.COMPANIONS
    if not people:
        return ("""<div class="honest"><h3>No companions yet</h3>
<p>We are hiring our first companions now. Until then, the founder attends every visit.</p></div>""")

    cards = ""
    for p in people:
        n = esc(p["photo"]) if p.get("photo") else ""
        photo = (f'<div class="rost-photo"><picture>'
                 f'<source type="image/webp" srcset="/assets/photos/{n}.webp 1x,'
                 f' /assets/photos/{n}@2x.webp 2x">'
                 f'<img src="/assets/photos/{n}.jpg"'
                 f' srcset="/assets/photos/{n}.jpg 1x, /assets/photos/{n}@2x.jpg 2x"'
                 f' alt="{esc(p["photoAlt"])}" width="200" height="200"'
                 ' loading="lazy" decoding="async"></picture></div>') if (photo and p.get("photo")) else ""
        police = (f'Police verified {esc(_date(p["policeVerified"]))}'
                  if p.get("policeVerified") else "Verification in progress")
        cert = (f'Kinvisit protocol certified {esc(_date(p["protocolCertified"]))}'
                if p.get("protocolCertified") else "In training")
        visits = p.get("visitsAttended", 0)
        cards += f"""<article class="rost-card">
  {photo}
  <div class="rost-body">
    <h3>{esc(p['name'])}</h3>
    <p class="rost-role">{esc(p['role'])}</p>
    <p class="rost-qual">{esc(p['qualification'])}</p>
    <ul class="rost-facts">
      <li>{police}</li>
      <li>{cert}</li>
      <li>{visits} visit{'s' if visits != 1 else ''} attended</li>
      <li>{esc(', '.join(p.get('languages', [])))}</li>
    </ul>
    <blockquote class="rost-words">{esc(p['inTheirWords'])}</blockquote>
  </div>
</article>"""

    n = len(people)
    return f'<div class="roster roster-{min(n, 3)}">{cards}</div>'


# ================================================== M6. ANNOTATED REPORT TOGGLE


def annotation_for(section_title):
    for title, text in C.ANNOTATIONS:
        if title == section_title:
            return text
    return None


def annotation_markup(section_title, uid):
    """Rendered inside each report section. Visible by default, collapsed by JS."""
    text = annotation_for(section_title)
    if not text:
        return ""
    return f"""<div class="annot" id="annot-{uid}" data-annot-section="{esc(section_title)}">
  <p><span class="annot-tag">Why this section is here</span>{text}</p>
</div>"""


def annotation_toggle():
    return """<div class="annot-toggle" data-mech="annotations">
  <span class="annot-toggle-label" id="annot-toggle-label">Reading mode</span>
  <div class="seg" role="group" aria-labelledby="annot-toggle-label">
    <button type="button" class="seg-btn" data-annot-mode="plain" aria-pressed="true">Read the report</button>
    <button type="button" class="seg-btn" data-annot-mode="annotated" aria-pressed="false">Read why each part is there</button>
  </div>
</div>"""


# ==================================================== M1. COMPOUNDING SCRUBBER


def compounding_scrubber():
    D = C.COMPOUNDING
    visits = D["visits"]
    order = D["medicationOrder"]
    q = D["carriedQuestion"]

    # Static table: the whole year, every visit, no JavaScript required.
    head = "".join(
        f'<th scope="col"><span class="cs-vn">Visit {v["n"]}</span>'
        f'<span class="cs-vd">{esc(v["date"])}</span>'
        f'<span class="cs-vs">{esc(v["specialty"])}</span></th>'
        for v in visits
    )
    rows = ""
    for med in order:
        cells = ""
        for v in visits:
            val = v["medications"].get(med)
            if not val:
                cells += ('<td class="cs-none"><span aria-hidden="true">&middot;</span>'
                          '<span class="vh">not prescribed</span></td>')
            elif val == "Withdrawn":
                cells += ('<td class="cs-stop"><span class="cs-mark" aria-hidden="true">&#10005;</span>'
                          'Withdrawn</td>')
            else:
                cells += f'<td>{esc(val)}</td>'
        rows += (f'<tr><th scope="row">{esc(med)}</th>{cells}'
                 f'<td class="cs-spacer"></td></tr>')

    steps = "".join(
        f'<button type="button" class="cs-step" data-visit="{v["n"]}" '
        f'aria-label="Visit {v["n"]}, {esc(v["date"])}, {esc(v["specialty"])}">{v["n"]}</button>'
        for v in visits
    )

    return f"""<section class="panel" id="compounding">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">What compounds</p>
      <h2>Drag through a year. This is what the twelfth doctor is shown.</h2>
    </div>

    <div class="cs" data-mech="compounding">
      {data_json("compounding-data", D)}

      <div class="cs-controls" hidden>
        <button type="button" class="cs-arrow" data-cs-nav="prev" aria-label="Previous visit">&#8592;</button>
        <div class="cs-track" role="group" aria-label="Choose a visit">{steps}</div>
        <button type="button" class="cs-arrow" data-cs-nav="next" aria-label="Next visit">&#8594;</button>
        <button type="button" class="cs-showall" data-cs-showall hidden>Show all twelve</button>
      </div>

      <p class="cs-counter" role="status" aria-live="polite">{esc(visits[-1]["counterLine"])}</p>

      <div class="cs-question" data-cs-question>
        <span class="cs-q-tag" data-cs-qtag>Answered</span>
        <span class="cs-q-text">{esc(q["text"])}</span>
        <span class="cs-q-res" data-cs-qres>{esc(q["resolution"])}</span>
      </div>

      <div class="cs-scroll" tabindex="0" role="region" aria-label="Medication history across twelve visits">
        <table class="cs-table">
          <caption class="vh">Every medicine recorded at each of twelve consultations</caption>
          <thead><tr><th scope="col">Medicine</th>{head}<th class="cs-spacer"><span class="vh">Visits still to come</span></th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      <p class="scroll-hint fine">Scroll the table sideways to move through the year.</p>
    </div>

    <p class="prose fine" style="margin-top:20px">Illustrative. Not a real patient. Nobody holds
      this table today. Not the cardiologist, not the nephrologist, not the family. It is built one
      visit at a time, and there is no way to build it retroactively.</p>
  </div>
</section>"""


# ========================================================= M2. GAP CALCULATOR


def gap_calculator():
    """Pure enhancement. Renders nothing without JavaScript, by design."""
    qs = ""
    for i, q in enumerate(C.GAP_Q, start=1):
        opts = "".join(
            f'<button type="button" class="gap-opt" data-gap-q="{q["id"]}" data-gap-v="{v}">{lbl}</button>'
            for v, lbl in q["options"]
        )
        qs += f"""<fieldset class="gap-q" data-gap-step="{i}">
  <legend>{q['q']}</legend>
  <div class="gap-opts">{opts}</div>
</fieldset>"""

    return f"""<section class="gap-section" data-mech="gap" hidden>
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Your number, not a statistic</p>
      <h2>How much of your parent's care is written down anywhere?</h2>
    </div>
    <div class="gap prose" style="margin-top:24px">
      {qs}
      <div class="gap-out" data-gap-out hidden role="status" aria-live="polite"></div>
    </div>
  </div>
</section>"""


# ====================================================== M7. WHATSAPP BUILDER


WA_STEPS = [
    ("location", "Where do you live?",
     ["Delhi NCR", "Elsewhere in India", "UK", "US", "Gulf", "Singapore", "Other"]),
    ("appointment", "Is the appointment booked?",
     ["Yes, I have a date", "Not yet", "I need help getting one"]),
    ("department", "Which department?",
     ["Cardiology", "Orthopaedics", "Nephrology", "Endocrinology", "Neurology",
      "General medicine", "Other"]),
]


def wa_builder(wa_number):
    steps = ""
    for i, (key, question, options) in enumerate(WA_STEPS, start=1):
        opts = "".join(
            f'<button type="button" class="wb-opt" data-wb-k="{key}" data-wb-v="{esc(o)}">{o}</button>'
            for o in options
        )
        steps += f"""<fieldset class="wb-step" data-wb-step="{i}">
  <legend><span class="wb-num">{i}</span>{question}</legend>
  <div class="wb-opts">{opts}</div>
</fieldset>"""

    return f"""<div class="wb" data-mech="wa-builder" data-wa-number="{wa_number}">
  <div class="wb-inner" hidden>
    {steps}
    <fieldset class="wb-step" data-wb-step="4">
      <legend><span class="wb-num">4</span>Anything you want raised in the room? Optional.</legend>
      <label class="vh" for="wb-note">Anything you want raised in the room</label>
      <textarea id="wb-note" class="wb-note" rows="3" maxlength="300"
        placeholder="For example: her hand has been swelling for months and we do not know if it has ever been mentioned."></textarea>
      <p class="fine">We compose this in your browser. Nothing is sent to us until you press send
        in WhatsApp.</p>
    </fieldset>

    <div class="wb-preview" data-wb-preview hidden>
      <h3>This is the message you will send</h3>
      <pre class="wb-msg" data-wb-msg tabindex="0"></pre>
      <div class="btn-row">
        <a class="btn btn-primary" data-wb-send href="#">Open WhatsApp with this message</a>
        <button type="button" class="btn btn-ghost" data-wb-edit>Edit</button>
        <button type="button" class="btn btn-ghost" data-wb-copy>Copy instead</button>
      </div>
      <p class="fine" data-wb-copied hidden role="status">Copied. Paste it into WhatsApp.</p>
    </div>
  </div>
</div>"""


# ========================================================= M8. CALLBACK CLOCK


CALLBACK_WINDOWS = [
    ("morning", "8am to 11am", 8, 11),
    ("afternoon", "1pm to 4pm", 13, 16),
    ("evening", "6pm to 9pm", 18, 21),
]


def callback_clock():
    opts = "".join(
        f'<button type="button" class="cc-win" data-cc-win="{wid}" data-cc-from="{a}" '
        f'data-cc-to="{b}" aria-pressed="{"true" if wid == "evening" else "false"}">'
        f'<span class="cc-win-l">{label}</span><span class="cc-win-d" data-cc-delhi></span></button>'
        for wid, label, a, b in CALLBACK_WINDOWS
    )
    return f"""<div class="cc" data-mech="callback">
  <noscript><p class="cc-static">We call between 6pm and 9pm in your local time, wherever you
    are. Tell us your city on the form below and we will work the timing out around you.</p></noscript>

  <div class="cc-live" hidden>
    <p class="cc-times" role="status" aria-live="polite">
      It is <strong data-cc-local>...</strong> where you are, and <strong data-cc-ist>...</strong>
      in Delhi.
    </p>
    <p class="cc-promise">We will call you between <strong data-cc-window>6pm and 9pm</strong> your
      time. In Delhi that is <strong data-cc-window-ist>...</strong>. That is our problem, not
      yours.</p>
    <details class="cc-details">
      <summary>Pick a different window</summary>
      <div class="cc-wins">{opts}</div>
      <p class="fine" data-cc-zone></p>
    </details>
  </div>

  <div class="cc-fallback" hidden>
    <p>We could not work out your time zone, and we would rather ask than guess.</p>
    <label for="cc-manual">Where are you?</label>
    <select id="cc-manual" data-cc-manual>
      <option value="">Choose</option>
      <option value="Asia/Kolkata">India</option>
      <option value="Europe/London">United Kingdom</option>
      <option value="America/New_York">US East</option>
      <option value="America/Los_Angeles">US West</option>
      <option value="Asia/Dubai">Gulf</option>
      <option value="Asia/Singapore">Singapore</option>
      <option value="Australia/Sydney">Australia</option>
    </select>
  </div>
</div>"""


# ========================================================== M10. SIBLING SHARE


def share_block(site_url, compact=False):
    variants = []
    for v in C.SHARE_VARIANTS:
        variants.append({
            "id": v["id"],
            "label": v["label"],
            "text": v["text"].format(
                url=site_url,
                record=rupees(3200).replace("&#8377;", "₹"),
                record2=rupees(5400).replace("&#8377;", "₹"),
            ),
        })
    chips = "".join(
        f'<button type="button" class="sh-chip" data-sh-v="{v["id"]}" '
        f'aria-pressed="{"true" if i == 0 else "false"}">{v["label"]}</button>'
        for i, v in enumerate(variants)
    )
    cls = "share share-compact" if compact else "share"
    return f"""<div class="{cls}" data-mech="share">
  {data_json("share-data", variants)}
  <button type="button" class="btn btn-ghost sh-open" data-sh-open>Send this to your brother or sister</button>
  <noscript><a class="btn btn-ghost" href="/conversations">Words to send your brother or sister</a></noscript>
  <div class="sh-panel" data-sh-panel hidden>
    <div class="sh-chips" role="group" aria-label="Who are you sending this to">{chips}</div>
    <label class="vh" for="sh-text">Message to send</label>
    <textarea id="sh-text" class="sh-text" data-sh-text rows="9"></textarea>
    <div class="btn-row">
      <button type="button" class="btn btn-primary" data-sh-send>Send</button>
      <button type="button" class="btn btn-ghost" data-sh-copy>Copy</button>
      <button type="button" class="btn btn-ghost" data-sh-close>Close</button>
    </div>
    <p class="fine" data-sh-status role="status"></p>
  </div>
</div>"""


def share_banner():
    return f"""<div class="via-banner" data-mech="via" hidden>
  <div class="wrap via-in">
    <p>{C.SHARE_BANNER}</p>
    <a class="btn btn-sm btn-dark" href="/record">Read the report</a>
    <button type="button" class="via-x" data-via-close aria-label="Dismiss">&#10005;</button>
  </div>
</div>"""


# ======================================================= M12. HOSPITAL CHECKER


def hospital_checker(compact=False):
    H = C.HOSPITALS
    options = "".join(f'<option value="{esc(h["name"])}"></option>' for h in H["hospitals"])
    lookup = [{"name": h["name"], "aliases": h["aliases"], "area": h["area"],
               "visits": h["visitsAttended"], "wait": h["typicalWaitMinutes"]}
              for h in H["hospitals"]]
    areas = "".join(f'<span class="area">{esc(a)}</span>' for a in H["areas"])

    static = f'<div class="areas" style="margin-top:16px">{areas}</div>'

    return f"""<div class="hc" data-mech="hospitals">
  {data_json("hospital-data", {"hospitals": lookup, "areas": H["areas"]})}
  <label class="hc-label" for="hc-input">Which hospital does your parent go to?</label>
  <div class="hc-row">
    <input id="hc-input" class="hc-input" type="text" list="hc-list" autocomplete="off"
      placeholder="Start typing a hospital name">
    <button type="button" class="btn btn-primary btn-sm" data-hc-go>Check</button>
  </div>
  <datalist id="hc-list">{options}</datalist>
  <div class="hc-out" data-hc-out hidden role="status" aria-live="polite"></div>
  <div class="hc-static">
    <p class="fine">We attend at any hospital, clinic, or diagnostic centre in these areas.</p>
    {static}
  </div>
</div>"""


# ====================================================== M13. ESCALATION LADDER


def escalation():
    tabs, panels = "", ""
    for i, e in enumerate(C.ESCALATION):
        tabs += (f'<button type="button" class="esc-tab" data-esc="{e["id"]}" '
                 f'aria-pressed="{"true" if i == 0 else "false"}">{esc(e["q"])}</button>')
        steps = "".join(
            f'<li class="esc-step"><span class="esc-t">{esc(t)}</span>'
            f'<span class="esc-d">{esc(d)}</span></li>'
            for t, d in e["steps"]
        )
        note = f'<p class="esc-note">{esc(e["note"])}</p>' if e.get("note") else ""
        panels += f"""<div class="esc-panel" id="esc-{e['id']}">
  <h3>{esc(e['q'])}</h3>
  <ol class="esc-steps">{steps}</ol>
  {note}
</div>"""
    return f"""<div class="esc" data-mech="escalation">
  <div class="esc-tabs" role="group" aria-label="Choose a situation">{tabs}</div>
  {panels}
</div>"""


# ============================================================ B3. THE PRICING


def _plan_card(p, featured=False):
    inc = "".join(f"<li>{i}</li>" for i in p["includes"])
    exc = ""
    if p["excludes"]:
        items = "".join(f"<li>{e}</li>" for e in p["excludes"])
        exc = (f'<div class="plan-exc"><p class="plan-exc-h">Not included</p>'
               f'<ul class="list no">{items}</ul>'
               f'<p class="fine">{p["excludeNote"]}</p></div>')
    kicker = f'<span class="flag-lbl">{p["kicker"]}</span>' if p.get("kicker") else ""
    btn = "btn-primary" if featured else "btn-ghost"
    return f"""<div class="plan" data-plan="{p['id']}" id="plan-{p['id']}">
  {kicker}
  <span class="per">{p['per']}</span>
  <span class="amt">{rupees(p['price'])}</span>
  <span class="fx" data-fx="{p['price']}" hidden></span>
  <p class="plan-sum">{p['summary']}</p>
  <ul>{inc}</ul>
  {exc}
  <p class="plan-rec" data-plan-rec hidden></p>
  <a class="btn {btn} btn-block" href="/book">Request a visit</a>
</div>"""


def pricing_recommender():
    opts = "".join(
        f'<button type="button" class="pr-opt" data-pr="{o["value"]}" data-plan="{o["plan"]}" '
        f'aria-pressed="false">{o["label"]}</button>'
        for o in C.DOCTOR_COUNT_OPTIONS
    )
    payload = {o["value"]: {"plan": o["plan"], "reason": o["reason"],
                            "singleLine": o["singleVisitLine"]}
               for o in C.DOCTOR_COUNT_OPTIONS}
    return f"""<div class="pr" data-mech="pricing">
  {data_json("pricing-data", payload)}
  <p class="pr-q" id="pr-q">How many doctors does your parent see?</p>
  <div class="pr-opts" role="group" aria-labelledby="pr-q">{opts}</div>
</div>"""


def plans_block():
    cards = "".join(_plan_card(p, featured=(p["id"] == "record")) for p in C.PLANS)
    e = C.EXTRA_VISIT
    return f"""{pricing_recommender()}
<div class="plans plans-3">{cards}</div>
<div class="extra-visit">
  <div>
    <p class="extra-h">{e['label']}</p>
    <p class="fine">{e['note']} Available only to families on a plan, because it is priced as a
      top-up rather than as a way to buy attendance without the record.</p>
  </div>
  <p class="extra-amt">{rupees(e['price'])}<span class="fx" data-fx="{e['price']}" hidden></span></p>
</div>"""


def currency_note():
    fx = {"date": C.FX_DATE,
          "rates": {k: {"symbol": v["symbol"], "rate": v["rate"], "regions": v["regions"]}
                    for k, v in C.FX.items()}}
    return f"""{data_json("fx-data", fx)}
<p class="fine fx-note" data-mech="currency" hidden>
  Prices are charged in rupees. The second figure is an approximate conversion at the rate on
  {C.FX_DATE}, shown so you know roughly what you are committing to. We do not charge in any other
  currency.
</p>"""


def overseas_tier():
    o = C.OVERSEAS
    inc = "".join(f"<li>{i}</li>" for i in o["includes"])
    return f"""<section class="overseas" data-mech="overseas" hidden id="abroad">
  <div class="wrap">
    <div class="prose">
      <p class="eyebrow">Because you are not in Delhi</p>
      <h2>{o['name']}</h2>
      <p class="lede">{o['summary']}</p>
    </div>
    <div class="ov-card">
      <div>
        <span class="per">{o['per']}</span>
        <span class="amt">{rupees(o['price'])}</span>
        <span class="fx" data-fx="{o['price']}" hidden></span>
      </div>
      <ul class="list yes">{inc}</ul>
    </div>
    <p class="prose fine" style="margin-top:16px">{o['note']} The rupee price is the same price we
      show everyone. We do not charge more because of where you live, and this tier exists because
      it contains different work, not a different market.</p>
    <div class="btn-row" style="margin-top:18px"><a class="btn btn-primary" href="/book">Request a visit</a></div>
  </div>
</section>"""


def overseas_toggle():
    """A real button on its own line, not an inline link, so the tap target is
    a full 44px on a phone."""
    return """<p class="ov-toggle"><button type="button" class="btn btn-ghost btn-sm" data-ov-show>
  I live outside India. Show me what changes.</button></p>"""


def policies_block():
    rows = "".join(
        f'<div class="pol"><h3>{esc(t)}</h3><p>{esc(b)}</p></div>'
        for t, b in C.POLICIES
    )
    return f'<div class="policies">{rows}</div>'


# ========================================================== M15. CONTEXT BAR


def context_bar(site_url):
    return f"""<div class="ctxbar" data-mech="ctxbar" hidden>
  <div class="ctxbar-in">
    <a class="btn btn-primary btn-sm" href="/book">Book a visit</a>
    <button type="button" class="btn btn-ghost btn-sm" data-ctx-share>Send this to your sibling</button>
    <button type="button" class="ctx-x" data-ctx-close aria-label="Dismiss this bar">&#10005;</button>
  </div>
</div>"""


# ========================================================== M16. CONSENT KIT


def consent_block():
    points = "".join(
        f'<div class="con-row"><h3>{esc(t)}</h3><p>{esc(b)}</p></div>'
        for t, b in C.CONSENT_POINTS
    )
    return f"""<div class="prose">
  <h2>Your parent has to agree to this.</h2>
  <p>{C.CONSENT_INTRO}</p>
</div>
<div class="consent" style="margin-top:26px">{points}</div>
<div class="honest" style="margin-top:24px">
  <h3>Withdrawal is theirs, not yours</h3>
  <p>{C.CONSENT_WITHDRAWAL}</p>
  <p>Some families find that line uncomfortable. We publish it because it is the correct position,
     and because a consent your parent cannot withdraw is not a consent.</p>
</div>"""


# ======================================================== M11. CONVERSATIONS


def conversations():
    out = ""
    for c in C.CONVERSATIONS:
        blocks = ""
        for heading, items in c["blocks"]:
            lis = "".join(f"<li>{i.format(record=rupees(3200))}</li>" for i in items)
            blocks += f'<h3>{esc(heading)}</h3><ul class="list plain">{lis}</ul>'
        out += f"""<section class="conv" id="conv-{c['id']}">
  <h2>{esc(c['q'])}</h2>
  <p class="lede">{esc(c['lede'])}</p>
  {blocks}
</section>"""
    return out
