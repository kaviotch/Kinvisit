/* M7. The WhatsApp message builder.
   The whole message is composed in the browser. Nothing reaches Kinvisit until
   the visitor presses send inside WhatsApp, and the free-text note is never
   sent to analytics. */
(function () {
  'use strict';
  var KV = window.KV;
  var root = document.querySelector('[data-mech="wa-builder"]');
  if (!root) return;

  var inner = root.querySelector('.wb-inner');
  var preview = root.querySelector('[data-wb-preview]');
  var msgBox = root.querySelector('[data-wb-msg]');
  var sendLink = root.querySelector('[data-wb-send]');
  var note = root.querySelector('.wb-note');
  var copied = root.querySelector('[data-wb-copied]');
  var number = root.getAttribute('data-wa-number');
  var picked = {};
  var started = false;

  function compose() {
    var lines = ["Hi, I'd like to book a Kinvisit visit.", ''];
    if (picked.location) lines.push("I'm in: " + picked.location);
    if (picked.appointment) lines.push('Appointment: ' + picked.appointment.toLowerCase());
    if (picked.department) lines.push('Department: ' + picked.department);
    var text = note && note.value.trim();
    if (text) lines.push('To raise: ' + text);
    lines.push('', 'Sent from kinvisit.in');
    return lines.join('\n');
  }

  function refresh() {
    var ready = picked.location && picked.appointment && picked.department;
    preview.hidden = !ready;
    if (!ready) return;
    var msg = compose();
    msgBox.textContent = msg;
    sendLink.setAttribute('href', 'https://wa.me/' + number + '?text=' + encodeURIComponent(msg));
  }

  KV.on(root, '.wb-opt', 'click', function (e, t) {
    var k = t.getAttribute('data-wb-k');
    picked[k] = t.getAttribute('data-wb-v');
    KV.press(root.querySelectorAll('[data-wb-k="' + k + '"]'), t);
    if (!started) { started = true; KV.track('wa_builder_started'); }
    KV.track('wa_builder_step', { step: k });
    refresh();
  });

  if (note) {
    note.addEventListener('input', refresh);
  }

  sendLink.addEventListener('click', function () {
    /* Categories only. The free text never leaves the browser. */
    KV.track('wa_builder_launched', {
      location: picked.location || 'unset',
      appointmentStatus: picked.appointment || 'unset',
      department: picked.department || 'unset'
    });
    /* If wa.me does not take over within a moment, fall back to copying. */
    window.setTimeout(function () {
      if (!document.hidden) {
        copied.textContent = 'If WhatsApp did not open, use Copy instead and paste it in.';
        copied.hidden = false;
      }
    }, 1500);
  });

  root.querySelector('[data-wb-edit]').addEventListener('click', function () {
    preview.hidden = true;
    if (note) note.focus();
  });

  root.querySelector('[data-wb-copy]').addEventListener('click', function () {
    var msg = compose();
    var done = function () {
      copied.textContent = 'Copied. Paste it into WhatsApp.';
      copied.hidden = false;
      KV.track('wa_builder_copied');
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(msg).then(done, function () {
        msgBox.focus();
        window.getSelection().selectAllChildren(msgBox);
      });
    } else {
      msgBox.focus();
      window.getSelection().selectAllChildren(msgBox);
    }
  });

  inner.hidden = false;
})();
