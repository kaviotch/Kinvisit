#!/usr/bin/env python3
"""
Drives every mechanism in a real browser and asserts on the result.

Headless Chrome will not scroll, so each page is opened in a window tall
enough to hold the whole document. Every mechanism root is then inside the
initial viewport, the loader's first sweep picks all of them up, and the
assertions run against a fully initialised page.

    python3 preview.py &      then      python3 test_mechanisms.py
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = "http://localhost:8899"

CASES = [
    ("index.html", 1200, 16000, r"""
  t('M1 controls revealed',        !q('.cs-controls').hidden);
  t('M1 starts at visit 1',        /^Visit 1\./.test(q('.cs-counter').textContent));
  t('M1 only visit 1 column',      vis('.cs-table thead th') === 3);  /* medicine + visit 1 + spacer */
  t('M1 hides unstarted medicines',vis('.cs-table tbody tr') === 2);
  q('.cs-step[data-visit="6"]').click();
  t('M1 visit 6 counter',          /^Visit 6\./.test(q('.cs-counter').textContent));
  t('M1 question resolves at 6',   q('[data-cs-question]').classList.contains('resolved'));
  q('.cs-step[data-visit="4"]').click();
  t('M1 question open at 4',       !q('[data-cs-question]').classList.contains('resolved'));
  t('M1 question shown at 4',      !q('[data-cs-question]').hidden);
  q('.cs-step[data-visit="1"]').click();
  t('M1 question hidden at 1',     q('[data-cs-question]').hidden);
  q('.cs-step[data-visit="12"]').click();
  t('M1 all 12 columns at end',    vis('.cs-table thead th') === 14);
  t('M1 all 10 medicines at end',  vis('.cs-table tbody tr') === 10);
  t('M1 withdrawn cells marked',   q('.cs-table td.cs-stop') !== null);

  t('M2 calculator revealed',      !q('[data-mech=gap]').hidden);
  click('[data-gap-q=doctors][data-gap-v="4"]');
  click('[data-gap-q=frequency][data-gap-v="12"]');
  click('[data-gap-q="full-list"][data-gap-v=no]');
  t('M2 arithmetic',               txt('[data-gap-out]').indexOf('48 consultations') > -1);
  t('M2 fraction of picture',      txt('[data-gap-out]').indexOf('a quarter of the picture') > -1);
  click('[data-gap-q="full-list"][data-gap-v=yes]');
  t('M2 honest when covered',      txt('[data-gap-out]').indexOf('better covered than most') > -1);
  t('M2 no alarm when covered',    txt('[data-gap-out]').indexOf('quarter of the picture') === -1);
  click('[data-gap-q=doctors][data-gap-v="1"]');
  click('[data-gap-q="full-list"][data-gap-v=no]');
  t('M2 single doctor copy',       txt('[data-gap-out]').indexOf('one doctor there is at least one') > -1);

  t('M6 seven annotations',        document.querySelectorAll('.annot').length === 7);
  t('M6 plain by default',         q('.annot').hidden === true);
  click('[data-annot-mode=annotated]');
  t('M6 opens annotations',        !q('.annot').hidden);
  click('[data-annot-mode=plain]');
  t('M6 collapses again',          q('.annot').hidden === true);

  t('M13 one branch shown',        vis('.esc-panel') === 1);
  click('.esc-tab[data-esc=emergency]');
  t('M13 switches branch',         !q('#esc-emergency').hidden && q('#esc-conflict').hidden);
  t('M13 emergency is honest',     txt('#esc-emergency').indexOf('not a clinician on duty') > -1);

  t('M15 context bar shown',       !q('[data-mech=ctxbar]').hidden);
  click('[data-ctx-close]');
  t('M15 dismisses',               q('[data-mech=ctxbar]').hidden);

  click('[data-sh-open]');
  t('M10 panel opens',             !q('[data-sh-panel]').hidden);
  t('M10 sibling text',            q('[data-sh-text]').value.indexOf('nursing-trained') === -1);
  t('M10 carries the price',       q('[data-sh-text]').value.indexOf('3,200') > -1);
  click('.sh-chip[data-sh-v=parent]');
  t('M10 parent variant differs',  q('[data-sh-text]').value.indexOf('They just write') > -1);

  t('no stat renders as zero',     !/(^|[^\d])0%/.test(copy()));
"""),

    ("book.html", 1200, 9000, r"""
  t('M7 builder revealed',         !q('.wb-inner').hidden);
  t('M7 preview hidden first',     q('[data-wb-preview]').hidden);
  click('[data-wb-k=location][data-wb-v=UK]');
  click('[data-wb-k=appointment][data-wb-v="Not yet"]');
  click('[data-wb-k=department][data-wb-v=Nephrology]');
  t('M7 preview appears',          !q('[data-wb-preview]').hidden);
  var msg = txt('[data-wb-msg]');
  t('M7 composes location',        msg.indexOf("I'm in: UK") > -1);
  t('M7 composes department',      msg.indexOf('Department: Nephrology') > -1);
  t('M7 signs the source',         msg.indexOf('Sent from kinvisit.in') > -1);
  t('M7 builds the wa.me link',    q('[data-wb-send]').href.indexOf('wa.me/918920428806') > -1);
  q('#wb-note').value = 'her hand has been swelling';
  q('#wb-note').dispatchEvent(new Event('input'));
  t('M7 includes the note',        txt('[data-wb-msg]').indexOf('To raise: her hand') > -1);
  t('M7 note stays client side',   q('[data-wb-send]').href.indexOf('swelling') > -1);

  t('M8 clock is live',            !q('.cc-live').hidden);
  t('M8 local time rendered',      /\d/.test(txt('[data-cc-local]')));
  t('M8 india time rendered',      /\d/.test(txt('[data-cc-ist]')));
  t('M8 delhi range rendered',     /(am|pm)/.test(txt('[data-cc-window-ist]')));
  t('M8 half hour offset kept',    /:\d\d|:30/.test(txt('[data-cc-ist]')) );
  click('.cc-win[data-cc-win=morning]');
  t('M8 window switches',          txt('[data-cc-window]').indexOf('8am') > -1);

  t('A2 four required fields',     document.querySelectorAll('form[name=visit-request] input[required]:not([type=checkbox])').length === 4);
  t('A2 plus the consent tick',    document.querySelectorAll('form[name=visit-request] input[type=checkbox][required]').length === 1);
  t('A2 no demo disclaimer',       copy().indexOf('not dispatch') === -1);
  t('M16 consent block present',   copy().indexOf('has to agree to this') > -1);
  t('M16 withdrawal is theirs',    copy().indexOf('do not need your permission') > -1);
"""),

    ("hospitals.html", 1200, 7000, r"""
  function ask(v){ q('.hc-input').value = v; q('[data-hc-go]').click(); return q('.hc-out'); }
  t('M12 known hospital',          ask('max saket').textContent.indexOf('Max Super Speciality, Saket') > -1);
  t('M12 admits never visited',    q('.hc-out').textContent.indexOf('not been to this one yet') > -1);
  t('M12 alias match',             ask('Sir Ganga Ram').textContent.indexOf('Sir Ganga Ram') > -1);
  t('M12 ncr but unlisted',        ask('Some clinic in Dwarka').className.indexOf('miss') > -1);
  t('M12 says no to Chennai',      ask('Apollo Chennai').className.indexOf('outside') > -1);
  t('M12 says no to Bangalore',    ask('Manipal Bangalore').className.indexOf('outside') > -1);
  t('M12 still yes to Delhi Apollo', ask('Indraprastha Apollo').textContent.indexOf('Apollo') > -1);
"""),

    ("pricing.html", 1200, 12000, r"""
  t('B2 three plans',              document.querySelectorAll('.plan').length === 3);
  t('B2 single visit is 2,200',    txt('#plan-single .amt').indexOf('2,200') > -1);
  t('B2 record is 3,200',          txt('#plan-record .amt').indexOf('3,200') > -1);
  t('B2 single excludes the file', txt('#plan-single').indexOf('No file is maintained') > -1);
  click('.pr-opt[data-pr="3"]');
  t('B3 recommends two visits',    q('#plan-record2').classList.contains('recommended'));
  t('B3 gives the reason',         txt('#plan-record2 [data-plan-rec]').indexOf('no single doctor sees the full medicine list') > -1);
  t('B3 warns on single visit',    txt('#plan-single [data-plan-rec]').indexOf('next doctor still starts from nothing') > -1);
  click('.pr-opt[data-pr="1"]');
  t('B3 one doctor gets single',   q('#plan-single').classList.contains('recommended'));
  t('B4 no-show policy',           copy().indexOf('your next visit is free') > -1);
  t('B4 cancellation policy',      copy().indexOf('More than four hours before') > -1);
  click('[data-ov-show]');
  t('M9 overseas tier reveals',    !q('[data-mech=overseas]').hidden);
  t('M9 tier is different work',   txt('[data-mech=overseas]').indexOf('twenty minute call') > -1);
  t('M9 same rupee price shown',   txt('[data-mech=overseas]').indexOf('7,500') > -1);
"""),

    ("record.html", 1200, 20000, r"""
  t('M6 toggle present',           q('[data-mech=annotations]') !== null);
  t('M6 annotations on all four',  document.querySelectorAll('.annot').length === 28);
  t('M6 all collapsed by default', vis('.annot') === 0);
  t('four visit panels',           document.querySelectorAll('.visit-panel').length === 4);
  t('one panel shown by tabs',     vis('.visit-panel') === 1);
"""),
    # M20. The rail. What is asserted is that it carries real orientation and
    # that it never swallows something else in the hero, which is the mistake
    # the first version made on /record.
    ("record.html", 1440, 3000, r"""
  t('M20 rail present',            !!q('.hero-rail'));
  t('M20 rail beside the text',    q('.hero-rail').getBoundingClientRect().left >
                                   q('.hero-main').getBoundingClientRect().right - 1);
  t('M20 rail has four facts',     document.querySelectorAll('.hero-rail dt').length === 4);
  t('M20 pair not inside the grid',!q('.hero-main').contains(q('.hero-pair')));
  t('M20 pair keeps its width',    Math.round(q('.hero-pair').getBoundingClientRect().width) > 700);
  t('M20 no page scroll',          document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
"""),
    # M16. The legal and consent surface. What is asserted here is the part a
    # browser can see: that consent is a real tick that blocks the form, that
    # the way in to the portal exists, and that no third party has appeared.
    ("book.html", 1200, 8000, r"""
  t('M16 consent is a checkbox',   q('#consent-visit').type === 'checkbox');
  t('M16 consent is required',     q('#consent-visit').hasAttribute('required'));
  t('M16 consent starts unticked', q('#consent-visit').checked === false);
  t('M16 notice sits above it',    /What we collect/.test(txt('.consent-notice')));
  t('M16 notice names withdrawal', /Taking it back/.test(txt('.consent-notice')));
  t('M16 notice names the board',  /Data\s+Protection\s+Board/.test(txt('.consent-notice')));
  q('#your-name').value = 'Test Person';
  q('#phone').value = '+91 9000000000';
  q('#hospital').value = 'Max Super Speciality, Saket';
  click('button[type="submit"]');
  t('M16 unticked blocks sending', q('#consent-visit').closest('.field').classList.contains('invalid'));
  t('M16 and says why',            /cannot arrange the visit/.test(txt('#consent-visit-err')));
  q('#consent-visit').checked = true;
  q('#consent-visit').dispatchEvent(new Event('input', {bubbles: true}));
  t('M16 ticking clears it',       !q('#consent-visit').closest('.field').classList.contains('invalid'));
  t('M16 target is thumb sized',   q('#consent-visit').getBoundingClientRect().width >= 20);
  t('M16 sign-in offered in nav',  !!q('.nav-login'));
  t('M16 sign-in goes to portal',  q('.nav-login').getAttribute('href') === '/portal');
  t('M16 no third-party frames',   document.querySelectorAll('iframe, embed, object').length === 0);
"""),
    ("cookies.html", 1200, 4000, r"""
  t('M16 states no cookies',       /sets no cookies/i.test(copy()));
  t('M16 no consent banner',       document.cookie === '');
  t('M16 names local storage',     /strictly necessary/.test(copy()));
  t('M16 links to privacy',        !!q('a[href="/privacy"]'));
"""),
    ("refunds.html", 1200, 4000, r"""
  t('M16 refund page reachable',   /Cancellation and refunds/.test(copy()));
  t('M16 states the four hours',   /four hours/.test(copy()));
  t('M16 states refund timing',    /three working days/.test(copy()));
  t('M16 keeps consumer rights',   /Consumer\s+Protection\s+Act/.test(copy()));
  t('M16 points back at terms',    !!q('a[href="/terms"]'));
"""),
    # M15. The portal. These run against a build with no Supabase project, so
    # what is proved here is the half that must hold with no backend at all:
    # the sign-in page says it is not connected instead of pretending to work,
    # a signed-in page never renders its body, and the local build opens the
    # desk without bouncing between two pages that both say the same thing.
    # The other half, that a family reads only its own visits, is enforced by
    # the policies in supabase/schema.sql and cannot be tested from a browser.
    ("portal.html", 1200, 4000, r"""
  t('M15 two doors offered',       document.querySelectorAll('[data-login]').length === 2);
  t('M15 family door present',     !!q('[data-login="family"]'));
  t('M15 companion door present',  !!q('[data-login="companion"]'));
  t('M15 no sign-up form',         !/sign\s*up|create an account|register/i.test(copy()));
  t('M15 says it is not wired',    !q('#pt-unconfigured').hidden);
  t('M15 both buttons disabled',   q('#family-submit').disabled && q('#companion-submit').disabled);
  t('M15 password fields masked',  q('#family-password').type === 'password' && q('#companion-password').type === 'password');
  t('M15 no marketing nav',        !q('header.nav'));
  t('M15 no sign-out when out',    q('#pt-signout').offsetParent === null);
  t('M15 no marketing bar',        !q('.ctxbar'));
  t('M15 no share banner',         !q('.via-banner'));
  t('M15 doors are equal height',  Math.abs(document.querySelectorAll('.pt-form')[0].offsetHeight - document.querySelectorAll('.pt-form')[1].offsetHeight) < 2);
  t('M15 no analytics on portal',  srcs().filter(function (u) { return /plaus/.test(u); }).length === 0);
  t('M15 every script same origin',srcs().filter(function (u) { return u.indexOf(location.origin + '/') !== 0; }).length === 0);
  t('M15 library is vendored',     srcs().filter(function (u) { return /vendor\/supabase/.test(u); }).length === 1);
  t('M15 no page scroll',          document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
"""),
    ("records.html", 1200, 4000, r"""
  t('M15 records has a gate',      !!q('[data-gate="family"]'));
  t('M15 gate wants a family',     q('[data-gate]').getAttribute('data-gate') === 'family');
  t('M15 local build says so',     /not connected to the portal/.test(txt('#rc-list')));
  t('M15 no record leaked',        !/Sushila|Metformin|eGFR/.test(copy()));
  t('M15 no analytics on records', srcs().filter(function (u) { return /plaus/.test(u); }).length === 0);
"""),
    # M14. The desk is the one mechanism with no static state to fall back on,
    # so what is tested is that it boots, that the report tracks the record
    # keystroke by keystroke, and that the sample marking survives until the
    # moment a companion types over it.
    ("desk.html", 1200, 6000, r"""
  t('M14 sheet rendered',          q('#dk-sheet').innerHTML.trim().length > 0);
  t('M14 sample banner shown',     /Sample. Not a real patient/.test(q('#dk-sheet').innerHTML));
  t('M14 asked rows seeded',       document.querySelectorAll('#dk-r-asked .dk-row').length === 2);
  t('M14 instructions in report',  /Fasting sugar log/.test(q('#dk-sheet').innerHTML));
  t('M14 medicine tone applied',   !!q('.dk-meds td.dk-moss'));
  t('M14 withdrawn tone unused',   !q('.dk-meds td.dk-clay'));
  t('M14 copy hidden on report',   q('#dk-copy').offsetParent === null);
  t('M14 message composed',        /Medicines changed today/.test(txt('#dk-wa')));
  click('#dk-tab-wa');
  t('M14 message pane opens',      !q('#dk-pane-wa').hidden);
  t('M14 report pane closes',      q('#dk-pane-report').offsetParent === null);
  t('M14 copy offered on message', q('#dk-copy').offsetParent !== null);
  t('M14 whatsapp link built',     /^https:\/\/wa\.me\/\?text=/.test(q('#dk-wa-send').getAttribute('href')));
  click('#dk-tab-report');
  click('[data-add="meds"]');
  t('M14 medicine row added',      document.querySelectorAll('#dk-r-meds .dk-row').length === 3);
  click('#dk-r-meds .dk-row:last-child [data-del]');
  t('M14 medicine row removed',    document.querySelectorAll('#dk-r-meds .dk-row').length === 2);
  var f = q('#dk-r-instructions .dk-row input[data-k="text"]');
  f.value = 'Bring the sugar log on 09 April.';
  f.dispatchEvent(new Event('input', {bubbles: true}));
  t('M14 report follows typing',   /Bring the sugar log on 09 April/.test(q('#dk-sheet').innerHTML));
  t('M14 sample marking cleared',  !/Sample. Not a real patient/.test(q('#dk-sheet').innerHTML));
  click('#dk-save');
  t('M14 filing refused offline',  /not connected to the portal/.test(txt('#dk-state')));
  t('M14 no page scroll',          document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);

  /* The three pickers. */
  t('M14 department is a list',    q('#dk-f-dept').tagName === 'SELECT');
  t('M14 departments offered',     q('#dk-f-dept').options.length > 15);
  t('M14 hospital grouped by area',q('#dk-f-where').querySelectorAll('optgroup').length >= 8);
  t('M14 all hospitals offered',   q('#dk-f-where').querySelectorAll('optgroup option').length === 26);
  t('M14 seeded hospital picked',  q('#dk-f-where').value === 'Max Super Speciality, Saket');
  t('M14 other field starts shut', q('#dk-o-where').offsetParent === null);
  t('M14 seeded department picked',q('#dk-f-dept').value === 'Endocrinology');
  var dept = q('#dk-f-dept');
  dept.value = 'Nephrology';
  dept.dispatchEvent(new Event('change', {bubbles: true}));
  t('M14 picking a department',    /Nephrology/.test(q('#dk-sheet').innerHTML));
  var hosp = q('#dk-f-where');
  hosp.value = 'Medanta The Medicity, Gurugram';
  hosp.dispatchEvent(new Event('change', {bubbles: true}));
  t('M14 picking a hospital',      /Medanta The Medicity/.test(q('#dk-sheet').innerHTML));
  t('M14 other field hidden again',q('#dk-o-where').offsetParent === null);
  hosp.value = '__other';
  hosp.dispatchEvent(new Event('change', {bubbles: true}));
  t('M14 other opens on request',  q('#dk-o-where').offsetParent !== null);
  q('#dk-f-where-other').value = 'Nursing home OPD, Karol Bagh';
  q('#dk-f-where-other').dispatchEvent(new Event('input', {bubbles: true}));
  t('M14 other reaches the report',/Nursing home OPD, Karol Bagh/.test(q('#dk-sheet').innerHTML));

  /* The question bank. */
  var bank = q('#dk-f-qbank');
  t('M14 question bank grouped',   bank.querySelectorAll('optgroup').length === 5);
  t('M14 question bank stocked',   bank.querySelectorAll('optgroup option').length === 17);
  var asked = document.querySelectorAll('#dk-r-asked .dk-row').length;
  bank.value = 'Who do we call if something changes at night?';
  bank.dispatchEvent(new Event('change', {bubbles: true}));
  t('M14 bank adds a question',    document.querySelectorAll('#dk-r-asked .dk-row').length === asked + 1);
  t('M14 bank question in report', /Who do we call if something changes at night/.test(q('#dk-sheet').innerHTML));
  t('M14 bank resets after use',   bank.value === '');
  t('M14 bank leaves answer open', q('#dk-r-asked .dk-row:last-child [data-k="a"]').value === '');
"""),
    # Headless clamps the window to 500px, which is still inside the
    # mechanism's own 760px narrow branch, so this exercises the phone path.
    ("index.html", 500, 19000, r"""
  t('narrow branch active',        window.matchMedia('(max-width: 760px)').matches);
  t('M1 controls visible',         !q('.cs-controls').hidden);
  t('M1 show-all offered',         !q('[data-cs-showall]').hidden);
  q('.cs-step[data-visit="7"]').click();
  t('M1 three visit window',       vis('.cs-table thead th') === 5);
  t('M1 counter is visit 7',       /^Visit 7\./.test(q('.cs-counter').textContent));
  click('[data-cs-showall]');
  t('M1 show-all opens the year',  vis('.cs-table thead th') === 14);
  t('M1 show-all hides itself',    q('[data-cs-showall]').hidden);
  t('M1 table scrolls, not page',  q('.cs-scroll').scrollWidth > q('.cs-scroll').clientWidth);
  t('mobile menu button present',  !!q('#burger'));
"""),
]

HARNESS = """
<script>
window.__results = [];
function t(name, ok) { window.__results.push((ok === true ? 'ok   ' : 'FAIL ') + name); }
function q(s) { return document.querySelector(s); }
function txt(s) { var e = q(s); return e ? e.textContent : ''; }
/* body.textContent would include this harness, so page copy means main. */
function copy() { return q('main').textContent + ' ' + q('.site-foot').textContent; }
function vis(s) {
  return Array.prototype.filter.call(document.querySelectorAll(s), function (e) {
    return !e.hidden;
  }).length;
}
function click(s) { var e = q(s); if (e) e.click(); else t('missing element ' + s, false); }
/* Every script the page actually loads. innerHTML would include this harness. */
function srcs() {
  return Array.prototype.map.call(document.querySelectorAll('script[src]'), function (e) {
    return e.src;
  });
}
window.addEventListener('error', function (e) { window.__results.push('FAIL js error: ' + e.message); });

/* Wait for the page to be ready, not for a number of milliseconds.

   Mechanism scripts are fetched when their root nears the viewport, so how
   long that takes depends on the connection, the size of the page, and
   whether this is the first Chrome launch of the run. A fixed delay was
   flaky in exactly that way: the homepage passed on its own and failed as
   the first case of a full run. This polls until no new mechanism script has
   appeared for 600ms, then runs the assertions. */
(function () {
  var CAP = 20000, SETTLE = 600, START = Date.now();
  var last = -1, stableSince = 0;

  function count() { return document.querySelectorAll('script[src*="/assets/js/"]').length; }

  function go() {
    try { __BODY__ } catch (e) { window.__results.push('FAIL threw: ' + e.message); }
    var out = document.createElement('div');
    out.id = 'testout';
    out.textContent = window.__results.join(' || ');
    document.body.appendChild(out);
  }

  function tick() {
    var n = count();
    var now = Date.now();
    if (n !== last) { last = n; stableSince = now; }
    var settled = n > 0 && (now - stableSince) >= SETTLE;
    if (settled || (now - START) > CAP) {
      if (!settled) window.__results.push('FAIL harness: scripts never settled');
      go();
      return;
    }
    setTimeout(tick, 100);
  }

  if (document.readyState === 'complete') setTimeout(tick, 100);
  else window.addEventListener('load', function () { setTimeout(tick, 100); });
})();
</script>
"""


def run(page, width, height, body):
    src = open(os.path.join(OUT, page), encoding="utf-8").read()
    harness = HARNESS.replace("__BODY__", body)
    tmp = "_t_%d_%s" % (width, page)
    open(os.path.join(OUT, tmp), "w", encoding="utf-8").write(
        src.replace("</body>", harness + "</body>")
    )
    try:
        dom = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--virtual-time-budget=25000", f"--window-size={width},{height}",
             "--dump-dom", f"{BASE}/{tmp}"],
            capture_output=True, text=True, timeout=120,
        ).stdout
    finally:
        os.remove(os.path.join(OUT, tmp))

    m = re.search(r'<div id="testout">(.*?)</div>', dom, re.S)
    if not m:
        return [f"FAIL {page}: harness produced no output"]
    return [r.strip() for r in m.group(1).split("||")]


def main():
    total = failed = 0
    for page, width, height, body in CASES:
        print(f"\n=== {page} at {width}px ===")
        for line in run(page, width, height, body):
            total += 1
            if line.startswith("FAIL"):
                failed += 1
            print("  " + line)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())