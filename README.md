# Kinvisit website

Static, no framework. Every route is a real HTML file at a real path and reads
correctly with JavaScript disabled. Every interactive mechanism is a progressive
enhancement over content that is already on the page.

```
tokens.css          the design system. The only place a colour, a size, a
                    space or a curve may be defined. check.py enforces it.
build.py            writes site/*.html. Page structure and long-form copy.
content.py          copy and data that changes without touching layout.
mechanisms.py       server-rendered markup for each interactive mechanism.
content/*.json      the numbers. Nothing renders until they are true.
check.py            copy, markup, privacy and budget checks.
test_mechanisms.py  drives every mechanism in a real browser.
test_nojs.py        proves every mechanism works with the scripts unreachable.
test_forms.py       submits both forms and checks what actually arrived.
copydiff.py         proves a redesign moved copy rather than rewriting it.
qa.py               layout QA: overlaps, crowding, real overflow, escapes.
standalone.py       builds the one file a companion can be given directly.
supabase/           the portal's schema and access rules. Run once, by hand.
content/business.json  the seller's legal identity. Ships empty. Nothing renders
                    until it is filled, the same rule as ledger.json.
gen_assets.py       renders the wordmark, share card, icons, and both PDFs.
gen_photos.py       builds every web variant of the four photographs.
photos/             the photograph masters. One per picture, edited nowhere else.
preview.py          local server that behaves like Netlify.
site/               the Netlify publish directory.
netlify/            the form confirmation-email function.
```

```bash
python3 build.py && python3 check.py     # rebuild and verify
python3 preview.py &                     # http://localhost:8899, real paths
python3 test_mechanisms.py               # 85 assertions in headless Chrome
python3 test_nojs.py                     # 18 assertions with no JavaScript
python3 test_forms.py                    # both forms, end to end
python3 qa.py                            # layout faults on every page, 5 widths
```

`qa.py` measures rather than opines. It reports four faults: two unrelated
blocks whose boxes intersect, two stacked blocks with almost no gap, a page
that really scrolls sideways, and an element escaping the container meant to
hold it. It tests horizontal overflow by trying to scroll the page, because
`documentElement.scrollWidth` counts content a scroller has already clipped
and reports overflow on pages that cannot move at all.

Form submissions in preview land in `_submissions.log`, in the same shape
Netlify delivers them, so you can read back exactly what the form sent.

```bash
python3 gen_assets.py                    # only when branding or the PDFs change
```

## Who attends, and what the site may say about it

The site never names the founder as the attendant. He has a page, his story is
on it, and the roster on `/about` records who covers visits today and what they
are not qualified as. Everywhere else the copy describes the role: "one named
companion, the same one each time".

**The site may not describe that person as clinically qualified until one is
hired.** `content/companions.json` carries `clinicallyQualified` per companion.
`content.py` reads it into `CLINICIAN_ON_ROSTER`, and the attendant copy on the
homepage and in the hero rails follows it, so the day a nursing or paramedic
qualified companion is hired and the certificate is on file, one field changes
the wording everywhere.

`check_attendant_claims()` in `check.py` fails the build on any page that says
a specialist, nurse or clinician attends while no companion records that
qualification. Future tense is allowed, because "every companion we hire will
be nursing or paramedic qualified" is a promise rather than a claim about who
is in the room this week.

This is not a style preference. A family is deciding whether a stranger sits in
their parent's consultation, and they decide on the strength of what that
person is. Saying "a specialist attends" when nobody clinical is on staff is a
misleading advertisement under the Consumer Protection Act, 2019, and it is the
one claim on this site that would be discovered on the first visit.

## Photographs and the mark

Four photographs, shot on location, each doing something the copy can only
assert: the person who actually attends, the report as a physical object, the
room the buyer is dreading, and the handwritten question list. `gen_photos.py`
builds WebP and JPEG at two widths from the masters in `photos/`, and fails if
one page load would cost a retina viewer more than 500KB of pictures. It is
328KB today.

**Both hospital photographs were checked for identifiable bystanders before
publishing.** The OPD frame is entirely backs of heads; the founder frame has
one person in the background whom the lens has thrown far enough out of focus
to be unrecognisable at 6x. Nothing was retouched. Re-run that check on any
new photograph taken inside a hospital: publishing a patient who did not agree
to it would contradict the whole product.

The wordmark is Geist outlines converted to a path by `gen_assets.py`, never
live text, because a mark set as `<text>` falls back to whatever face the
reader's machine has and the report is opened as a PDF on machines that have
never heard of Geist. The favicon is the same outlines. `check.py` fails the
build if a second mark appears or if the wordmark regains a `<text>` element.

## The report as a document

The sheet always sat on a deeper surface. What kept it reading as a section of
a web page was that it had no letterhead, no reference anyone could quote, no
ruled fields, and nobody's name at the bottom. It now has all four, plus a
second sheet showing behind it, and `report.js` renders the same letterhead in
the desk and in the family's portal from the same markup. A reference is
derived from the visit rather than stored, so it cannot drift from the record
it names.

## Legal, consent, and what was deliberately not built

Five pages carry the legal surface: `/privacy`, `/terms`, `/refunds`,
`/cookies`, and `/consent`. `/refunds` repeats clause 5 of the terms because
every Indian payment gateway wants a standalone cancellation and refund policy
before it will process a rupee. If one changes, change both; `check.py` cannot
tell you they have drifted.

**Consent is a tick, not a line of small print.** The DPDP Act, 2023 wants
consent that is free, specific, informed and unambiguous, given by a clear
affirmative action, next to a notice saying what is collected, what for, how to
withdraw, and how to complain. Both forms now carry that notice and a required
checkbox, and `site.js` was reading `input.value` for it, which is `"yes"`
ticked or not, so an unticked box used to pass validation.

**There is no cookie banner because there are no cookies.** Plausible is
cookieless; the only device storage is the portal session and a companion's
working draft, both strictly necessary. A banner for storage that is exempt
from consent teaches people to click through the ones that are not.
`check_third_parties()` keeps that sentence true by failing the build on any
embed or outside origin not named in `/cookies`.

Not done, on purpose:

- **No alt-text work.** The site has no images. The only `<img>` in the source
  is inside an HTML comment showing where the founder's photograph goes.
- **No image licensing review.** Every asset under `site/assets` is generated
  by `gen_assets.py` from the tokens. Nothing is licensed from anyone.
- **No fake reviews removed.** There were none. The two quotes are the
  founder's own words, attributed to him by name, and `companions.json` still
  reads `visitsAttended: 0` with `ledger.json` unpublished.

`content/business.json` is the one thing left unfilled. The Consumer
Protection (E-Commerce) Rules 2020 require a legal name, a principal
geographic address and a named grievance officer to be displayed. It ships
empty and renders nothing, because an invented address on a legal page is
worse than a missing one. Fill it and the details appear in the footer, on
`/refunds`, and in the consent notice.

## The portal

Three routes sit behind a sign-in, and none of them is in `sitemap.xml`:

```
/portal     two doors, families on the left, companions on the right
/records    a family reads its own consultations, and nothing else
/desk       a companion writes one up and files it
```

**The security boundary is `supabase/schema.sql`, not the JavaScript.** Every
table has row level security on and no policy grants a blanket read. A family
reaches a visit only through a `patients` row that names their account. The
guard in `portal.js` decides what to render; Postgres decides what exists. If
the guard were wrong tomorrow, a signed-out visitor would reach an empty page
rather than somebody's medical history, because the query returns nothing.

Consequences worth keeping:

- **Never filter records in JavaScript.** Ask for the rows and let the
  database refuse. Filtering in the browser is how one family ends up reading
  another family's record.
- **`supabase.js` is vendored**, in `site/assets/js/vendor/`. Portal pages
  hold a session, and a third-party script host is a third party who can take
  it. Refetch the pinned version to update it; never point a script tag at a
  CDN.
- **Portal pages have their own CSP** in `netlify.toml`, without the
  `'unsafe-inline'` the marketing pages need for JSON-LD. On a page with a
  session, injected script takes an account rather than defacing a page.
- **No analytics on any signed-in page.** Plausible is cookieless and takes no
  free text, but the fact that a family opened their medical record is itself
  the sensitive part.
- **There is no sign-up form.** Accounts are issued from the Supabase
  dashboard. Turn off "Allow new users to sign up" in the project, or people
  can create accounts you did not issue. They would read nothing, because an
  account with no `profiles` row fails every policy closed, but it should not
  exist.
- **Nothing deletes a visit.** There is no delete policy on `visits` on
  purpose.

### Standing it up

1. Create a Supabase project in `ap-south-1` (Mumbai).
2. Run `supabase/schema.sql` in the SQL editor.
3. Authentication > Providers > Email: turn **off** new sign-ups.
4. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Netlify's environment.
   `build.py` writes them into `assets/js/config.js` at build time, so no key
   is committed. The anon key is public by design; the service-role key must
   never appear anywhere under `site/`, and `build_config()` refuses to write
   one.
5. Add each family and companion by hand, per the comment at the foot of
   `schema.sql`.

Without steps 1 and 4 the portal says it is not connected and both doors stay
shut, and `/desk` opens in local mode: a working tool that can file nothing.
That is also how the offline file below behaves, and it is why an unconfigured
build leaks nothing. It cannot reach a database at all.

### Still to do before real patients

The consent and privacy review your `/consent` page already asks for now
covers stored data as well as attendance, because this holds medical records
rather than only producing them. That review has not happened.

## The report desk, `/desk`

The tool a companion opens in the hospital. They type the consultation in and
the family's report builds itself alongside, with the WhatsApp message ready
before they leave the building. Department and hospital are pickers; the
hospital list is `content/hospitals.json`, so the desk and the coverage
checker on `/hospitals` cannot drift apart. The question bank is the set a
companion is there to ask when nobody in the family can.

It is the one page here that cannot work without JavaScript, and the only
exception to the rule at the top of this file. A report generator with no
script generates nothing, so instead of showing a form that would produce
nothing it says what it needs and gives the office number. `test_nojs.py`
asserts that, rather than letting the exception go unrecorded.

Two deliberate limits:

- **Nothing typed into it leaves the browser.** There is not one `track()`
  call in `desk.js`. On a page holding a patient record, even a category name
  is more than an analytics provider should get.
- **A filed visit goes to the family's portal**, not to the companion's
  browser. Half-typed drafts still sit in `localStorage`, because an OPD with
  no signal is the normal case and a locked phone must not lose a
  consultation, but pressing "File this visit" writes the row the family
  reads.

```bash
python3 build.py && python3 standalone.py   # -> kinvisit-report-desk.html
```

That writes a single file with the fonts and both scripts inlined and the
marketing nav and footer removed. It opens by double clicking, needs no server
and no network, and can be handed to a companion before the domain resolves.
It is built from `site/desk.html` and is never edited by hand.

## What the checks enforce

`check.py` fails the build on any of: a colour pair under 4.5:1 computed
from `tokens.css` rather than trusted from a comment, a third-party embed or
an outside origin not named in `/cookies`, a claim of police verification that
`companions.json` does not record, a missing legal page, a homepage that stops
linking to one, a data-collecting form with no required consent checkbox, a hardcoded colour outside `tokens.css`,
a colour literal that is not an alpha of ink or paper, a font weight other than
400 or 500, a font family that is not a token, a forbidden family (Inter,
Roboto, Arial, any system stack), `--ink-40` used as a text colour, an em dash
or en dash in visible copy, a
banned marketing word, an emoji in **any** file including comments, unbalanced
tags, a broken internal link, a dangling id or `label for`, a skipped heading
level, a missing title, description, canonical, OG image, `lang` or skip link,
an `img` without `alt`, a price on the homepage that does not appear on
`/pricing`, homepage JavaScript over 60KB gzipped, a `track()` call that could
carry health free text, and any copy that promises a clinician who has not been
hired.

Current state: **all checks pass, 85/85 mechanism assertions, 18/18 with
JavaScript unavailable, and every form assertion.** No horizontal scrolling at 320px, 375px or 768px on
any of the fifteen pages, and none at 200% text zoom.

## The domain, which is the blocking problem

`kinvisit.in` is registered but has **no DNS record**. It resolves nowhere. No
Netlify subdomain answers either. Nothing is live, so:

- The robots-disallow that was reported for `kinvisit.in` was not this site. It
  was whatever the registrar serves on an unpointed domain.
- Canonical URLs now come from the environment. `build.py` reads Netlify's
  `URL`, so a deploy always canonicalises to the address that served it, and
  `CONTEXT` decides `robots.txt`: production allows crawling, every preview
  deploy disallows it and adds `noindex`. Point the DNS and the metadata is
  correct with no code change.
- Until the domain resolves, none of the analytics in Part G will record
  anything, so the Part K question of credibility versus awareness stays open.

## Before this goes live

1. **Point the DNS.** Everything else on this list is smaller than this one.
2. **Create `hello@kinvisit.in`.** It is in the footer, on five pages, and is
   the `From` address of the confirmation email. Mail to it bounces today.
3. **Fill in `content/ledger.json` and set `published: true`.** It ships with
   zeros and does not render anywhere, because publishing a visit count nobody
   has verified is worse than publishing nothing. Give the real numbers and the
   band appears on the homepage, on `/proof`, and on `/promise`.
4. **Add your photograph** at `site/assets/kunal.jpg` and set `photo` in
   `content/companions.json`. The card renders without an image rather than
   with a generic avatar, but a founder who will not show his face is a problem
   for a trust product.
5. **Turn on Netlify form notifications** for `visit-request` and
   `visit-details`, and set `RESEND_API_KEY` and `INTERNAL_EMAIL` for the
   confirmation email. Without the key the function exits quietly and Netlify
   still records every submission, so nothing is lost.
6. **Create the Plausible site.** Events already wired: `share_sent`,
   `share_recipient_arrived`, `compounding_scrubber_engaged` and
   `_completed`, `wa_builder_launched`, `gap_calculator_completed`,
   `hospital_checked`, `report_annotation_opened`, `callback_window_selected`,
   `pricing_recommender_used`, `overseas_tier_viewed`, `escalation_viewed`.
7. **Paste the live URL into WhatsApp on a real phone** and confirm the card
   shows the consultation report.

## Two things that need a person, not a build

- **`/consent` and the consent PDF must be reviewed by a lawyer**, and the
  Hindi must be checked by a native speaker, before either is used to take
  consent from anyone. Both currently say so on their face, and the PDF carries
  a draft banner. The emergency branch of the escalation ladder on the homepage
  needs the same review.
- **`content/compounding-demo.json` needs a nurse to read it.** It is one
  authored twelve-month story and it is labelled illustrative everywhere it
  appears, but it should be clinically plausible line by line before it is the
  centrepiece of the homepage. `clinicallyReviewed` is `false` in the file.

## Every figure on the site

Sources are in the header comment of `build.py`. If a figure is not there, it is
not on the site.

- **62.4% of over-60s live with at least one chronic condition**, **32.1% with
  two or more**, so more than half of those with any condition have two or more.
  LASI Wave 1 2017-18, n = 31,464, via BMC Geriatrics 2023.
- **29.7% live in a household with no adult child.** Same survey, n = 30,370.
- **149 million aged 60+ in 2022, 347 million projected by 2050.** UNFPA India
  Ageing Report 2023.

Three figures from the previous build were cut because they could not be
verified: "21% with a chronic condition", "1 in 5 live alone or with only a
spouse", and "23 crore over 60 by 2036".

## Deliberate departures from the brief

- **Real files, not a catch-all.** The brief asked for history routing plus
  `/* /index.html 200`. Netlify serves `/pricing` from `pricing.html` with no
  configuration, which gives real paths, a real per-page title, and pages that
  render with JavaScript off. The catch-all cannot do the last one, and the
  brief also requires it.
- **The stat cut went the other way.** Part E said keep 62% and 30% and cut
  "more than half". The two survive as one sentence on the 62% stat, because
  the multimorbidity number is the whole argument for the file and dropping it
  entirely costs more than the tightening gains. Three stat blocks became two,
  which is what Part E was really asking for.
- **Mechanism 3, the report preview builder, is not built.** It needs
  encrypted server-side storage of health-adjacent free text, a 90-day deletion
  job, and PDF email delivery. That is backend infrastructure this project does
  not have, and the brief says to skip rather than ship a degraded version. The
  honest interim is that `/book` already captures the same question in one
  field, and the sample report PDF is downloadable.
- **An email field on the booking form is optional, not absent.** A2 reduced
  required fields to three. Email is the fourth field and is optional, because
  the confirmation email in Part 5 cannot be sent to a phone number.
- **The founding-family offer is still not on the site.** It is a pricing
  commitment and it is yours to make.

## The design system

Six colours, measured not estimated. Paper `#FCFBF9`, paper-deep `#F4F1EB`,
ink `#14140F`, a deep slate-teal accent `#1E4D52` used only for links and the
primary CTA, and two muted semantics that appear in the report and the
medication tables and nowhere else: withdrawn `#8A4034`, substituted `#3F5F3A`.
Everything else is ink at an alpha.

Every combination clears WCAG AA on both backgrounds. The lowest text contrast
on the site is 5.27:1. The one exception is the "not prescribed" cell, which is
a decorative middot with `aria-hidden` and the real text in a visually hidden
span, and it carries an explicit exemption marker that `check.py` looks for.

Five type sizes, 88 / 52 / 32 / 18 / 13, contracting to 40 / 28 / 22 / 18 / 13
on a phone. Two weights, 400 and 500. Three families: Geist for the site,
Literata for the report, Geist Mono for every dose, date and label. The report
is set in a different family from the page on purpose, so it reads as a printed
clinical document embedded in a site rather than as another styled section.

## Performance

The homepage is 22.4KB gzipped including all CSS, which is inlined. Zero
render-blocking external requests. All three faces are self-hosted from
`assets/fonts` under the SIL Open Font License, 84KB total, with Geist
preloaded and all three on `font-display: swap`, so no text waits on a network
font and no reader on a health page is announced to a third-party font host.
Mechanism scripts load only when their section approaches the viewport: 10.4KB
gzipped on the homepage against a 60KB budget. The only third-party request is
Plausible, deferred.
