# Functional Specification: AI Voice Receptionist "Anna" for a Hotel and SPA Group

> Specifies what the product does for the Bukowy Dwór health resort: an ElevenLabs Agents voice receptionist designed around the needs of guests aged 60 and over.

> **Canonical document.** This specification combines business requirements and the needs of the target audience (guests aged 60+) with the capabilities of the **ElevenLabs Agents (Conversational AI)** platform.
> Technical details (models, acoustic parameters, JSON schemas, costs) are maintained in the **implementation plan** (`docs/implementation-plan.md`), which is the source of truth for technical configuration.
> This specification defines WHAT the product does; the implementation plan defines HOW it is configured.

**Platform:** ElevenLabs Agents (Conversational AI)
**Persona:** Anna
**Guest profile:** guests aged 60+, guests who value calm, guests with medical and rehabilitation needs
**Environment:** multi-site hotels, health resorts, thermal resorts
**Pilot site:** Uzdrowisko Termalne "Bukowy Dwór", Krynica-Zdrój

---

## 1. System Concept

The system performs the tasks of a hotel receptionist over a voice channel. On the ElevenLabs platform it combines:
- the native conversational engine (**ElevenLabs Agents**): speech-to-text (STT), an LLM orchestrator and text-to-speech (TTS) in a single conversational loop,
- a knowledge base (**RAG**: 5 Markdown files),
- tools (**Tool Calling / Webhooks**) connected to the property management system (PMS), the SPA booking system and the SMS gateway,
- native call transfer (**Human Handoff**).

### Model stack (details in implementation plan §1.2)
| Layer | Selection |
|---|---|
| STT | Scribe v2 Realtime (~150 ms) |
| LLM | GPT-4o Mini or Gemini 2.5 Flash |
| TTS | Eleven v3 Conversational (~280 ms, high expressiveness) |

> Goal: minimise latency while preserving a natural, warm voice, which is essential for senior guests.

---

## 2. Persona and Voice ("Anna")

- **Name:** Anna.
- **Voice (PoC):** the premade voice **Jessica: Playful, Bright, Warm** (ID: `cgSgspJ2msm6clMCkdW9`), or a dedicated voice created with **Voice Design**.
- **Voice parameters:** stability `0.80`, similarity_boost `0.75`, speed `0.85x`.
- **Style:** empathetic, unhurried, very courteous; no jargon (for example, "a text message to your phone" rather than "an SMS with a payment link").

### Acoustic parameters for senior guests (turn-taking)
- `turn_timeout` = **3.0 s** (a longer silence window, because callers speak more slowly),
- `turn_eagerness` = **Patient** (the agent does not interrupt and waits patiently for information).

---

## 3. Functional Scope

### 3.1. Reservations and availability
- Room availability checks, with a preference for ground-floor rooms or rooms near a lift for senior guests.
- Price calculation (therapy packages, health-resort and loyalty discounts).
- Room and SPA treatment reservations; deposit policy (30%) and cancellation policy (14 days).

### 3.2. Medical, SPA and wellness services
- Bookings for balneological treatments, massages and consultations.
- Pre-treatment screening questions on contraindications before a treatment is confirmed.
- Pool infrastructure information (water temperatures, gentle entry points, lifts).

### 3.3. Dining and diets
- Therapeutic diets (diabetic, easily digestible, gluten-free / dairy-free) recorded in the guest profile.
- Meal times, waiter assistance, and complimentary room service in case of illness.

### 3.4. Practical information and getting here
- Point-by-point navigation ("next to the old pump room", "flat route").
- Complimentary golf-cart transfer from the railway station (booking required at least 24 hours in advance).
- Architectural accessibility information (no thresholds, lifts with voice announcements).

### 3.5. Complaints, assistance and emergency reporting
- Reports of faults and requests for items (orthopaedic pillow, shower chair).
- Health emergency: immediate connection to the duty room (room 101) or the emergency number.

---

## 4. Demonstration Scenarios (PoC)

For the demonstration, the agent handles three paths smoothly, using mock data:

**A. SPA booking.** The guest asks about a massage. The agent checks available times (mock), proposes slots, collects details step by step, paraphrases the agreed details, confirms them and sends an "SMS" (a Telegram or WhatsApp webhook).

**B. Information (RAG).** The guest asks about meal times or whether the pool requires a swimming cap. The agent answers only from the knowledge base.

**C. Escalation (Human Handoff).** An unusual request, a complaint or medical requirements. The agent recognises that it is outside its competence and transfers the call to the "real reception" (transfer to a phone number).

---

## 5. Canonical Tool Set (Tool Calling)

Full JSON schemas are in the implementation plan §4. This list is consistent across the PoC and the target version:

| Tool | Role | Type |
|---|---|---|
| `check_spa_availability` | free SPA treatment slots | Webhook (mock PMS) |
| `book_spa_appointment` | SPA treatment booking | Webhook (mock PMS) |
| `check_room_availability` | rooms free for the requested period | Webhook (mock PMS) |
| `send_sms_summary` | reservation summary to the guest's phone | Webhook (Telegram/WhatsApp in the PoC; Twilio in Phase II) |
| `transfer_to_human` | transfer to reception or the duty room | native `transfer_to_number` |

---

## 6. Knowledge Base (RAG)

Five Markdown files (Bukowy Dwór), located in `agent/knowledge_base/`. Usage modes (`usage_mode`) are assigned as follows:

| Mode | Files | Rationale |
|---|---|---|
| `prompt` (full context, always included in the prompt) | `05_procedures_and_policies.md`, `03_rooms_and_pricing.md` | Critical prices and procedures must never be skipped by RAG retrieval |
| `auto` (semantic search / RAG) | `01_general_info_and_directions.md`, `02_spa_treatments_and_health.md`, `04_restaurant_and_diets.md` | Extensive descriptive content; only the matching fragments are injected |

### Strict grounding (eliminating hallucinations)
The agent answers exclusively on the basis of the knowledge base and tool results. If information is not available, it politely declines and calls `transfer_to_human`. It never invents prices, appointment times or diet details.

---

## 7. SMS Communication and Stay Assistant

- The agent asks which number notifications should be sent to (the guest or a carer, such as a daughter or son).
- Message types: confirmation with an advance payment, a reminder three days before arrival (including transport), and an evening schedule of treatments.
- **PoC:** Telegram/WhatsApp webhook (demonstration impact on a secondary display).
- **Phase II:** production Twilio SMS API.

---

## 8. Scaling Across a Hotel Network (Multi-Property)

A single parent agent, "Anna", uses **Dynamic Variables / Overrides**. The initialisation payload `conversation_initiation_client_data` overrides the hotel name, location, reception phone number and hotel ID. For telephony, metadata is passed in the SIP signalling (**UUI, RFC 7433**). Result: one agent, many properties, no duplicated configuration. (Details: implementation plan §5.)

---

## 9. Security and GDPR

1. **Signed URLs** (`/get_signed_url`, valid for 15 minutes): the widget does not use the main API key.
2. **Zero Retention Mode (ZRM):** audio and transcripts are processed only in RAM and are never written to disk (Enterprise).
3. **Conversation History Redaction:** automatic masking of personal and medical data.
4. **Data Residency:** processing within the EU (DPA / GDPR compliance).
5. **Data minimisation:** only first name, last name, phone number and preferences are collected; verbal consent is required for sensitive data.

---

## 10. Costs and Limits (Summary)

| | PoC (demo) | Production (Enterprise) |
|---|---|---|
| Plan | Creator (~$22/month) | Scale/Enterprise (~$299/month) |
| Minutes | 275 | 3 738 |
| Concurrent calls | 10 | 30 (+ Burst Pricing up to 90) |

The full table is in implementation plan §7.

---

## 11. Deployment Roadmap

### MVP / PoC (Phase 1)
1. RAG with the complete knowledge base (5 files, `prompt` / `auto` modes).
2. Availability and booking tools on mock PMS interfaces.
3. Preliminary reservations and SMS (Telegram/WhatsApp webhook).
4. Seamless transfer to a live receptionist (`transfer_to_number`).

### Phase II (extension)
1. Integration with the medical billing system and the SPA electronic records system.
2. Multilingual support (DE/EN) with the same standard of empathy.
3. Outbound Voice AI: outgoing calls before arrival (confirmation and transport).
4. Production Twilio SMS and PBX routing (reception vs. medical duty room).

---

## 12. References

- **Technical plan (source of truth):** `docs/implementation-plan.md`
- **Knowledge base (RAG):** `agent/knowledge_base/` (5 files)
- **System prompt:** `agent/system_prompt.md`
- **Workflow and procedures:** `agent/workflow/` and `docs/agent-workflows-and-procedures.md`
- **Architecture:** `docs/architecture.md`
- **Operating procedures:** `docs/operating-procedures.md`
- **Agent audit:** `docs/agent-audit.md`
- **UX design and demo:** `docs/ux-design.md`, `docs/demo-script.md`
- **Mock backend and frontend:** `mock_backend/`, `frontend/`
