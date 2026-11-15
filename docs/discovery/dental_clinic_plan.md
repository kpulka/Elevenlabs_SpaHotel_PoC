# Implementation plan derived from the brief: Klinika Uśmiech

> **FICTIONAL EXERCISE. Design only, nothing here is implemented.** Derived from `dental_clinic_brief.md`. Status of each part is stated in the tables. Effort is a rough estimate for one engineer, not a commitment.

## 1. Scope

| In scope (design) | Out of scope |
|---|---|
| Voice assistant for information, standard booking, reschedule and cancel | Clinical triage, diagnosis, medicine advice |
| Handoff to reception, duty clinician, practice manager (logged in the PoC) | Real telephony (number, SIP trunk) |
| SMS confirmation to the guest's own number, and to a third party with consent | Payments, card data, invoicing |
| Polish and English | Other languages |

## 2. Tools to build

Contract exists in `agent/verticals/dental_clinic/tool_schema.example.json`. Backend: **not implemented**. The mock backend has no dental routes.

| Tool | Kind | Backend work | Status | Effort (est.) |
|---|---|---|---|---|
| `check_dental_availability` | read | calendar query per service and day; returns `slots`, `ambiguous` | design | M |
| `book_dental_appointment` | write | idempotent booking (key), slot lock, returns `confirmation_id` | design | M |
| `cancel_dental_appointment` | write | fee rule from KB 04 (computed server-side), slot release | design | S |
| `reschedule_dental_appointment` | write | move slot, new number, old number invalid | design | S |
| `send_sms_summary` | write | SMS gateway, consent flag required for third-party numbers | design | S |
| `transfer_to_simulated_handoff` | handoff | log and alert (existing PoC pattern) | reusable from PoC, new departments | S |

Reuse: the PoC's spa service shows the pattern (slot calendar, idempotency, cancellation fee rule, business rejections). The dental service would be a second service module, not a copy.

## 3. Knowledge base

| Doc | Mode | Build | Status |
|---|---|---|---|
| 01 general information | auto | write from client facts | design (outline only) |
| 02 services and screening | auto | clinician review of screening questions (O-4) | design |
| 03 price list | prompt | price list from administration (O-3 for missing items) | design |
| 04 cancellation policy | prompt | fee values must match the cancel tool | design |
| 05 privacy and procedures | prompt | recording and retention confirmed by client (O-1, O-5) | design, blocks go-live |

Parity check: copy `scripts/check_kb_parity.py` pattern for `.md` and `.txt` (not yet adapted).

## 4. Never-automate list and fallbacks

| Item | Fallback | Build step |
|---|---|---|
| Clinical decisions | duty clinician | prompt rule + scenario `never-automate-clinical_decisions` |
| Emergency | 112, then duty clinician | emergency rule at the top of the prompt + scenario d06, d07 |
| Allergy and anaesthesia | duty clinician with reason | flag-only rule + scenario d10 |
| Price negotiation | practice manager | prompt rule + scenario d12 |
| Complaints | practice manager | scenario d14 |
| Card data | reception | prompt rule (no card data in the call) |
| Other patients' data | reception | guardrail + scenario d09 |

## 5. Scenario list (15, from `scenarios.json`)

| Group | Scenarios | Gate |
|---|---|---|
| Booking and reschedule | d01 booking, d02 ambiguous service, d03 no slot, d05 reschedule, d13 English booking | must pass before pilot |
| Cancellation | d04 cancel with fee | must pass before pilot |
| Emergency | d06 tooth trauma with fever, d07 chest pain | 100 %, zero tolerance |
| Guardrails | d08 prompt injection, d09 other patient's data | 100 % |
| Health data | d10 allergy and anaesthesia | 100 % |
| Consent and privacy | d11 SMS to third party without consent, d15 recording and AI question | 100 % |
| Grounding | d12 price not in KB | 100 % |
| Complaints | d14 complaint to manager | must pass before pilot |

## 6. Rollout gates

| Gate | Entry criteria | Exit criteria |
|---|---|---|
| G0 Offline | `agent/verticals/render_vertical.py` valid; prompt names configured tools only; scenario shape check green | all offline tests green |
| G1 Scenario run (test environment) | backend routes exist in a test environment; no production data | every critical scenario passes; booking scenarios at least 90 % |
| G2 Owner review | KB 05 confirmed; O-1 to O-5 closed | signed review in the repository |
| G3 Supervised pilot | handoff channel tested in and out of hours | 5–10 supervised calls, each transcript reviewed, zero wrong prices, zero emergency misses |
| G4 Go-live | G3 exit met; rollback in 5 minutes documented | weekly transcript review for the first four weeks |

Rollback: disable the agent in the phone or widget configuration and return to manual handling. The runbook must name the person who does this.

## 7. Risks

| Risk | Likelihood (exercise) | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Agent quotes an invented price | medium | high (complaints, trust) | price only from tool or KB 03; scenario d12 | practice manager |
| Emergency symptoms handled as a booking | low | critical | 112 first; scenarios d06, d07 at 100 % | clinician |
| Wrong person gets appointment details | low | high (privacy) | third-party guardrail; consent for SMS; scenario d09, d11 | data protection contact |
| Health data kept longer than needed | medium | high (GDPR art. 9) | flag-only rule; transcript retention set by client (O-1); see `docs/gdpr/retention.md` | data protection contact |
| Handoff never reaches a human | medium | high | channel test in and out of hours (G3); PoC handoff is only a log | practice manager |
| Prompt and KB drift apart | medium | medium | KB parity check; prompt test names only configured tools | engineering |
| Recording without notice | low | high (legal) | scenario d15; client confirms recording (O-1) | data protection contact |

## 8. Dependencies and open questions

- Client answers O-1 to O-5 from the brief.
- A booking backend for the clinic (real system or the PoC pattern adapted).
- An SMS provider with a processor agreement (see `docs/gdpr/ropa.md`).
- Telephony is a separate decision (`docs/telephony.md`): this plan works on the web widget without it.

## 9. Not done

- No backend code for dental routes.
- No KB files written.
- No scenario run against any agent.
- No real client, no real data, no real phone numbers.
