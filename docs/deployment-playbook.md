# Deployment Playbook

> How this PoC becomes a production rollout at a hotel client: phases, exit gates, go-live checklist,
> security and operations. Numbers come from [business-case.md](business-case.md); the incidents behind
> the runbook are written up in [lessons-learned.md](lessons-learned.md).

## 1. Delivery phases and exit gates

| Phase | Goal | Key activities | Exit gate |
|---|---|---|---|
| **0. Discovery** (1–2 wks) | Understand reality | Call-log analysis, listening at the desk, PMS/PBX inventory, risk workshop | Agreed scope, baseline KPIs, a written list of "never automate" topics |
| **1. Design** (1 wk) | Conversation and safety design | Personas, conversation flows, escalation matrix, KB curated with the SPA/medical lead | Signed-off KB and escalation rules |
| **2. Build** (2 wks) | Working agent and integrations | Prompt, workflow, procedures, tool adapters to the real PMS, SMS, telemetry | Scripted scenario suite passes in staging |
| **3. Shadow / internal pilot** (2 wks) | Prove safety offline | Staff call the agent; transcripts reviewed daily; no real guests | Zero critical findings for 5 consecutive days |
| **4. Limited live pilot** (4 wks) | Real guests, small scope | Web widget + one number, SPA topics only, handoff always on | Safety KPIs hold; containment and conversion trend towards targets |
| **5. Scale** | All inbound topics and channels | Rooms, restaurant, after-hours routing, more languages | Steering-committee review |
| **6. Operate** | Continuous improvement | Weekly transcript review, KB change process, quarterly red-team | Ongoing |

The engineering equivalent of this phase model is what this repository already does at PoC scale:
the work was cut into phases with written briefs, each phase ends with a full gate (backend tests, type-check,
i18n parity, generated-data check, production build) and CI must be green on `main`.

## 2. Go-live checklist

**Agent**
- [ ] System prompt and knowledge base reviewed by the SPA/medical lead and the general manager
- [ ] Every "never automate" topic has a tested escalation path
- [ ] Scenario suite passes: happy paths, edge cases, adversarial prompts, language switch, noisy audio
- [ ] Fallback message and human handoff verified end-to-end, including out-of-hours behaviour

**Integration**
- [ ] Stable HTTPS endpoint; every webhook authenticated (shared secret or mTLS)
- [ ] Idempotency on booking calls; timeouts and retry policy agreed
- [ ] PMS sandbox tested with realistic data; rate limits understood
- [ ] Alerting on tool error rate and latency

**Security and compliance** — see section 4.

**Operations**
- [ ] Named owner for KB updates, prompt changes and incident response
- [ ] Rollback: the previous agent version/branch can be re-activated in minutes
- [ ] Outage runbook available (section 5)

## 3. Production target architecture

| Concern | This PoC | Production |
|---|---|---|
| Channel | Web widget; telephony-ready but not wired to a trunk | Hotel PBX / SIP trunk with `transfer_to_number` to the desk |
| Webhook hosting | Local laptop behind a Cloudflare quick tunnel | Containerised service on a managed platform, fixed domain, WAF, autoscaling |
| Webhook authentication | Shared secret in the `X-Webhook-Secret` header on the seven tool endpoints; HMAC-SHA256 with a timestamp (300 s window) available per request; **off when `ANNA_WEBHOOK_SECRET` is empty** (demo mode) | HMAC required for every call, or mTLS; IP allow-list; secret rotation |
| PMS | FastAPI mock implementing the booking contract | One adapter per PMS (Opera Cloud, Mews, Protel, …) behind the same HTTP contract |
| Secrets | Local `.env` files, never committed (`--env-file` for the container) | Secret manager, rotating keys, least-privilege API keys per environment |
| Environments | One | dev / staging / prod, using ElevenLabs agent **branches** and versions per environment |
| Observability | Console log plus Telegram alerts | Structured logs, per-conversation tracing, dashboards, alerting |
| Evaluation | Manual runs and the simulation runbook | Automated simulated-conversation tests in CI on every prompt or KB change |

## 4. Security, privacy and compliance

- **Data minimisation** — the agent collects only what a booking needs: name, treatment, date, phone. No
  health details enter tool payloads; clinical topics are escalated, not recorded.
- **Region and retention** — EU data residency; transcript and audio retention set to the shortest period
  that still supports quality review; zero-retention considered for sensitive deployments (plan-dependent).
- **Legal basis and transparency** — the guest is told at the start that they are talking to an AI
  assistant; processing documented under GDPR (controller/processor roles, DPA with the platform,
  sub-processors listed).
- **Access control** — API keys stay server-side. This repository issues **signed URLs** from a Next.js API
  route so the key never reaches the browser (`frontend/app/api/anna/signed-url`).
- **Prompt injection and abuse** — tools accept only schema-validated parameters, and the backend enforces
  business rules independently of the model: the LLM is never trusted for authorisation or pricing.
- **Auditability** — every request gets a request ID. A conversation ID is read from the `X-Conversation-Id` header or the `conversation_id` query parameter, and both are written to the JSON logs. The tool configuration has to send one of them for a tool call to be traced to its conversation; wiring that into the ElevenLabs tools is an open item.
- **Red-teaming** — before go-live and quarterly: jailbreak attempts, medical-advice baiting,
  price manipulation, PII fishing.

## 4a. Operational prerequisite: the webhook secret must reach the agent

With `ANNA_WEBHOOK_SECRET` set, every tool call from the agent must carry the same value in the
`X-Webhook-Secret` request header. Configure it on each of the seven tools in the ElevenLabs workspace before
enabling the secret; otherwise the calls are rejected with `401` and the procedures fail. The tunnel start scripts
refuse to open a public tunnel while the secret is empty, so an unauthenticated public endpoint is not started by
accident.

## 5. Failure modes and runbook

| Symptom | Likely cause | First check | Guest-facing behaviour |
|---|---|---|---|
| All tools fail | Webhook endpoint down, tunnel URL changed, port conflict (`8000` is taken on the demo host — the backend runs on `8011`) | `/health`, DNS, tunnel status | The agent says it cannot reach the system and offers a handoff; it retries once first |
| One tool fails | Upstream PMS error, or a tool schema drifted from the backend | Tool error log, recent deploys | Same, for that capability only |
| Widget button does nothing | Widget script blocked or not yet loaded (it used to come from a public CDN; now it is self-hosted) | Browser console, network tab | Phone number offered as fallback |
| Agent answers outside scope | Knowledge-base gap or prompt regression | Transcript review, scenario suite | Fix KB or prompt, add a regression scenario |
| Sentiment drops on slow turns | Provider latency, or a slow PMS call | Per-turn latency breakdown | Consider a faster model for tool-light turns |

**Before spending credits, verify the plumbing.** The simulation runbook performs a webhook health
preflight: it resolves all seven tools of the agent and probes `/health` on each host, so a dead tunnel
fails fast with a clear message instead of producing three failed conversations:

```bash
python mock_backend/tunnel/run_simulations.py --check     # credits, backend, webhook hosts, agent branch
```

## 6. Cost model (production)

Cost per call ≈ (agent minutes × platform rate) + telephony minutes + hosting + SMS. With the plans current
at the time of writing this is **≈ $0.08 per platform minute**, and 1,000 three-minute calls per month fit
inside the $299 Scale plan. Control levers: concise prompts (fewer tokens per turn), splitting the
knowledge base between in-context and RAG, shorter greetings, model choice per use case, a hard maximum call
duration. Track **cost per resolved call**, not cost per minute — a cheap call that ends in a handoff is not
cheap.

## 7. Governance

- **Change control** — prompt, knowledge base and workflow changes go through a pull request, run the
  scenario suite, and are promoted dev → staging → prod.
- **Review cadence** — weekly transcript sampling (safety and quality), monthly KPI review with the steering
  group, quarterly red-team.
- **Ownership** — business owner (GM), content owner (SPA/medical lead), technical owner (IT), data
  protection owner (DPO).

## 8. Roadmap beyond the pilot

1. Telephony go-live with SIP transfer and call-queue context
2. Real PMS adapter and SMS gateway replacing the mock
3. Automated evaluation harness with nightly regression runs
4. Outbound use cases: appointment reminders, no-show recovery (with consent)
5. Multi-property rollout: one core agent, per-hotel knowledge base and variables

## 9. Deploy to a managed PaaS

> **Status: config provided, not deployed.** Nothing in this repository deploys to a cloud platform, and the
> files below have not been run against a live account. They describe how the backend would run on a managed
> platform instead of a laptop behind a quick tunnel.

What is in the repository:

- `mock_backend/Dockerfile`: the image (Python 3.12 slim, non-root user, `/health` health check, `/var/lib/anna`
  for the SQLite file).
- `mock_backend/fly.toml`: Fly.io app configuration. One machine, a `/health` check every 30 s, a volume mounted at
  `/var/lib/anna`, `ANNA_DB_PATH` inside that volume, and `auto_stop_machines = "off"`. Secrets are set with
  `fly secrets`, not in the file.
- `mock_backend/compose.yaml`: the same image run locally with a named volume, for a rehearsal before a platform
  deployment.

Steps a deployment would take (not run):

1. Create the app and a one-gigabyte volume; set `ANNA_WEBHOOK_SECRET` as a secret (and the optional Telegram variables).
2. Deploy, then check `/health` and `/docs` on the platform host.
3. Point the seven agent tools at the fixed HTTPS host with `mock_backend/tunnel/sync_agent_tools.py --base-url https://<host>`.
   The quick tunnel is then no longer needed.
4. Confirm that every tool sends the `X-Webhook-Secret` header (section 4a).
5. Run the preflight before spending credits: `python mock_backend/tunnel/run_simulations.py --check`.

Exit criteria before a go-live decision:

- A fixed domain with a valid TLS certificate, and `CORS_ORIGINS` set to the website origin instead of `*`.
- The volume backup has been restored once in a test.
- `/metrics` and the logs are reachable only by the operator.
- The previous image tag is known, so a rollback is one deploy away.

Known limits of this configuration: one machine only (the SQLite file is local to one volume, and there is no
cross-machine locking), a shared-secret webhook scheme (section 3), and no managed database.
