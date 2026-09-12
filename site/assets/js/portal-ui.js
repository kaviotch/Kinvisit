/* M27. The reception counter.

   Everything in this file is presentation. It signs nobody in, it reads
   nothing from the database, and if it fails to load the sign-in page is the
   plain pair of forms it has always been: the two controls it owns are
   rendered hidden and only this file reveals them.

   One rule held throughout. Nothing on the board is invented. The clock is
   the visitor's own clock, the link field is the protocol the page arrived
   over, the counter is whichever form holds the caret, and the status is
   only ever set from something that actually happened. A board showing a
   made-up queue length would be the most convincing thing on the page and
   the only dishonest one. */
(function () {
  'use strict';

  var doors = document.querySelector('.pt-doors');
  if (!doors) return;

  var board = document.querySelector('[data-pt-board]');

  /* ------------------------------------------------------------- the board */

  var fields = {};
  if (board) {
    Array.prototype.forEach.call(board.querySelectorAll('[data-pt]'), function (el) {
      fields[el.getAttribute('data-pt')] = el;
    });
  }

  /* Write a field only when the value has changed, and mark it so the tick
     animation runs. Rewriting an unchanged value would restart the animation
     on every keystroke, which is the opposite of what it is for.

     textContent, never innerHTML. Everything written here is one of a dozen
     fixed words, and it should stay impossible for that to stop being true
     by accident. */
  function set(name, value) {
    var el = fields[name];
    if (!el || el.getAttribute('data-v') === value) return;
    el.setAttribute('data-v', value);
    el.textContent = value;
    el.classList.remove('ticked');
    void el.offsetWidth;            /* restart, rather than queue, the tick */
    el.classList.add('ticked');
  }

  function state(name) { if (board) board.setAttribute('data-state', name); }

  /* The wall clock, written into its two digit pairs so the colon between
     them is left alone: it is blinking, and it belongs to the stylesheet.
     Checked every second and written on the minute, and deliberately outside
     set(), because a board field that ticks every sixty seconds for no reason
     is the sort of movement that makes a page tiring rather than alive. */
  var hh = board && board.querySelector('[data-pt-hh]');
  var mm = board && board.querySelector('[data-pt-mm]');
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function clock() {
    if (!hh || !mm) return;
    var d = new Date();
    hh.textContent = pad(d.getHours());
    mm.textContent = pad(d.getMinutes());
  }
  clock();
  setInterval(clock, 1000);

  /* What the page was actually served over. On the deployed site this is
     https and says so; opened from a file or over a local preview it says
     that instead of claiming a security property it does not have. */
  set('link', location.protocol === 'https:' ? 'Secure'
            : location.protocol === 'file:' ? 'Offline copy'
            : 'Local');

  /* ------------------------------------------- which counter you stand at */

  var resting = 'Reception';

  function rest() {
    set('counter', '--');
    set('status', resting);
    state(resting === 'Reception' ? 'open' : 'closed');
  }

  doors.addEventListener('focusin', function (e) {
    var form = e.target.closest ? e.target.closest('[data-login]') : null;
    if (!form || form.classList.contains('is-busy')) return;
    set('counter', form.getAttribute('data-counter'));
    /* A build with no project behind it stays closed however much anyone
       stands at the counter. Standing there is true, so the number lights;
       the status is not overwritten with something that is not. */
    if (resting !== 'Reception') return;
    set('status', 'At counter ' + form.getAttribute('data-counter'));
    state('at');
  });

  doors.addEventListener('focusout', function () {
    /* focusout fires before focusin on the element being moved to, so let the
       move land before deciding the counter is empty. */
    setTimeout(function () {
      if (doors.querySelector('.is-busy')) return;
      if (doors.contains(document.activeElement)) return;
      rest();
    }, 0);
  });

  /* --------------------------------------------------- the two attendants */

  Array.prototype.forEach.call(doors.querySelectorAll('[data-login]'), function (form) {
    var pw = form.querySelector('input[type="password"]');
    var peek = form.querySelector('[data-pt-peek]');
    var caps = form.querySelector('[data-pt-caps]');
    var email = form.querySelector('input[type="email"]');

    /* Unmasking a password is a real need on a phone in a corridor, and the
       alternative is people typing it into the email field to read it. The
       caret is put back where it was so the field does not jump to the end. */
    if (pw && peek) {
      peek.hidden = false;
      peek.addEventListener('click', function () {
        var shown = pw.type === 'text';
        var at = pw.selectionStart;
        pw.type = shown ? 'password' : 'text';
        peek.setAttribute('aria-pressed', shown ? 'false' : 'true');
        peek.textContent = shown ? 'Show' : 'Hide';
        try { pw.focus(); pw.setSelectionRange(at, at); } catch (err) { pw.focus(); }
      });
    }

    /* Caps Lock is the single commonest reason a correct password is refused,
       and the browser will not tell anyone unless we ask. */
    if (pw && caps) {
      var look = function (e) {
        var on = false;
        try { on = e.getModifierState && e.getModifierState('CapsLock'); } catch (err) { on = false; }
        caps.hidden = !on;
      };
      pw.addEventListener('keydown', look);
      pw.addEventListener('keyup', look);
      pw.addEventListener('blur', function () { caps.hidden = true; });
    }

    /* A tick beside the label once the address parses. It is not a claim that
       the account exists, only that this is the shape of an email, which is
       the mistake worth catching before a password is typed. */
    if (email) {
      var judge = function () {
        var field = email.closest('.field');
        if (field) field.classList.toggle('is-ok', !!email.value && email.validity.valid);
      };
      email.addEventListener('input', judge);
      email.addEventListener('blur', judge);
    }
  });

  /* ------------------------------------- what the auth module tells us of */

  document.addEventListener('kv:portal', function (e) {
    var d = e.detail || {};
    var form = d.kind ? doors.querySelector('[data-login="' + d.kind + '"]') : null;

    if (d.state === 'closed') {
      resting = 'Closed';
      rest();
      return;
    }
    if (d.state === 'open') { resting = 'Reception'; rest(); return; }

    if (d.state === 'checking') {
      if (form) form.classList.add('is-busy');
      set('counter', d.kind === 'companion' ? '02' : '01');
      set('status', 'Checking');
      state('busy');
      return;
    }
    if (d.state === 'refused') {
      if (form) form.classList.remove('is-busy');
      set('status', 'Not recognised');
      state('refused');
      return;
    }
    if (d.state === 'admitted') {
      set('status', 'Come through');
      state('at');
    }
  });

  rest();
})();
