# Design Rationale and Discovery Approach

> **Purpose:** This document records how the guest-communication problem at Bukowy Dwór was framed, which design decisions were taken and why, and how the main concerns raised by the steering committee are addressed. It is intended for the client steering committee and the delivery team.

---

## 1. Establishing context before design

The solution was not designed from a generic template. The first step was to confirm the operating context with the hotel, so that the architecture reflects real constraints. The questions below were used to open the discovery sessions:

> *"Before we propose an architecture, we need to confirm the business and operational context. Which property management system (PMS) does the hotel operate? Are incoming guest calls handled through an on-premise PBX with SIP trunks, or are we also targeting visitors to the website? And what is the acceptable risk level for clinical enquiries compared with standard reservations?"*

Why this order matters:
- It anchors the design in the hotel's real systems and telephony, rather than in a generic demonstration.
- It establishes a consultative working relationship with the client, in which the hotel's operators contribute their knowledge of guests and systems.

---

## 2. Problem decomposition

Every open-ended design question was broken down using the same five-step frame:

```
1. WHO is the user?            -> Persona, cognitive load, speech habits
2. WHAT is the job-to-be-done? -> Direct booking, grounded FAQs, medical screening
3. WHERE does it run?          -> Omnichannel: SIP telephony trunk + WebRTC widget
4. WHEN can it fail?           -> Hallucinations, PMS outages, contraindications
5. HOW do we measure success?  -> Booking conversion, first-response latency (<500 ms), ROI
```

### 2.1 User
- Senior guests (60+) form a large share of the hotel's guests: 60-70% in the resort's own estimate.
- This group strongly prefers a telephone call to an app or an online booking form.
- Typical behaviour: speaks slowly, pauses mid-sentence, often does not recall the medical names of treatments (for example, "the spine treatment with warm mud"), and hangs up if interrupted or misunderstood repeatedly.
- The persona used in the design is an archetype of a thermal-spa guest, not an individual.

### 2.2 Job-to-be-done
- Book spa treatments and rooms directly.
- Answer routine questions (opening hours, directions, dietary menus, resort rules) from a verified source.
- Screen for health contraindications before a treatment is booked, and escalate emergencies to staff.

### 2.3 Channel
- **Telephone:** the hotel's existing number, connected through a SIP trunk to the agent.
- **Web widget:** a floating button on the hotel website, with an avatar, live transcript and on-screen confirmation.
- Both channels use the same agent and the same knowledge base, so the guest experience is consistent.

### 2.4 Failure modes
- Hallucinated information (prices, treatment availability, health advice).
- Loss of the booking system (PMS) during a call.
- Missed contraindications for balneological treatments.
- Speech recognition errors, particularly with regional accents.

### 2.5 Success metrics
- Booking conversion from calls and widget sessions.
- First-response latency below 500 ms.
- Return on investment (see section 4.4).
- Recommended addition from the discovery workshop: customer satisfaction (CSAT). An assistant that handles 90% of calls but frustrates guests is not a success.

---

## 3. Key design decisions and trade-offs

### Decision 1: Native ElevenLabs agent instead of a custom STT -> LLM -> TTS pipeline

- **Reasoning:** a cascaded pipeline (separate speech-to-text, language-model and text-to-speech services) accumulates latency beyond 2.0 seconds. For an older guest, each second of silence weakens the feeling of being in a conversation and reduces trust. ElevenLabs Conversational AI combines recognition, orchestration and speech synthesis in one cloud loop, with a measured end-to-end response of about 430 ms and natural turn-taking.
- **Trade-off:** less control over each individual component, and a dependency on one platform. This is accepted because the time to a working, measurable deployment is shorter, and the agent configuration (prompts, tools, knowledge base) remains under the hotel's control.

### Decision 2: Eleven v3 Conversational voice instead of Flash

- **Reasoning:** Flash is about four times faster (75 ms synthesis against 280 ms for v3), but it sacrifices emotional warmth and prosody. For elderly guests, a calm and empathetic tone is a primary driver of trust. The extra roughly 200 ms of synthesis time is considered worth the gain in guest comfort and booking completion.
- **Trade-off:** a slightly slower response. Speech pacing is compensated for with the timing settings in decision 5.

### Decision 3: Prompt context for critical rules, knowledge base for detail

- **Reasoning:** core operating procedures and base pricing stay permanently in the prompt (`prompt` mode) for deterministic access without retrieval. Detailed treatment catalogues and driving directions are stored in the vector knowledge base (`auto` mode), retrieved when needed.
- **Result:** the prompt stays lean (about 400 words), token consumption is lower, and the design can grow to many properties and documents without prompt bloat.
- **Trade-off:** retrieval adds a dependency on knowledge base quality. Content gaps show up as escalations rather than errors, so the knowledge base needs an owner (see section 5).

### Decision 4: Strict grounding

- **Reasoning:** in healthcare hospitality, an incorrect price is a commercial inconvenience. An incorrect balneological contraindication is a serious medical and legal liability. The agent is therefore configured to answer only from the verified knowledge base, and to hand over to staff when information is missing (see section 4.2).
- **Trade-off:** more escalations to reception during the early phase, until the knowledge base covers the questions guests actually ask.

### Decision 5: Timing tuned for senior callers

- `turn_timeout: 3.0 s` (the default of about 1.2 s cut seniors off when they paused to breathe or think).
- `turn_eagerness: Patient`, so the agent does not speak over natural pauses.
- Speech speed set to 0.85x.
- **Trade-off:** a slightly slower reply for callers who finish quickly. This is an intentional choice for this audience.

### Decision 6: One central agent for the hotel network

- **Reasoning:** instead of maintaining ten separate agents, one master agent is used. Property-specific data (`hotel_name`, `location`, `reception_phone`, `pms_id`) is supplied as dynamic variables.
- **Mechanism:** the inbound telephony header (RFC 7433 SIP User-to-User Information) carries the property parameters for each incoming call.
- **Result:** onboarding a new property requires a configuration profile, not a copy of the prompt and agent logic.

---

## 4. Responses to stakeholder questions

### 4.1 Clinical risk

**Question:** can the assistant put guests at risk by booking a treatment that is unsafe for them?

**Response:**
- Before a balneological treatment (sulphur or mud bath) is booked, the agent asks screening questions about acute heart conditions, circulatory problems and skin inflammation.
- If a contraindication is mentioned, the agent explains the risk in plain language, recommends a consultation with the resort physician, and does not book the treatment.
- Emergency symptoms (for example, chest pain or shortness of breath) trigger an immediate transfer to the nursing duty desk.
- The agent does not give medical advice or diagnose. Its role is to screen, record and escalate.

**Limits we are open about:** screening relies on what the guest reports. The list of contraindications and the escalation rules should be signed off by the resort's medical staff before go-live (see section 5).

### 4.2 Hallucinations

**Question:** what happens when a guest asks something the assistant does not know?

**Response:**
- The agent is configured for strict grounding, with a low model temperature (0.1) to reduce variation in answers.
- Answers are drawn only from the five curated knowledge base documents (general information and directions, spa treatments and health, rooms and pricing, restaurant and diets, procedures and policies).
- If the answer is not in the knowledge base, the agent says so plainly and transfers the call to a receptionist. Prices and availability are never estimated.
- Booking confirmations are given only after the booking system has returned a successful response.

**Limits we are open about:** coverage depends on the knowledge base. Gaps lead to escalation, which is safe but adds workload for reception until the content is extended.

### 4.3 PMS outages

**Question:** what happens if the hotel's booking system is unavailable during a call?

**Response:**
- If a booking-system call does not respond within 5 seconds, the agent apologises, explains that the connection to the booking system has briefly dropped, and transfers the guest to reception, who can check and book directly.
- A booking is never confirmed to the guest unless the system has confirmed it, so there is no risk of a guest believing they are booked when they are not.
- After three consecutive failed attempts to understand the guest, the call is always escalated.

**Limits we are open about:** in the proof-of-concept, the booking system is a mock service. In production, the PMS dependency needs monitoring and an agreed fallback process with the hotel's reception team. Two-way PMS synchronisation is planned for Phase II.

### 4.4 Cost and return on investment

**Question:** does the investment pay back?

**Response, using the figures available to the design team:**
- **Subscription (scale tier):** $299 per month, including 3,738 minutes of calls.
- **Entry plan (proof of concept):** $22 per month, including 275 minutes. Its cost is roughly equivalent to one hour of receptionist time (about $25).
- **Revenue at risk outside staffed hours:** the front desk is not staffed after 10:00 PM. An average spa-stay booking is worth $400-$800.
- **Scenario:** capturing five after-hours bookings per month would generate $2,000-$4,000 in incremental revenue. The original analysis estimates that this would cover the annual contract in under 60 days.
- **Capacity:** 10 concurrent channels on the entry plan; 30 concurrent channels on the scale plan, with bursts up to 90.

**Note:** these are planning estimates. Booking values and after-hours call volumes should be confirmed with the hotel's finance team before the business case is finalised (see section 5).

### 4.5 Privacy and data protection

**Question:** how is guest data protected, given that calls may contain health information?

**Response:**
- **Zero Retention Mode (ZRM):** audio is processed in volatile memory and removed when the session ends.
- **Redaction:** personal data (national identification numbers, telephone numbers, health notes) is masked in stored conversation logs.
- **EU data residency:** compute, model inference and vector embeddings are located in EU regions (Frankfurt or Dublin).
- **Signed URLs:** the web widget receives a short-lived token (15-minute time-to-live) and never the platform API key.

**Next steps for the hotel:** a data processing agreement with the platform provider, and review by the hotel's data protection officer, are preconditions for go-live. This document does not replace that legal review.

---

## 5. Open items for the steering committee

| # | Item | Owner | Why it matters |
|---|---|---|---|
| 1 | Clinical sign-off on screening questions and escalation rules | Resort medical staff | Clinical risk (section 4.1) |
| 2 | Confirm booking values and after-hours call volumes | Hotel finance | Basis of the return on investment (section 4.4) |
| 3 | Confirm per-minute overage rate for the scale plan | Delivery team | Needed to forecast usage costs |
| 4 | Data processing agreement and DPO review | Hotel legal / DPO | Privacy preconditions (section 4.5) |
| 5 | Named owner for the knowledge base content | Hotel management | Coverage determines escalation rate (section 4.2) |
| 6 | Operating process when the booking system is down | Hotel reception | Fallback behaviour (section 4.3) |
