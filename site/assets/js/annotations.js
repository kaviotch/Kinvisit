/* M6. The annotated report.
   Without this file every annotation is already on the page, visible, below
   its section. All this does is let a reader collapse them. */
(function () {
  'use strict';
  var KV = window.KV;

  Array.prototype.forEach.call(document.querySelectorAll('[data-mech="annotations"]'), function (root) {
    var buttons = root.querySelectorAll('[data-annot-mode]');
    var annots = document.querySelectorAll('.annot');
    if (!annots.length) return;

    /* Plain is the default once JavaScript is here: the report has to read as
       a clinical document first, and as an explained one only if asked. With
       no JavaScript every annotation is already open, which is the right
       fallback because nothing can be toggled. */
    var STORE = 'kv-annot-mode';
    var mode = 'plain';
    try { mode = window.sessionStorage.getItem(STORE) || 'plain'; } catch (e) { /* private mode */ }

    function apply(next, announce) {
      mode = next;
      try { window.sessionStorage.setItem(STORE, next); } catch (e) { /* private mode */ }
      Array.prototype.forEach.call(annots, function (a) { a.hidden = next === 'plain'; });
      Array.prototype.forEach.call(buttons, function (b) {
        b.setAttribute('aria-pressed', b.getAttribute('data-annot-mode') === next ? 'true' : 'false');
      });
      if (announce) {
        KV.track('report_annotation_mode', { mode: next });
      }
    }

    Array.prototype.forEach.call(buttons, function (b) {
      b.addEventListener('click', function () {
        apply(b.getAttribute('data-annot-mode'), true);
      });
    });

    /* Opening one section on its own is worth knowing about, because it says
       which part of the deliverable buyers care about. */
    Array.prototype.forEach.call(annots, function (a) {
      var seen = false;
      a.addEventListener('mouseenter', function () {
        if (seen || mode !== 'annotated') return;
        seen = true;
        KV.track('report_annotation_opened', { section: a.getAttribute('data-annot-section') });
      });
    });

    apply(mode, false);
  });
})();
