# E8: 10-minute user test (script + observation sheet)

Status: READY TO RUN (human step). Anyone on the team can run this with one parent,
neighbour, or friend who has never seen the app. Total: 10 minutes. Do it once,
paste the quote, tick E8.

## Setup (1 min, before the participant arrives)

1. `python app/app.py` and open the local URL in a browser.
2. Open this file and a notes app (or paper) for observations.
3. Say only: "We're testing our app, not you. There are no wrong answers.
   Please think out loud while you use it."

## The session (8 min)

| Min | Task (read aloud, then stay silent) | What to watch for |
|-----|--------------------------------------|-------------------|
| 0-3 | "Your electric car needs charging tonight. Use the app to decide when to start it." | Can they pick region, appliance, wait time without help? Do they read the big answer first? |
| 3-5 | "Now show me what actually happened on that day, and tell me in your own words whether following the advice helped." | Do they find the hindsight check? Can they paraphrase the saving correctly? |
| 5-7 | "Your dishwasher can wait up to 3 days. Is that better or worse than charging the car tonight, and why?" | Do the % and gram numbers confuse them? Do they notice the naive-midnight baseline? |
| 7-8 | "What confused you, if anything? What would you change?" | Write down exact words. This is the most valuable minute. |

Do NOT explain the app during the tasks. If they get stuck for more than 60
seconds, note where, give the smallest hint, and note that you did.

## Record (1 min, right after)

Paste the filled block below into this file, commit it, tick E8:

```
Date:
Participant (first name + relation, e.g. "Priya, neighbour"):
Completed all 3 tasks without help? (yes / needed hint at step __):
One thing that confused them (their words):
One quote we can use in the write-up/video (their words):
Would they trust it enough to delay charging? (yes / no / maybe + why):
Tester initials:
```

## How to use the result

- One honest confusion -> one sentence in README Limits or one wording fix in
  `app/app.py` (B owns the app; propose the text here, don't edit the app).
- One good quote -> `docs/VIDEO_SCRIPT.md` closing or the form's impact answer.
- If the participant cannot complete task 1 unaided, that outranks every other
  polish item: fix the main screen first.
