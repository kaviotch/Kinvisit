/* B3 the plan recommender, M9 currency display and the overseas tier.
   One file, because all three answer the same question: which of these am I
   actually buying, and what does it cost where I live. */
(function () {
  'use strict';
  var KV = window.KV;

  /* ------------------------------------------------- B3. the recommender */

  var pr = document.querySelector('[data-mech="pricing"]');
  if (pr) {
    var rules = KV.json('pricing-data') || {};
    var opts = pr.querySelectorAll('.pr-opt');

    KV.on(pr, '.pr-opt', 'click', function (e, t) {
      var key = t.getAttribute('data-pr');
      var rule = rules[key];
      if (!rule) return;

      KV.press(opts, t);

      Array.prototype.forEach.call(document.querySelectorAll('.plan'), function (card) {
        var mine = card.getAttribute('data-plan') === rule.plan;
        card.classList.toggle('recommended', mine);
        var note = card.querySelector('[data-plan-rec]');
        if (!note) return;

        if (mine) {
          note.innerHTML = '<b>Recommended for you</b>' + rule.reason;
          note.hidden = false;
        } else if (card.getAttribute('data-plan') === 'single') {
          note.innerHTML = '<b>What a single visit gives you</b>' + rule.singleLine;
          note.hidden = false;
        } else {
          note.hidden = true;
        }
      });

      KV.track('pricing_recommender_used', { doctors: key, plan: rule.plan });
    });
  }

  /* --------------------------------- M9. currency display, and the tier */

  var fx = KV.json('fx-data');
  var zone = '';
  try { zone = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { zone = ''; }

  var ZONE_REGION = [
    [/^Asia\/(Kolkata|Calcutta)$/, 'IN'],
    [/^Europe\/(London|Belfast)$/, 'GB'],
    [/^Europe\/Dublin$/, 'IE'],
    [/^Europe\/(Berlin|Paris|Amsterdam|Madrid|Rome|Brussels|Vienna|Lisbon|Helsinki)$/, 'DE'],
    [/^America\/(Toronto|Vancouver|Edmonton|Winnipeg|Halifax)$/, 'CA'],
    [/^America\//, 'US'],
    [/^Asia\/(Dubai|Muscat|Qatar|Riyadh|Kuwait|Bahrain)$/, 'AE'],
    [/^Asia\/(Singapore|Kuala_Lumpur)$/, 'SG'],
    [/^Australia\//, 'AU'],
    [/^Pacific\/Auckland$/, 'AU']
  ];

  var region = '';
  for (var i = 0; i < ZONE_REGION.length; i++) {
    if (ZONE_REGION[i][0].test(zone)) { region = ZONE_REGION[i][1]; break; }
  }

  var currency = null;
  if (fx && region && region !== 'IN') {
    Object.keys(fx.rates).forEach(function (code) {
      if (fx.rates[code].regions.indexOf(region) !== -1) currency = { code: code, d: fx.rates[code] };
    });
  }

  if (currency) {
    Array.prototype.forEach.call(document.querySelectorAll('[data-fx]'), function (el) {
      var inr = parseInt(el.getAttribute('data-fx'), 10);
      var local = Math.round(inr / currency.d.rate);
      el.textContent = 'approximately ' + currency.d.symbol + local +
        ', at the rate on ' + fx.date;
      el.hidden = false;
    });
    var note = document.querySelector('.fx-note');
    if (note) note.hidden = false;
    KV.track('pricing_currency_detected', { currency: currency.code, region: region });
  }

  /* The tier is revealed automatically for a detected overseas visitor, and
     manually for anyone else, because detection is a guess and the price is
     not a secret. */
  var tier = document.querySelector('[data-mech="overseas"]');
  if (!tier) return;

  function reveal(source) {
    if (!tier.hidden) return;
    tier.hidden = false;
    KV.track('overseas_tier_viewed', { source: source });
  }

  if (region && region !== 'IN') reveal('detected');

  var toggle = document.querySelector('[data-ov-show]');
  if (toggle) {
    if (!tier.hidden) toggle.closest('.ov-toggle').hidden = true;
    toggle.addEventListener('click', function () {
      reveal('manual');
      tier.scrollIntoView({ behavior: KV.reduced ? 'auto' : 'smooth', block: 'start' });
    });
  }

  KV.on(tier, 'a[href="/book"]', 'click', function () {
    KV.track('overseas_tier_cta_clicked');
  });
})();
