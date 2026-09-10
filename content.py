#!/usr/bin/env python3
"""
Kinvisit content layer.

Everything a human might want to change without touching layout lives here or
in content/*.json. Numbers that make a claim about the business come from JSON
so they can be corrected in one place and so nothing renders until it is true.

House rules enforced by check.py: no em dashes, no en dashes, no emoji, no
banned marketing vocabulary, and every number either sourced or labelled
illustrative.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")


def load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        return json.load(f)


LEDGER = load("ledger.json")
COMPANIONS = load("companions.json")["companions"]
HOSPITALS = load("hospitals.json")
BUSINESS = load("business.json")


# Whether anyone on the roster is clinically qualified. Every line on the site
# that describes who attends reads this, so the day a nursing or paramedic
# qualified companion is hired and the certificate is on file, one field in
# companions.json changes the copy everywhere. Until then the site describes
# what it actually staffs.
CLINICIAN_ON_ROSTER = any(
    c.get("clinicallyQualified") for c in load("companions.json")["companions"]
)

ATTENDS_SHORT = (
    "A qualified companion at every visit" if CLINICIAN_ON_ROSTER
    else "The same named companion at every visit"
)

ATTENDS_RAIL = (
    "A nursing or paramedic qualified companion" if CLINICIAN_ON_ROSTER
    else "One named companion, the same one each time"
)
COMPOUNDING = load("compounding-demo.json")


# ============================================================ B. THE PRICING
#
# Restructured. The old table had a dominated tier: a one-off visit at 1,800
# undercut the 2,500 monthly plan that included the same single visit, so the
# cheapest way to buy was also the way that built no record. The record is the
# asset, so the record is now the thing being sold and attendance alone is
# priced as the lesser product it is.

PLANS = [
    {
        "id": "single",
        "name": "Single visit",
        "price": 2200,
        "per": "one visit",
        "kicker": None,
        "summary": "One attended consultation. One written report, delivered the same day.",
        "includes": [
            "A companion in the room for the whole consultation",
            "Your questions asked, and the answers written down",
            "Instructions and dosages recorded as given",
            "The report in your inbox before midnight India time",
        ],
        "excludes": [
            "No file is maintained after this visit",
            "No questions carried forward to the next appointment",
            "No medication reconciliation across visits",
        ],
        "excludeNote": "This is a transcript of one room.",
    },
    {
        "id": "record",
        "name": "The record, monthly",
        "price": 3200,
        "per": "per month",
        "kicker": "The file",
        "summary": "One attended consultation a month, and the maintained health file.",
        "includes": [
            "Everything in a single visit",
            "Medication history maintained across every visit",
            "Your questions carried forward until they are answered",
            "Unresolved items tracked and raised at the next appointment",
            "Unlimited calls about any past report, at no charge",
        ],
        "excludes": [],
        "excludeNote": None,
    },
    {
        "id": "record2",
        "name": "The record, two visits",
        "price": 5400,
        "per": "per month",
        "kicker": None,
        "summary": "Two attended consultations a month, and the maintained health file.",
        "includes": [
            "Everything in the record plan",
            "Two attended consultations a month",
            "Diagnostics and labs accompanied",
            "Priority scheduling",
        ],
        "excludes": [],
        "excludeNote": None,
    },
]

EXTRA_VISIT = {
    "price": 1600,
    "label": "Additional visit on a plan",
    "note": "Flat rate, however long the hospital takes.",
}

# B3. The recommender. Answers map to a plan and a reason.
DOCTOR_COUNT_OPTIONS = [
    {
        "value": "1",
        "label": "One",
        "plan": "single",
        "reason": "With one doctor, start with one visit and read the report before you commit "
                  "to anything monthly.",
        "singleVisitLine": "One doctor, one transcript. That is a fair match, and it is the "
                           "cheapest honest answer we can give you.",
    },
    {
        "value": "2",
        "label": "Two",
        "plan": "record",
        "reason": "Two doctors means two prescriptions and nobody comparing them. The "
                  "reconciliation is the point.",
        "singleVisitLine": "At two specialists, a single visit gives you one transcript. The "
                           "other doctor still starts from nothing.",
    },
    {
        "value": "3",
        "label": "Three or more",
        "plan": "record2",
        "reason": "With three specialists, no single doctor sees the full medicine list. That is "
                  "the specific problem the file solves.",
        "singleVisitLine": "At three specialists, a single visit gives you one transcript. The "
                           "next doctor still starts from nothing.",
    },
]

# B4. Policies. Every one of these is a purchase blocker if it is unanswered.
POLICIES = [
    ("If the hospital cancels or reschedules",
     "Nothing is billed. We rebook with you at no charge, however many times the hospital moves "
     "the appointment."),
    ("If you cancel",
     "More than four hours before the appointment, nothing is billed. Inside four hours, or once "
     "the companion has reached the hospital, the visit is billed in full. On a plan, a cancelled "
     "visit does not roll over into the next month."),
    ("If our companion does not arrive",
     "The visit is not billed and your next visit is free. We will tell you before you have to "
     "ask."),
    ("If the report is late",
     "Same day means before midnight India time on the day of the consultation. If it arrives "
     "after that, the visit is not billed. On a plan that is a credit against your next month, "
     "not a refund to your card, because we have not taken a card payment for it yet."),
    ("What is never billed",
     "Waiting time at the hospital, travel anywhere within Delhi NCR, phone calls about any past "
     "report, and corrections to a report we got wrong."),
]


# ====================================================== C. TRUST ARCHITECTURE
#
# Today's reality first, the standard being built toward second, framed as
# future. The previous order listed the hiring standard and then disclosed that
# none of those people exist, which reads as a bait and switch.

TODAY_HEADING = "Right now, one named companion attends every visit."

TODAY_BODY = [
    "Kinvisit is new. Until our nursing lead is hired and has trained the first companions, one "
    "named companion attends every consultation, writes every report, and signs it. You are not "
    "being handed to a rotating pool, and you are not being handed to a clinician either: the "
    "companion attending today is not clinically qualified, and this page says so for as long as "
    "that is true.",
]

TODAY_PRACTICAL = [
    "One person, named, whose number you have.",
    "The same person at every visit, so your parent is not meeting a stranger twice.",
    # Rendered from companions.json rather than asserted here. Claiming a
    # verification the roster does not record is the one lie this page
    # could tell that would matter, and check.py now fails the build on it.
    "A written confidentiality agreement covering your parent's records, viewable on request.",
]

FUTURE_STANDARD_HEADING = "The standard every companion will meet before their first booking."

FUTURE_STANDARD = [
    "Nursing or paramedic qualified, with certificates verified before hiring",
    "Police verified and background checked",
    "Certified on a 40 hour Kinvisit protocol covering consultation etiquette, question "
    "discipline, medication reconciliation, and report writing",
    "Bound by a written confidentiality agreement covering your parent's records",
    "Every report reviewed and co-signed by our nursing lead, once that role is filled",
]

TRUST_COMMITMENT = (
    "We will name every companion on this page as they join, with their qualification and the "
    "date they were verified. If this section ever shows an unnamed companion, we have broken a "
    "promise."
)


# ================================================ M6. THE ANNOTATED REPORT
#
# Section key must match the h3 text rendered in render_visit().

ANNOTATIONS = [
    ("Seen at",
     "The consultant's name is in your copy. We withhold it here because this is a public page "
     "and the doctor did not consent to being named on our website."),
    ("What the family asked, and what came back",
     "These questions came from you, in writing, before the appointment. The companion does not "
     "invent questions in the room."),
    ("Instructions, as given",
     "Verbatim. Not summarised, not interpreted. If the doctor said something ambiguous, it "
     "appears here ambiguous, and it goes into Unresolved."),
    ("Medication",
     "This is where the value is. The reconciliation is a comparison between what was just "
     "prescribed and everything your parent already takes. It is also the section with the most "
     "legal weight, which is why our nursing lead co-signs it once that role is filled."),
    ("Tests",
     "Ordered is not the same as booked, and booked is not the same as done. We track all three."),
    ("Unresolved",
     "The most important section. Anything that did not get an answer goes here, and it becomes "
     "the first item on the question list for the next appointment, automatically."),
    ("Next visit",
     "Written on the day, so the family does not reconstruct it from memory three weeks later."),
]


# ================================================== M13. THE ESCALATION LADDER
#
# Times do the persuasive work. Vague reassurance reads as marketing.

ESCALATION = [
    {
        "id": "conflict",
        "q": "What if something is wrong in the room?",
        "steps": [
            ("11:42", "Companion notices the new prescription conflicts with a standing medicine."),
            ("11:43", "Companion raises it with the treating doctor, as a question, not a challenge."),
            ("11:51", "If it is still unresolved, the companion steps into the corridor and calls you."),
            ("11:52", "You are on the phone with the person who was in the room, while your parent "
                      "is still in the building."),
            ("Same day", "It is in the report, in writing, in the Unresolved section."),
        ],
        "note": None,
    },
    {
        "id": "doctor",
        "q": "What if the doctor will not engage?",
        "steps": [
            ("11:38", "Doctor declines to have the companion in the room, or declines to answer "
                      "questions put by anyone other than the patient."),
            ("11:39", "Companion does not argue. The room stays entirely in the doctor's control."),
            ("11:40", "Companion waits immediately outside with your written question list."),
            ("12:10", "Your parent comes out. The companion goes through the prescription and the "
                      "instructions with them, line by line, and photographs every page."),
            ("Same day", "You get a report marked as recorded outside the room, so you know "
                         "exactly how the information reached us. We do not present secondhand "
                         "notes as if we heard them first hand."),
        ],
        "note": "This has a real cost. A report taken outside the room is weaker than one taken "
                "inside it, and we label it that way rather than hiding the difference.",
    },
    {
        "id": "emergency",
        "q": "What if my parent has a fall or a medical emergency during the visit?",
        "steps": [
            ("Immediately", "The companion calls for the hospital's own clinical staff. We are "
                            "inside a hospital, and the people qualified to respond are already "
                            "there."),
            ("Within a minute", "The companion tells those staff what is on the current medicine "
                                "list and hands over the health file. That file is often the "
                                "fastest source of drug and allergy information in the room."),
            ("Next", "The companion calls you, whatever hour it is where you are."),
            ("Until relieved", "The companion stays with your parent until a family member or "
                               "hospital staff formally takes over. They do not leave at the end "
                               "of the booked slot."),
        ],
        "note": "Read this plainly. Our companion is not a clinician on duty and will not "
                "intervene medically. They summon the people who can, they hand over the "
                "information, they call you, and they stay. Kinvisit is not an emergency service. "
                "If your parent needs urgent help at home, call your local emergency number.",
    },
    {
        "id": "disagree",
        "q": "What if I disagree with what the doctor said?",
        "steps": [
            ("Same day", "You have it in writing, which means you are disagreeing with a record "
                         "rather than with your parent's memory of a record."),
            ("Any time after", "Call us. We will tell you exactly what was said and what was not "
                               "said. We will not tell you whether the doctor was right."),
            ("Next appointment", "Your disagreement becomes a written question at the top of the "
                                 "list, and it is put to the doctor in the room."),
            ("If you want another opinion", "Take the report to any doctor you choose. It is "
                                            "yours. We do not refer, we take no commission, and "
                                            "we have no view on which doctor you should see."),
        ],
        "note": "We will never tell you that a doctor is wrong. We are not qualified to, and a "
                "companion who does that is a danger to your parent.",
    },
]


# ====================================================== M10. SIBLING SHARE

SHARE_VARIANTS = [
    {
        "id": "sibling",
        "label": "To a sibling",
        "text": (
            "I found this. It is a service in Delhi that sends a trained person into Papa's "
            "consultations and writes down everything the doctor says, the same day.\n\n"
            "It is {record} a month for one visit, or {record2} for two.\n\n"
            "Read this bit before you say no, it is the actual report they send: {url}/record\n\n"
            "The reason I think we should do it: nobody has the full list of what he takes. Not "
            "the cardiologist, not the nephrologist, not us."
        ),
    },
    {
        "id": "spouse",
        "label": "To a spouse",
        "text": (
            "About my parents. I keep saying I do not know what is actually happening at their "
            "appointments, and this is the thing that fixes it.\n\n"
            "Someone trained goes into the consultation, asks the questions we write down, and "
            "sends a written report the same day. {record} a month.\n\n"
            "This is what the report looks like: {url}/record\n\n"
            "I would rather spend this than keep having the same phone call where they tell me "
            "the doctor said it's fine."
        ),
    },
    {
        "id": "parent",
        "label": "To my parent",
        "text": (
            "Ma, I found something. A trained person can come with you to your appointments and "
            "write down what the doctor says, so I know what is happening and you do not have to "
            "remember all of it. They do not interfere. They just write.\n\n"
            "Can I book one and you see if you like it?\n\n"
            "{url}"
        ),
    },
]

SHARE_BANNER = (
    "Someone in your family sent you this. Start here: the report they wanted you to see."
)


# ==================================================== M11. THE CONVERSATIONS

CONVERSATIONS = [
    {
        "id": "parent",
        "q": "Telling your parent someone will be in the room.",
        "lede": "This is the conversation people put off, and it is the one that decides whether "
                "any of this happens.",
        "blocks": [
            ("What works", [
                "Make it about you, not about them. <strong>I need to know what is happening. I "
                "cannot be there.</strong>",
                "Give them the veto up front. <strong>If you hate it after one visit we stop.</strong>",
                "Be specific about what the person will and will not do. They write. They do not "
                "advise, and they do not speak for you.",
            ]),
            ("What does not work", [
                "<strong>You cannot remember things properly anymore.</strong> This is heard as an "
                "accusation about their mind, and it will end the conversation.",
                "<strong>The doctor probably is not telling you everything.</strong> This attacks "
                "a relationship they value and did not ask you to inspect.",
                "Presenting it as already decided. A parent who feels managed will refuse on "
                "principle.",
            ]),
            ("A message you can send, as written", [
                "Ma, I found something. A trained person can come with you to your appointments "
                "and write down what the doctor says, so I know what is happening and you do not "
                "have to remember all of it. They do not interfere. They just write. Can I book "
                "one and you see if you like it?",
            ]),
            ("If they still say no", [
                "This happens, and there is a smaller version of the service that works anyway. "
                "The companion waits outside the consultation room, and afterwards goes through "
                "the prescription and the instructions with your parent, line by line, and "
                "photographs every page.",
                "You get a report that is honestly labelled as recorded outside the room. It is "
                "weaker than the full thing. It is a great deal better than a blurry photograph "
                "three weeks late.",
                "Most parents who agree to that version stop objecting by the second or third "
                "visit, once they have seen that nobody interfered with their doctor.",
            ]),
        ],
    },
    {
        "id": "sibling",
        "q": "Telling your sibling this is worth paying for.",
        "lede": "The objection is almost always the same sentence, and it is a reasonable one.",
        "blocks": [
            ("The objection", [
                "<strong>Why can't Chachu just go with him? He lives twenty minutes away.</strong>",
            ]),
            ("The honest answer", [
                "Chachu can go. Chachu should go. Somebody from the family in that waiting room "
                "matters, and no service replaces it.",
                "What Chachu cannot do is compare a new prescription against nine standing "
                "medicines and notice the one that should not be there. That is a trained task, "
                "and it is the task that catches things.",
                "And Chachu will not write a dated report. Not because he does not care, but "
                "because nobody writes reports for their own family. So three months later the "
                "information exists only as what somebody remembers.",
                "It is a division of labour, not a replacement of family.",
            ]),
            ("If the objection is really about money", [
                "Say the number out loud rather than around it. It is {record} a month, which is "
                "less than most families spend on a single diagnostic test they did not need "
                "because nobody had the previous result.",
                "Offer to split it. Offer to pay it yourself for two months and let the report "
                "make the argument.",
            ]),
            ("A message you can send, as written", [
                "I know Chachu goes and I am not saying he should stop. The bit nobody is doing "
                "is checking the new prescription against everything else Papa already takes, and "
                "writing it down so the next doctor can read it. That is what this is. Look at "
                "the sample report before you decide, it takes two minutes.",
            ]),
        ],
    },
    {
        "id": "doctor",
        "q": "Telling the doctor who this person is.",
        "lede": "Families fear an awkward scene. Here is the whole script, so you know in advance "
                "exactly what will be said.",
        "blocks": [
            ("What the companion says, on entering", [
                "<strong>I am here on behalf of the family. I will not interrupt. I am writing "
                "down your instructions so they reach the daughter in London correctly.</strong>",
            ]),
            ("Why doctors rarely object", [
                "It asks nothing of them. No form to sign, no extra explanation, no second "
                "opinion being solicited in front of them.",
                "It is framed as a transcription task, which it is, and not as oversight.",
                "The room stays entirely in the doctor's control, and the companion leaves the "
                "moment they are asked to.",
            ]),
            ("If the doctor says no", [
                "The companion says <strong>of course</strong> and steps outside. There is no "
                "negotiation and no second attempt.",
                "You still get a report, labelled as recorded outside the room.",
            ]),
            ("What the companion never says", [
                "Anything beginning <strong>are you sure</strong>.",
                "Any reference to what another doctor said, unless the family asked for that "
                "question to be raised and it is read out as the family's question, not the "
                "companion's opinion.",
                "Any medical suggestion of any kind.",
            ]),
        ],
    },
]


# ====================================================== M9. THE OVERSEAS TIER

OVERSEAS = {
    "name": "Kinvisit Abroad",
    "price": 7500,
    "per": "per month",
    "summary": "Two attended consultations. Everything in the record plan. Plus what distance "
               "actually costs you.",
    "includes": [
        "A scheduled twenty minute call with the person who was in the room, at an hour that "
        "works where you live",
        "Reports also delivered as a single running PDF you can send to any doctor anywhere",
        "A named second contact in Delhi who can go on forty-eight hours notice",
        "WhatsApp response within four hours, in your waking hours",
    ],
    "note": "You are not paying for more visits. You are paying to be less far away. The call "
            "with the person who was in the room is the product.",
}

# Display only. We do not charge in these currencies. Rate date is shown on the page so an
# out of date number is visibly out of date rather than quietly wrong.
FX_DATE = "6 September 2026"
FX = {
    "GBP": {"symbol": "£", "rate": 111.0, "regions": ["GB"]},
    "USD": {"symbol": "$", "rate": 88.0, "regions": ["US", "CA"]},
    "AED": {"symbol": "AED ", "rate": 24.0, "regions": ["AE", "SA", "QA", "OM", "KW", "BH"]},
    "SGD": {"symbol": "S$", "rate": 68.0, "regions": ["SG", "MY"]},
    "AUD": {"symbol": "A$", "rate": 58.0, "regions": ["AU", "NZ"]},
    "EUR": {"symbol": "€", "rate": 95.0, "regions": ["DE", "FR", "NL", "IE", "ES", "IT"]},
}


# ======================================================== M2. GAP CALCULATOR

GAP_Q = [
    {
        "id": "doctors",
        "q": "How many different doctors does your parent see?",
        "options": [("1", "1"), ("2", "2"), ("3", "3"), ("4", "4 or more")],
    },
    {
        "id": "frequency",
        "q": "Roughly how often?",
        "options": [("12", "Monthly"), ("5", "Every two or three months"),
                    ("2", "Twice a year"), ("1", "Only when something happens")],
    },
    {
        "id": "full-list",
        "q": "Does any one of those doctors have the full list of what your parent takes?",
        "options": [("yes", "Yes"), ("no", "No"), ("unknown", "I don't know")],
    },
]


# ====================================================== M16. THE CONSENT KIT

CONSENT_INTRO = (
    "Before the first visit we obtain your parent's spoken agreement, on a recorded call or in "
    "person, that a Kinvisit companion may attend their consultation and that their medical "
    "information may be written down and sent to you. We do this ourselves. You do not have to "
    "have that conversation alone, though it goes better if you have it first."
)

CONSENT_WITHDRAWAL = (
    "Your parent can end this at any time by telling the companion or calling us. They do not "
    "need your permission, and we will tell you the same day."
)

CONSENT_POINTS = [
    ("What we ask for",
     "Permission for one named Kinvisit companion to sit in on your consultations, to write down "
     "what the doctor says, and to send that written record to a named family member."),
    ("What gets written down",
     "The date, the hospital, the department, what you asked, what the doctor said, the medicines "
     "you were prescribed, the medicines you already take, any tests ordered, and anything that "
     "was left unanswered."),
    ("What does not get written down",
     "Anything you tell the companion privately and ask them not to record. You can say that at "
     "any point, including during the consultation."),
    ("Who receives it",
     "One named family member, and nobody else. Not the hospital, not any other doctor, not any "
     "insurer, not any pharmacy or laboratory. We take no commission from any of them."),
    ("How long it is kept",
     "For as long as the family holds an account, and for three years after the last visit. "
     "Billing records are kept for eight years because Indian tax law requires it."),
    ("How you stop it",
     "Tell the companion, or call the number on this page. It stops immediately. You do not need "
     "anyone's permission, and we will tell your family the same day that you have withdrawn."),
]

# Hindi version of the consent one pager. Written to be read aloud to a parent.
# MUST be reviewed by a native Hindi speaker and by a lawyer before it is used
# for real consent. It is published as a draft and marked as one.
CONSENT_HI = [
    ("हम क्या पूछ रहे हैं",
     "हम आपकी अनुमति चाहते हैं कि किनविज़िट का एक व्यक्ति आपके डॉक्टर की मुलाक़ात में आपके साथ बैठे, "
     "डॉक्टर जो कहें उसे लिख ले, और वह लिखा हुआ रिकॉर्ड आपके परिवार के एक सदस्य को भेजे।"),
    ("क्या लिखा जाएगा",
     "तारीख़, अस्पताल, विभाग, आपने क्या पूछा, डॉक्टर ने क्या कहा, कौन सी दवाएँ दी गईं, आप पहले से कौन सी "
     "दवाएँ लेते हैं, कौन सी जाँच कही गई, और कौन सी बात का जवाब नहीं मिला।"),
    ("क्या नहीं लिखा जाएगा",
     "जो बात आप निजी तौर पर कहें और लिखने से मना करें। आप किसी भी समय ऐसा कह सकते हैं, मुलाक़ात के "
     "बीच में भी।"),
    ("यह किसे मिलेगा",
     "आपके परिवार के केवल एक व्यक्ति को, और किसी को नहीं। अस्पताल को नहीं, किसी दूसरे डॉक्टर को नहीं, "
     "बीमा कंपनी को नहीं, दवाख़ाने या लैब को नहीं। हम इनमें से किसी से कोई कमीशन नहीं लेते।"),
    ("यह कितने समय तक रखा जाएगा",
     "जब तक आपका परिवार हमारे साथ है, और आख़िरी मुलाक़ात के तीन साल बाद तक। बिल के काग़ज़ आठ साल तक "
     "रखने पड़ते हैं क्योंकि भारतीय कर क़ानून ऐसा कहता है।"),
    ("आप इसे कैसे बंद कर सकते हैं",
     "साथ आए व्यक्ति को बता दीजिए, या इस पन्ने पर दिए नंबर पर फ़ोन कीजिए। यह तुरंत बंद हो जाएगा। "
     "इसके लिए आपको किसी की अनुमति की ज़रूरत नहीं है, और हम उसी दिन आपके परिवार को बता देंगे कि "
     "आपने मना कर दिया है।"),
]
