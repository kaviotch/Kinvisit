/* Kinvisit. Progressive enhancement only.
   Every fact on this site is in the HTML. Nothing here is load-bearing. */
(function () {
  'use strict';

  document.documentElement.classList.add('js');

  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------- mechanism loader ----
     Nothing here loads on page load. A mechanism script is fetched the first
     time its root element comes near the viewport, so the homepage ships the
     core file and nothing else until the reader scrolls to something that
     needs it. If a fetch fails the mechanism stays in its static state, which
     is always a complete and usable state. */

  var loaded = {};

  function loadMech(name) {
    if (loaded[name]) return;
    loaded[name] = true;
    var s = document.createElement('script');
    s.src = '/assets/js/' + name + '.js';
    s.defer = true;
    s.onerror = function () { loaded[name] = false; };
    document.head.appendChild(s);
  }

  var ALIAS = { via: 'share', ctxbar: 'share', currency: 'pricing', overseas: 'pricing' };
  /* The desk is the whole of /desk, not something scrolled to, so it loads
     at once rather than on a crossing. */
  var EAGER = { ctxbar: 1, via: 1, currency: 1, overseas: 1, pricing: 1,
                desk: 1, records: 1 };

  function wire() {
    var roots = document.querySelectorAll('[data-mech]');
    if (!roots.length) return;

    var pending = [];

    var observer = ('IntersectionObserver' in window)
      ? new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (!e.isIntersecting) return;
            observer.unobserve(e.target);
            var n = e.target.getAttribute('data-mech');
            loadMech(ALIAS[n] || n);
          });
        }, { rootMargin: '300px 0px' })
      : null;

    Array.prototype.forEach.call(roots, function (root) {
      var name = root.getAttribute('data-mech');
      if (EAGER[name] || !observer) {
        loadMech(ALIAS[name] || name);
        return;
      }
      observer.observe(root);
      pending.push(root);
    });

    /* An observer only reports a crossing. A reader who lands on an anchor,
       restores a scroll position, or jumps with the End key never crosses
       anything, so we also sweep on scroll. Both paths are idempotent. */
    if (!pending.length) return;

    var queued = false;
    function sweep() {
      queued = false;
      var h = window.innerHeight;
      pending = pending.filter(function (root) {
        var r = root.getBoundingClientRect();
        if (r.top > h + 400 || r.bottom < -400) return true;
        observer.unobserve(root);
        var n = root.getAttribute('data-mech');
        loadMech(ALIAS[n] || n);
        return false;
      });
      if (!pending.length) {
        window.removeEventListener('scroll', onScroll);
        window.removeEventListener('resize', onScroll);
      }
    }
    /* Throttled on a timer rather than an animation frame. requestAnimationFrame
       does not run in a backgrounded tab, and a mechanism that only loads when
       the tab is painting is a mechanism that sometimes never loads. */
    var last = 0;
    function onScroll() {
      var now = Date.now();
      if (now - last > 120) { last = now; sweep(); return; }
      if (queued) return;
      queued = true;
      window.setTimeout(function () { last = Date.now(); sweep(); }, 130);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    sweep();
  }

  /* ---------------------------------------------------------- analytics */

  function track(name, props) {
    try {
      if (typeof window.plausible === 'function') window.plausible(name, props ? { props: props } : undefined);
    } catch (e) { /* analytics must never break the page */ }
  }
  window.kvTrack = track;

  /* The only surface a mechanism module may rely on. */
  window.KV = {
    track: track,
    reduced: reduced,
    on: function (root, sel, type, fn) {
      root.addEventListener(type, function (e) {
        var t = e.target.closest ? e.target.closest(sel) : null;
        if (t && root.contains(t)) fn(e, t);
      });
    },
    press: function (nodes, active) {
      Array.prototype.forEach.call(nodes, function (n) {
        n.setAttribute('aria-pressed', n === active ? 'true' : 'false');
      });
    },
    json: function (id) {
      var el = document.getElementById(id);
      try { return el ? JSON.parse(el.textContent) : null; } catch (e) { return null; }
    }
  };

  /* -------------------------------------------------------- mobile menu */

  var burger = document.getElementById('burger');
  var menu = document.getElementById('menu');

  if (burger && menu) {
    var setMenu = function (open) {
      menu.hidden = !open;
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      document.body.style.overflow = open ? 'hidden' : '';
    };
    setMenu(false);
    burger.addEventListener('click', function () {
      setMenu(menu.hidden);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !menu.hidden) { setMenu(false); burger.focus(); }
    });
    menu.addEventListener('click', function (e) {
      if (e.target.closest('a')) setMenu(false);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth >= 940 && !menu.hidden) setMenu(false);
    });
  }

  /* ------------------------------------------------------------- motion
     One orchestrated page load with staggered reveals, then scroll reveals
     on the report and the medication table only. Everything else is static.
     Under prefers-reduced-motion nothing runs at all: the elements are
     simply marked done on the first frame. */

  var loadables = document.querySelectorAll('[data-load]');
  if (loadables.length) {
    if (reduced) {
      Array.prototype.forEach.call(loadables, function (el) { el.classList.add('lit'); });
    } else {
      var step = parseInt(
        getComputedStyle(document.documentElement).getPropertyValue('--stagger'), 10) || 60;
      Array.prototype.forEach.call(loadables, function (el, i) {
        window.setTimeout(function () { el.classList.add('lit'); }, 80 + i * step);
      });
    }
  }

  var revealables = document.querySelectorAll('.rv');
  if (revealables.length) {
    if (reduced || !('IntersectionObserver' in window)) {
      Array.prototype.forEach.call(revealables, function (el) { el.classList.add('in'); });
    } else {
      var ro = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('in');
          ro.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });
      Array.prototype.forEach.call(revealables, function (el) { ro.observe(el); });
    }
  }

  /* No count-up on statistics. A partially animated number is a wrong number,
     and these are health figures. They render once, from the HTML. */

  /* ------------------------------------------------------ record tabs --
     Without JS all four visits are stacked and the tabs are jump links. */

  var tablist = document.getElementById('visitTabs');
  if (tablist) {
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('.visit-tab'));
    var panels = tabs.map(function (t) { return document.querySelector(t.getAttribute('href')); });

    if (tabs.length && panels.every(Boolean)) {
      tablist.setAttribute('role', 'tablist');
      tablist.setAttribute('aria-label', 'Sample visits');

      var select = function (i, focus) {
        tabs.forEach(function (t, j) {
          t.setAttribute('role', 'tab');
          t.setAttribute('aria-selected', i === j ? 'true' : 'false');
          t.setAttribute('tabindex', i === j ? '0' : '-1');
          panels[j].hidden = i !== j;
          panels[j].setAttribute('role', 'tabpanel');
          panels[j].setAttribute('tabindex', '0');
        });
        if (focus) tabs[i].focus();
      };

      tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function (e) {
          e.preventDefault();
          select(i);
          track('Record Visit Viewed', { visit: String(i + 1) });
        });
        tab.addEventListener('keydown', function (e) {
          var next = null;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (i + 1) % tabs.length;
          if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (i - 1 + tabs.length) % tabs.length;
          if (e.key === 'Home') next = 0;
          if (e.key === 'End') next = tabs.length - 1;
          if (next !== null) { e.preventDefault(); select(next, true); }
        });
      });

      select(0);
    }
  }

  /* ------------------------------------------------------------- forms */

  Array.prototype.forEach.call(document.querySelectorAll('form[data-validate]'), function (form) {
    /* The required attributes stay in the markup so that a reader without
       JavaScript still gets the browser's own validation. Here, where we can
       do better, we turn that off and own it, because a native validation
       bubble is not an inline error message: it is inconsistent between
       browsers, it vanishes on the next click, and a screen reader announces
       it once and never again. */
    form.noValidate = true;

    function showError(field, message) {
      field.classList.add('invalid');
      var err = field.querySelector('.err');
      if (err) err.textContent = message;
      var input = field.querySelector('input, textarea, select');
      if (input) {
        input.setAttribute('aria-invalid', 'true');
        if (err && err.id) input.setAttribute('aria-errormessage', err.id);
      }
    }

    function clearError(field) {
      field.classList.remove('invalid');
      var input = field.querySelector('input, textarea, select');
      if (input) input.removeAttribute('aria-invalid');
    }

    function problem(input) {
      var required = input.hasAttribute('required');

      /* A checkbox always reports its value attribute, ticked or not, so
         reading .value here would let a required consent box through unticked.
         Consent that can be skipped is not consent. */
      if (input.type === 'checkbox') {
        return (required && !input.checked)
          ? 'We cannot arrange the visit without this.'
          : null;
      }

      var value = input.value.trim();
      if (required && !value) return 'This one we do need.';
      if (!value) return null;   /* an empty optional field is fine */

      if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)) {
        return 'That email address does not look complete.';
      }
      if (input.type === 'tel' && value.replace(/[^\d]/g, '').length < 8) {
        return 'Please include the country code and the full number.';
      }
      if (input.type === 'number') {
        var n = Number(value);
        var min = input.getAttribute('min'), max = input.getAttribute('max');
        if (isNaN(n)) return 'Please use digits only.';
        if (min !== null && n < Number(min)) return 'That looks too low.';
        if (max !== null && n > Number(max)) return 'That looks too high.';
      }
      return null;
    }

    /* Re-check a field the moment it stops being wrong, never before. */
    form.addEventListener('input', function (e) {
      var field = e.target.closest ? e.target.closest('.field') : null;
      if (!field || !field.classList.contains('invalid')) return;
      var input = field.querySelector('input, textarea, select');
      if (input && !problem(input)) clearError(field);
    });

    /* And check on the way out of a field, so an error is not saved up until
       the reader presses the button at the bottom of a long form. */
    form.addEventListener('focusout', function (e) {
      var field = e.target.closest ? e.target.closest('.field') : null;
      if (!field) return;
      var input = field.querySelector('input, textarea, select');
      if (!input) return;
      if (input.type !== 'checkbox' && !input.value.trim() && !input.hasAttribute('required')) return;
      var msg = problem(input);
      if (msg) showError(field, msg); else clearError(field);
    });

    form.addEventListener('submit', function (e) {
      var firstBad = null;

      Array.prototype.forEach.call(form.querySelectorAll('.field'), function (field) {
        var input = field.querySelector('input, textarea, select');
        if (!input || input.type === 'hidden') return;
        clearError(field);
        var msg = problem(input);
        if (!msg) return;
        showError(field, msg);
        if (!firstBad) firstBad = field;
      });

      if (firstBad) {
        e.preventDefault();
        var bad = firstBad.querySelector('input, textarea, select');
        if (bad) bad.focus();
        firstBad.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' });
        track('Form Rejected', { form: form.getAttribute('name') || 'unnamed' });
        return;
      }

      track(form.getAttribute('data-event') || 'Form Submitted');
    });
  });

  /* --------------------------------------------------------- tracking */

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a');
    if (!link) return;
    var href = link.getAttribute('href') || '';
    if (href.indexOf('wa.me') !== -1) track('WhatsApp Click', { page: location.pathname });
    else if (href.indexOf('.pdf') !== -1) track('Sample PDF Download');
    else if (href.indexOf('tel:') === 0) track('Phone Click');
  });

  wire();

  if (document.body.getAttribute('data-page') === 'home') {
    var fired = false;
    window.addEventListener('scroll', function () {
      if (fired) return;
      var h = document.documentElement;
      var depth = (h.scrollTop + window.innerHeight) / h.scrollHeight;
      if (depth >= 0.75) { fired = true; track('Home Scroll 75'); }
    }, { passive: true });
  }
})();
