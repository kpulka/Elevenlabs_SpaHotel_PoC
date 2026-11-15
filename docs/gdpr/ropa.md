# Record of processing activities (RoPA), Art. 30 GDPR: PoC voice receptionist

> **Not legal advice. Draft for the fictional spa "Bukowy Dwór" (PoC).** Items marked `[CONFIRM]` need a decision by the controller. Legal bases marked `[COUNSEL]` need a lawyer's review. Status labels are explained in [README.md](README.md).

## 1. Controller and contacts

| Item | Value |
|---|---|
| Controller | Uzdrowisko Termalne „Bukowy Dwór" (fictional) |
| Representative | `[CONFIRM]` |
| Data protection officer or contact | `[CONFIRM]`: use a role mailbox, not a personal address. The contact must appear in the privacy notice. |
| Processing system | "Anna", a voice assistant for information and booking (ElevenLabs Conversational AI agent + mock backend in this repo) |
| Channel | web voice widget (PoC). Telephony is not connected: see `docs/telephony.md`. |

## 2. Processing activities

Legal basis column: the proposed basis. `[COUNSEL]` = needs legal review.

| # | Activity | Data subjects | Data categories | Purpose | Legal basis (proposed) | Source in repo |
|---|---|---|---|---|---|---|
| A1 | Voice conversation with the AI assistant (audio and transcript on the platform) | guests, relatives calling for a guest | voice, transcript, name, contact details given in the call; **health information** if volunteered | answer questions, take bookings and changes | Art. 6(1)(b) for booking steps; for health information Art. 9(2)(a) explicit consent `[COUNSEL]` | `agent/system_prompt_v3.md`, `agent/config/anna_v3.json` |
| A2 | Booking of treatments (slot calendar) | guests | name, service, date and time, confirmation number | create, change and cancel bookings | Art. 6(1)(b) | `mock_backend/services/spa.py`, `mock_backend/routers/spa.py` |
| A3 | Cancellation and fee decision | guests | confirmation number, appointment time, cancellation reason (free text), `medical_release` flag | apply the fee rule; release the slot | Art. 6(1)(b); reason text and medical flag Art. 9(2)(a) `[COUNSEL]` | `mock_backend/responses/cancel.py`, `schemas.py` (`AnulowanieSPA`) |
| A4 | Handoff to staff (alert and log) | guests | department, reason (may contain health context), guest name | pass a request to a person | Art. 6(1)(b) and (f) `[COUNSEL]`; health context Art. 9(2)(a) | `mock_backend/routers/comms.py` (`/transfer_to_simulated_handoff`) |
| A5 | Confirmation text to the guest or to a third party (SMS in the design; in the PoC printed and relayed to Telegram) | guests; **third parties** whose number is given (relatives) | phone number, summary text | confirm a booking | Art. 6(1)(b) for the guest's own number; third party: consent of that person `[COUNSEL]` | `mock_backend/routers/comms.py` (`send_sms_summary`) |
| A6 | Operational logs of the backend | guests (indirectly), staff | request id, event name, masked phone, conversation id (field exists; not yet set, see known gaps) | diagnose faults | Art. 6(1)(f) `[COUNSEL]` | `mock_backend/logs.py` |
| A7 | Evaluation of the agent with simulated conversations | none (synthetic guests) | synthetic transcripts; redacted before saving | test scenarios | not personal data when synthetic; real transcripts must not be used | `mock_backend/tunnel/transcripts.py`, `evals/` |
| A8 | Website widget (signed session link, browser identifier) | website visitors | IP address in server logs; anonymous user id stored in the browser | open a voice session | Art. 6(1)(a) for the voice session `[COUNSEL]` | `frontend/app/api/anna/signed-url`, widget file `frontend/public/widget/convai-widget-embed.js` |
| A9 | Website analytics | website visitors | pseudonymous usage data | measure use of the site | Art. 6(1)(a) `[CONFIRM]` (consent banner not verified in this package) | `frontend/package.json` (`@vercel/analytics`) |
| A10 | Notification of the team through a messaging bot (Telegram) | staff; guests indirectly | the same content as A4 and A5 | alert staff | Art. 6(1)(f) `[COUNSEL]` | `mock_backend/telegram.py` |

Known gaps in A2–A5 (from the code, not yet fixed):

- The guest name is included in the Telegram alert text (`mock_backend/routers/comms.py`, `guest_name`). Masking is planned.
- The recipient phone number is returned unmasked in one response field (`delivered_to`).
- Health context in free text (reason, handoff reason) is not separated from other text.

## 3. Data categories and special-category data

| Category | Art. 9? | Examples in this system | Minimisation rule (design) |
|---|---|---|---|
| Identity | no | guest name | use only for the booking; mask in logs (in repo for logs); mask in alerts (gap) |
| Contact | no | phone number (guest or relative) | mask in logs (in repo); send only with consent for third parties |
| Booking | no | service, date, time, confirmation number | none beyond the booking |
| **Health** | **yes** | balneology screening answers, cardiovascular and implant questions, diabetic or gluten-free diet, `medical_release` flag, hospital stay mentioned as a reason | flags only, never diagnoses; no health text in logs; see `dpia-lite.md` |
| Voice | biometric only if used to identify | recording of the call | no speaker identification in this system (design: keep it that way) |

## 4. Recipients and processors

| Recipient | Role | Data | Location | Basis and status |
|---|---|---|---|---|
| ElevenLabs | processor (conversational AI platform: speech-to-text, LLM, text-to-speech, storage of conversations) | A1, A3, A4 content, voice | `[CONFIRM]` against the contract; not verifiable from the repo | **Platform (verify)**: DPA and sub-processors must be obtained. The repo's architecture text describes EU residency, zero retention and PII redaction; these are **Design / Enterprise tier** (see section 6). |
| Model provider behind the agent's LLM (a Gemini model per the agent config) | sub-processor of the platform | prompt inputs including conversation content | per platform contract | **Platform (verify)** |
| Telegram | recipient of alerts (A4, A5, A10) | the alert text | Telegram infrastructure (outside the EEA may apply) `[COUNSEL]` | In repo (relay exists). Recommend: stop sending health context and full names; see known gaps. |
| Cloudflare | transit of webhook requests through a quick tunnel in the PoC | webhook payloads (may contain names and reasons) | Cloudflare global network | In repo (tunnel scripts); PoC only. Production needs a named host and a processor contract. |
| Vercel | hosting and analytics of the website | visitor data (A8, A9) | per vendor; `[CONFIRM]` | In repo (package dependency). Hosting and analytics contracts `[CONFIRM]`. |
| SMS gateway | not connected in the PoC | would receive A5 | would need a processor contract | **Design (not implemented)** |
| Hotel or spa booking system (PMS) | none in the PoC; slots are in memory | A2 | `[CONFIRM]` | **Design (not implemented)** |

## 5. Transfers outside the EEA

| Flow | Status |
|---|---|
| Platform processing in the US or elsewhere | **Platform (verify)**: confirm processing locations in the platform's documentation and contract. EU residency is an Enterprise-tier design statement, not a verified fact for this agent. |
| Telegram | `[COUNSEL]`: transfer mechanism to be confirmed, or content minimised so that no health data and no full names are sent |
| Vercel and Cloudflare | `[CONFIRM]`: transfer mechanism in their terms |

## 6. Plan-dependent statements (must not be presented as current)

| Feature | Status | Source of the claim |
|---|---|---|
| Zero Retention Mode | **Design / Enterprise tier**, not active on the Creator plan | `docs/pl/audyt_agenta_2026-08.md` section 3 |
| Conversation history redaction (PII in transcripts stored by the platform) | **Design / Enterprise tier** | same |
| EU data residency (Frankfurt) | **Design / Enterprise tier** | `docs/architecture.md` (relabelled) |
| Data processing agreement signed with the platform | **Platform (verify)** | not evidenced in this repo |
| SIP UUI guest context on telephony | **Design (not implemented)** | `docs/telephony.md` |

## 7. Retention pointer

Retention periods per data class are in [retention.md](retention.md). This record does not repeat them.

## 8. Security measures (summary)

| Measure | Status |
|---|---|
| Webhook authentication with a shared secret (`X-Webhook-Secret`) | In repo (`mock_backend/routers/security.py`); **fails open when the secret is empty** (returns without checking; known gap, demo and test mode) |
| Inbound HMAC check (`X-Anna-Signature` with `X-Anna-Timestamp`) | In repo (`mock_backend/routers/security.py`, when those headers are sent) |
| Outbound signed events (HMAC-SHA256 with timestamp) | Reference receiver and tests in repo (`integrations/n8n/`); the backend emitter status is in `integrations/n8n/README.md` |
| Log masking (phone numbers, no names in JSON logs) | In repo |
| Transcript redaction for evaluation | In repo |
| Access control to the platform console | `[CONFIRM]` |
| Encryption in transit | Platform and tunnel (HTTPS); `[CONFIRM]` for production hosts |
| Encryption at rest of stored bookings | Not applicable: bookings are in memory in the PoC |

## 9. Review

| Date | Reviewer (role) | Change |
|---|---|---|
| `[CONFIRM]` | controller | first approval |
