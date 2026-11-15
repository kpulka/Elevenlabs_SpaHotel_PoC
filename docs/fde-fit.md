# Forward Deployed Engineer work: where it is in this repository

This document maps the work a Forward Deployed Engineer does on a voice-agent project to the artifacts in this
repository. Each row has a status, and the statuses are meant to be checked, not admired:

- **Implemented**: the artifact exists, runs, and is covered by an offline check or a test.
- **Partial**: something exists, but a part of the responsibility is missing or not proven.
- **Design only**: written down as a design or a config; not running in the repository.
- **Not implemented**: no artifact yet.

Paths are relative to the repository root. The status column was checked against the files at the time of writing.

| What the work involves | Where it is in the repository | Status |
|---|---|---|
| Capture requirements and turn them into a plan | `agent/_template/` (starter for a new agent: brief, prompt, KB outline, scenarios); `docs/discovery/dental_clinic_brief.md` (a filled-in brief for a fictional client) | Implemented for a fictional client (the brief is an exercise, not a real engagement) |
| Second client, from the same template | `agent/verticals/dental_clinic/`: client file, prompt, KB outline, 15 scenario definitions, tool schema example. No knowledge-base files yet, nothing uploaded, nothing run | Partial |
| Prompt, procedures and workflow for the agent | `agent/system_prompt_v3.md`, `agent/procedures/` (7 published procedures), `agent/workflow/`, `agent/config/anna_v3.json` | Implemented |
| Guardrails and known failure modes | Prompt rules for handoff and medical topics; tests for business rules (cancellation fee, unknown reservation, past dates); injection and ambiguity scenarios in `mock_backend/tunnel/scenarios.py`. An emergency-escalation scenario is not in the repository yet | Partial |
| Tool-calling contract between agent and backend | `mock_backend/schemas.py`, `mock_backend/tunnel/tool_schemas.py`, `mock_backend/tests/openapi.snapshot.json` with its contract test | Implemented |
| Webhooks and authentication | `mock_backend/routers/security.py` (shared secret; HMAC with timestamp per request); `ANNA_ENV=prod` refuses to start without a secret; tests in `mock_backend/tests/test_auth.py` | Implemented |
| Outbound events to CRM, calendar or automation tools | `mock_backend/events.py` (HMAC-signed events); `integrations/n8n/` (receiver verified offline; the workflow JSON is not run in a live n8n) | Partial |
| Persistence and SQL | `mock_backend/sqlite_store.py` behind `ANNA_DB_PATH`: schema versions with rollback on a failed migration, a unique index that stops a second booking of one slot, bookings and idempotency keys that survive a restart. Tests in `mock_backend/tests/test_sqlite_store.py` and `test_concurrency.py` | Implemented |
| Workflow thinking: state of a booking and its transitions | `docs/flows/` (cancellation and reschedule diagrams, derived from the procedures and `services/spa.py`); transitions tested offline in `mock_backend/tests/test_flow_transitions.py` | Implemented (two procedures; the other five are not diagrammed) |
| Idempotency for bookings | Idempotency key on booking calls; tests in `mock_backend/tests/test_idempotency.py` | Implemented |
| Observability and debugging in production | `mock_backend/logs.py` (JSON logs with request IDs and, when the tool call sends one, conversation IDs), `mock_backend/metrics.py` and `/metrics`, `mock_backend/tests/test_observability.py` | Implemented |
| Deployment and cloud | `mock_backend/Dockerfile` (built and health-checked in CI); `mock_backend/compose.yaml` and `mock_backend/fly.toml` (config, not deployed); the playbook section 9 | Design only (image built in CI; no managed deployment) |
| Telephony and voice channel | None in the code: the agent runs on the web widget (`phone_numbers` is empty). The status, options and a design-only sequence diagram are in `docs/telephony.md`; the SIP design is also in `docs/architecture.md` | Design only (no phone number, no call evidence) |
| Evaluation of agent behaviour | `evals/README.md`; scenarios and the offline sequence check in `mock_backend/tunnel/`; `run_simulations.py` runs live simulations on demand (costs credits). `evals/rag/` holds 48 knowledge-base questions with an offline ground-truth check (it does not measure retrieval quality yet). No live results or transcripts are published in the repository | Partial |
| Grounding and knowledge base | `agent/knowledge_base/` (source) and `agent/knowledge_base_txt/` (uploaded copy); parity check in `scripts/check_kb_parity.py` run in CI | Partial (parity checked; a prompt-to-KB grounding lint is not in place yet) |
| Privacy and health-adjacent data | `docs/gdpr/` (record of processing, DPIA-lite, retention matrix: drafts, not legal advice); principles in the playbook section 4; the agent prompt stores a flag, not a diagnosis; the website has a demo privacy page (`frontend/app/polityka/`) and a consent notice before the voice session | Partial (drafts; retention periods, legal basis and DPO are marked "to be defined by the controller") |
| Product feedback to the platform vendor | `docs/PRODUCT_FEEDBACK.md`: PF-01 to PF-12, prioritised, each grounded in a fact documented in this repository | Implemented |
| Postmortems and incident write-ups | `docs/lessons-learned.md`: eight incidents, each pointing to the file that shows it | Implemented |
| Reusable templates and playbooks | `agent/_template/`, `docs/deployment-playbook.md` (phases, go-live checklist, runbook, PaaS section) | Implemented (see the second-client row for the drafted second vertical) |
| Website and widget for the client | `frontend/`: Next.js PL/EN site, self-hosted voice widget, signed-URL proxy, request guard and rate limit, tests | Implemented |
| Business case and ROI | `docs/business-case.md`: scope boundary ("never automate" list), KPIs, economics with every assumption labelled | Implemented |
| Security practice for the repository | `SECURITY.md`; CI jobs for gitleaks (full history), CodeQL (Python, JavaScript/TypeScript), dependency audit (advisory); Dependabot | Implemented |
| Bilingual delivery (PL and EN) | Documentation: English first, Polish originals in `docs/pl/`; site and widget in PL and EN. The agent prompt is written in Polish and carries a rule to answer in the caller's language; three English scenarios exist in `mock_backend/tunnel/scenarios.py` but have not been run live | Partial |
| Continuous quality gates | `.github/workflows/ci.yml`: backend tests with a coverage threshold, ruff, mypy, repository gates, container health check, frontend typecheck, lint, tests and build, and an optional Playwright job | Implemented |

## What this document does not claim

- Telephony is not connected. No phone number is attached to the agent, and no call has been transferred to a human.
- Nothing is deployed to a managed platform. The live demo runs from a laptop behind a quick tunnel.
- The n8n workflow has not been executed in a live n8n instance.
- The repository does not contain published results of live evaluation runs.
- No real guest data has been processed. The hotel, the prices, the staff and the photographs are fictional.
