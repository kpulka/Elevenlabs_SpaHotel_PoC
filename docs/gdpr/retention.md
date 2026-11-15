# Retention matrix per data class (PoC)

> **Not legal advice. Working draft.** Periods marked *proposal* are engineering suggestions for the controller to accept, change or reject. Periods marked *platform* depend on settings and contracts that this repository cannot read. `[CONFIRM]` = decision pending. See [README.md](README.md) for status labels.

## Principles

1. **Shortest period that serves the purpose.** A booking is kept as long as the treatment is relevant plus the period the business needs for its records. Conversation content is kept for the shortest time the platform allows.
2. **Health data gets the strictest rule.** Health flags and reasons are not copied into logs, alerts or analytics.
3. **Deletion is a step with an owner**, not a hope. Each row names how deletion happens.
4. **Repository content holds no personal data.** Test data uses fictional names and masked numbers.

## Matrix

| # | Data class | Where it lives | Purpose | Retention in the PoC today | Retention proposal | Deletion mechanism | Status |
|---|---|---|---|---|---|---|---|
| R-01 | Live audio | platform, during the session | conversation | not stored by this repo | end of session | platform | **Platform (verify)** |
| R-02 | Transcript of a conversation | platform storage | record of the conversation, quality checks | platform default `[CONFIRM]` | shortest setting the platform allows; zero retention only on higher plans | platform setting or API `[CONFIRM]` | **Platform (verify)**; zero retention is **Design / Enterprise tier** |
| R-03 | Booking record (slot, name, service, time, confirmation number) | backend process memory | booking | until process restart (`db_path` default `:memory:`, `mock_backend/config.py`) | as long as the appointment plus the business record period `[CONFIRM]` | restart clears memory; persistent store not yet built | **In repo** (memory); persistence **Design (not implemented)** |
| R-04 | Cancellation reason (free text) | backend memory; **console demo log** (`mock_backend/responses/cancel.py`) | fee decision and audit | printed to stdout while `ANNA_DEMO_LOGS` is on (default on) | do not store free text; keep only the category, or none | fix the demo log; no store | **In repo: known gap** |
| R-05 | Handoff alert (department, reason, guest name) | backend memory; Telegram chat (`mock_backend/telegram.py`) | ask staff to call back | Telegram history, no deletion by the app | flag and department only; delete chat history after 30 days (*proposal*) | manual chat cleanup or bot policy; to be automated | **In repo: known gap** (full name in text) |
| R-06 | SMS summary content | backend log line; Telegram relay when configured; no SMS provider | confirmation to guest or relative | same as R-05 | no health content in the text; 30 days in chat (*proposal*) | as R-05 | **In repo: simulated** |
| R-07 | Backend structured logs (JSON) | stdout, shipped by the host | diagnose faults | depends on the host and log shipper | 30 days (*proposal*) | log shipper policy | **In repo** for content (masked phone, no names); host retention **[CONFIRM]** |
| R-08 | Demo console output | terminal | live demonstrations | until the terminal closes | off outside demos | `ANNA_DEMO_LOGS=0` | **In repo** (switch exists) |
| R-09 | Evaluation transcripts | `evals/transcripts/` on the developer machine | scenario evaluation | redacted before saving (`mock_backend/tunnel/transcripts.py`); not committed (`.gitignore` line 91) | delete after the evaluation review, or within 30 days (*proposal*) | manual delete | **In repo** (redaction and ignore rule) |
| R-10 | Repository content (fixtures, docs, tests) | git history | tests and documentation | fictional names only | no personal data ever committed | review before commit | **In repo** as a rule; history rewrite is a separate decision (`_private/`) |
| R-11 | n8n executions (if the example workflow is deployed) | n8n database | record of event handling | n8n pruning setting `[CONFIRM]` | 7 days (*proposal*) | n8n execution pruning | **Design** (example only, not deployed) |
| R-12 | Web server and hosting logs (IP addresses) | hosting platform | operations and security | vendor default `[CONFIRM]` | vendor default unless the controller sets less | hosting settings | **Platform (verify)** |
| R-13 | Web analytics | analytics vendor | usage measurement | vendor default `[CONFIRM]` | only with consent `[COUNSEL]` | vendor settings | **Platform (verify)** |
| R-14 | Widget browser identifier (`elevenlabs_convai_user_id` in local storage) | guest's browser | anonymous session identity in the widget | until the guest clears browser data | none beyond the browser | guest clears browser data | **In repo** (widget file observed); purpose and basis `[COUNSEL]` |
| R-15 | Signed session tokens | in transit between the browser and the platform | open a voice session | short-lived (15 minutes, per `docs/architecture.md`) | none stored | expiry | **Design** claim: verify the token TTL in the route handler |

## Deletion requests

| Request | Affected rows | Steps |
|---|---|---|
| Delete booking | R-03, R-05, R-06 (chat), R-07 (logs by reference only) | delete or cancel the booking; remove chat messages that name the guest; logs are not edited |
| Delete transcript | R-02 | delete through the platform console or API `[CONFIRM]`; record the date in the request file |
| Delete evaluation data | R-09 | delete the local files; no sync to other devices |

## Review cadence

Review this matrix before any live use, after any change to the platform plan, and at least once a year. Record the review in the RoPA review table.
