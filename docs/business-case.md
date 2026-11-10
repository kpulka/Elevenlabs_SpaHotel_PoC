# Business Case

> Why a voice agent for a spa hotel, what it should change, how success would be measured — and what must **not** be automated.
> Recruiter-facing companion to [deployment-playbook.md](deployment-playbook.md) and [lessons-learned.md](lessons-learned.md).

## 1. Context

Bukowy Dwór is a health resort in Krynica-Zdrój that runs three businesses on one telephone line:
**hospitality** (rooms, restaurant), **wellness** (SPA treatments on a tight daily schedule) and
**light medical services** (treatments that are prescribed, or sensitive to health conditions).

Its core guests are 60+, often calling from landlines, speaking slowly, repeating themselves, and asking
about diets, mobility and contraindications. That profile is the constraint the whole design is built around.

## 2. Problem

| Pain | Effect |
|---|---|
| The desk answers the same questions all day (hours, directions, prices, diets) | Staff time on low-value work; queues at check-in |
| Calls outside desk hours and during peaks go unanswered | Lost SPA and room bookings, especially off-season |
| SPA scheduling needs back-and-forth (slot, therapist, preparation rules) | Long calls, booking errors, no-shows |
| Seniors distrust IVRs and chatbots | Digital self-service never gets adopted in this segment |
| Clinical questions arrive unannounced in routine calls | Liability if the model improvises an answer |

## 3. Proposed solution

An always-available agent ("Anna") that behaves like a calm, competent receptionist: it books and changes
SPA treatments, checks room availability, answers from vetted hotel content, sends confirmations and hands
the guest to a human whenever the question is outside its mandate.

**Scope boundaries (by design)**

| Automate | Never automate |
|---|---|
| Availability and booking of SPA treatments | Medical advice, contraindication judgements |
| Room availability and price quotes | Price negotiation, exceptions to policy |
| FAQs: directions, hours, meals, diets | Complaints with compensation decisions (escalate with context) |
| Standard policy explanations (cancellation fee, deposit, check-in/out) | Anything missing from the knowledge base |

The line between the two columns is enforced by the prompt, by the procedures and by the backend — not by
good intentions. See [the 7 procedures](../docs/elevenlabs_agent_procedures.md) and
[the audit of the live agent](../docs/audyt_agenta_2026-08.md).

## 4. Value drivers

1. **Capture** — answer 100 % of inbound calls, 24/7; convert out-of-hours interest into bookings.
2. **Capacity** — absorb routine calls so staff can serve guests standing in the lobby.
3. **Consistency** — every guest hears the same, current policy instead of four different recollections.
4. **Data** — structured intent and outcome for every call: what guests ask for and where they drop.
5. **Guest experience** — no hold music; slow, patient pacing tuned for older guests.

## 5. KPIs

| KPI | Definition | Pilot target |
|---|---|---|
| Containment rate | Calls resolved without handoff, *excluding* mandated escalations | Baseline in weeks 1–2, then set |
| Booking conversion | Calls with booking intent → confirmed booking | Baseline, then +X pp |
| Correct handoff rate | Clinical / out-of-scope questions escalated rather than answered | ≈ 100 % (safety KPI, no trade-off) |
| Grounding failures | Statements not supported by KB or tool output, from sampled transcripts | 0 critical, < 1 % minor |
| Guest satisfaction | Post-call rating, complaint count | At least parity with the human desk |
| Time to first word | End of guest speech → start of reply | Sub-second perceived |
| Cost per handled call | Platform minutes + telephony + infrastructure | Compare to the loaded cost of a desk minute |

Targets are deliberately **not** pre-filled: they are set against the client's own call logs in week 1–2.
Inventing them in advance would be false precision.

## 6. Illustrative economics

> **Illustrative only.** Every input below is an assumption to be replaced with client data. Platform
> pricing changes; figures reflect 2026-11 and an FX rate of 4.0 PLN/USD.

| Input | Assumption |
|---|---|
| Platform, Creator | $22 / month for 275 call minutes |
| Platform, Scale | $299 / month for 3,738 call minutes |
| Effective rate (both plans) | **≈ $0.08 / minute** (299 ÷ 3,738 = 0.080) |
| Receptionist, Poland | ≈ 25 PLN / h gross ≈ $6 / h; employer overhead adds ~20–40 % |
| Average routine call | 3 minutes |
| Routine calls handled by the agent | 1,000 per month (assumption) |

**Cost side.** 1,000 calls × 3 min = 3,000 minutes → the **Scale** plan ($299), still inside its 3,738-minute
allowance. The human equivalent is 50 hours of talk time × 25 PLN ≈ 1,250 PLN ≈ **$312** gross, more with
overhead. So at this volume the platform is roughly **at parity with the wage it replaces** — labour is not
where the money is.

**Revenue side.** A night room booking is worth ≈ 500 PLN (≈ $125). Three captured bookings per month
(≈ $375) cover the monthly Scale plan outright, and that is the honest framing used in the deck:

> `275 min AI ($22 ≈ 88 PLN)` ≈ 3.5 hours of receptionist wage — parity, not a saving to bank on.
> `3 × 500 PLN` captured at night ≈ $375 — covers the $299/month plan.

Key sensitivities: average call duration, the share of calls that end in handoff, and — above all — the real
number and value of missed calls, which must be measured before go-live rather than assumed.

## 7. Risks and how the design answers them

| Risk | Mitigation in this solution |
|---|---|
| Hallucinated price or medical statement | Grounding-only prompt, temperature 0.1, critical KB pinned in-context, hard "no information → handoff" rule |
| Integration outage (PMS, network, tunnel) | Retry-once policy in the prompt, an honest "I cannot reach the system" path, handoff; the tool URLs are re-pointed automatically after every tunnel restart |
| Guest dislikes talking to a machine | A human is offered at any moment; warm voice, 0.85× speed, patient turn-taking |
| Privacy (voice recordings, health-adjacent data) | EU data residency, retention controls, no health details in tool payloads — see [playbook §4](deployment-playbook.md#4-security-privacy-and-compliance) |
| Staff resistance | Positioned as load relief, not redundancy; staff receive handoff context |
| Vendor or model change | Prompt, procedures and knowledge base are plain text in this repository; the LLM is a configuration parameter |

## 8. Stakeholders

| Stakeholder | Interest |
|---|---|
| General manager | Revenue, guest satisfaction, reputation |
| Front-desk lead | Workload, handoff quality, trust in the tool |
| SPA / medical lead | Safety rules, schedule integrity, contraindications |
| IT / PMS owner | Integration effort, security, vendor lock-in |
| Data protection officer | Legal basis, retention, processors |

## 9. Recommendation

Run a **time-boxed pilot** on the web widget plus one phone number, scoped to the SPA department, with human
handoff always available, a weekly transcript review and success measured against the KPIs above. Expand to
rooms — then to all inbound calls — only after the safety KPIs hold. The phased plan, gates and runbook are
in [deployment-playbook.md](deployment-playbook.md).
