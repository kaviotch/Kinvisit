/* M10 sibling share, plus the ?via=share arrival banner and M15 context bar.
   These three are one file because they are one behaviour: a family member
   sends the page, somebody else arrives on it, and the bar exists to catch the
   moment the reader wants to go and talk to their family. */
(function () {
  'use strict';
  var KV = window.KV;

  /* ------------------------------------------------------ the share panel */

  var variants = KV.json('share-data') || [];

  Array.prototype.forEach.call(document.querySelectorAll('[data-mech="share"]'), function (root) {
    var panel = root.querySelector('[data-sh-panel]');
    var text = root.querySelector('[data-sh-text]');
    var status = root.querySelector('[data-sh-status]');
    var chips = root.querySelectorAll('.sh-chip');
    var current = variants[0];
    if (!current) return;

    function pick(id) {
      variants.forEach(function (v) { if (v.id === id) current = v; });
      text.value = current.text;
      KV.press(chips, root.querySelector('[data-sh-v="' + current.id + '"]'));
      KV.track('share_variant_selected', { variant: current.id });
    }

    function open() {
      panel.hidden = false;
      text.value = current.text;
      text.focus();
      KV.track('share_opened', { page: location.pathname });
    }

    root.querySelector('[data-sh-open]').addEventListener('click', open);
    root.openSharePanel = open;

    KV.on(root, '.sh-chip', 'click', function (e, t) { pick(t.getAttribute('data-sh-v')); });

    root.querySelector('[data-sh-close]').addEventListener('click', function () {
      panel.hidden = true;
    });

    root.querySelector('[data-sh-send]').addEventListener('click', function () {
      var body = text.value;
      var done = function (channel) {
        KV.track('share_sent', { channel: channel, variant: current.id });
        status.textContent = 'Sent. If they ask, the report is the thing to point them at.';
      };
      if (navigator.share) {
        navigator.share({ text: body }).then(function () { done('native'); },
          function () { /* cancelled, and that is not a failure */ });
      } else {
        window.location.href = 'https://wa.me/?text=' + encodeURIComponent(body);
        done('whatsapp');
      }
    });

    root.querySelector('[data-sh-copy]').addEventListener('click', function () {
      var body = text.value;
      var done = function () {
        status.textContent = 'Copied.';
        KV.track('share_sent', { channel: 'copy', variant: current.id });
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(body).then(done, function () { text.select(); });
      } else {
        text.select();
        done();
      }
    });
  });

  /* ------------------------------------------- the arrival banner (?via=) */

  var banner = document.querySelector('[data-mech="via"]');
  if (banner) {
    var isVia = /(^|[?&])via=share(&|$)/.test(location.search);
    var dismissed = false;
    try { dismissed = window.sessionStorage.getItem('kv-via') === 'x'; } catch (e) { /* ignore */ }
    if (isVia && !dismissed) {
      banner.hidden = false;
      KV.track('share_recipient_arrived', { page: location.pathname });
      banner.querySelector('[data-via-close]').addEventListener('click', function () {
        banner.hidden = true;
        try { window.sessionStorage.setItem('kv-via', 'x'); } catch (e) { /* ignore */ }
      });
    }
  }

  /* ----------------------------------------------------- M15 context bar */

  var bar = document.querySelector('[data-mech="ctxbar"]');
  if (!bar) return;

  var gone = false;
  try { gone = window.sessionStorage.getItem('kv-ctx') === 'x'; } catch (e) { /* ignore */ }
  if (gone) return;

  bar.querySelector('[data-ctx-close]').addEventListener('click', function () {
    bar.hidden = true;
    document.body.classList.remove('has-ctxbar');
    try { window.sessionStorage.setItem('kv-ctx', 'x'); } catch (e) { /* ignore */ }
  });

  bar.querySelector('[data-ctx-share]').addEventListener('click', function () {
    var host = document.querySelector('[data-mech="share"]');
    if (host && host.openSharePanel) {
      host.scrollIntoView({ behavior: KV.reduced ? 'auto' : 'smooth', block: 'center' });
      host.openSharePanel();
    } else {
      window.location.href = '/record';
    }
  });

  var shown = false;
  function maybeShow() {
    if (shown) return;
    var h = document.documentElement;
    var depth = (h.scrollTop + window.innerHeight) / h.scrollHeight;
    /* A short page is already past 60 percent on load, and a reader who
       arrived on an anchor never fires a scroll event at all. */
    if (depth < 0.6) return;
    shown = true;
    bar.hidden = false;
    document.body.classList.add('has-ctxbar');
    window.removeEventListener('scroll', maybeShow);
  }
  window.addEventListener('scroll', maybeShow, { passive: true });
  maybeShow();
})();
