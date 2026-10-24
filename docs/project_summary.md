# Transportation Operations Wingman: Project Summary

**See which deliveries need attention, understand the evidence, and prepare the next action without searching several systems.**

This is a working prototype for a regional delivery operations manager. It is built on synthetic data and is an independent demonstration, not an official Yzer product or system.

## The problem

To answer "what needs my attention right now?", a manager reconciles a shipment export, dispatch notes from the field, and a folder of customer procedures. The information exists. It's just in different places, and it has to be pulled together before every decision.

## What the prototype does

| Workflow | What the manager gets |
| --- | --- |
| **Find exceptions** | Filter by customer and region. A queue shows the flagged shipments, highest severity first. Each flag has its rule, threshold and age, for example "Window ended 1:00 PM; not delivered." |
| **Explain a shipment** | One screen holds the shipment facts, scan timeline, dispatch notes, and the procedure that applies to *that customer*. One click asks for a plain-language explanation. Every statement links back to its source, and the explanation proposes a next action and owner for review. |
| **Brief the manager** | A summary of the current queue: counts, a proposed action per shipment grounded in the procedure on file, and links back to the records. |

## Why it can be trusted

- **Rules decide, AI explains.** Which shipments are flagged, how many, and how late are all calculated by documented, tested rules. The AI writes the narrative and cannot change those numbers. A briefing whose counts don't match the rules is rejected.
- **Every claim is cited and checked.** Each answer must cite the shipment, scan, note, flag or procedure section it relies on. Citations are checked against the evidence before anything is shown. If a check fails, the app retries once and then shows an honest error. It never shows unchecked text.
- **Unknowns are stated, not guessed.** A missing ETA reads "Unavailable from source." When the driver's and the customer's accounts conflict, the answer shows both sides and is marked "Needs verification." When no procedure exists for an issue, the gap is reported.
- **Field notes are treated as data, not instructions.** The test data includes a planted note that tries to instruct the AI to mark shipments delivered. An evaluation case checks that the answer stays on the real issue. In the latest live run, the AI also labeled the note suspicious and said it was not followed.
- **Customer separation.** One customer's procedures are never shown for another customer's shipment. This is enforced in the database and again in the search index, and tested.

## Results so far (measured, not estimated)

All figures come from the 20-case evaluation set, run against the live AI providers (`evaluation/reports/latest_live.md`):

| Measure | Result |
| --- | --- |
| Evaluation cases passed | 20 of 20 (63 of 63 checks) |
| Exception rules vs. hand-written answer key | 9 of 9 expected flags; 0 false flags across the 92 normal shipments |
| Correct procedure retrieved (top 5) | 100% |
| Cross-customer leaks | 0 |
| AI answers passing validation on the first attempt | 12 of 12 |
| AI response time | about 12 s median, 15 s slowest |
| AI cost | about $0.05 per explanation or briefing; about $0.55 for a full 20-case evaluation run |
| Automated tests | 105, all passing; they never call paid services |

The evaluation also caught real problems, which were fixed before the demo:
- Early answers were too long and needed retries. A tighter prompt took retries from 4 of 12 calls to 0.
- A briefing once said "no procedure on file" when one existed. The briefing now receives the applicable procedures, and the app rejects that kind of false claim.

**Not yet measured:** time saved. The plan is to time the same task (preparing the Tampa exception briefing) by hand and with the prototype on the same synthetic scenario, and report both with the sample size. Any weekly-hours estimate will show its inputs (managers × briefings per week × minutes saved ÷ 60) and will not be presented as verified savings.

## Path to the real systems

The app reads shipments through a **canonical shipment schema**. A small adapter maps a TMS export into it. The included CSV adapter validates timezones, regions, customers, delivery windows and duplicate records, and reports rejected rows instead of guessing. Connecting a real TMS means writing one adapter for its export or API. The rules, screens and AI layer don't change. See `docs/tms_integration.md`.

## How it's built

Django, with Django's own login on every page and a separate non-admin demo account. Exception rules are plain, tested Python. AI explanations come from Claude through LangChain, validated against strict schemas. Procedure search uses Hugging Face embeddings stored in Pinecone, but only within the procedures the database allows for that customer. LangSmith traces every AI call. The app deploys on PythonAnywhere. Details: `docs/ai_architecture.md`, `docs/exception_rules.md`, `README.md`.

## Limitations

- Synthetic data: 100 shipments, 3 fictional customers, 3 Florida regions, and 6 short procedures.
- No connection to a real TMS. Read-only. It takes no operational actions and sends nothing to customers.
- No predictive ETA. An ETA is shown only when the source provides one.
- It runs on SQLite as a single-user demo. It's a prototype, not a production system.

## Proposed next step

Run a narrow pilot with **one operations manager in one region**, fed by a read-only TMS export through the existing adapter. Over two to four weeks, measure:
- whether the flags match what the manager would have flagged
- whether the manager actually uses the tool
- how much time briefing preparation takes before and after

Expand only if those numbers justify it.
