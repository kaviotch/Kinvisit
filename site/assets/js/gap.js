/* M2. The gap calculator.
   Arithmetic only: visits per year is frequency times doctors. It never names
   a condition, a medicine, a risk, or an interaction, and the answer changes
   honestly when the visitor says nothing is wrong. */
(function () {
  'use strict';
  var KV = window.KV;
  var root = document.querySelector('[data-mech="gap"]');
  if (!root) return;

  var out = root.querySelector('[data-gap-out]');
  var answers = {};
  var started = false;

  var WORD = { 1: 'one', 2: 'two', 3: 'three', 4: 'four or more' };

  function paragraph() {
    var doctors = parseInt(answers.doctors, 10);
    var perDoctor = parseInt(answers.frequency, 10);
    var total = doctors * perDoctor;
    var list = answers['full-list'];

    var head = 'Your parent will have roughly ' + total + ' consultation' +
      (total === 1 ? '' : 's') + ' this year, across ' + WORD[doctors] + ' doctor' +
      (doctors === 1 ? '' : 's') + '.';

    var mid, tail;

    if (list === 'yes') {
      mid = 'Then your parent is better covered than most. What Kinvisit adds in that case is ' +
        'the written record of what was said in the room, which the medicine list does not ' +
        'capture.';
      tail = 'A medicine list tells you what they take. It does not tell you what the doctor ' +
        'said, what was asked and not answered, or what nobody wrote down.';
    } else if (doctors === 1) {
      mid = 'With one doctor there is at least one person who could hold the whole picture, ' +
        'if anyone is writing it down.';
      tail = total + ' room' + (total === 1 ? '' : 's') + ' this year. Each one starts from what ' +
        'your parent remembers, and ends with a piece of paper.';
    } else {
      mid = 'If no single doctor holds the full medicine list, then on average each one is ' +
        'making decisions with about ' + fraction(doctors) + ' of the picture.';
      tail = 'There is no chart being built. Each of those ' + total + ' rooms starts from what ' +
        'your parent remembers, and ends with a piece of paper.';
    }

    var cta = total + ' consultation' + (total === 1 ? '' : 's') + '. Kinvisit writes down all of them.';

    return '<h3>' + head + '</h3>' +
      '<p>' + mid + '</p>' +
      '<p>' + tail + '</p>' +
      '<p class="gap-cta"><strong>' + cta + '</strong><br>' +
      '<a class="btn btn-primary" href="/record" style="margin-top:12px">' +
      'See the report you would receive</a></p>';
  }

  function fraction(n) {
    return { 1: 'all', 2: 'half', 3: 'a third', 4: 'a quarter' }[n] || 'a fraction';
  }

  KV.on(root, '.gap-opt', 'click', function (e, t) {
    var key = t.getAttribute('data-gap-q');
    answers[key] = t.getAttribute('data-gap-v');
    KV.press(root.querySelectorAll('[data-gap-q="' + key + '"]'), t);

    if (!started) { started = true; KV.track('gap_calculator_started'); }

    if (answers.doctors && answers.frequency && answers['full-list']) {
      out.innerHTML = paragraph();
      out.hidden = false;
      KV.track('gap_calculator_completed', {
        doctors: answers.doctors,
        frequency: answers.frequency,
        hasFullList: answers['full-list']
      });
    }
  });

  root.hidden = false;
})();
