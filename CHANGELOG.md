# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) for its releases.

## [Unreleased]

No version is tagged for these changes. They are on the `fde-readiness` branch and will be released after review.

### Security

- Webhook authentication on the seven tool endpoints: the `X-Webhook-Secret` header is compared in constant time.
  An optional per-request HMAC-SHA256 signature with a timestamp (300-second replay window) is accepted as well.
  Authentication is off only when `ANNA_WEBHOOK_SECRET` is empty (demo mode; the backend logs a warning at start).
- `ANNA_ENV=prod` makes the backend refuse to start without the webhook secret, and without a signing secret when
  outbound events are configured.
- The tunnel start scripts refuse to open a public tunnel while the secret is empty. Container configuration is
  passed with `--env-file` instead of `-e KEY=VALUE`, so values do not appear in the process list.
- Frontend: origin check and a per-process rate limit on the signed-URL route.
- CI: gitleaks over the full history, CodeQL for Python and JavaScript/TypeScript, Dependabot for pip, npm and
  GitHub Actions, and an advisory dependency audit.

### Added

- Observability: request IDs, JSON logs (`ANNA_LOG_FORMAT=json`) with a conversation ID taken from the
  `X-Conversation-Id` header or the `conversation_id` query parameter, and a `/metrics` endpoint.
- Idempotency keys for bookings: a retried request returns the existing booking.
- SQLite store behind `ANNA_DB_PATH`, with a schema-version table.
- Signed outbound integration events and an n8n receiver example in `integrations/n8n/`, verified offline. The n8n
  workflow has not been run in a live n8n instance.
- Agent evaluation: scenario definitions, an offline sequence check and the simulation runner in `mock_backend/tunnel/`,
  plus the `agent/_template` starter for a new agent.
- Repository gates in CI: knowledge-base parity (`scripts/check_kb_parity.py`) and, when the scripts are present,
  the prompt-versus-knowledge-base lint and the tool-contract check.
- Frontend: a structured logger, environment validation, unit tests for the request guard, the rate limiter and the
  contact form, and a Playwright job that runs when the Playwright configuration exists.
- Booking flows: state diagrams for cancellation and rescheduling in `docs/flows/`, with each transition tested offline.
- A fictional second client, built from `agent/_template`: a discovery brief (`docs/discovery/`) and a dental-clinic
  vertical draft in `agent/verticals/dental_clinic/` (outline, prompt, scenario definitions). It is not uploaded and not run.
- Deployment: `mock_backend/compose.yaml` (local run with a persistent volume) and `mock_backend/fly.toml`
  (configuration only, not deployed). The playbook has a section on managed-platform deployment.
- Documentation: `SECURITY.md`, `CONTRIBUTING.md`, the pull request template, `docs/repo-guide.md` and
  `docs/fde-fit.md` (responsibilities mapped to artifacts, with statuses).

### Changed

- Python 3.12 everywhere: CI, the backend image and the documentation.
- The backend image moved from `mock_backend/tunnel/Dockerfile` to `mock_backend/Dockerfile`. The build context is
  `mock_backend/`, and `.dockerignore` and `.containerignore` exclude tests, the tunnel directory and secrets.
- Tunnel scripts use `set -euo pipefail`, and their shared logic lives in `mock_backend/tunnel/_common.sh`.
- CI is split into jobs (backend with a coverage threshold, lint, types, repository gates, container health check,
  frontend, end-to-end, advisory audit, secret scan). Actions are pinned by major version tag.
- Presentation: the enterprise-tier features (Zero Retention Mode, PII redaction, EU data residency with a DPA, SIP UUI,
  multi-hotel scaling) are labelled as design for the Enterprise plan. The live agent runs on the Creator plan. Both
  PPTX files are regenerated from `content_*.json`, and the landing page links to release v1.0.1.
- The README is shorter. The repository map, quality gates and known limitations moved to `docs/repo-guide.md`.
- `NOTICE.md` and the documentation use neutral wording: the project is described as a portfolio case study.
- The test count is no longer hard-coded in the documentation; see CI for the current number.

### Fixed

- The landing page linked to the superseded release v1.0.0.
- Python was stated as 3.11+, 3.12+ and 3.13 in different places; it is now 3.12 everywhere.
- The incident count in the documentation is eight, matching `docs/lessons-learned.md`.
- `.gitignore` covers SQLite files, coverage output, Playwright reports and `frontend/tsconfig.tsbuildinfo`.

## [1.0.1] - 2026-11-10

### Fixed

- Corrected case-study decks (PPTX and HTML) with the arithmetic aligned across the deck, the business case and
  the generator: $0.08 per minute, $22 / 275 min and $299 / 3,738 min.
- Fact audit of the public documentation.

### Notes

- Editable PPTX files are attached to this release. `v1.0.0` is superseded because its decks carry the
  pre-correction ROI figures.

## [1.0.0] - 2026-11-09

### Added

- Portfolio release: FastAPI mock PMS with business-rule tests, Next.js PL/EN site with the voice widget and a
  signed-URL proxy, CI (pytest, ruff, mypy, frontend typecheck/lint/tests/build), bilingual case-study deck.
