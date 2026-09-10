/* M15b. What a family reads.

   Every visit their companion has filed, newest first, and the same document
   the desk produced on the day. The query below asks for every visit row it
   can see; it does no filtering of its own, because filtering in the browser
   is how one family ends up reading another family's record. Postgres decides
   what "can see" means, and returns nothing else. */
(function () {
  'use strict';

  var root = document.querySelector('[data-mech="records"]');
  if (!root || !window.KVPortal) return;

  var R = window.KVReport;

  function $(id) { return document.getElementById(id); }
  function db() { return window.KVPortal.client; }

  var FOOT = {
    disclaimer: 'Kinvisit is not a medical provider. Our companions document and clarify. ' +
      'They do not diagnose, prescribe, or advise. Every clinical decision on this record ' +
      'was made by the treating doctor.',
    email: 'hello@kinvisit.in',
    phone: '+91 89204 28806'
  };

  var visits = [];
  var patientOf = {};
  var current = null;

  function show(visit) {
    current = visit;
    $('dk-sheet').innerHTML = R.html(
      R.fromRow(visit, patientOf[visit.patient_id]), FOOT);
    var rows = root.querySelectorAll('[data-visit]');
    for (var i = 0; i < rows.length; i++) {
      rows[i].setAttribute('aria-current',
        rows[i].getAttribute('data-visit') === visit.id ? 'true' : 'false');
    }
  }

  function renderList() {
    if (!visits.length) {
      $('rc-list').innerHTML =
        '<p class="dk-empty">No consultations have been filed yet. The first one appears ' +
        'here the evening after the visit.</p>';
      $('dk-sheet').innerHTML =
        '<p class="dk-empty">Your first report will show here.</p>';
      return;
    }
    var out = '';
    for (var i = 0; i < visits.length; i++) {
      var v = visits[i];
      var when = v.visit_date ? R.longDate(v.visit_date) : 'Date not recorded';
      var name = patientOf[v.patient_id] || (v.detail || {}).patient || '';
      var label = [v.department || 'Consultation', when, name].filter(Boolean).join(', ');
      out += '<button type="button" class="rc-row" data-visit="' + R.esc(v.id) +
        '" aria-current="false" aria-label="Read the report from ' + R.esc(label) + '">' +
        '<span class="rc-dept">' + R.esc(v.department || 'Consultation') + '</span>' +
        '<span class="rc-when">' + R.esc(when) + '</span>' +
        '<span class="rc-where">' + R.esc(v.hospital || '') + '</span>' +
        (name ? '<span class="rc-for">' + R.esc(name) + '</span>' : '') +
      '</button>';
    }
    $('rc-list').innerHTML = out;
  }

  /* The count a family asked for: how many visits, and when the last one was. */
  function renderCounts() {
    var byPatient = {};
    for (var i = 0; i < visits.length; i++) {
      var v = visits[i];
      if (!byPatient[v.patient_id]) byPatient[v.patient_id] = { n: 0, last: '' };
      byPatient[v.patient_id].n += 1;
      if (v.visit_date && v.visit_date > byPatient[v.patient_id].last) {
        byPatient[v.patient_id].last = v.visit_date;
      }
    }
    var out = '';
    for (var id in byPatient) {
      if (!byPatient.hasOwnProperty(id)) continue;
      var c = byPatient[id];
      out += '<div class="rc-count">' +
        '<span class="rc-count-n">' + c.n + '</span>' +
        '<span class="rc-count-lab">' +
          R.esc(patientOf[id] || 'Patient') + ', ' +
          (c.n === 1 ? 'one consultation attended' : c.n + ' consultations attended') +
        '</span>' +
        (c.last ? '<span class="rc-count-last">Most recent, ' +
                  R.esc(R.longDate(c.last)) + '</span>' : '') +
      '</div>';
    }
    $('rc-counts').innerHTML = out;
  }

  function fail(message) {
    $('rc-list').innerHTML = '<p class="dk-empty">' + R.esc(message) + '</p>';
    /* An empty sheet beside the message reads as a page that failed to load
       rather than one with nothing to show. */
    $('dk-sheet').innerHTML = '<p class="dk-empty">Nothing to show here yet.</p>';
  }

  window.KVPortal.guard('family').then(function (who) {
    if (!who) {
      if (document.documentElement.classList.contains('local')) {
        fail('This build is not connected to the portal yet, so there are no records to show.');
      }
      return;
    }

    db().from('patients').select('id, name').then(function (pres) {
      if (!pres.error && pres.data) {
        for (var i = 0; i < pres.data.length; i++) {
          patientOf[pres.data[i].id] = pres.data[i].name;
        }
      }
      return db().from('visits')
        .select('id, patient_id, visit_date, department, hospital, doctor, companion, ' +
                'recon, next_visit, detail')
        .order('visit_date', { ascending: false })
        .limit(200);
    }).then(function (res) {
      if (!res || res.error) {
        fail('Could not load your records. Try again, or message us.');
        return;
      }
      visits = res.data || [];
      renderCounts();
      renderList();
      if (visits.length) show(visits[0]);
    }).catch(function () {
      fail('No connection. Check the signal and try again.');
    });
  });

  KV.on(root, '[data-visit]', 'click', function (e, t) {
    var id = t.getAttribute('data-visit');
    for (var i = 0; i < visits.length; i++) {
      if (visits[i].id === id) { show(visits[i]); return; }
    }
  });

  var print = $('rc-print');
  if (print) print.addEventListener('click', function () { window.print(); });
})();
