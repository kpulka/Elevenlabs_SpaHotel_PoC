# Product feedback: voice-agent platform (from this project)

> **Scope and evidence.** Every item below is grounded in facts written in this repository: `docs/lessons-learned.md`, `docs/pl/audyt_agenta_2026-08.md` (historical audit plus the 2026-11 addendum), `agent/procedures/`, `scripts/deploy_kb_and_tools.py`, `mock_backend/tunnel/run_simulations.py`, and `frontend/public/widget/`. Where the repo records a behaviour but not a root cause, the item says so. Where a question is open, it is listed as a question, not a claim. Nothing here was re-run for this document; repro steps are the ones recorded in the sources.

## Priority scale

| Priority | Meaning |
|---|---|
| **P0** | Silent wrong behaviour in production or a core flow with no error signal |
| **P1** | Significant impact on a regulated or safety-relevant flow, or a recurring operations cost. A workaround exists but is manual. |
| **P2** | Friction or quality improvement. Impact is limited. |

## Summary

| ID | Problem (short) | Priority |
|---|---|---|
| PF-01 | KB update returns `200` and ignores the uploaded content | P0 |
| PF-02 | Procedures: publish and version IDs are not documented | P1 |
| PF-03 | Compile returns `400 Invalid JSON content` for deterministic procedures | P1 |
| PF-04 | Hosted prompt can differ from the file; no read-back or diff | P1 |
| PF-05 | Escalation tool needs telephony; no escalation path for a web-only agent | P1 |
| PF-06 | Prompt can name tools that are not configured; nothing flags it | P1 |
| PF-07 | Webhook URL is repeated in every tool; tunnel restarts break tools one by one | P1 |
| PF-08 | Redaction, zero retention and residency are plan-gated and not visible per plan | P1 |
| PF-09 | Open question: what identifiers the tool-call payload carries | P1 |
| PF-10 | Widget script on a public CDN is on the critical path | P2 |
| PF-11 | Default session length is short for slow speakers | P2 |
| PF-12 | Simulation runs have no cost estimate before they start | P2 |

## Detail

| ID | Problem | Impact | Repro steps | Workaround used here | Proposed fix | Priority |
|---|---|---|---|---|---|---|
| PF-01 | `PATCH /v1/convai/knowledge-base/{id}` accepts a multipart upload, returns `200`, and ignores `content`. The agent keeps the old text. (lessons 7) | Wrong business information with a success signal. Found only by reading an answer. | 1. Change a KB document locally. 2. `PATCH` the document with the new file. 3. Receive `200`. 4. Ask the agent the changed question. 5. Old answer. | Create a new document, re-point the agent, delete the old one. Read-back check planned (see `docs/postmortems/2026-kb-update-200-ok-changed-nothing.md`). | Apply the content, or return `4xx` with "content not supported; use POST". Return the stored content hash in the response. | **P0** |
| PF-02 | Procedures: the 2026-08 audit found that attaching a procedure needs a `version_id`, that drafts have `version_id = None`, and that the OpenAPI has no publish endpoint. The 2026-11 addendum lists seven published procedures, but the repo does not record which call published them. | Procedures cannot be versioned as code. The repo cannot show how the live state was produced. | 1. `POST` a procedure (draft, `has_draft=true`). 2. `PATCH` the agent's `procedures` with `{id: {procedure_id, version_id}}`. 3. `version_id` is `None` for the draft. 4. No publish call in the OpenAPI (audit section 6, 2026-08). | Seven IDs are kept in `agent/procedures/procedure_ids.json`. Policy text lives in `procedures_7.md` and is also in the prompt. | Document the publish flow and version IDs in the API reference. Return a version ID from create. | P1 |
| PF-03 | Compile of a `deterministic` procedure returns `400 Invalid JSON content` without a field pointer. | The deterministic type could not be used, so the escalation decision procedure was dropped. | 1. Create a `deterministic` procedure. 2. Call compile. 3. `400 Invalid JSON content` (audit section 6, 2026-08). | Use `free_form` only. | Name the field and the rule that failed. Publish the JSON schema for `content`. | P1 |
| PF-04 | The hosted prompt can hold a different version from the repository file. The 2026-11 audit addendum records a length difference. There is no documented way to read back and diff the live prompt. | A reviewed prompt may not be the deployed one. | 1. `GET /v1/convai/agents/{id}`. 2. Compare the prompt text with `agent/system_prompt_v3.md`. 3. Lengths differ (audit section 7). | Manual comparison. A `diff` command is **design only**, not implemented. | Versioned prompts with an ID and content hash. A dry-run diff endpoint. | P1 |
| PF-05 | The built-in transfer tool (`transfer_to_number`) needs telephony. The web-widget agent has no phone number (`phone_numbers: []`), so there is no executable escalation. | A safety rule ("hand over to a human") could not be executed. The prompt had to be rewritten. (lessons 2; audit sections 2 and 5) | 1. Agent on the web widget only. 2. Prompt instructs escalation. 3. No escalation tool can run. | Simulated handoff webhook that logs and alerts. The caller is told it is a request, not a call. | A web-channel escalation primitive (notify an operator, open a ticket) with the same status and logs as a transfer. | P1 |
| PF-06 | A prompt named `transfer_to_human` in eight places. No tool of that name existed, and nothing flagged the mismatch. (lessons 2; audit section 2) | The agent could not follow the rule and produced no error. | 1. Prompt names a tool. 2. Agent configuration has no tool with that name. 3. No warning on save. | Audit as a release step. This repo's dental vertical has a test that checks the prompt only names configured tools (`mock_backend/tests/test_render_vertical.py`). | A lint on save: tool names in the prompt must exist in the agent's tool list. Show unresolved names. | P1 |
| PF-07 | Each tool stores the full webhook URL. A quick tunnel gets a new hostname on each start, so tools break one by one. One old script knew only five of seven tools. (lessons 4; audit section 2) | Partial outage mid-call. Hard to see which tool is stale. | 1. Restart a quick tunnel. 2. New hostname. 3. Tools still point to the old host. 4. Calls fail on some tools. | `sync_agent_tools.py` rewrites every tool by name, with a `--check` preflight. | One base URL per agent (or per environment) that all tools inherit. A per-tool health view. | P1 |
| PF-08 | Zero retention mode, conversation redaction and EU residency are not available on the Creator plan. The agent runs on that plan. Monitoring was disabled. (audit section 3) | Regulated use cases (health data) need these controls. The plan gate is not visible from the agent configuration. | 1. Creator plan agent. 2. Look for redaction or zero retention settings. 3. Not available (audit section 3). | Data minimisation in the prompt (flags, not diagnoses). Local transcript redaction in the evaluation tools (`mock_backend/tunnel/transcripts.py`). Documented as design in `docs/architecture.md`. | Show a feature matrix per plan in the console and the API. Offer retention settings on lower tiers, or document the plan gate in the API reference. | P1 |
| PF-09 | **Open question.** Does the tool-call payload include a conversation identifier and a timestamp? The repo's backend log format has a `conversation_id` field, but the repo does not show what the platform sends. | Without a shared identifier, the team cannot follow one conversation from the platform into backend logs. | Not reproducible from this repo. The backend does not read a conversation id from the payload yet. | None yet. The log field exists; population is planned. | Document the tool-call payload fields, including any conversation and call identifiers. | P1 |
| PF-10 | The web widget defines its element only after a script from a public CDN loads. When the CDN is blocked, nothing is clickable. (lessons 3) | The voice feature disappears on locked-down networks, with no error for the user. | 1. Block the CDN. 2. Load the page. 3. No widget element is defined. | The script is self-hosted at `/widget/convai-widget-embed.js`. | A versioned npm package with subresource-integrity hashes, and an error event for failed loads. | P2 |
| PF-11 | The default maximum session length is 300 s. For callers aged 60+ with slow speech, this is short. The audit recommended 600–900 s, and the addendum records 900 s. (audit sections 2, 3 and 7) | Calls end mid-task. | 1. Slow-speaking caller. 2. Booking takes more than five minutes. 3. Session ends. | Raised to 900 s (addendum, 2026-11). | A higher default, or a warning before the limit. | P2 |
| PF-12 | Simulation runs can exhaust credits. The runner has a dedicated exit code for "credits exhausted" (3) and for timeouts (4). There is no cost estimate before a run. (`mock_backend/tunnel/run_simulations.py`) | Surprise cost, and a partial run can be mistaken for a complete one. | 1. Start a full scenario run. 2. Credits run out mid-run. 3. Exit code 3. | The runner reports the exit code. Budget tracking is not in the repo. | A cost estimate per simulation, and a run status that lists completed and skipped scenarios. | P2 |

## Requests that are not yet filed

- A changelog for platform API behaviour, with the date each endpoint's semantics changed. Several items above would have been caught by it.
- A sandbox agent with the same features as the production plan, for testing without spending credits.

## What works well (for balance)

- Webhook tools defined with JSON Schema work with a plain FastAPI backend (the mock backend in this repo, seven tools).
- The repo's offline scenario format and runner give a repeatable way to structure prompt tests. The gap is cost visibility before a live run (PF-12).
