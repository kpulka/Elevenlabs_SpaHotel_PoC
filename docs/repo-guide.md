# Repository guide

This page holds what used to sit in the README: the repository map, the quality gates, and the known
limitations. Start with the [README](../README.md) for the overview and [docs/INDEX.md](INDEX.md) for which
document is canonical for which topic.

## Repository map

```
agent/              the agent as configured: system prompt v3, procedures, workflow graph, tool definitions,
                    knowledge base (.md source + .txt uploaded to ElevenLabs), config/, _template/ (starter
                    for a new agent), archive/ (superseded prompts)
evals/              scenario evaluation: how to run the simulations and what they check (README.md);
                    transcripts/ holds generated output only (ignored, except a placeholder)
integrations/n8n/   example receiver for the signed outbound events (design / example, not deployed)
mock_backend/       FastAPI mock PMS: routers/ (HTTP contract), services/ (business rules), store.py and
                    sqlite_store.py (state), schemas.py (request models), catalog.py (treatment catalogue),
                    logs.py and metrics.py (observability), events.py (signed outbound events),
                    tests/, tunnel/ (demo start scripts, webhook sync, simulation runner)
                    Dockerfile, compose.yaml and fly.toml (container, local compose, PaaS config not deployed)
frontend/           Next.js site (PL/EN), voice widget, signed-URL proxy, contact form (demo)
docs/               INDEX.md, the English documents, pl/ (Polish originals of the architecture and procedures)
presentation/       case-study deck (PL/EN): content_*.json (source), generate_deck.py, verify_deck.py,
                    HTML views, assets
scripts/            repository gates that run in CI (knowledge-base parity and other checks)
.github/            CI, CodeQL, Dependabot, pull request template
scripts/deploy_kb_and_tools.py   REST script that uploads the knowledge base and re-points the agent's tools
```

## Quality gates

Run from the repository root unless noted. The exact commands are in [CONTRIBUTING.md](../CONTRIBUTING.md).

| Gate | What it checks | Where |
|---|---|---|
| backend tests with coverage | contract, business rules, idempotency, auth, observability; coverage threshold | `ci.yml` job `backend` |
| ruff, mypy | lint and types of `mock_backend/` | jobs `lint`, `types` |
| repo gates | deck figures agree across artifacts, `docs/INDEX.md` matches `docs/`, knowledge-base parity, prompt-vs-KB lint and tool contract (when those scripts exist) | job `repo-gates` |
| container | the image builds, starts and answers `/health` | job `docker-build` |
| frontend | typecheck, ESLint, Vitest, PL/EN key parity, generated hotel data matches the backend, production build | job `frontend` |
| browser e2e | Playwright smoke test; runs only when `frontend/playwright.config.ts` exists | job `e2e` |
| dependency audit | `pip-audit` and `pnpm audit --prod`; advisory (does not fail the build) | job `audit` |
| secret scan | gitleaks over the full git history | job `gitleaks` |
| static analysis | CodeQL for Python and JavaScript/TypeScript, on pull requests and weekly | `codeql.yml` |

GitHub Actions are pinned by major version tag, not by commit SHA. Dependabot proposes updates weekly.

## Known limitations

Read these before judging the demo.

- **Telephony is not implemented.** The agent runs through the web widget only (`phone_numbers` is empty). The
  handoff is simulated by `transfer_to_simulated_handoff`, which logs the handoff and sends an alert; no call is
  transferred. The telephony design is described in the architecture document, not built.
- **The public demo runs on a laptop.** It is served through a Cloudflare quick tunnel whose URL changes on every
  start; the start scripts re-point the agent's tools to the new URL. A Fly.io configuration exists in
  `mock_backend/fly.toml`, but nothing has been deployed from it.
- **State is in memory by default.** Without `ANNA_DB_PATH` a restart resets bookings and slots. With
  `ANNA_DB_PATH` set, bookings are stored in SQLite. The backend is designed for one worker process.
- **Webhook authentication is a shared secret by default.** The agent's tool calls send `X-Webhook-Secret`;
  per-request HMAC signatures with a timestamp are supported as an opt-in. When `ANNA_WEBHOOK_SECRET` is empty,
  authentication is off (demo mode). The secret must also be configured on the tools in the ElevenLabs workspace.
- **The knowledge base is a snapshot.** Prices and policies live in the Markdown source and in the text files
  uploaded to ElevenLabs. Re-uploading is a manual step; the API does not update a document's content in place.
- **Live evaluation transcripts are not in the repository.** The scenario suite and its offline checks run in CI.
  Live simulation runs cost ElevenLabs credits and are run on demand; `evals/transcripts/` holds only a placeholder.
- **The contact form is a demo.** It validates input and shows a confirmation; it sends no e-mail.
- **Rate limiting is per process.** The signed-URL route uses an in-memory limiter, and it takes the client
  address from `X-Forwarded-For`. That is only meaningful behind a proxy that sets the header; a shared store
  is needed before running several instances.
- **Language is handled on the client.** PL/EN lives in a context plus `localStorage`, not in `[lang]` routes, so
  there is one set of URLs and no `hreflang`. The decision and the conditions for changing it are in
  [adr-language-routing.md](adr-language-routing.md).
- **Fictional data only.** The hotel, prices, staff and photographs are invented (see [NOTICE.md](../NOTICE.md)).
  No guest data is processed.
