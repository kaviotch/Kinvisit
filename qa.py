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

  /* Invisible text. A token used as both a background and the colour of the
     text on it renders nothing, and it is invisible in the source too: both
     sides read as var(--ink). Compare what the browser actually computed. */
  /* Walk up compositing every translucent layer onto the one behind it. A
     semi-transparent panel is not the colour it declares: --hairline at 0.14
     over white renders as light grey, and reading the declared value alone
     reports text as invisible when it is perfectly legible. */
  function bgOf(el) {
    var stack = [], n = el;
    while (n && n !== document.documentElement) {
      var c = getComputedStyle(n).backgroundColor;
      var m = c && c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?/);
      if (m) {
        var a = m[4] === undefined ? 1 : parseFloat(m[4]);
        if (a > 0) {
          stack.push([+m[1], +m[2], +m[3], a]);
          if (a >= 0.999) break;
        }
      }
      n = n.parentElement;
    }
    var out = [255, 255, 255];
    for (var i = stack.length - 1; i >= 0; i--) {
      var L = stack[i];
      out = [0, 1, 2].map(function (k) { return L[k] * L[3] + out[k] * (1 - L[3]); });
    }
    return 'rgb(' + out.map(Math.round).join(', ') + ')';
  }
  function parse(c) {
    var m = c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    return m ? [+m[1], +m[2], +m[3]] : null;
  }
  function lin(v) { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
  function lum(c) { return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]); }
  function contrast(a, b) {
    var la = lum(a), lb = lum(b), hi = Math.max(la, lb), lo = Math.min(la, lb);
    return (hi + 0.05) / (lo + 0.05);
  }
  Array.prototype.forEach.call(document.querySelectorAll('main *'), function (e) {
    var own = Array.prototype.filter.call(e.childNodes, function (n) {
      return n.nodeType === 3 && n.textContent.trim().length > 1;
    });
    if (!own.length) return;
    var r = box(e);
    if (r.width < 2 || r.height < 2) return;
    var cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || +cs.opacity === 0) return;
    var fg = parse(cs.color), bg = parse(bgOf(e));
    if (!fg || !bg) return;
    var c = contrast(fg, bg);
    if (c < 1.6) {
      out.push('INVISIBLE ' + c.toFixed(2) + ':1 :: ' + name(e));
    }
  });

  /* Voids. Two shapes of wasted space, both measured rather than judged:
     paper below the last thing in a section, and one column of a grid ending
     far above its neighbour. */
  Array.prototype.forEach.call(document.querySelectorAll('main section'), function (sec) {
    var sr = box(sec);
    if (sr.height < 120) return;
    var lowest = sr.top;
    Array.prototype.forEach.call(sec.querySelectorAll('*'), function (e) {
      var cs = getComputedStyle(e);
      if (cs.position === 'fixed' || cs.visibility === 'hidden') return;
      var r = box(e);
      if (r.width < 2 || r.height < 2) return;
      if (r.bottom > lowest) lowest = r.bottom;
    });
    var pad = parseFloat(getComputedStyle(sec).paddingBottom) || 0;
    var slack = Math.round(sr.bottom - lowest - pad);
    if (slack > 150) {
      out.push('VOID-BELOW ' + slack + 'px of empty paper under ' + name(sec).slice(0, 60));
    }
  });

  Array.prototype.forEach.call(document.querySelectorAll('main .wrap, main .hero-rail'), function (g) {
    if (getComputedStyle(g).display !== 'grid') return;
    var kids = Array.prototype.filter.call(g.children, function (e) {
      var r = box(e); return r.height > 4;
    });
    if (kids.length < 2) return;
    var rows = {};
    kids.forEach(function (e) {
      var r = box(e);
      var key = Math.round(r.top / 8);
      (rows[key] = rows[key] || []).push(r);
    });
    Object.keys(rows).forEach(function (k) {
      var r = rows[k];
      if (r.length < 2) return;
      var lo = Math.min.apply(null, r.map(function (x) { return x.bottom; }));
      var hi = Math.max.apply(null, r.map(function (x) { return x.bottom; }));
      if (hi - lo > 220) {
        out.push('VOID-BESIDE ' + Math.round(hi - lo) + 'px, one column of ' +
                 name(g).slice(0, 46) + ' ends far above its neighbour');
      }
    });
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
    # Underscore-prefixed files are working documents: design samples and the
    # temporary pages the suites write. check.py skips them for the same
    # reason, and they are not part of the site until they are.
    pages = sorted(os.path.basename(p) for p in
                   __import__("glob").glob(os.path.join(OUT, "*.html"))
                   if not os.path.basename(p).startswith("_"))
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
