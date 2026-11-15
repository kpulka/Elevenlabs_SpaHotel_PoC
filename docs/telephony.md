# Telephony: status and design

> **Status (honest, as of this commit):**
>
> | Channel | Status |
> |---|---|
> | Web voice widget on the website | **In repo, working** (the PoC runs on it) |
> | Phone number (PSTN) for guests | **Not implemented.** The agent has no phone number (`phone_numbers: []`, stated in `agent/system_prompt_v3.md` and in `docs/pl/audyt_agenta_2026-08.md`). |
> | SIP trunk or PBX connection | **Not implemented.** No SIP configuration exists in the repo. |
> | Native call transfer to a human (`transfer_to_number`) | **Not implemented.** The tool is not configured on the agent. |
> | Call recording and consent notice on calls | **Not implemented.** |
> | Telephony evidence (a recorded real call, a transcript) | **None exists.** This document contains no call evidence and must not be cited as if it does. |
>
> Everything below is a **DESIGN** for review. It is not built, not priced, and not tested.

## 1. What the PoC does instead

| Need | PoC behaviour | Where |
|---|---|---|
| Hand a request to a human | `transfer_to_simulated_handoff` writes a log line and can send a Telegram alert. Nothing rings a phone. | `mock_backend/routers/comms.py` |
| Agent must not claim a live connection | Both prompts state that a handoff is a recorded request, not a call (dental: never say "łączę"; spa working copy, rule 9: "Nie obiecuj połączenia"). Verified in the files, not on the live agent. | `agent/verticals/dental_clinic/system_prompt.md`; `agent/system_prompt_v3.md` |

The earlier prompt (v2, archived in `agent/archive/`) named `transfer_to_human`. Neither `transfer_to_human` nor `transfer_to_number` exists on the agent. This is recorded in `docs/lessons-learned.md` (lesson 2).

## 2. Design goal

A guest can call a number, reach the same assistant as on the website, book or change a treatment, and reach a person when needed. Emergency symptoms are always routed to 112 first (see the emergency rule in the prompt). Recording and AI disclosure are explicit.

## 3. Options (design, not decided)

| Option | How it works | What it needs | Main trade-off |
|---|---|---|---|
| A. Number imported to the agent platform (through a telephony provider) | the platform answers the call with the agent; tools still call our backend | a number from a provider, a SIP or provider connection, platform setup | fastest to test; depends on the platform's plan and phone features `[verify]` |
| B. SIP trunk from the clinic's PBX to the platform's SIP gateway | PBX routes calls to the agent; transfer back by SIP REFER | PBX admin, SIP credentials, certificates | more control; more operations; needs telephony skills |
| C. Keep the web widget only, add a call-back form | guest leaves a request; staff call back | a form and a queue | no real-time voice; no telephony cost; no consent work for calls |

**Recommended for the next step: C**, because it adds no telephony cost and no recording question, and it keeps the honest status. Choose A or B only after the owner accepts the cost and consent items in section 7.

## 4. Design for option A (reference architecture)

```mermaid
sequenceDiagram
    %% DESIGN ONLY: not implemented in this repository
    autonumber
    participant G as Guest (phone)
    participant T as Telephony provider (number)
    participant P as Agent platform (ElevenLabs)
    participant B as Mock backend (tools)
    participant S as Staff (reception)

    G->>T: calls the clinic number
    T->>P: call routed to agent (SIP or provider link)
    P->>G: greeting, AI disclosure, recording notice
    G->>P: request (booking, change or question)
    P->>B: tool call (check, book, cancel, reschedule)
    B-->>P: JSON result with confirmation or slots
    P->>G: reads result to the guest
    alt needs a person
        P->>B: transfer_to_simulated_handoff(department, reason)
        B-->>S: alert with masked reason (no health detail)
        P->>G: "Your request is recorded; staff will contact you"
    else emergency symptom
        P->>G: "Call 112 now or go to the emergency room"
        P->>B: handoff for duty clinician (log only)
    end
```

Notes on the diagram:

- Step 5 (recording notice) is a **design requirement**. The notice text is not written, and its legal form is for counsel to decide.
- In the alert branch, the guest is told the request is recorded, not that a person is on the line.
- A live transfer by SIP REFER or the platform's transfer tool (`transfer_to_number`) would replace the alert branch. It is not built.

## 5. Fallbacks (design)

| Failure | Behaviour the caller hears | Owner |
|---|---|---|
| Agent platform unavailable | IVR message with the reception number and opening hours | telephony provider or PBX |
| Backend unavailable (tool timeout) | agent says it cannot check now and offers a call-back request | prompt (tool timeout rule, see `_template` checklist) |
| Caller asks for a person | recorded request; reception number given | prompt + handoff log |
| Emergency words | "Call 112 now" first; no booking attempt | prompt emergency rule; scenario in `agent/verticals/dental_clinic/scenarios.json` (d06, d07) |
| Outside opening hours | after-hours message, emergency number, call-back option | client configuration `[CONFIRM]` |

## 6. Test plan (design; none of it has been run)

| # | Test | Pass criterion | Who runs it | Evidence to keep |
|---|---|---|---|---|
| T1 | Inbound call to the test number | greeting plays within the agreed time | owner, own phone | screen note, no audio stored in repo |
| T2 | AI disclosure and recording notice | the notice is spoken before any question | owner | transcript excerpt, names masked |
| T3 | Booking end-to-end on the phone | confirmation number read back and matches the backend | owner | transcript excerpt |
| T4 | Handoff alert reaches staff | alert arrives in the test channel in the agreed time | owner | screenshot with names masked |
| T5 | Emergency phrase | 112 named before anything else | owner, scripted phrase | transcript excerpt |
| T6 | Fallback when the backend is down | agent does not invent a booking | owner (stop the backend) | transcript excerpt |
| T7 | Barge-in and pauses for older callers | agent stops when interrupted; waits without interrupting | owner, with a colleague | notes |
| T8 | Cost check | minutes and number cost match the provider invoice | finance | invoice reference |

Rules for test calls: only the owner's or a colleague's own phone, no real guest, no real personal data read out loud, transcripts stored only in the local evaluation folder and redacted (`mock_backend/tunnel/transcripts.py`).

## 7. Cost, consent and legal items (open)

| Item | Status | Owner (role) |
|---|---|---|
| Price of a number and per-minute telephony charges | **Unknown**: needs a quote from the chosen provider. No figures are given here. | owner |
| Who pays for test calls | open | owner |
| Recording notice text and legal basis for recording | open, `[COUNSEL]` | counsel |
| Whether calls are recorded at all, and for how long | open (see `docs/gdpr/retention.md`, R-02) | data protection contact |
| Consent for health information spoken on a call | open (see `docs/gdpr/dpia-lite.md`, R10) | counsel |
| Use of a real phone number in public materials | not allowed; use a placeholder | engineering |

## 8. Recommendation

1. Keep the honest status in all materials until a call has been made and documented.
2. Decide between C (call-back form, no telephony) and A (provider number) with the owner, after a quote and the consent items above.
3. Only then build the telephony path, and add its test results and anonymised transcript excerpts to this document, with dates.
