/* M13. The escalation ladder.
   Without this file all four sequences are on the page, one after another.
   This just lets a reader pick the one they are actually worried about. */
(function () {
  'use strict';
  var KV = window.KV;
  var root = document.querySelector('[data-mech="escalation"]');
  if (!root) return;

  var tabs = root.querySelectorAll('.esc-tab');
  var panels = root.querySelectorAll('.esc-panel');
  if (!tabs.length || tabs.length !== panels.length) return;

  function show(id, announce) {
    Array.prototype.forEach.call(panels, function (p) {
      p.hidden = p.id !== 'esc-' + id;
    });
    Array.prototype.forEach.call(tabs, function (t) {
      t.setAttribute('aria-pressed', t.getAttribute('data-esc') === id ? 'true' : 'false');
    });
    if (announce) KV.track('escalation_viewed', { branch: id });
  }

  KV.on(root, '.esc-tab', 'click', function (e, t) {
    show(t.getAttribute('data-esc'), true);
  });

  root.querySelector('.esc-tabs').addEventListener('keydown', function (e) {
    var list = Array.prototype.slice.call(tabs);
    var i = list.indexOf(document.activeElement);
    if (i === -1) return;
    var d = { ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1 }[e.key];
    if (!d) return;
    e.preventDefault();
    var next = list[(i + d + list.length) % list.length];
    next.focus();
    show(next.getAttribute('data-esc'), true);
  });

  show(tabs[0].getAttribute('data-esc'), false);
})();
