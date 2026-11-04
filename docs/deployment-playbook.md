# Deployment Playbook

> How I would take this PoC to a production rollout at a hotel client: phases, gates, checklists, security and operations.

## 1. Delivery phases and exit gates

| Phase | Goal | Key activities | Exit gate |
|---|---|---|---|
| **0. Discovery** (1–2 wks) | Understand reality | Call-log analysis, listening sessions at the desk, PMS/PBX inventory, risk workshop ([question bank](discovery-questions.md)) | Agreed scope, baseline KPIs, list of "never automate" topics |
| **1. Design** (1 wk) | Conversation + safety design | Personas, conversation flows, escalation matrix, KB curation with SPA/medical lead ([UX](ux-design.md), [rationale](design-rationale.md)) | Signed-off KB and escalation rules |
| **2. Build** (2 wks) | Working agent + integrations | Prompt, workflow, procedures, tool adapters to the real PMS, SMS, telemetry | Scripted scenario suite passes in staging |
| **3. Shadow / internal pilot** (2 wks) | Prove safety offline | Staff call the agent; transcripts reviewed daily; no real guests | Zero critical findings for 5 consecutive days |
| **4. Limited live pilot** (4 wks) | Real guests, small scope | Web widget + one number, SPA topics only, handoff always on | Safety KPIs hold; containment and conversion trending to targets |
| **5. Scale** | All inbound topics and channels | Rooms, restaurant, after-hours routing, multi-language | Steering committee review |
| **6. Operate** | Continuous improvement | Weekly transcript review, KB change process, quarterly red-team | Ongoing |

## 2. Go-live checklist

**Agent**
- [ ] System prompt and KB reviewed by SPA/medical lead and general manager
- [ ] Every "never automate" topic has a tested escalation path
- [ ] Scenario suite (happy paths, edge cases, adversarial, language switch, noisy audio) passes
- [ ] Fallback message and human handoff verified end-to-end (including out-of-hours behaviour)

**Integration**
- [ ] Stable HTTPS endpoint, authentication on every webhook (shared secret / mTLS)
- [ ] Idempotency on booking calls; timeouts and retry policy agreed
- [ ] PMS sandbox tested with realistic data; rate limits understood
- [ ] Alerting on tool error rate and latency

**Security & compliance** – see section 4.

**Operations**
- [ ] Named owner for KB updates, prompt changes and incident response
- [ ] Rollback: previous agent version/branch can be re-activated in minutes
- [ ] Runbook for outage (see section 5)

## 3. Production target architecture

| Concern | PoC | Production |
|---|---|---|
| Channel | Web widget | + SIP trunk from hotel PBX/Twilio with `transfer_to_number` to the desk |
| Webhook hosting | Laptop behind quick tunnel | Containerised service on managed platform with fixed domain, WAF and autoscaling |
| Webhook auth | None | Signed requests (shared secret or mTLS), IP allow-list |
| PMS | FastAPI mock | Adapter per PMS (Mews, Opera Cloud, Protel, …) behind the same HTTP contract |
| Secrets | Local `.env` | Secret manager; rotating keys; least-privilege API keys |
| Environments | One | dev / staging / prod, agent **branches** and versions per environment |
| Observability | Console + Telegram | Structured logs, tracing per conversation id, dashboards, alerting |
| Evaluation | Manual scripts | Automated simulated-conversation tests in CI on every prompt/KB change |

## 4. Security, privacy and compliance

- **Data minimisation** – the agent collects only what a booking needs (name, treatment, date, phone). It does not store health details; clinical topics are escalated, not recorded in tool payloads.
- **Region and retention** – use EU data residency, configure transcript/audio retention to the shortest period that supports quality review; consider zero-retention for sensitive deployments (plan-dependent).
- **Legal basis and transparency** – disclose at the start that the guest is talking to an AI assistant; document processing under GDPR (controller/processor roles, DPA with the platform, sub-processors).
- **Access control** – API keys server-side only (this repo uses signed URLs so the key never reaches the browser); least-privilege keys; separate keys per environment.
- **Prompt-injection and abuse** – tools accept only validated, schema-checked parameters; the backend enforces business rules independently of the model (never trust the LLM for authorisation or pricing).
- **Auditability** – every booking carries the conversation id so any action can be traced to a transcript.
- **Red-teaming** – before go-live and quarterly: jailbreak attempts, medical-advice baiting, price-manipulation, PII fishing.

## 5. Failure modes and runbook

| Symptom | Likely cause | First check | Guest-facing behaviour |
|---|---|---|---|
| All tools fail | Webhook endpoint down / tunnel URL changed / port conflict | Health endpoint, DNS, tunnel status | Agent says it cannot reach the system and offers handoff (it retries once first) |
| One tool fails | Upstream (PMS) error or schema change | Tool error log, recent deploys | Same, for that capability only |
| Widget button does nothing | Widget script blocked or not loaded | Browser console, network tab | Show phone number as fallback |
| Agent answers outside scope | KB gap or prompt regression | Transcript review, scenario suite | Fix KB/prompt, add regression scenario |
| Latency spikes | LLM/TTS provider or slow PMS | Per-turn latency breakdown | Consider faster model for tool-light turns |

Real incidents of this kind from the PoC are written up in [lessons-learned.md](lessons-learned.md).

## 6. Cost model (production)

Cost per call ≈ (agent minutes × platform rate) + telephony minutes + hosting + SMS. Control levers: concise prompts (fewer tokens per turn), KB split between in-context and RAG, shorter greetings, model choice per use-case, hard max call duration. Track cost per resolved call, not only per minute.

## 7. Governance

- **Change control** – prompt, KB and workflow changes go through pull requests, run the scenario suite, and are promoted dev → staging → prod.
- **Review cadence** – weekly transcript sampling (safety + quality), monthly KPI review with the steering group, quarterly red-team.
- **Ownership** – business owner (GM), content owner (SPA/medical lead), technical owner (IT), data protection owner (DPO).

## 8. Roadmap beyond the pilot

1. Telephony go-live with SIP transfer and call-queue context passing
2. Real PMS adapter and SMS gateway
3. Automated evaluation harness and nightly regression runs
4. Outbound use-cases: appointment reminders, no-show recovery (with consent)
5. Multi-property rollout with per-hotel KB and shared core agent
