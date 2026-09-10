/* M12. The hospital coverage checker.
   Three outcomes, and the one that matters most is the third. A service that
   clearly says no is more credible than one that says yes to everything, and
   the misses are a demand signal worth reading. */
(function () {
  'use strict';
  var KV = window.KV;
  var root = document.querySelector('[data-mech="hospitals"]');
  if (!root) return;

  var data = KV.json('hospital-data');
  if (!data) return;

  var input = root.querySelector('.hc-input');
  var out = root.querySelector('[data-hc-out]');

  var NCR = ['delhi', 'ncr', 'gurugram', 'gurgaon', 'noida', 'ghaziabad', 'faridabad',
             'greater noida', 'vaishali', 'indirapuram', 'dwarka', 'rohini', 'saket',
             'okhla', 'lajpat', 'vasant', 'pitampura', 'janakpuri', 'karol bagh',
             'nehru place', 'sohna', 'manesar', 'sonipat', 'bahadurgarh'];

  function normalise(s) {
    return s.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  }

  /* A hospital chain has branches in cities we do not serve. Someone typing
     Apollo Chennai must be told no, not matched to the Delhi Apollo on the
     strength of one shared word. City wins over chain, always. */
  var ELSEWHERE = ['chennai', 'mumbai', 'bombay', 'bengaluru', 'bangalore', 'hyderabad',
                   'kolkata', 'calcutta', 'pune', 'ahmedabad', 'jaipur', 'lucknow',
                   'chandigarh', 'kochi', 'cochin', 'coimbatore', 'nagpur', 'indore',
                   'bhopal', 'patna', 'surat', 'vizag', 'visakhapatnam', 'mysore',
                   'madurai', 'thiruvananthapuram', 'trivandrum', 'guwahati', 'dehradun',
                   'agra', 'kanpur', 'varanasi', 'amritsar', 'ludhiana', 'shimla',
                   'goa', 'ranchi', 'raipur', 'bhubaneswar', 'vijayawada', 'nashik'];

  function elsewhere(query) {
    var q = normalise(query);
    return ELSEWHERE.some(function (city) {
      return new RegExp('(^| )' + city + '( |$)').test(q);
    });
  }

  function match(query) {
    var q = normalise(query);
    if (!q) return null;
    if (elsewhere(query)) return null;
    var best = null;
    data.hospitals.forEach(function (h) {
      var keys = [normalise(h.name)].concat(h.aliases.map(normalise));
      keys.forEach(function (k) {
        if (!k) return;
        var hit = k === q || k.indexOf(q) === 0 || q.indexOf(k) === 0 ||
                  (q.length >= 4 && k.indexOf(q) !== -1);
        if (hit && (!best || k.length < best.len)) best = { h: h, len: k.length };
      });
    });
    return best ? best.h : null;
  }

  function looksNCR(query) {
    var q = normalise(query);
    return NCR.some(function (a) { return q.indexOf(a) !== -1; });
  }

  function render(query) {
    var found = match(query);
    var cls = 'hc-out', html, result;

    if (found) {
      result = 'covered';
      var first = '<p><strong>Yes. We attend at ' + escapeHTML(found.name) + '.</strong></p>';
      var second;
      if (found.visits > 0) {
        second = '<p>We have attended ' + found.visits + ' visit' +
          (found.visits === 1 ? '' : 's') + ' there' +
          (found.wait ? ', where the OPD wait has been running about ' + found.wait +
            ' minutes. That does not change your price.' : '.') + '</p>';
      } else {
        second = '<p>We have not been to this one yet, and we are not going to pretend ' +
          'otherwise. It is in ' + escapeHTML(found.area) + ', we go there, and we will ' +
          'confirm the appointment within a day of you asking.</p>';
      }
      html = first + second +
        '<p><a class="btn btn-primary btn-sm" href="/book" style="margin-top:8px">Tell us the appointment</a></p>';
    } else if (looksNCR(query) && !elsewhere(query)) {
      result = 'ncr-unlisted';
      cls += ' miss';
      html = '<p><strong>Not on our list, but it is in Delhi NCR, so we will go.</strong></p>' +
        '<p>Our list only covers the larger hospitals. We attend at any hospital, clinic, or ' +
        'diagnostic centre in NCR, including small practices. Tell us the appointment and we ' +
        'will confirm within a day.</p>' +
        '<p><a class="btn btn-primary btn-sm" href="/book" style="margin-top:8px">Tell us the appointment</a></p>';
    } else {
      result = 'outside';
      cls += ' outside';
      html = '<p><strong>We do not know that one, and it may be outside Delhi NCR.</strong></p>' +
        '<p>Delhi NCR is the only area we operate in today, and we will not pretend otherwise. ' +
        'If it is in NCR, send it to us and we will confirm. If it is not, tell us where you ' +
        'are and we will let you know if that changes.</p>' +
        '<p><a class="btn btn-ghost btn-sm" href="/book" style="margin-top:8px">Ask us anyway</a></p>';
    }

    out.className = cls;
    out.innerHTML = html;
    out.hidden = false;

    /* The raw query is a place name, not health information, and the misses
       are the expansion roadmap. */
    KV.track('hospital_checked', result === 'covered'
      ? { result: result }
      : { result: result, query: normalise(query).slice(0, 60) });
  }

  function escapeHTML(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  root.querySelector('[data-hc-go]').addEventListener('click', function () {
    if (input.value.trim()) render(input.value);
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); if (input.value.trim()) render(input.value); }
  });
})();
