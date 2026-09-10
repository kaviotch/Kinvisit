/* M8. The callback clock.
   All arithmetic goes through Intl with an explicit time zone, so India's
   half-hour offset and every DST transition are handled by the platform rather
   than by hand. If we cannot determine the visitor's zone we ask, because a
   wrong time here is worse than no time. */
(function () {
  'use strict';
  var KV = window.KV;
  var root = document.querySelector('[data-mech="callback"]');
  if (!root) return;

  var IST = 'Asia/Kolkata';
  var live = root.querySelector('.cc-live');
  var fallback = root.querySelector('.cc-fallback');

  var zone = null;
  try { zone = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { zone = null; }

  function parts(date, tz) {
    var f = new Intl.DateTimeFormat('en-GB', {
      timeZone: tz, hour12: false,
      year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
    });
    var o = {};
    f.formatToParts(date).forEach(function (p) { o[p.type] = p.value; });
    return o;
  }

  function clockIn(date, tz) {
    return new Intl.DateTimeFormat('en-GB', {
      timeZone: tz, hour: 'numeric', minute: '2-digit', hour12: true
    }).format(date).replace(/\s?(am|pm)/i, function (m, s) { return s.toLowerCase(); });
  }

  /* The instant at which the wall clock in tz reads hh:00 on the tz-local day
     that contains `ref`. Two passes, because the first guess can land on the
     wrong side of a DST change. */
  function wallTime(ref, tz, hh) {
    var p = parts(ref, tz);
    var target = Date.UTC(+p.year, +p.month - 1, +p.day, hh, 0, 0);
    var guess = new Date(target);
    for (var i = 0; i < 2; i++) {
      var g = parts(guess, tz);
      var got = Date.UTC(+g.year, +g.month - 1, +g.day, +g.hour, +g.minute, 0);
      guess = new Date(guess.getTime() + (target - got));
    }
    return guess;
  }

  function hour12(date, tz) {
    return new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: 'numeric', hour12: true })
      .format(date).replace(/\s?(am|pm)/i, function (m, s) { return s.toLowerCase(); });
  }

  function delhiRange(from, to, tz) {
    var now = new Date();
    var a = wallTime(now, tz, from);
    var b = wallTime(now, tz, to);
    var sameDay = parts(a, IST).day === parts(b, IST).day;
    var label = hour12(a, IST) + ' to ' + hour12(b, IST);
    if (!sameDay) label += ' the next day';
    return label;
  }

  function start(tz) {
    zone = tz;
    fallback.hidden = true;
    live.hidden = false;

    var wins = root.querySelectorAll('.cc-win');
    var chosen = root.querySelector('[data-cc-win="evening"]') || wins[0];

    function paintWindows() {
      Array.prototype.forEach.call(wins, function (w) {
        var from = +w.getAttribute('data-cc-from');
        var to = +w.getAttribute('data-cc-to');
        w.querySelector('[data-cc-delhi]').textContent = 'Delhi ' + delhiRange(from, to, tz);
      });
    }

    function paintChoice() {
      var from = +chosen.getAttribute('data-cc-from');
      var to = +chosen.getAttribute('data-cc-to');
      root.querySelector('[data-cc-window]').textContent =
        chosen.querySelector('.cc-win-l').textContent;
      root.querySelector('[data-cc-window-ist]').textContent = delhiRange(from, to, tz);
      KV.press(wins, chosen);
    }

    function tick() {
      var now = new Date();
      root.querySelector('[data-cc-local]').textContent = clockIn(now, tz);
      root.querySelector('[data-cc-ist]').textContent = clockIn(now, IST);
      paintWindows();
      paintChoice();
    }

    var zoneNote = root.querySelector('[data-cc-zone]');
    if (zoneNote) {
      zoneNote.textContent = 'We read your time zone as ' + tz.replace(/_/g, ' ') +
        '. If that is wrong, tell us on the call and we will change it.';
    }

    KV.on(root, '.cc-win', 'click', function (e, t) {
      chosen = t;
      paintChoice();
      KV.track('callback_window_selected', {
        window: t.getAttribute('data-cc-win'),
        zone: tz
      });
    });

    tick();
    /* Every half minute, so the clock is right across an hour boundary and
       across a DST change while the page is left open. */
    window.setInterval(tick, 30000);
  }

  if (zone) {
    try {
      clockIn(new Date(), zone);
      start(zone);
      return;
    } catch (e) { /* fall through to asking */ }
  }

  fallback.hidden = false;
  var select = root.querySelector('[data-cc-manual]');
  select.addEventListener('change', function () {
    if (select.value) start(select.value);
  });
})();
