> **Status:** aktualny (2026-11) — tłumaczenie EN dokumentu `docs/architektura_stack_technologiczny.md` (wersja źródłowa: PL).

# Enterprise System Architecture & Tech Stack — Virtual AI Receptionist (Bukowy Dwór)

> Technical implementation reference, enterprise architecture, interfaces, connectors, and communication protocols connecting **ElevenLabs Conversational AI** with hotel and medical resort infrastructure.

---

## 1. End-to-End Architectural Overview

The system is built upon the **Cloud-Native Unified Conversational Loop** paradigm, eliminating the multi-second latency typical of traditional cascaded pipelines (STT → External LLM → TTS).

The architecture spans 5 core layers:
1. **Omnichannel Inbound Layer** — Telephony SIP Trunking (RFC 3261) and Web/Mobile WebRTC full-duplex audio.
2. **Edge Security & Authorization Layer** — 15-min TTL Signed URLs, Zero Retention Mode (ZRM), and EU Data Residency.
3. **ElevenLabs AI Core Engine** — Unified STT (Scribe v2), LLM Orchestrator (GPT-4o Mini / Gemini 2.5), Vector RAG, and Emotional TTS (Eleven v3 Conversational).
4. **Tool Calling & Integration Layer** — Deterministic HTTPS POST Webhooks, JSON Schema parameter validation, and SIP REFER call handoff.
5. **Hospitality Enterprise Systems** — Hotel PMS/ERP database (e.g., Opera Cloud, Mews, Protel, KWHotel), SMS dispatch gateways (Twilio / SMSAPI), and on-duty medical staff.

---

## 2. Mermaid.js System Architecture Diagram

```mermaid
flowchart TB
    %% STYLING DEFINITIONS
    classDef clientLayer fill:#1B2A4A,stroke:#C9A84C,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef edgeLayer fill:#233458,stroke:#C9A84C,stroke-width:2px,color:#FFFFFF;
    classDef aiCore fill:#FDFAF5,stroke:#1B2A4A,stroke-width:3px,color:#1B2A4A,font-weight:bold;
    classDef aiSub fill:#EBF3EB,stroke:#7A9E7E,stroke-width:2px,color:#1B2A4A;
    classDef webhookLayer fill:#E8DCC8,stroke:#C9A84C,stroke-width:2px,color:#1B2A4A,font-weight:bold;
    classDef backendLayer fill:#FFFFFF,stroke:#1B2A4A,stroke-width:2px,color:#1B2A4A;
    classDef pmsLayer fill:#FFF3CD,stroke:#856404,stroke-width:2px,color:#856404,font-weight:bold;
    classDef secLayer fill:#F8D7DA,stroke:#721C24,stroke-width:2px,color:#721C24;

    %% 1. INBOUND
    subgraph INBOUND ["📱 1. OMNICHANNEL INBOUND CHANNELS"]
        direction LR
        PHONE["☎️ Standard Telephony<br/>(PSTN / GSM / VoLTE)"]:::clientLayer
        SIP_TRUNK["🏢 Hotel PBX Central Switch<br/>(Twilio / Asterisk / FreePBX)<br/>SIP Trunking RFC 3261"]:::clientLayer
        WEB_CLIENT["💻 Web / Mobile WebRTC Client<br/>(Next.js 16 + React 19)<br/>@elevenlabs/convai-widget-embed"]:::clientLayer
        
        PHONE -->|"G.711 / Opus Audio"| SIP_TRUNK
    end

    %% 2. EDGE & SECURITY
    subgraph EDGE ["🔒 2. EDGE GATEWAY & SECURITY"]
        direction TB
        SIP_URI["ElevenLabs SIP Gateway<br/>sip:agent_id@sip.elevenlabs.io<br/>+ SIP UUI RFC 7433 Headers"]:::edgeLayer
        SIGNED_URL_API["Next.js Route Handler<br/>GET /api/anna/signed-url<br/>(15-min TTL Signed Tokens)"]:::edgeLayer
        SEC_POL["Security & Compliance:<br/>• Zero Retention Mode (ZRM)<br/>• EU Data Residency (Frankfurt)<br/>• PII Redaction in Transcripts"]:::secLayer
    end

    SIP_TRUNK -->|"SIP / TLS + SRTP Audio"| SIP_URI
    WEB_CLIENT -->|"Fetch Signed URL"| SIGNED_URL_API
    SIGNED_URL_API -->|"WSS Secure Handshake"| WSS_CONN

    %% 3. ELEVENLABS AI CORE
    subgraph AI_CORE ["⚡ 3. ELEVENLABS CONVERSATIONAL AI ENGINE (EU CLOUD)"]
        direction TB
        
        WSS_CONN["🌐 Transport Layer:<br/>WebSockets / WebRTC Opus Audio"]:::aiSub
        
        subgraph LOOP ["Unified Conversational Loop (~430ms)"]
            STT["🎙️ STT: Scribe v2 Realtime<br/>• Latency: ~150ms<br/>• Language: pl-PL with VAD<br/>• Noise Suppression & Voice Activity"]:::aiSub
            
            ORCHESTRATOR["🧠 LLM Orchestrator & State Machine<br/>• Model: GPT-4o Mini / Gemini 2.5 Flash<br/>• Temp: 0.1 (Strict Grounding)<br/>• Workflows & SOP Procedures"]:::aiCore
            
            TTS["🔊 TTS: Eleven v3 Conversational<br/>• Latency: ~280ms<br/>• Voice ID: Jessica (Warm/Calm)<br/>• Speed: 0.85x (Senior Acoustic Tuning)"]:::aiSub
            
            STT -->|"Real-time streaming text"| ORCHESTRATOR
            ORCHESTRATOR -->|"Streaming response tokens"| TTS
        end

        subgraph RAG_KB ["📚 Vector Knowledge Base"]
            KB1["01_informacje_ogolne_i_dojazd.md"]:::aiSub
            KB2["02_katalog_zabiegow_spa_i_zdrowie.md"]:::aiSub
            KB3["03_pokoje_i_cennik.md"]:::aiSub
            KB4["04_restauracja_i_diety.md"]:::aiSub
            KB5["05_procedury_i_polityki.md"]:::aiSub
        end

        ORCHESTRATOR <-->|"Semantic Search / Prompt Injection"| RAG_KB
    end

    SIP_URI --> WSS_CONN
    WSS_CONN --> STT
    TTS --> WSS_CONN
    WSS_CONN -->|"Full-duplex audio stream"| WEB_CLIENT
    WSS_CONN -->|"Full-duplex audio stream"| SIP_TRUNK

    %% 4. TOOL CALLING & INTEGRATION
    subgraph INTEGRATION ["🔧 4. TOOL CALLING & INTEGRATION LAYER"]
        direction TB
        TOOL_ROUTER["Tool Dispatcher - ElevenLabs Client Tools<br/>HTTPS POST with JSON Body + Bearer Token"]:::webhookLayer
        
        subgraph TOOLS ["Registered Tools (Client Tools)"]
            T1["check_spa_availability"]:::webhookLayer
            T2["book_spa_appointment"]:::webhookLayer
            T3["check_room_availability"]:::webhookLayer
            T4["send_sms_summary"]:::webhookLayer
            T5["transfer_to_number"]:::webhookLayer
        end

        TOOL_ROUTER --> T1
        TOOL_ROUTER --> T2
        TOOL_ROUTER --> T3
        TOOL_ROUTER --> T4
        TOOL_ROUTER --> T5
    end

    ORCHESTRATOR -->|"Tool invocation trigger - JSON Schema"| TOOL_ROUTER
    TOOL_ROUTER -->|"JSON payload response"| ORCHESTRATOR

    %% 5. BACKEND & PMS
    subgraph BACKEND ["🏨 5. HOSPITALITY BACKEND, PMS & COMMUNICATIONS"]
        direction TB
        
        FASTAPI_GW["Gateway PoC: FastAPI mock_backend<br/>• Uvicorn ASGI Server<br/>• Pydantic v2 Validation<br/>• ngrok / Cloudflare Tunnel for HTTPS"]:::backendLayer
        
        PMS_CORE["Hotel PMS / ERP Database<br/>(Opera Cloud / Mews / Protel / KWHotel)<br/>• Balneology treatment schedule<br/>• Room inventory & folio management"]:::pmsLayer
        
        SMS_GW["Messaging & Notification Gateway<br/>• Twilio / SMSAPI / Infobip REST API<br/>• Telegram Bot API"]:::backendLayer
        
        HUMAN_ESC["Human Staff Escalation<br/>• Front Desk: +48 18 123 45 67<br/>• Nurse Station: +48 18 123 45 99<br/>(SIP REFER Native Transfer)"]:::pmsLayer
    end

    T1 -->|"HTTPS POST Webhook"| FASTAPI_GW
    T2 -->|"HTTPS POST Webhook"| FASTAPI_GW
    T3 -->|"HTTPS POST Webhook"| FASTAPI_GW
    T4 -->|"HTTPS POST Webhook"| FASTAPI_GW
    FASTAPI_GW <-->|"SQL / REST API"| PMS_CORE
    FASTAPI_GW -->|"HTTP POST"| SMS_GW
    T5 -->|"SIP REFER / Handoff"| HUMAN_ESC
```

---

## 3. Comprehensive Tech Stack Specifications

### A. Client & Web Experience
- **Framework:** Next.js 16 (App Router), React 19, TypeScript 5.
- **Styling:** Tailwind CSS v4, Radix UI Primitives, Lucide Icons.
- **Voice SDK:** `@elevenlabs/convai-widget-embed` (0.16.4+).
- **Transport Security:** Next.js Server Route Handler `GET /api/anna/signed-url` generates temporary Signed WebRTC/WSS URLs with 15-minute TTL without exposing server `xi-api-key`.

### B. Telephony Gateway & SIP Trunking
- **Protocols:** SIP Trunking (RFC 3261) with TLS and SRTP encryption.
- **Telco Infrastructure:** Twilio Elastic SIP Trunking / Kamailio SBC / Asterisk PBX.
- **Multi-Tenant Context Injection:** Uses **RFC 7433 SIP UUI (User-to-User Information)** header to pass property parameters in-band:
  ```http
  User-to-User: hotel_id=bukowy_dwor;ani=+48600111222;lang=pl-PL;encoding=hex
  ```
- **Call Escalation:** Native `SIP REFER` executes warm transfers to physical receptionists or emergency medical staff without terminating the underlying trunk line.

### C. ElevenLabs Conversational AI Engine
- **Speech-to-Text (STT):** `Scribe v2 Realtime` (~150ms latency, Polish balneology vocabulary customization, robust noise suppression).
- **LLM Reasoning:** `GPT-4o Mini` / `Gemini 2.5 Flash` (temperature 0.1, strict grounding system prompt, dynamic workflow state machines).
- **Knowledge Base (RAG):** 5 Markdown files partitioned into `prompt` mode (critical safety rules & base pricing) and `auto` mode (semantic vector retrieval).
- **Text-to-Speech (TTS):** `Eleven v3 Conversational` (~280ms latency, voice ID Jessica `cgSgspJ2msm6clMCkdW9`, pacing calibrated to 0.85x for senior cognitive comfort).

### D. Tool Calling & Webhook Connectors
- **Communication:** Outbound HTTPS POST requests from ElevenLabs cloud with JSON payload and Bearer token / HMAC authentication.
- **5 Client Tools:**
  1. `check_spa_availability(service_name, date)` → Queries real-time slot calendar in PMS.
  2. `book_spa_appointment(service_name, date, time, guest_name)` → Locks slot, creates folio, returns `SPA-XXXX`.
  3. `check_room_availability(room_type, check_in, check_out)` → Checks room inventory and total pricing.
  4. `send_sms_summary(phone_number, summary_text, id)` → Dispatches SMS/Telegram confirmation.
  5. `transfer_to_number(phone_number)` → Initiates SIP transfer to human desk.

### E. Enterprise Security & GDPR Compliance
- **Zero Retention Mode (ZRM):** Audio streams are processed strictly in volatile RAM and destroyed upon session termination.
- **Conversation History Redaction:** Automated masking of PII (national IDs, phone numbers, health notes) in log storage.
- **EU Data Residency:** All compute, model inference, and vector embeddings reside strictly within EU regions (Frankfurt / Dublin).
