/* M17. The visit day.
   The list in the page is the whole day in India time. This turns it into a
   dial you drag through, one moment at a time, and says what the clock read
   wherever the reader lives. Every conversion goes through Intl with an
   explicit time zone, so British and American summer time come from the
   platform rather than from a table here.

   The dial is a port of the Gaussian tick scale in Great UI's revision
   timeline (MIT, Saurabh Sharma): ticks swell towards the one in focus and
   the row slides to keep it centred. */
(function () {
  'use strict';
  var KV = window.KV;
  var root = document.querySelector('[data-mech="visit-day"]');
  if (!root) return;
  var D = KV.json('visit-day-data');
  if (!D || !D.events || !D.events.length) return;

  var IST = 'Asia/Kolkata';
  var SLOT = 15;           /* minutes per tick */
  var PITCH = 12;          /* px per tick: .vd-tick width + .vd-ticks gap */
  var SIGMA = 4.5;
  var BASE = 14, BUMP = 34, EV_BASE = 24;

  var events = D.events;
  var d = D.date.split('-');
  /* Midnight in Delhi on the visit date, as an instant. India has no DST. */
  var midnight = Date.UTC(+d[0], +d[1] - 1, +d[2]) - 330 * 60000;
  var first = Math.floor((events[0].t - 20) / SLOT) * SLOT;
  var last = Math.ceil((events[events.length - 1].t + 40) / SLOT) * SLOT;
  var count = (last - first) / SLOT + 1;

  function slotOf(t) { return Math.round((t - first) / SLOT); }
  var evSlots = events.map(function (e) { return slotOf(e.t); });

  var dial = root.querySelector('[data-vd-dial]');
  var row = root.querySelector('[data-vd-ticks]');
  var select = root.querySelector('[data-vd-zone]');
  var items = root.querySelectorAll('.vd-ev');
  var phone = root.querySelector('[data-vd-phone]');
  var empty = root.querySelector('[data-vd-empty]');

  /* ---------------------------------------------------------- the ticks */

  var ticks = [];
  var frag = document.createDocumentFragment();
  for (var k = 0; k < count; k++) {
    var tk = document.createElement('span');
    tk.className = 'vd-tick';
    if (((first + k * SLOT) % 60 + 60) % 60 === 0) tk.className += ' vd-hour';
    if (evSlots.indexOf(k) > -1) tk.className += ' vd-evt';
    frag.appendChild(tk);
    ticks.push(tk);
  }
  row.appendChild(frag);

  /* ------------------------------------------------------------ the zone */

  var detected = null;
  try { detected = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { detected = null; }
  if (detected === 'Asia/Calcutta') detected = IST;

  function valid(tz) {
    try { new Intl.DateTimeFormat('en-GB', { timeZone: tz }).format(0); return true; }
    catch (e) { return false; }
  }

  if (detected && valid(detected)) {
    var known = select.querySelector('option[value="' + detected + '"]');
    if (!known) {
      known = document.createElement('option');
      known.value = detected;
      known.textContent = detected.split('/').pop().replace(/_/g, ' ');
      select.insertBefore(known, select.firstChild);
    }
    known.textContent += ' (your time zone)';
    select.value = detected;
  }

  function cityName() {
    var o = select.options[select.selectedIndex];
    return o.textContent.replace(' (your time zone)', '');
  }

  function fmt(t, tz, opts) {
    opts.timeZone = tz;
    return new Intl.DateTimeFormat('en-GB', opts).format(new Date(midnight + t * 60000))
      .replace(/\s?(am|pm)/i, function (m, s) { return s.toLowerCase(); });
  }

  function clock(t, tz) { return fmt(t, tz, { hour: 'numeric', minute: '2-digit', hour12: true }); }
  function day(t, tz) { return fmt(t, tz, { weekday: 'long', day: 'numeric', month: 'long' }); }
  function hour(t, tz) { return +fmt(t, tz, { hour: '2-digit', hour12: false }) % 24; }

  /* What the reader is most likely doing. Hedged, because it is a guess. */
  function state(h) {
    if (h < 5) return 'You are probably asleep.';
    if (h < 7) return 'You are probably not up yet.';
    if (h < 9) return 'Your morning is starting.';
    if (h < 13) return 'The middle of your working morning.';
    if (h < 14) return 'Around your lunch.';
    if (h < 18) return 'Your working afternoon.';
    if (h < 22) return 'Your evening.';
    return 'Late, where you are.';
  }

  /* ------------------------------------------------------------ painting */

  var cur = 0;          /* the event on show */
  var pos = evSlots[0]; /* the slot the dial is centred on */
  var engaged = false, completed = false;

  function eventAt(slot) {
    var i = 0;
    for (var j = 0; j < evSlots.length; j++) if (evSlots[j] <= slot) i = j;
    return i;
  }

  function nearest(slot) {
    var best = 0;
    for (var j = 1; j < evSlots.length; j++) {
      if (Math.abs(evSlots[j] - slot) < Math.abs(evSlots[best] - slot)) best = j;
    }
    return best;
  }

  function paintDial() {
    for (var k = 0; k < count; k++) {
      var dist = k - pos;
      var f = Math.exp(-(dist * dist) / (2 * SIGMA * SIGMA));
      var isEv = ticks[k].className.indexOf('vd-evt') > -1;
      ticks[k].style.height = Math.round((isEv ? EV_BASE : BASE) + BUMP * f) + 'px';
      ticks[k].classList.toggle('on', k === evSlots[cur]);
    }
    var x = dial.clientWidth / 2 - (pos * PITCH + 1.5);
    row.style.transform = 'translateX(' + x + 'px)';
  }

  function paint() {
    var ev = events[cur];
    var tz = select.value;

    Array.prototype.forEach.call(items, function (li, j) { li.classList.toggle('is-on', j === cur); });

    root.querySelector('[data-vd-local]').textContent = clock(ev.t, tz);
    var sameDay = day(ev.t, tz) === day(ev.t, IST);
    root.querySelector('[data-vd-state]').textContent =
      (sameDay ? '' : day(ev.t, tz) + '. ') + state(hour(ev.t, tz));

    /* The phone holds every message that has arrived by now. */
    Array.prototype.forEach.call(phone.querySelectorAll('.vd-msg'), function (m) { m.remove(); });
    var shown = 0;
    events.forEach(function (e, j) {
      if (j > cur || !e.msg) return;
      var p = document.createElement('p');
      p.className = 'vd-msg vd-from-' + e.msg.from;
      var who = document.createElement('span');
      who.className = 'vd-msg-who';
      /* A message from the evening before says so, in the reader's own days. */
      var stamp = clock(e.t, tz);
      if (day(e.t, tz) !== day(ev.t, tz)) stamp = fmt(e.t, tz, { weekday: 'short' }) + ' ' + stamp;
      who.textContent = (e.msg.from === 'you' ? 'You' : 'Kinvisit') + ', ' + stamp;
      p.appendChild(who);
      p.appendChild(document.createTextNode(e.msg.text));
      phone.appendChild(p);
      shown++;
    });
    empty.hidden = shown > 0;

    dial.setAttribute('aria-valuenow', String(cur));
    dial.setAttribute('aria-valuetext',
      clock(ev.t, IST) + ' in Delhi, ' + clock(ev.t, tz) + ' in ' + cityName() + '. ' + ev.title);

    root.querySelector('[data-vd-nav=prev]').disabled = cur === 0;
    root.querySelector('[data-vd-nav=next]').disabled = cur === events.length - 1;
    paintDial();
  }

  function summary() {
    var tz = select.value;
    var c = events[0];
    events.forEach(function (e) { if (e.id === D.consultEvent) c = e; });
    var line;
    if (tz === IST) {
      line = 'In India the consultation starts at ' + clock(c.t, tz) +
        ' on a working ' + fmt(c.t, IST, { weekday: 'long' }) + '. Being in the same country is not the same as being in the room.';
    } else {
      line = 'In ' + cityName() + ', the eight minutes that mattered start at ' + clock(c.t, tz) +
        (day(c.t, tz) === day(c.t, IST) ? '' : ' on ' + day(c.t, tz)) + '. ' + state(hour(c.t, tz));
    }
    root.querySelector('[data-vd-sum]').textContent = line;
  }

  function go(i, fromDrag) {
    cur = Math.max(0, Math.min(events.length - 1, i));
    if (!fromDrag) pos = evSlots[cur];
    paint();
    if (!engaged) {
      engaged = true;
      KV.track('visit_day_engaged', { zone: select.value });
    }
    if (cur === events.length - 1 && !completed) {
      completed = true;
      KV.track('visit_day_completed', { zone: select.value });
    }
  }

  /* ------------------------------------------------------------- input */

  KV.on(root, '[data-vd-nav]', 'click', function (e, t) {
    go(cur + (t.getAttribute('data-vd-nav') === 'next' ? 1 : -1));
  });

  dial.addEventListener('keydown', function (e) {
    var k = e.key, to = null;
    if (k === 'ArrowRight' || k === 'ArrowUp') to = cur + 1;
    else if (k === 'ArrowLeft' || k === 'ArrowDown') to = cur - 1;
    else if (k === 'Home') to = 0;
    else if (k === 'End') to = events.length - 1;
    if (to === null) return;
    e.preventDefault();
    go(to);
  });

  /* Dragging moves the strip under the needle, like film through a gate:
     pull left and the day moves forward. A tap without a drag jumps to the
     moment nearest the tick that was tapped. */
  var drag = null;
  dial.addEventListener('pointerdown', function (e) {
    drag = { x: e.clientX, from: pos, moved: false };
    try { dial.setPointerCapture(e.pointerId); } catch (err) { /* older Safari */ }
  });
  dial.addEventListener('pointermove', function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.x;
    if (!drag.moved && Math.abs(dx) < 4) return;
    drag.moved = true;
    root.classList.add('vd-dragging');
    pos = Math.max(0, Math.min(count - 1, drag.from - Math.round(dx / PITCH)));
    go(eventAt(pos), true);
  });
  function end(e) {
    if (!drag) return;
    root.classList.remove('vd-dragging');
    if (drag.moved) {
      go(nearest(pos));
    } else {
      var r = dial.getBoundingClientRect();
      var slot = pos + Math.round((e.clientX - r.left - r.width / 2) / PITCH);
      go(nearest(slot));
    }
    drag = null;
  }
  dial.addEventListener('pointerup', end);
  dial.addEventListener('pointercancel', end);

  select.addEventListener('change', function () { summary(); paint(); });
  window.addEventListener('resize', paintDial, { passive: true });

  /* ---------------------------------------------------------------- boot */

  root.classList.add('vd-on');
  root.querySelector('.vd-head').hidden = false;
  root.querySelector('.vd-you').hidden = false;
  root.querySelector('.vd-dial-wrap').hidden = false;
  root.querySelector('.vd-hint').hidden = false;
  root.querySelector('.vd-here-l').hidden = false;
  var lede = document.querySelector('[data-vd-lede]');
  if (lede) {
    lede.textContent = 'The same visit as report #04, from the night before to the report. ' +
      'Drag through it. One clock is Delhi. The other is wherever you are.';
  }
  summary();
  paint();
})();
