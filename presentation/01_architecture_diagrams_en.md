# Architecture Diagrams — Virtual AI Receptionist "Bukowy Dwór"

> Production-ready Mermaid.js diagrams translated to English for presentation slides, technical documentation, system design reviews, and Excalidraw whiteboarding.

---

## DIAGRAM 1 — High-Level Conversational Flow (Unified AI Loop)

```mermaid
flowchart LR
    CALLER(["📞 Hotel Guest Calling\n(Senior 60+)"])

    subgraph EL ["☁️ ElevenLabs Conversational AI (EU Cloud)"]
        STT["🎙️ STT Engine\nScribe v2 Realtime\n~150 ms"]
        LLM["🧠 LLM Orchestrator\nGPT-4o Mini / Gemini 2.5\ntemp: 0.1 (Strict Grounding)"]
        TTS["🔊 TTS Engine\nEleven v3 Conversational\n~280 ms, 0.85x speed"]
        KB[("📚 Vector RAG Knowledge Base\n5 Curated Markdown Files")]
        TOOLS["🔧 Tool Calling Engine\n4 HTTPS Webhooks"]
    end

    subgraph BACKEND ["🖥️ PMS & Telephony Gateway"]
        PMS["📋 Hotel PMS Gateway\ncheck_spa_availability\nbook_spa_appointment\ncheck_room_availability"]
        SMS["📱 SMS & Messaging Gateway\nsend_sms_summary\n(Twilio / Telegram)"]
    end

    HUMAN(["👤 On-Duty Human Staff\nFront Desk / Nurse Desk\nSIP REFER Transfer"])

    CALLER -->|"Voice stream (Opus)"| STT
    STT -->|"Real-time text transcript"| LLM
    LLM <-->|"Semantic vector search"| KB
    LLM -->|"Deterministic tool execution"| TOOLS
    TOOLS <-->|"HTTPS POST (JSON)"| PMS
    TOOLS <-->|"HTTPS POST (JSON)"| SMS
    LLM -->|"Streamed response tokens"| TTS
    TTS -->|"Synthesized speech audio"| CALLER
    LLM -->|"Escalation trigger"| HUMAN
```

---

## DIAGRAM 2 — Detailed Sequence Diagram (SPA Booking & Tool Invocation)

```mermaid
sequenceDiagram
    autonumber
    actor Guest as 👴 Guest (Senior 60+)
    participant Phone as 📞 WebRTC / SIP Phone
    participant STT as 🎙️ STT (Scribe v2)
    participant LLM as 🧠 LLM Orchestrator
    participant RAG as 📚 Vector RAG KB
    participant Tools as 🔧 Tool Calling
    participant PMS as 🏨 Hotel PMS Gateway
    participant SMS as 📲 SMS Gateway
    participant TTS as 🔊 TTS (Eleven v3)

    Guest->>Phone: "Hello, I would like to book a mud bath for tomorrow..."
    Phone->>STT: Stream audio frames (Opus codec)
    STT->>LLM: Streamed transcript (~150 ms)
    LLM->>RAG: Semantic search (02_katalog_zabiegow_spa_i_zdrowie.md)
    RAG-->>LLM: Match: "Thermal Mud Bath, 30 min, 130 PLN. Check cardiac contraindications."
    LLM->>TTS: "Certainly. Before checking times, do you have any heart conditions or acute inflammation?"
    TTS-->>Guest: Warm spoken voice (~280 ms)
    Guest->>Phone: "No, my doctor approved it."
    Phone->>STT: Audio stream
    STT->>LLM: "No, doctor approved"
    LLM->>Tools: check_spa_availability(service_name="kąpiel borowinowa", date="2026-08-25")
    Tools->>PMS: POST /check_spa_availability
    PMS-->>Tools: {"available": true, "slots": ["10:00", "14:30", "15:00"]}
    Tools-->>LLM: Available slots injected into context
    LLM->>TTS: "I have openings tomorrow at 10:00 AM, 2:30 PM, and 3:00 PM. Which works best?"
    TTS-->>Guest: Spoken audio
    Guest->>Phone: "Two thirty, please. My name is John Smith."
    Phone->>STT: Audio stream
    STT->>LLM: "Two thirty, John Smith"
    LLM->>TTS: "Splendid. To confirm: Mud Bath on August 25th at 2:30 PM for Mr. John Smith. Is that correct?"
    TTS-->>Guest: Paraphrased confirmation
    Guest->>Phone: "Yes, exactly."
    Phone->>STT: Audio stream
    STT->>LLM: "Yes"
    LLM->>Tools: book_spa_appointment(service="kąpiel borowinowa", date="2026-08-25", time="14:30", guest_name="John Smith")
    Tools->>PMS: POST /book_spa_appointment
    PMS-->>Tools: {"success": true, "confirmation_id": "SPA-4821"}
    LLM->>Tools: send_sms_summary(phone="+48600111222", summary="Mud Bath booked for 2:30 PM", id="SPA-4821")
    Tools->>SMS: POST /send_sms_summary
    SMS-->>Tools: {"delivered": true}
    LLM->>TTS: "You are all set! Your booking number is SPA-4821. I have sent an SMS summary to your phone."
    TTS-->>Guest: Final confirmation
```

---

## DIAGRAM 3 — Medical Escalation Protocol (Strict Grounding & Safety)

```mermaid
flowchart TD
    QUERY["🗣️ Guest Inbound Query"] --> CHECK{"Clinical Safety Check:\n1. Emergency Symptoms (chest pain, shortness of breath)?\n2. Balneology Contraindications?\n3. Answer completely missing from RAG?"}

    CHECK -->|"YES — Emergency Symptom"| NURSE["🚨 Protocol A: Medical Emergency\n1. Empathetic reassuring message\n2. Immediate priority SIP transfer to Nurse Desk"]
    CHECK -->|"YES — Missing RAG Info"| FRONTDESK["👤 Protocol B: Human Handoff\n1. Transparent explanation\n2. Warm transfer to Front Desk"]
    CHECK -->|"NO — Grounded In Knowledge Base"| SAFE["✅ Normal Conversational Flow\nDirect grounded response from curated KB"]

    NURSE --> TRANSFER_NURSE[["🔧 transfer_to_number(+48 18 123 45 99)"]]
    FRONTDESK --> TRANSFER_REC[["🔧 transfer_to_number(+48 18 123 45 67)"]]
```

---

## DIAGRAM 4 — Multi-Tenant Hotel Chain Scaling (Sub-Linear Architecture)

```mermaid
flowchart TD
    subgraph INBOUND_NUMBERS ["Inbound Phone Lines per Hotel Property"]
        H1["Hotel 1: Krynica-Zdrój\n+48 18 100 00 01"]
        H2["Hotel 2: Szczawnica\n+48 18 100 00 02"]
        H3["Hotel 3: Ciechocinek\n+48 54 100 00 03"]
    end

    subgraph TELEPHONY ["PBX / SIP Trunking (Twilio / Kamailio)"]
        SIP_HEADER["Inject RFC 7433 SIP UUI Header:\nUser-to-User: hotel_id=H1;lang=pl;currency=PLN"]
    end

    subgraph ELEVENLABS ["ElevenLabs Conversational AI Engine"]
        MASTER_AGENT["🧠 1 Master Agent Core (Anna)\nDynamic Context Injection via Variables"]
    end

    subgraph DATA_SOURCES ["Multi-Tenant Knowledge & PMS Layer"]
        PMS_MULTI["🏨 Central PMS API / Database Router\nQueries partition based on hotel_id"]
    end

    H1 & H2 & H3 --> SIP_HEADER
    SIP_HEADER --> MASTER_AGENT
    MASTER_AGENT <--> PMS_MULTI
```

---

## DIAGRAM 5 — Complete End-to-End Enterprise Tech Stack

```mermaid
flowchart TB
    classDef clientLayer fill:#1B2A4A,stroke:#C9A84C,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef edgeLayer fill:#233458,stroke:#C9A84C,stroke-width:2px,color:#FFFFFF;
    classDef aiCore fill:#FDFAF5,stroke:#1B2A4A,stroke-width:3px,color:#1B2A4A,font-weight:bold;
    classDef aiSub fill:#EBF3EB,stroke:#7A9E7E,stroke-width:2px,color:#1B2A4A;
    classDef webhookLayer fill:#E8DCC8,stroke:#C9A84C,stroke-width:2px,color:#1B2A4A,font-weight:bold;
    classDef backendLayer fill:#FFFFFF,stroke:#1B2A4A,stroke-width:2px,color:#1B2A4A;
    classDef pmsLayer fill:#FFF3CD,stroke:#856404,stroke-width:2px,color:#856404,font-weight:bold;
    classDef secLayer fill:#F8D7DA,stroke:#721C24,stroke-width:2px,color:#721C24;

    subgraph INBOUND ["📱 1. OMNICHANNEL INBOUND CHANNELS"]
        direction LR
        PHONE["☎️ Telephony PSTN / GSM / VoLTE"]:::clientLayer
        SIP_TRUNK["🏢 Hotel PBX Central Switch\n(Twilio / Asterisk / FreePBX)\nSIP Trunking RFC 3261"]:::clientLayer
        WEB_CLIENT["💻 Web / Mobile WebRTC App\n(Next.js 16 + React 19)\n@elevenlabs/convai-widget-embed"]:::clientLayer
        PHONE -->|"G.711 / Opus Audio"| SIP_TRUNK
    end

    subgraph EDGE ["🔒 2. EDGE GATEWAY & SECURITY"]
        direction TB
        SIP_URI["ElevenLabs SIP Gateway\nsip:agent_id@sip.elevenlabs.io\n+ SIP UUI RFC 7433 Headers"]:::edgeLayer
        SIGNED_URL_API["Next.js Route Handler\nGET /api/anna/signed-url\n(15-min TTL Signed Tokens)"]:::edgeLayer
        SEC_POL["Security & Compliance:\n• Zero Retention Mode (ZRM)\n• EU Data Residency (Frankfurt)\n• Automated PII Redaction"]:::secLayer
    end

    SIP_TRUNK -->|"SIP / TLS + SRTP"| SIP_URI
    WEB_CLIENT -->|"Fetch Signed URL"| SIGNED_URL_API
    SIGNED_URL_API -->|"WSS Secure Handshake"| WSS_CONN

    subgraph AI_CORE ["⚡ 3. ELEVENLABS CONVERSATIONAL AI ENGINE (EU CLOUD)"]
        direction TB
        WSS_CONN["🌐 Transport Layer:\nWebSockets / WebRTC Opus Audio"]:::aiSub
        
        subgraph LOOP ["Unified Conversational Loop (~430ms)"]
            STT["🎙️ STT: Scribe v2 Realtime\n• Latency: ~150ms\n• Acoustic Model: pl-PL with VAD\n• Background Noise Suppression"]:::aiSub
            ORCHESTRATOR["🧠 LLM Orchestrator & State Machine\n• Model: GPT-4o Mini / Gemini 2.5 Flash\n• Temp: 0.1 (Strict Grounding)\n• Dynamic Workflows & SOP Procedures"]:::aiCore
            TTS["🔊 TTS: Eleven v3 Conversational\n• Latency: ~280ms\n• Voice ID: Jessica (Warm/Calm)\n• Speed: 0.85x (Senior Acoustic Tuning)"]:::aiSub
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
        ORCHESTRATOR <-->|"Semantic search & prompt injection"| RAG_KB
    end

    SIP_URI --> WSS_CONN
    WSS_CONN --> STT
    TTS --> WSS_CONN
    WSS_CONN -->|"Full-duplex audio stream"| WEB_CLIENT
    WSS_CONN -->|"Full-duplex audio stream"| SIP_TRUNK

    subgraph INTEGRATION ["🔧 4. TOOL CALLING & INTEGRATION LAYER"]
        direction TB
        TOOL_ROUTER["Tool Dispatcher (Client Tools)\nHTTPS POST + Bearer Auth"]:::webhookLayer
        subgraph TOOLS ["Registered Tools"]
            T1["check_spa_availability"]:::webhookLayer
            T2["book_spa_appointment"]:::webhookLayer
            T3["check_room_availability"]:::webhookLayer
            T4["send_sms_summary"]:::webhookLayer
            T5["transfer_to_number"]:::webhookLayer
        end
        TOOL_ROUTER --> T1 & T2 & T3 & T4 & T5
    end

    ORCHESTRATOR -->|"Tool invocation trigger (JSON Schema)"| TOOL_ROUTER
    TOOL_ROUTER -->|"JSON payload response"| ORCHESTRATOR

    subgraph BACKEND ["🏨 5. HOSPITALITY BACKEND, PMS & COMMUNICATIONS"]
        direction TB
        FASTAPI_GW["PMS Gateway: FastAPI Server\n• Uvicorn ASGI Server\n• Pydantic v2 Validation\n• ngrok / Cloudflare Tunnel"]:::backendLayer
        PMS_CORE["Hotel PMS / ERP Database\n(Opera Cloud / Mews / Protel)\n• Spa treatment schedules\n• Room inventory & folio management"]:::pmsLayer
        SMS_GW["Messaging & Notification Gateways\n• Twilio / SMSAPI REST API\n• Telegram Bot API"]:::backendLayer
        HUMAN_ESC["Human Staff Escalation\n• Front Desk: +48 18 123 45 67\n• Nurse Station: +48 18 123 45 99\n(SIP REFER Transfer)"]:::pmsLayer
    end

    T1 & T2 & T3 & T4 -->|"HTTPS POST Webhooks"| FASTAPI_GW
    FASTAPI_GW <-->|"SQL / REST API"| PMS_CORE
    FASTAPI_GW -->|"HTTP POST"| SMS_GW
    T5 -->|"SIP REFER Handoff"| HUMAN_ESC
```
