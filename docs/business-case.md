# Business Case

> Why a voice agent for a spa hotel, what it should change, how success is measured — and what must **not** be automated.

## 1. Context

A health-resort hotel combines three businesses on one phone line: **hospitality** (rooms, restaurant), **wellness** (SPA treatments with a tight daily schedule) and **light medical services** (treatments prescribed or sensitive to health conditions). Its core guests are 60+, often calling on landlines, speaking slowly, repeating themselves and asking about diets, mobility and contraindications.

## 2. Problem

| Pain | Effect |
|---|---|
| Front desk answers the same questions all day (opening hours, directions, prices, diets) | Staff time spent on low-value work; queues at check-in |
| Calls outside desk hours and during peaks go unanswered | Lost SPA and room bookings, especially off-season |
| SPA scheduling needs back-and-forth (slot, therapist, preparation rules) | Long calls, errors, no-shows |
| Seniors distrust IVRs and chatbots | Digital self-service has low adoption in this segment |
| Clinical questions arrive unannounced in routine calls | Liability if answered incorrectly |

## 3. Proposed solution

An always-available agent ("Anna") that behaves like a calm, competent receptionist: books and changes SPA treatments, checks rooms, answers from vetted hotel content, sends confirmations, and escalates to a human whenever a question is outside its mandate.

**Scope boundaries (by design)**

| Automate | Never automate |
|---|---|
| Availability and booking of SPA treatments | Medical advice, contraindication judgements |
| Room availability and price quotes | Price negotiation, exceptions to policy |
| FAQs: directions, hours, meals, diets | Complaints with compensation decisions (escalate with context) |
| Standard policy explanations (cancellation, deposit, check-in) | Anything missing from the knowledge base |

## 4. Value drivers

1. **Capture** – answer 100 % of inbound calls, 24/7; convert out-of-hours interest into bookings.
2. **Capacity** – absorb routine calls so staff focus on guests in the lobby.
3. **Consistency** – every guest hears the same, current policy.
4. **Data** – structured intent and outcome data for every call (what guests ask for, where they drop).
5. **Guest experience** – no hold music; patient pacing tuned for older guests.

## 5. KPIs

| KPI | Definition | Target for pilot (to be baselined with the client) |
|---|---|---|
| Containment rate | Calls resolved without human handoff, *excluding* mandated escalations | Baseline in week 1–2, then set |
| Booking conversion | Calls with intent to book → confirmed booking | Baseline, then +X pp |
| Correct handoff rate | Clinical / out-of-scope questions escalated rather than answered | ≈ 100 % (safety KPI, no trade-off) |
| Hallucination rate | Statements not supported by KB/tool output, from sampled transcripts | 0 critical, <1 % minor |
| Guest satisfaction | Post-call rating / complaint count | At least parity with human desk |
| Time to first word | Latency from end of guest speech to start of reply | Sub-second perceived |
| Cost per handled call | Platform minutes + telephony + infra | Compare to loaded cost of a desk minute |

Targets are intentionally left to be set against a measured baseline in the client's own call logs; inventing them in advance would be false precision.

## 6. Illustrative economics

> **Illustrative only.** All inputs below are assumptions to be replaced with client data. Platform pricing changes; check current plans.

| Input | Assumption |
|---|---|
| Conversational AI cost | ≈ USD 0.08 per minute (order of magnitude, plan-dependent) |
| Loaded cost of a receptionist hour (Poland) | ≈ USD 15–25 |
| Average routine call | 3 minutes |
| Routine calls handled by agent | 1 000 per month (assumption) |

- Agent: 1 000 calls × 3 min × 0.08 ≈ **USD 240 / month** (plus telephony and hosting).
- Human equivalent: 50 hours × USD 15–25 ≈ **USD 750–1 250 / month** of desk time that is *redeployed*, not necessarily eliminated.
- The larger lever is usually **revenue capture** (one additional multi-night stay or a package of treatments per week can outweigh platform costs) rather than labour savings. This must be validated by measuring missed calls and their value before go-live.

Key sensitivity: average call duration and the share of calls that end in handoff.

## 7. Risks and how the design answers them

| Risk | Mitigation in this solution |
|---|---|
| Hallucinated price or medical statement | Strict grounding prompt, temperature 0.1, critical KB in-context, hard "no info → handoff" rule |
| Integration outage (PMS / network) | Tool-level retry policy in the prompt, honest "I can't reach the system" path, handoff; see [lessons learned](lessons-learned.md) |
| Guest dislikes talking to a machine | Immediate offer of a human at any time; warm voice, slow pace |
| Privacy (health-adjacent data, voice recordings) | EU data residency, retention controls, minimal data in tools — see [playbook](deployment-playbook.md#security-privacy-and-compliance) |
| Staff resistance | Position as assistant for routine load; staff receive handoff context |
| Vendor / model change | Prompt and KB are plain text in the repo; LLM is a config parameter |

## 8. Stakeholders

| Stakeholder | Interest |
|---|---|
| General manager | Revenue, guest satisfaction, reputation |
| Front-desk lead | Workload, handoff quality, trust in the tool |
| SPA / medical lead | Safety rules, schedule integrity, contraindications |
| IT / PMS owner | Integration effort, security, vendor lock-in |
| Data protection officer | GDPR basis, retention, processors |

## 9. Recommendation

Run a **time-boxed pilot** on the web widget and one phone number for a single department (SPA), with human handoff always available, a weekly transcript review, and success measured against the KPIs above. Expand to rooms, then to all inbound calls, only after the safety KPIs hold. The phased plan is in the [deployment playbook](deployment-playbook.md).
