# V1 Interview Guide & Thought Process — Deployment Strategist (Case Study)

> **Objective:** Demonstrate structured thinking out loud, business-to-technical mapping, domain empathy, and bias for action to the ElevenLabs hiring team.

---

## 1. The First 60 Seconds: Clarifying Before Solving

Never jump straight into drawing architecture boxes. Senior deployment strategists ask **calibrated discovery questions**:

> *"Before proposing an architecture, I would like to clarify the business and operational context: What existing Property Management System (PMS) does the hotel chain operate? Are incoming guest calls handled via on-premise PBX SIP trunks, or are we targeting website visitors? And what is the risk tolerance regarding clinical inquiries versus standard reservations?"*

### Why this works:
- Proves you design for real enterprise constraints, not generic demos.
- Establishes a collaborative, consultative peer dynamic.

---

## 2. Problem Decomposition Framework (Think Out Loud)

Use this 5-step decomposition when addressing any open-ended design challenge:

```
1. WHO is the user?            → Persona, cognitive load, speech habits
2. WHAT is the job-to-be-done? → Direct booking, grounded FAQs, medical triage
3. WHERE does it run?          → Omnichannel: SIP Telephony Trunk + WebRTC widget
4. WHEN can it fail?           → Hallucinations, PMS outages, contraindications
5. HOW do we measure success?  → Booking conversion, first-response latency (<500ms), ROI
```

---

## 3. Core Architectural Decisions & Justifications

### Q1: "Why use a native ElevenLabs Agent instead of a custom STT → LLM → TTS cascade?"
**Answer:**
> *"A cascaded pipeline (external STT + LLM API + TTS API) introduces cumulative latencies exceeding 2.0 seconds. For a 72-year-old guest, every second of dead air breaks conversational presence and breeds distrust. ElevenLabs Conversational AI unifies speech recognition, LLM orchestration, and speech synthesis into a single sub-500ms cloud loop, creating natural human-like turn-taking."*

### Q2: "ElevenLabs Flash is 4x faster (75ms). Why did you choose Eleven v3 Conversational (280ms)?"
**Answer:**
> *"Flash provides blistering speed, but sacrifices emotional warmth and prosodic nuance. For elderly spa guests, a soothing, empathetic tone is not a luxury — it is the primary trust driver. A 200ms increase in synthesis time is well worth the dramatic boost in guest retention and booking completion."*

### Q3: "Why not inject all hotel information directly into the System Prompt?"
**Answer:**
> *"We keep core operating procedures and base pricing permanently in prompt context (`prompt mode`) for zero-latency deterministic access. However, detailed treatment catalogs and regional driving directions are stored in a Vector Knowledge Base (`auto mode`). This keeps the prompt lean (~400 words), minimizes token consumption, and allows the system to scale to hundreds of properties without prompt bloat."*

### Q4: "What happens when a guest asks a question outside the knowledge base?"
**Answer:**
> *"We enforce a strict zero-hallucination policy (`strict grounding`). In healthcare hospitality, a hallucinated price is an inconvenience, but a hallucinated balneology contraindication is a serious medical and legal liability. If information is missing from the verified knowledge base, Anna transparently acknowledges this and initiates a warm SIP transfer to the human front desk."*

---

## 4. Multi-Tenant Scaling & Commercial ROI

### Scaling Across 10 Hotel Properties:
- Instead of maintaining 10 siloed agents, we deploy **1 Master Agent Core** paired with **Dynamic Variables** (`hotel_name`, `location`, `reception_phone`, `pms_id`).
- Inbound telephony passes these variables dynamically inside the **RFC 7433 SIP UUI (User-to-User Information)** signaling header.
- Adding a new property requires creating a configuration profile in PMS — zero code or prompt duplication.

### Financial Justification (ROI Calculation):
- **Scale Subscription Tier:** $299/mo includes 3,738 minutes (~$0.027/min).
- **Labor Parity:** 275 minutes equals ~1 hour of human receptionist wage ($22 vs $25).
- **The True ROI Driver:** The hotel front desk is unstaffed after 10:00 PM. An average spa stay booking represents $400–$800. Capturing just **5 after-hours bookings per month** generates **$2,000–$4,000 in incremental revenue**, paying for the entire annual ElevenLabs contract in under 60 days.
