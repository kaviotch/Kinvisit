/* M15. The portal.

   This file signs people in and decides which of the two doors they came
   through. It is worth being exact about what it is and is not.

   It is NOT the security boundary. Everything here runs in a browser the
   visitor controls, so every check below can be skipped by anyone willing to
   open the console. The boundary is row level security in Postgres: a session
   that is not entitled to a row is handed nothing, whatever page it asks
   from. What this file does is make the right thing happen for the honest
   majority, and fail politely rather than showing an empty page.

   Two consequences worth keeping in mind when editing:
     - Never put anything secret in here. The anon key is public by design.
     - Never decide what a family may read by filtering in JavaScript. Ask for
       the rows and let the database refuse. */
(function () {
  'use strict';

  var cfg = window.KV_CONFIG || {};
  var ready = !!(cfg.supabaseUrl && cfg.supabaseAnonKey && window.supabase);

  var client = ready
    ? window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
      })
    : null;

  /* Supabase returns its own messages, which name internals a family should
     not have to read. These are the only ones we show. */
  function readable(error) {
    var m = (error && error.message ? error.message : '').toLowerCase();
    if (m.indexOf('invalid login') > -1 || m.indexOf('credentials') > -1) {
      return 'That email and password do not match an account.';
    }
    if (m.indexOf('email not confirmed') > -1) {
      return 'This account has not been activated yet. Check your invitation email.';
    }
    if (m.indexOf('rate') > -1 || m.indexOf('many') > -1) {
      return 'Too many attempts. Wait a minute and try again.';
    }
    if (m.indexOf('failed to fetch') > -1 || m.indexOf('network') > -1) {
      return 'No connection. Check the signal and try again.';
    }
    return 'Could not sign you in. Try again, or message us and we will help.';
  }

  function profile() {
    return client.from('profiles').select('role, full_name').maybeSingle();
  }

  window.KVPortal = {
    ready: ready,
    client: client,

    /* Send someone to the page their role belongs to. */
    home: function (role) { return role === 'companion' ? '/desk' : '/records'; },

    readable: readable,

    /* Used by every signed-in page. Resolves with the profile, or null, and
       never throws: a page that cannot tell who you are must say so rather
       than break. */
    session: function () {
      if (!ready) return Promise.resolve(null);
      return client.auth.getSession().then(function (res) {
        if (!res || !res.data || !res.data.session) return null;
        return profile().then(function (p) {
          if (!p || p.error || !p.data) return null;
          return { user: res.data.session.user, role: p.data.role, name: p.data.full_name };
        });
      }).catch(function () { return null; });
    },

    signOut: function () {
      if (!ready) return Promise.resolve();
      return client.auth.signOut().catch(function () {});
    },

    /* The signed-in header, on every portal page. */
    chrome: function (who) {
      var name = document.getElementById('pt-name');
      var out = document.getElementById('pt-signout');
      if (name && who) name.textContent = who.name || who.user.email;
      if (out) {
        out.hidden = !who;
        out.addEventListener('click', function () {
          out.disabled = true;
          window.KVPortal.signOut().then(function () { window.location.href = '/portal'; });
        });
      }
    },

    /* Hold the page in its waiting state until the role is known. A page that
       renders first and redirects afterwards shows a signed-out visitor the
       shape of somebody's medical record, briefly. This one does not. */
    guard: function (wantRole) {
      var gateEl = document.querySelector('[data-gate]');
      var waiting = gateEl && gateEl.querySelector('.pt-waiting');
      var denied = gateEl && gateEl.querySelector('.pt-denied');
      var bodies = document.querySelectorAll('.pt-body');

      function refuse() {
        if (waiting) waiting.hidden = true;
        if (denied) denied.hidden = false;
        /* A short pause so the reason is readable before the page changes. */
        setTimeout(function () { window.location.href = '/portal'; }, 2500);
        return null;
      }

      function reveal() {
        if (gateEl) gateEl.hidden = true;
        for (var i = 0; i < bodies.length; i++) bodies[i].hidden = false;
      }

      /* No project configured. This build cannot reach the database at all,
         so there is nothing here to protect and nothing to sign in to: it is
         the offline file standalone.py produces, or a developer's checkout.
         Open the tool in local mode rather than bounce between two pages that
         both say the same thing. */
      if (!ready) {
        reveal();
        document.documentElement.classList.add('local');
        return Promise.resolve(null);
      }

      return window.KVPortal.session().then(function (who) {
        if (!who || who.role !== wantRole) return refuse();
        reveal();
        document.documentElement.classList.add('authed');
        window.KVPortal.chrome(who);
        return who;
      });
    }
  };

  /* ------------------------------------------------------ the sign-in page */

  var forms = document.querySelectorAll('[data-login]');
  if (!forms.length) return;

  /* The counter overhead (portal-ui.js) listens for these and reflects them
     on the board. It is presentation only, it is loaded before this file so
     nothing is missed, and every announcement below is made at the moment
     the thing it names actually happens. If that file is absent these are
     events nobody hears, which is the intended failure. */
  function announce(name, kind) {
    document.dispatchEvent(new CustomEvent('kv:portal', {
      detail: { state: name, kind: kind || null }
    }));
  }

  var unconfigured = document.getElementById('pt-unconfigured');
  if (!ready && unconfigured) {
    unconfigured.hidden = false;
    for (var f = 0; f < forms.length; f++) {
      var btn = forms[f].querySelector('button[type="submit"]');
      if (btn) btn.disabled = true;
    }
    announce('closed');
    return;
  }
  announce('open');

  /* Already signed in? Do not make someone type a password they just used. */
  window.KVPortal.session().then(function (who) {
    if (who) window.location.href = window.KVPortal.home(who.role);
  });

  Array.prototype.forEach.call(forms, function (form) {
    var kind = form.getAttribute('data-login');
    var error = document.getElementById(kind + '-error');
    var submit = document.getElementById(kind + '-submit');

    function fail(message) {
      error.textContent = message;
      error.hidden = false;
      submit.disabled = false;
      submit.textContent = submit.getAttribute('data-label');
      form.classList.remove('is-busy');
      announce('refused', kind);
    }

    submit.setAttribute('data-label', submit.textContent);

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = document.getElementById(kind + '-email').value.trim();
      var password = document.getElementById(kind + '-password').value;
      if (!email || !password) { fail('Enter your email and your password.'); return; }

      error.hidden = true;
      submit.disabled = true;
      submit.textContent = 'Signing in';
      form.classList.add('is-busy');
      announce('checking', kind);

      client.auth.signInWithPassword({ email: email, password: password })
        .then(function (res) {
          if (res.error) { fail(readable(res.error)); return; }
          return profile().then(function (p) {
            var role = p && p.data ? p.data.role : null;
            if (!role) {
              /* An account with no role reads nothing anyway. Say so here
                 rather than let them land on an empty page. */
              return window.KVPortal.signOut().then(function () {
                fail('This account is not set up yet. Message us and we will finish it.');
              });
            }
            if (role !== kind) {
              return window.KVPortal.signOut().then(function () {
                fail(role === 'companion'
                  ? 'That is a companion account. Use the companion form.'
                  : 'That is a family account. Use the family form.');
              });
            }
            announce('admitted', kind);
            window.location.href = window.KVPortal.home(role);
          });
        })
        .catch(function () { fail(readable(null)); });
    });
  });
})();
