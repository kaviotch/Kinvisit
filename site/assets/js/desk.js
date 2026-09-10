/* M14. The report desk. A companion types the consultation into the left
   column and the family's report builds itself on the right.

   Two things are deliberate. Nothing a companion types is sent anywhere: the
   record lives in this browser and leaves it only when the companion presses
   send inside WhatsApp or saves the file. And there is no track() call in this
   file at all, because a patient record is the one place on this site where
   even a category name is too much to hand an analytics provider. */
(function () {
  'use strict';

  var root = document.querySelector('[data-mech="desk"]');
  if (!root) return;

  function $(id) { return document.getElementById(id); }

  function esc(v) { return window.KVReport.esc(v); }

  var R = window.KVReport;
  var longDate = R.longDate;
  var STATUS = R.STATUS;
  var STATUS_ORDER = R.STATUS_ORDER;
  var has = R.has;
  var filled = R.filled;

  var DISCLAIMER = root.getAttribute('data-disclaimer') || '';
  var EMAIL = root.getAttribute('data-email') || '';
  var PHONE = root.getAttribute('data-phone') || '';

  var DRAFT_KEY = 'kinvisit.desk.draft';
  var STORE_KEY = 'kinvisit.desk.records';

  /* A companion's own drafts still live in this browser, because an OPD with
     no signal is the normal case and a half-typed consultation must survive a
     locked phone. The filed record, by contrast, goes to the database, where
     the family can reach it. */

  /* --------------------------------------------------------------- state */
  function blank() {
    return {
      id: null, patient: '', date: '', dept: '', where: '', doctor: '', companion: '',
      asked: [], instructions: [], meds: [], recon: '', tests: [], flags: [], next: ''
    };
  }

  /* The desk opens on a worked example so the format is visible before the
     first record is typed. The first keystroke clears the sample banner. */
  function example() {
    var r = blank();
    r.patient = 'Sushila M.';
    r.date = '2026-03-12';
    r.dept = 'Endocrinology';
    r.where = 'Max Super Speciality, Saket';
    r.doctor = 'Consultant endocrinologist';
    r.companion = 'Kinvisit companion';
    r.asked = [
      { q: 'Her right hand has been swelling since January. Has it ever been mentioned?',
        a: 'No note of it in the file. Doctor examined it, said to keep watching it, ordered no test.' },
      { q: 'Are the morning sugars high enough to change anything?',
        a: 'Yes. Metformin doubled from today.' }
    ];
    r.instructions = [
      { text: 'Metformin to 1000mg twice daily, from tomorrow morning.' },
      { text: 'Fasting sugar log to be brought to every visit.' },
      { text: 'Return in four weeks. Sooner if the swelling spreads above the wrist.' }
    ];
    r.meds = [
      { name: 'Metformin 500mg BD to 1000mg BD', status: 'increased',
        why: 'Fasting sugars high through February. HbA1c 8.4%.' },
      { name: 'Atorvastatin 10mg OD', status: 'unchanged', why: 'Continued.' }
    ];
    r.recon = 'Checked against 3 standing medicines. No interaction flagged.';
    r.tests = [{ text: 'None ordered.' }];
    r.flags = [{ text: 'Right-hand swelling. Doctor advised monitoring. No test ordered.',
                 state: 'open' }];
    r.next = '09 April 2026, nephrology referral';
    return r;
  }

  var rec = blank();
  var isExample = false;

  /* --------------------------------------------------------- row builders */
  var LISTS = {
    asked: {
      target: 'dk-r-asked', count: 'dk-c-asked', empty: 'No questions recorded yet.',
      make: function () { return { q: '', a: '' }; },
      row: function (item, i) {
        return '<div class="dk-row dk-qa" data-i="' + i + '">' +
          '<div class="dk-stack">' +
            '<label><span class="dk-lab">Question ' + (i + 1) + '</span>' +
            '<textarea data-k="q" placeholder="What the family needed asked">' +
            esc(item.q) + '</textarea></label>' +
            '<label><span class="dk-lab">What the doctor said</span>' +
            '<textarea data-k="a" placeholder="The answer, in the doctor&#39;s words">' +
            esc(item.a) + '</textarea></label>' +
          '</div>' +
          '<button type="button" class="dk-x" data-del aria-label="Remove question ' +
          (i + 1) + '">&times;</button>' +
        '</div>';
      }
    },
    instructions: {
      target: 'dk-r-instructions', count: 'dk-c-instructions',
      empty: 'No instructions recorded yet.',
      make: function () { return { text: '' }; },
      row: function (item, i) {
        return '<div class="dk-row dk-line" data-i="' + i + '">' +
          '<label><span class="dk-lab">Instruction ' + (i + 1) + '</span>' +
          '<input type="text" data-k="text" value="' + esc(item.text) +
          '" placeholder="What the family does next"></label>' +
          '<button type="button" class="dk-x" data-del aria-label="Remove instruction ' +
          (i + 1) + '">&times;</button>' +
        '</div>';
      }
    },
    meds: {
      target: 'dk-r-meds', count: 'dk-c-meds', empty: 'No medicine changes recorded yet.',
      make: function () { return { name: '', status: 'started', why: '' }; },
      row: function (item, i) {
        var opts = '';
        for (var j = 0; j < STATUS_ORDER.length; j++) {
          var k = STATUS_ORDER[j];
          opts += '<option value="' + k + '"' + (item.status === k ? ' selected' : '') +
                  '>' + STATUS[k].label + '</option>';
        }
        return '<div class="dk-row dk-med" data-i="' + i + '">' +
          '<div class="dk-medtop">' +
            '<label><span class="dk-lab">Medicine and dose</span>' +
            '<input type="text" data-k="name" value="' + esc(item.name) +
            '" placeholder="Metformin 1000mg BD"></label>' +
            '<label><span class="dk-lab">Change</span>' +
            '<select data-k="status">' + opts + '</select></label>' +
            '<button type="button" class="dk-x" data-del aria-label="Remove medicine ' +
            (i + 1) + '">&times;</button>' +
          '</div>' +
          '<label><span class="dk-lab">Why it changed</span>' +
          '<input type="text" data-k="why" value="' + esc(item.why) +
          '" placeholder="The reason the doctor gave"></label>' +
        '</div>';
      }
    },
    tests: {
      target: 'dk-r-tests', count: 'dk-c-tests', empty: 'No tests recorded yet.',
      make: function () { return { text: '' }; },
      row: function (item, i) {
        return '<div class="dk-row dk-line" data-i="' + i + '">' +
          '<label><span class="dk-lab">Test ' + (i + 1) + ' and result</span>' +
          '<input type="text" data-k="text" value="' + esc(item.text) +
          '" placeholder="Renal panel. eGFR 58 mL per min."></label>' +
          '<button type="button" class="dk-x" data-del aria-label="Remove test ' +
          (i + 1) + '">&times;</button>' +
        '</div>';
      }
    },
    flags: {
      target: 'dk-r-flags', count: 'dk-c-flags', empty: 'Nothing left unresolved.',
      make: function () { return { text: '', state: 'open' }; },
      row: function (item, i) {
        return '<div class="dk-row dk-flagrow" data-i="' + i + '">' +
          '<label><span class="dk-lab">What is still open</span>' +
          '<input type="text" data-k="text" value="' + esc(item.text) +
          '" placeholder="Swelling unresolved across two visits."></label>' +
          '<label><span class="dk-lab">State</span><select data-k="state">' +
            '<option value="open"' + (item.state === 'open' ? ' selected' : '') + '>Open</option>' +
            '<option value="resolved"' + (item.state === 'resolved' ? ' selected' : '') +
            '>Resolved</option>' +
          '</select></label>' +
          '<button type="button" class="dk-x" data-del aria-label="Remove flag ' +
          (i + 1) + '">&times;</button>' +
        '</div>';
      }
    }
  };

  function renderList(key) {
    var spec = LISTS[key];
    var items = rec[key];
    var out = [];
    for (var i = 0; i < items.length; i++) out.push(spec.row(items[i], i));
    $(spec.target).innerHTML = items.length
      ? out.join('')
      : '<p class="dk-empty">' + spec.empty + '</p>';
    $(spec.count).textContent = items.length ? '(' + items.length + ')' : '';
  }

  /* The report and the message both come from the shared renderer, so what a
     companion checks here is exactly what the family opens later. */
  function reportHTML() {
    return R.html(rec, { sample: isExample, disclaimer: DISCLAIMER, email: EMAIL, phone: PHONE });
  }

  function waText() { return R.message(rec); }

  /* --------------------------------------------------------------- render */
  var msgTimer = null;

  function say(text) {
    $('dk-state').textContent = text;
    if (msgTimer) clearTimeout(msgTimer);
    if (text) msgTimer = setTimeout(function () { $('dk-state').textContent = ''; }, 4000);
  }

  function render() {
    $('dk-sheet').innerHTML = reportHTML();
    var msg = waText();
    $('dk-wa').textContent = msg;
    $('dk-wa-send').setAttribute('href', 'https://wa.me/?text=' + encodeURIComponent(msg));
    try {
      localStorage.setItem(DRAFT_KEY, JSON.stringify({ rec: rec, isExample: isExample }));
    } catch (e) { /* a full or blocked store must not stop the report */ }
  }

  function touched() { isExample = false; }

  /* -------------------------------------------------------------- wiring */
  var FIELDS = ['patient', 'date', 'doctor', 'companion', 'recon', 'next'];
  var CHOICES = ['dept', 'where'];

  for (var fi = 0; fi < FIELDS.length; fi++) {
    (function (k) {
      $('dk-f-' + k).addEventListener('input', function (e) {
        touched();
        rec[k] = e.target.value;
        render();
      });
    })(FIELDS[fi]);
  }

  /* A picker holds one of its own options or the word for everything else.
     The record only ever stores the finished string, so nothing downstream
     needs to know which of the two a companion used. */
  function choiceHas(key, value) {
    var sel = $('dk-f-' + key);
    for (var i = 0; i < sel.options.length; i++) {
      if (sel.options[i].value === value) return true;
    }
    return false;
  }

  function showOther(key, on) {
    $('dk-o-' + key).hidden = !on;
  }

  function readChoice(key) {
    var sel = $('dk-f-' + key);
    return sel.value === '__other' ? $('dk-f-' + key + '-other').value : sel.value;
  }

  function writeChoice(key) {
    var value = rec[key] || '';
    var known = value && value !== '__other' && choiceHas(key, value);
    $('dk-f-' + key).value = known ? value : (value ? '__other' : '');
    $('dk-f-' + key + '-other').value = known ? '' : value;
    showOther(key, !known && !!value);
  }

  for (var ci = 0; ci < CHOICES.length; ci++) {
    (function (k) {
      $('dk-f-' + k).addEventListener('change', function () {
        touched();
        var other = $('dk-f-' + k).value === '__other';
        showOther(k, other);
        rec[k] = readChoice(k);
        render();
        if (other) $('dk-f-' + k + '-other').focus();
      });
      $('dk-f-' + k + '-other').addEventListener('input', function () {
        touched();
        rec[k] = readChoice(k);
        render();
      });
    })(CHOICES[ci]);
  }

  /* Picking a standard question adds it as a row with the answer left open,
     because the answer is the part only the companion can supply. */
  /* Choosing the patient also fills the name the report prints, because
     retyping a name that is already in the record is how they end up
     different. It stays editable: the file may say something the family does
     not use. */
  $('dk-f-patient-id').addEventListener('change', function (e) {
    var sel = e.target;
    var name = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : '';
    if (!sel.value) return;
    touched();
    rec.patient = name;
    $('dk-f-patient').value = name;
    render();
  });

  $('dk-f-qbank').addEventListener('change', function (e) {
    var q = e.target.value;
    if (!q) return;
    e.target.value = '';
    touched();
    rec.asked.push({ q: q, a: '' });
    renderList('asked');
    render();
    var rows = $('dk-r-asked').querySelectorAll('.dk-row');
    var last = rows[rows.length - 1];
    if (last) {
      var answer = last.querySelector('[data-k="a"]');
      if (answer) answer.focus();
    }
  });

  function rowWrite(e) {
    var row = e.target.closest ? e.target.closest('.dk-row') : null;
    if (!row) return;
    var listKey = row.parentNode.id.slice(5);
    if (!LISTS[listKey]) return;
    var k = e.target.getAttribute('data-k');
    if (!k) return;
    touched();
    rec[listKey][+row.getAttribute('data-i')][k] = e.target.value;
    render();
  }

  root.addEventListener('input', rowWrite);
  root.addEventListener('change', function (e) {
    if (e.target.tagName === 'SELECT' && e.target.closest('.dk-row')) rowWrite(e);
  });

  KV.on(root, '[data-add]', 'click', function (e, t) {
    var key = t.getAttribute('data-add');
    touched();
    rec[key].push(LISTS[key].make());
    renderList(key);
    render();
    var rows = $(LISTS[key].target).querySelectorAll('.dk-row');
    var last = rows[rows.length - 1];
    if (last) {
      var field = last.querySelector('input, textarea');
      if (field) field.focus();
    }
  });

  KV.on(root, '[data-del]', 'click', function (e, t) {
    var row = t.closest('.dk-row');
    var key = row.parentNode.id.slice(5);
    touched();
    rec[key].splice(+row.getAttribute('data-i'), 1);
    renderList(key);
    render();
  });

  /* tabs */
  function selectTab(which) {
    var isReport = which === 'report';
    $('dk-tab-report').setAttribute('aria-selected', String(isReport));
    $('dk-tab-wa').setAttribute('aria-selected', String(!isReport));
    $('dk-pane-report').hidden = !isReport;
    $('dk-pane-wa').hidden = isReport;
    $('dk-copy').hidden = isReport;
    $('dk-wa-send').hidden = isReport;
    $('dk-print').hidden = !isReport;
  }

  $('dk-tab-report').addEventListener('click', function () { selectTab('report'); });
  $('dk-tab-wa').addEventListener('click', function () { selectTab('wa'); });

  $('dk-copy').addEventListener('click', function () {
    var msg = waText();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(msg).then(
        function () { say('Message copied'); },
        function () { say('Could not copy. Select the text and copy it.'); }
      );
    } else {
      say('Select the text and copy it.');
    }
  });

  /* The report sheet is the only thing on the printed page, so a companion
     with no other tooling can still hand the family a PDF. */
  $('dk-print').addEventListener('click', function () { window.print(); });

  /* ---------------------------------------------------------- form load */
  function fill() {
    for (var i = 0; i < FIELDS.length; i++) $('dk-f-' + FIELDS[i]).value = rec[FIELDS[i]] || '';
    for (var c = 0; c < CHOICES.length; c++) writeChoice(CHOICES[c]);
    for (var k in LISTS) if (LISTS.hasOwnProperty(k)) renderList(k);
    render();
  }

  $('dk-new').addEventListener('click', function () {
    rec = blank();
    isExample = false;
    fill();
    say('New record');
    $('dk-f-patient').focus();
  });

  /* ------------------------------------------------- filing to the record */

  var who = null;          /* the signed-in companion, once the guard resolves */
  var patients = [];       /* patients this companion may file against         */
  var filing = false;

  function db() { return window.KVPortal && window.KVPortal.client; }

  function renderFiled(rows) {
    if (!rows || !rows.length) {
      $('dk-saved-list').innerHTML = '<p class="dk-empty">You have not filed a visit yet.</p>';
      return;
    }
    var out = '';
    for (var i = 0; i < rows.length; i++) {
      var d = rows[i];
      var bits = [];
      if (has(d.department)) bits.push(d.department);
      if (has(d.visit_date)) bits.push(longDate(d.visit_date));
      var name = (d.detail && d.detail.patient) || 'Unnamed patient';
      out += '<div class="dk-saved-row">' +
        '<span class="dk-who">' + esc(name) + '</span>' +
        '<span class="dk-meta">' + esc(bits.join(', ') || 'No date') + '</span>' +
        '<button type="button" class="dk-link" data-open="' + esc(d.id) +
        '" aria-label="Open the record for ' + esc(name) + ', ' +
        esc(bits.join(', ') || 'no date') + '">Open</button>' +
        '<span></span></div>';
    }
    $('dk-saved-list').innerHTML = out;
  }

  function loadFiled() {
    if (!db()) return Promise.resolve();
    return db().from('visits')
      .select('id, visit_date, department, hospital, doctor, companion, recon, next_visit, detail')
      .order('visit_date', { ascending: false })
      .limit(100)
      .then(function (res) {
        if (res.error) {
          $('dk-saved-list').innerHTML =
            '<p class="dk-empty">Could not load your filed visits.</p>';
          return;
        }
        renderFiled(res.data);
        var tally = $('dk-tally');
        if (tally) {
          var n = res.data.length;
          tally.textContent = n === 1
            ? 'One visit filed so far.'
            : n + ' visits filed so far.';
        }
      });
  }

  /* A record is filed against a patient, and the patient row is what carries
     the family's right to read it. No patient, no filing: a consultation
     written against nobody would be invisible to the family it was for. */
  function loadPatients() {
    if (!db()) return Promise.resolve();
    return db().from('patients').select('id, name').order('name')
      .then(function (res) {
        if (res.error || !res.data) return;
        patients = res.data;
        var sel = $('dk-f-patient-id');
        var opts = '<option value="">Choose the patient this visit was for</option>';
        for (var i = 0; i < patients.length; i++) {
          opts += '<option value="' + esc(patients[i].id) + '">' +
                  esc(patients[i].name) + '</option>';
        }
        sel.innerHTML = opts;
      });
  }

  $('dk-save').addEventListener('click', function () {
    if (filing) return;
    var sel = $('dk-f-patient-id');
    var patientId = sel ? sel.value : '';

    if (isExample) { say('This is the sample record. Type over it first.'); return; }
    if (document.documentElement.classList.contains('local')) {
      say('This copy is not connected to the portal, so nothing can be filed from it.');
      return;
    }
    if (!db() || !who) { say('You are signed out. Sign in again before filing.'); return; }
    if (!patientId) { say('Choose which patient this visit was for'); sel.focus(); return; }

    filing = true;
    $('dk-save').disabled = true;
    say('Filing');

    var row = R.toRow(rec);
    row.patient_id = patientId;
    row.companion_id = who.user.id;

    var q = rec.id
      ? db().from('visits').update(row).eq('id', rec.id).select('id').maybeSingle()
      : db().from('visits').insert(row).select('id').maybeSingle();

    q.then(function (res) {
      filing = false;
      $('dk-save').disabled = false;
      if (res.error) {
        say('Could not file it. The record is still here, so try again.');
        return;
      }
      if (res.data && res.data.id) rec.id = res.data.id;
      say('Filed. The family can see it now.');
      loadFiled();
    }).catch(function () {
      filing = false;
      $('dk-save').disabled = false;
      say('No connection. The record is still here, so try again.');
    });
  });

  KV.on(root, '[data-open]', 'click', function (e, t) {
    if (!db()) return;
    var id = t.getAttribute('data-open');
    db().from('visits').select('*').eq('id', id).maybeSingle().then(function (res) {
      if (res.error || !res.data) { say('Could not open that visit'); return; }
      rec = R.fromRow(res.data, (res.data.detail || {}).patient);
      rec.id = res.data.id;
      isExample = false;
      fill();
      var sel = $('dk-f-patient-id');
      if (sel) sel.value = res.data.patient_id || '';
      say('Opened ' + (rec.patient || 'record'));
      window.scrollTo({ top: 0, behavior: KV.reduced ? 'auto' : 'smooth' });
    });
  });

  /* --------------------------------------------------------------- start */
  var draft = null;
  try { draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null'); } catch (e) { draft = null; }

  if (draft && draft.rec) {
    var base = blank();
    for (var bk in base) {
      if (base.hasOwnProperty(bk) && draft.rec[bk] !== undefined) base[bk] = draft.rec[bk];
    }
    rec = base;
    isExample = !!draft.isExample;
  } else {
    rec = example();
    isExample = true;
  }

  fill();
  selectTab('report');

  /* The desk draws itself straight away so a companion is never watching a
     blank page, but it holds every database call until the guard has confirmed
     a companion account. The guard is a courtesy; row level security is what
     actually stops a family account reading these rows. */
  if (window.KVPortal) {
    window.KVPortal.guard('companion').then(function (session) {
      if (!session) return;
      who = session;
      if (!rec.companion || isExample) {
        rec.companion = session.name || '';
        $('dk-f-companion').value = rec.companion;
        render();
      }
      loadPatients();
      loadFiled();
    });
  }
})();
