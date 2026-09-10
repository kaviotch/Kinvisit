#!/usr/bin/env python3
"""
Layout QA across every page, in a real browser, at several widths.

Four things it looks for, all of them the kind of fault that is obvious to a
reader and invisible in the markup:

  overlap    two unrelated blocks whose boxes intersect. Text sitting on top
             of a picture, a number colliding with a caption.
  crowding   two stacked blocks with almost no gap between them, which reads
             as one block and hides where a section ends.
  overflow   the page scrolls sideways.
  escape     an element sticking out past the container that is supposed to
             hold it.

    python3 preview.py &      then      python3 qa.py

It reports positions, not opinions. Anything it prints is measured.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = "http://localhost:8899"

WIDTHS = [1440, 1100, 820, 600, 390]

PROBE = r"""
<script>
window.__qa = [];
function box(e) { return e.getBoundingClientRect(); }
function name(e) {
  var n = e.tagName.toLowerCase();
  if (e.id) n += '#' + e.id;
  else if (e.className && typeof e.className === 'string' && e.className.trim())
    n += '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.');
  var t = (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 34);
  return n + (t ? ' "' + t + '"' : '');
}
function related(a, b) { return a.contains(b) || b.contains(a); }

function run() {
  var out = [];
  var de = document.documentElement;

  /* documentElement.scrollWidth counts content that a scroller has already
     clipped, so it reports overflow on pages that cannot be scrolled at all.
     The honest test is whether the page actually moves. */
  var before = window.scrollX;
  window.scrollTo(9999, window.scrollY);
  var moved = Math.round(window.scrollX);
  window.scrollTo(before, window.scrollY);
  if (moved > 1) out.push('OVERFLOW page really scrolls sideways by ' + moved + 'px');

  /* Content blocks worth checking. Fixed and sticky things are excluded:
     they are meant to sit over the page. */
  var sel = 'h1,h2,h3,p.lede,p.eyebrow,figure,img,.num,figcaption,.stat,table,dl,.btn';
  var all = Array.prototype.filter.call(document.querySelectorAll(sel), function (e) {
    var r = box(e), cs = getComputedStyle(e);
    if (r.width < 2 || r.height < 2) return false;
    if (cs.position === 'fixed' || cs.position === 'sticky') return false;
    if (cs.visibility === 'hidden' || e.closest('[hidden]')) return false;
    if (e.closest('.ctxbar, .via-banner, .fab, .menu, .nav')) return false;
    return true;
  });

  for (var i = 0; i < all.length; i++) {
    for (var j = i + 1; j < all.length; j++) {
      var a = all[i], b = all[j];
      if (related(a, b)) continue;
      var ra = box(a), rb = box(b);
      var ox = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
      var oy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      if (ox > 3 && oy > 3) {
        out.push('OVERLAP ' + Math.round(ox) + 'x' + Math.round(oy) + 'px :: ' +
                 name(a) + '  ||  ' + name(b));
      }
    }
  }

  /* Crowding: direct children of a wrap that stack with almost no air. */
  Array.prototype.forEach.call(document.querySelectorAll('.wrap, .prose'), function (wrap) {
    if (wrap.closest('section') === null) return;
    var kids = Array.prototype.filter.call(wrap.children, function (e) {
      var r = box(e); return r.height > 4 && getComputedStyle(e).position === 'static';
    });
    for (var k = 1; k < kids.length; k++) {
      var prev = box(kids[k - 1]), cur = box(kids[k]);
      if (cur.left > prev.right - 2 || prev.left > cur.right - 2) continue;  /* side by side */
      /* A block whose own padding supplies the air is not crowded. */
      var padBelow = parseFloat(getComputedStyle(kids[k - 1]).paddingBottom);
      var padAbove = parseFloat(getComputedStyle(kids[k]).paddingTop);
      if (padBelow + padAbove >= 14) continue;
      var gap = cur.top - prev.bottom;
      if (gap >= 0 && gap < 14) {
        out.push('CROWDED ' + Math.round(gap) + 'px between ' +
                 name(kids[k - 1]) + '  and  ' + name(kids[k]));
      }
    }
  });

  /* Escape: content wider than the container meant to hold it. */
  Array.prototype.forEach.call(document.querySelectorAll('main .wrap'), function (wrap) {
    var w = box(wrap), cs = getComputedStyle(wrap);
    var padL = parseFloat(cs.paddingLeft), padR = parseFloat(cs.paddingRight);
    Array.prototype.forEach.call(wrap.querySelectorAll(sel), function (e) {
      if (getComputedStyle(e).position !== 'static') return;
      /* Wide content is allowed to overflow a container built to scroll it. */
      var sc = e.parentElement;
      while (sc && sc !== wrap) {
        var ov = getComputedStyle(sc).overflowX;
        if (ov === 'auto' || ov === 'scroll') return;
        sc = sc.parentElement;
      }
      var r = box(e);
      if (r.width < 2) return;
      if (r.left < w.left + padL - 2 || r.right > w.right - padR + 2) {
        out.push('ESCAPE ' + name(e) + ' by ' +
                 Math.round(Math.max(w.left + padL - r.left, r.right - (w.right - padR))) + 'px');
      }
    });
  });

  var d = document.createElement('div');
  d.id = 'qa' + 'out';
  d.textContent = out.length ? out.join(' ~~ ') : 'clean';
  document.body.appendChild(d);
}

(function () {
  var CAP = 20000, SETTLE = 600, START = Date.now(), last = -1, stable = 0;
  function n() { return document.querySelectorAll('script[src*="/assets/js/"]').length; }
  function tick() {
    var c = n(), now = Date.now();
    if (c !== last) { last = c; stable = now; }
    if ((c > 0 && now - stable >= SETTLE) || now - START > CAP) { run(); return; }
    setTimeout(tick, 100);
  }
  if (document.readyState === 'complete') setTimeout(tick, 100);
  else window.addEventListener('load', function () { setTimeout(tick, 100); });
})();
</script>
"""


def check(page, width):
    src = open(os.path.join(OUT, page), encoding="utf-8").read()
    tmp = os.path.join(OUT, "_qa_%d_%s" % (width, page))
    open(tmp, "w", encoding="utf-8").write(src.replace("</body>", PROBE + "</body>"))
    try:
        dom = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--virtual-time-budget=25000", f"--window-size={width},9000",
             "--dump-dom", f"{BASE}/{os.path.basename(tmp)}"],
            capture_output=True, text=True, timeout=120).stdout
    finally:
        os.remove(tmp)
    m = re.search(r'<div id="qaout">(.*?)</div>', dom, re.S)
    if not m:
        return ["probe produced no output"]
    body = m.group(1).strip()
    if body == "clean":
        return []
    import html as _h
    return [_h.unescape(x.strip()) for x in body.split("~~")]


def main():
    pages = sorted(os.path.basename(p) for p in
                   __import__("glob").glob(os.path.join(OUT, "*.html")))
    total = 0
    for page in pages:
        findings = {}
        for w in WIDTHS:
            for line in check(page, w):
                findings.setdefault(line, []).append(w)
        if findings:
            print(f"\n=== {page}")
            for line, widths in sorted(findings.items()):
                print(f"  [{','.join(str(x) for x in widths):<26}] {line}")
                total += 1
    print(f"\n{total} finding(s) across {len(pages)} pages at {WIDTHS}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
