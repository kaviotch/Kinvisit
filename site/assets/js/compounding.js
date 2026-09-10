/* M1. The compounding record scrubber.
   Without this file the page already shows the full twelve-visit table and the
   final counter line. This turns that table into something you build with your
   own hand, one visit at a time. */
(function () {
  'use strict';
  var KV = window.KV;
  var data = KV.json('compounding-data');
  var root = document.querySelector('[data-mech="compounding"]');
  if (!data || !root) return;

  var visits = data.visits;
  var q = data.carriedQuestion;
  var table = root.querySelector('.cs-table');
  var controls = root.querySelector('.cs-controls');
  var steps = root.querySelectorAll('.cs-step');
  var counter = root.querySelector('.cs-counter');
  var qBox = root.querySelector('[data-cs-question]');
  var qTag = root.querySelector('[data-cs-qtag]');
  var qRes = root.querySelector('[data-cs-qres]');
  var showAll = root.querySelector('[data-cs-showall]');
  var scroll = root.querySelector('.cs-scroll');
  if (!table || !controls) return;

  var narrow = window.matchMedia('(max-width: 760px)');
  var current = 1;
  var everything = false;
  var engaged = false;
  var completed = false;

  /* Column 0 is the medicine name and always stays. */
  var headCells = table.tHead.rows[0].cells;
  var bodyRows = table.tBodies[0].rows;

  function visibleColumns() {
    if (everything) {
      var all = [];
      for (var i = 1; i <= visits.length; i++) all.push(i);
      return all;
    }
    if (narrow.matches) {
      /* Current, previous, and the first, so the growth is still legible. */
      var want = [1, current - 1, current].filter(function (v, i, a) {
        return v >= 1 && v <= current && a.indexOf(v) === i;
      });
      return want.sort(function (a, b) { return a - b; });
    }
    var upto = [];
    for (var j = 1; j <= current; j++) upto.push(j);
    return upto;
  }

  function render(announce) {
    var show = visibleColumns();

    /* The last column is a spacer that absorbs slack, so it is never toggled. */
    for (var c = 1; c <= visits.length; c++) {
      var on = show.indexOf(c) !== -1;
      headCells[c].hidden = !on;
      for (var r = 0; r < bodyRows.length; r++) {
        bodyRows[r].cells[c].hidden = !on;
      }
    }

    /* A medicine row is only meaningful once that medicine exists. */
    for (var r2 = 0; r2 < bodyRows.length; r2++) {
      var med = data.medicationOrder[r2];
      var appeared = false;
      for (var v = 0; v < current; v++) {
        if (visits[v].medications[med]) { appeared = true; break; }
      }
      bodyRows[r2].hidden = !appeared;
    }

    Array.prototype.forEach.call(steps, function (s, i) {
      var n = i + 1;
      s.setAttribute('aria-current', n === current ? 'true' : 'false');
      s.classList.toggle('done', n < current);
    });

    counter.textContent = visits[current - 1].counterLine;

    var raised = q.raisedAt, resolved = q.resolvedAt;
    if (current < raised) {
      qBox.hidden = true;
    } else {
      qBox.hidden = false;
      var isResolved = current >= resolved;
      qBox.classList.toggle('resolved', isResolved);
      qTag.textContent = isResolved ? 'Answered' : 'Unresolved';
      qRes.hidden = !isResolved;
    }

    root.querySelector('[data-cs-nav="prev"]').disabled = current === 1;
    root.querySelector('[data-cs-nav="next"]').disabled = current === visits.length;
    if (showAll) showAll.hidden = !narrow.matches || everything;

    if (announce && !engaged) { engaged = true; KV.track('compounding_scrubber_engaged'); }
    if (announce && current >= 10 && !completed) {
      completed = true;
      KV.track('compounding_scrubber_completed', { visit: String(current) });
    }
  }

  function go(n, announce) {
    current = Math.min(Math.max(n, 1), visits.length);
    render(announce !== false);
    if (scroll && !KV.reduced) {
      scroll.scrollTo({ left: scroll.scrollWidth, behavior: 'smooth' });
    } else if (scroll) {
      scroll.scrollLeft = scroll.scrollWidth;
    }
  }

  KV.on(root, '[data-cs-nav]', 'click', function (e, t) {
    go(current + (t.getAttribute('data-cs-nav') === 'next' ? 1 : -1));
  });
  KV.on(root, '.cs-step', 'click', function (e, t) {
    go(parseInt(t.getAttribute('data-visit'), 10));
  });
  if (showAll) {
    showAll.addEventListener('click', function () {
      everything = true;
      current = visits.length;
      render(true);
    });
  }

  root.querySelector('.cs-track').addEventListener('keydown', function (e) {
    var d = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1 }[e.key];
    if (d) { e.preventDefault(); go(current + d); steps[current - 1].focus(); }
    if (e.key === 'Home') { e.preventDefault(); go(1); steps[0].focus(); }
    if (e.key === 'End') { e.preventDefault(); go(visits.length); steps[visits.length - 1].focus(); }
  });

  narrow.addEventListener('change', function () { render(false); });

  controls.hidden = false;
  go(1, false);
})();
