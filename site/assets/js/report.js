/* M15a. The consultation report, rendered.

   One renderer, used twice: the desk shows a companion what the family will
   receive, and the family's portal shows them the same thing months later. If
   these were two pieces of code they would drift, and the family would
   eventually be reading a different document from the one that was written. */
(function () {
  'use strict';

  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'];

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* The report prints the date the way a family reads it, never as ISO. */
  function longDate(iso) {
    if (!iso) return '';
    var p = String(iso).split('-');
    if (p.length !== 3) return iso;
    var m = parseInt(p[1], 10);
    if (!m || m > 12) return iso;
    return String(parseInt(p[2], 10)) + ' ' + MONTHS[m - 1] + ' ' + p[0];
  }

  /* Seven changes, three colours. Moss is a medicine gained, clay is one taken
     away, plain is one that did not move. */
  var STATUS = {
    started:     { label: 'Started',     tone: 'moss' },
    increased:   { label: 'Increased',   tone: 'moss' },
    substituted: { label: 'Substituted', tone: 'moss' },
    reduced:     { label: 'Reduced',     tone: 'clay' },
    withdrawn:   { label: 'Withdrawn',   tone: 'clay' },
    unchanged:   { label: 'Unchanged',   tone: 'plain' },
    held:        { label: 'Held',        tone: 'plain' }
  };
  var STATUS_ORDER = ['started', 'increased', 'substituted', 'reduced',
                      'withdrawn', 'unchanged', 'held'];

  function has(v) { return v && String(v).trim().length > 0; }

  /* The letterhead mark is carried in the page rather than fetched, so the
     desk keeps it in a hospital with no signal. */
  function mark() {
    var t = document.getElementById('kv-mark');
    return t ? t.innerHTML : 'Kinvisit';
  }

  /* The same reference the printed record carries, derived from the visit so
     it cannot drift from the record it names. A document a family cannot
     quote back at us on the phone is a web page. */
  function reference(r) {
    if (!has(r.date)) return 'KV/UNISSUED';
    var p = String(r.date).split('-');
    var dept = String(r.dept || 'GEN').toUpperCase().replace(/[^A-Z]/g, '').slice(0, 4) || 'GEN';
    return 'KV/' + p[0] + '/' + p[1] + p[2] + '/' + dept;
  }

  function filled(list) {
    var out = [];
    list = list || [];
    for (var i = 0; i < list.length; i++) if (has(list[i].text)) out.push(list[i]);
    return out;
  }

  function html(r, opt) {
    opt = opt || {};
    r = r || {};
    var out = [];

    out.push('<div class="dk-doc-head">' +
      '<div class="dk-brand">' + mark() + '</div>' +
      '<dl class="dk-ref">' +
        '<div><dt>Document</dt><dd>Consultation record</dd></div>' +
        '<div><dt>Reference</dt><dd>' + esc(reference(r)) + '</dd></div>' +
        '<div><dt>Issued</dt><dd>' + esc(has(r.date) ? longDate(r.date) : 'Not dated') +
        '</dd></div>' +
      '</dl></div>');

    if (opt.sample) {
      out.push('<div class="dk-banner"><strong>Sample. Not a real patient.</strong> ' +
        'Every name, date, dose and result below is illustrative. Type over it to start ' +
        'a real record.</div>');
    }

    out.push('<div class="dk-vhead"><h2>' +
      (has(r.dept) ? esc(r.dept) : '<span class="dk-blank">Department not recorded</span>') +
      '</h2><span class="dk-when">' +
      (has(r.date) ? esc(longDate(r.date)) : 'Date not recorded') + '</span></div>');

    var kv = '<tr><th>Patient</th><td>' +
      (has(r.patient) ? esc(r.patient) : '<span class="dk-blank">Not recorded</span>') +
      '</td></tr>';
    if (has(r.where)) kv += '<tr><th>Where</th><td>' + esc(r.where) + '</td></tr>';
    if (has(r.doctor)) kv += '<tr><th>Doctor</th><td>' + esc(r.doctor) + '</td></tr>';
    if (has(r.companion)) kv += '<tr><th>Companion</th><td>' + esc(r.companion) + '</td></tr>';
    out.push('<table class="dk-kv">' + kv + '</table>');

    var asked = [];
    var ask = r.asked || [];
    for (var i = 0; i < ask.length; i++) {
      if (has(ask[i].q) || has(ask[i].a)) asked.push(ask[i]);
    }
    if (asked.length) {
      out.push('<h3>What the family asked</h3>');
      for (var a = 0; a < asked.length; a++) {
        out.push('<div class="dk-qa-out"><p class="dk-q">' + esc(asked[a].q) + '</p>' +
          (has(asked[a].a) ? '<p class="dk-a">' + esc(asked[a].a) + '</p>' : '') + '</div>');
      }
    }

    var ins = filled(r.instructions);
    if (ins.length) {
      var li = '';
      for (var n = 0; n < ins.length; n++) li += '<li>' + esc(ins[n].text) + '</li>';
      out.push('<h3>What the doctor instructed</h3><ul>' + li + '</ul>');
    }

    var meds = [];
    var md = r.meds || [];
    for (var m = 0; m < md.length; m++) if (has(md[m].name)) meds.push(md[m]);
    if (meds.length) {
      var rows = '';
      for (var p = 0; p < meds.length; p++) {
        var st = STATUS[meds[p].status] || STATUS.started;
        rows += '<tr><td class="dk-m">' + esc(meds[p].name) + '</td>' +
          '<td class="dk-s dk-' + st.tone + '">' + st.label + '</td>' +
          '<td>' + (has(meds[p].why) ? esc(meds[p].why) : '&middot;') + '</td></tr>';
      }
      out.push('<h3>Medicines changed today</h3><table class="dk-meds">' +
        '<thead><tr><th>Medicine</th><th>Change</th><th>Why</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table>');
    }

    if (has(r.recon)) {
      out.push('<h3>Reconciliation</h3><p class="dk-recon">' + esc(r.recon) + '</p>');
    }

    var tests = filled(r.tests);
    if (tests.length) {
      var tl = '';
      for (var t = 0; t < tests.length; t++) tl += '<li>' + esc(tests[t].text) + '</li>';
      out.push('<h3>Tests</h3><ul>' + tl + '</ul>');
    }

    var flags = filled(r.flags);
    if (flags.length) {
      var fl = '';
      for (var f = 0; f < flags.length; f++) {
        fl += '<li>' + esc(flags[f].text) + ' <span class="dk-mark dk-' +
          (flags[f].state === 'resolved' ? 'resolved' : 'open') + '">' +
          (flags[f].state === 'resolved' ? 'Resolved' : 'Open') + '</span></li>';
      }
      out.push('<h3>Left unresolved</h3><ul class="dk-flags">' + fl + '</ul>');
    }

    if (has(r.next)) out.push('<h3>Next visit</h3><p class="dk-next">' + esc(r.next) + '</p>');

    out.push('<div class="dk-doc-foot">' + esc(opt.disclaimer || '') + '<br>' +
      esc(opt.email || '') + ' &middot; ' + esc(opt.phone || '') + ' &middot; kinvisit.in</div>');

    return out.join('');
  }

  function message(r) {
    r = r || {};
    var L = ['*Kinvisit consultation record*'];

    var head = [];
    if (has(r.patient)) head.push(r.patient);
    if (has(r.date)) head.push(longDate(r.date));
    if (head.length) L.push(head.join(', '));

    var place = [];
    if (has(r.dept)) place.push(r.dept);
    if (has(r.where)) place.push(r.where);
    if (place.length) L.push(place.join(', '));

    var ask = r.asked || [], asked = [];
    for (var i = 0; i < ask.length; i++) if (has(ask[i].q)) asked.push(ask[i]);
    if (asked.length) {
      L.push('', '*What we asked*');
      for (var a = 0; a < asked.length; a++) {
        L.push((a + 1) + '. ' + asked[a].q);
        if (has(asked[a].a)) L.push('   Doctor: ' + asked[a].a);
      }
    }

    var ins = filled(r.instructions);
    if (ins.length) {
      L.push('', '*What to do now*');
      for (var n = 0; n < ins.length; n++) L.push('- ' + ins[n].text);
    }

    var md = r.meds || [], meds = [];
    for (var m = 0; m < md.length; m++) if (has(md[m].name)) meds.push(md[m]);
    if (meds.length) {
      L.push('', '*Medicines changed today*');
      for (var p = 0; p < meds.length; p++) {
        var st = STATUS[meds[p].status] || STATUS.started;
        L.push('- ' + meds[p].name + ' (' + st.label + ')');
      }
    }

    var tests = filled(r.tests);
    if (tests.length) {
      L.push('', '*Tests*');
      for (var t = 0; t < tests.length; t++) L.push('- ' + tests[t].text);
    }

    var flags = filled(r.flags);
    if (flags.length) {
      L.push('', '*Still open*');
      for (var f = 0; f < flags.length; f++) {
        L.push('- ' + flags[f].text + (flags[f].state === 'resolved' ? ' (resolved)' : ''));
      }
    }

    if (has(r.next)) L.push('', '*Next visit*', r.next);

    L.push('', 'The full written record follows. Kinvisit companions document and clarify. ' +
      'They do not diagnose, prescribe, or advise.');
    return L.join('\n');
  }

  /* A visits row from Postgres, back into the shape the renderer reads. The
     database keeps the columns it needs to sort and filter on; everything the
     report says lives in detail. */
  function fromRow(row, patientName) {
    var d = row.detail || {};
    return {
      patient: patientName || d.patient || '',
      date: row.visit_date || '',
      dept: row.department || '',
      where: row.hospital || '',
      doctor: row.doctor || '',
      companion: row.companion || '',
      recon: row.recon || '',
      next: row.next_visit || '',
      asked: d.asked || [],
      instructions: d.instructions || [],
      meds: d.meds || [],
      tests: d.tests || [],
      flags: d.flags || []
    };
  }

  function toRow(rec) {
    return {
      visit_date: rec.date || null,
      department: rec.dept || '',
      hospital: rec.where || '',
      doctor: rec.doctor || '',
      companion: rec.companion || '',
      recon: rec.recon || '',
      next_visit: rec.next || '',
      detail: {
        patient: rec.patient || '',
        asked: rec.asked || [],
        instructions: rec.instructions || [],
        meds: rec.meds || [],
        tests: rec.tests || [],
        flags: rec.flags || []
      }
    };
  }

  window.KVReport = {
    esc: esc,
    has: has,
    filled: filled,
    longDate: longDate,
    STATUS: STATUS,
    STATUS_ORDER: STATUS_ORDER,
    html: html,
    message: message,
    fromRow: fromRow,
    toRow: toRow
  };
})();
