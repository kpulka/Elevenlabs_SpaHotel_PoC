# Diagramy Architektury — Wirtualny Recepcjonista AI „Bukowy Dwór"

Gotowe diagramy Mermaid do wklejenia na slajdy lub do Excalidraw.

---

## DIAGRAM 1 — Główny przepływ konwersacyjny (High-level, na slajd tytułowy)

```mermaid
flowchart LR
    CALLER(["📞 Gość dzwoni\n(senior 60+)"])

    subgraph EL ["☁️ ElevenLabs Conversational AI"]
        STT["🎙️ STT\nScribe v2 Realtime\n~150 ms"]
        LLM["🧠 LLM\nGPT-4o Mini\ntemp: 0.1"]
        TTS["🔊 TTS\nEleven v3 Conversational\n~280 ms"]
        KB[("📚 Baza Wiedzy RAG\n5 plików Markdown")]
        TOOLS["🔧 Tool Calling\n4 webhooki"]
    end

    subgraph BACKEND ["🖥️ Mock Backend (PoC)"]
        PMS["📋 PMS Mock\ncheck_spa_availability\nbook_spa_appointment\ncheck_room_availability"]
        SMS["📱 SMS / Telegram\nsend_sms_summary"]
    end

    HUMAN(["👤 Recepcja\ntransfer_to_number"])

    CALLER -->|"mowa"| STT
    STT -->|"transkrypcja"| LLM
    LLM <-->|"semantic search"| KB
    LLM -->|"wywołanie narzędzia"| TOOLS
    TOOLS <-->|"HTTP POST"| PMS
    TOOLS <-->|"HTTP POST"| SMS
    LLM -->|"tekst odpowiedzi"| TTS
    TTS -->|"synteza mowy"| CALLER
    LLM -->|"eskalacja"| HUMAN
```

---

## DIAGRAM 2 — Szczegółowy przepływ danych (System Design, na slajd techniczny)

```mermaid
sequenceDiagram
    actor Gość as 👴 Gość (senior)
    participant Phone as 📞 Telefon / WebRTC
    participant STT as 🎙️ STT (Scribe v2)
    participant LLM as 🧠 LLM (GPT-4o Mini)
    participant RAG as 📚 RAG / KB
    participant Tools as 🔧 Tool Calling
    participant Mock as 🖥️ Mock Backend
    participant TTS as 🔊 TTS (Eleven v3)

    Gość->>Phone: "Dzień dobry, chciałbym zarezerwować masaż..."
    Phone->>STT: stream audio (WebRTC)
    STT->>LLM: transkrypcja (~150 ms)
    LLM->>RAG: semantic search — katalog zabiegów
    RAG-->>LLM: fragment: "Masaż leczniczy pleców, 30 min, 120 PLN"
    LLM->>Tools: check_spa_availability("masaż leczniczy pleców", "2026-08-27")
    Tools->>Mock: POST /check_spa_availability
    Mock-->>Tools: {slots: ["10:00","14:30","15:00"]}
    Tools-->>LLM: dostępne godziny
    LLM->>TTS: "Mam dostępne: 10:00, 14:30 i 15:00. Która godzina Panu odpowiada?"
    TTS->>Phone: synteza mowy (~280 ms)
    Phone->>Gość: odpowiedź Anny

    Note over Gość,TTS: Łączna latencja: ~430 ms (STT+TTS) + czas LLM

    Gość->>Phone: "Poproszę 14:30"
    Phone->>STT: stream audio
    STT->>LLM: transkrypcja
    LLM->>Tools: book_spa_appointment(...)
    Tools->>Mock: POST /book_spa_appointment
    Mock-->>Tools: {confirmation_id: "SPA-4821", success: true}
    LLM->>Tools: send_sms_summary(phone, summary, "SPA-4821")
    Tools->>Mock: POST /send_sms_summary
    Mock-->>Tools: {success: true} + 📲 Telegram/konsola
    LLM->>TTS: "Rezerwacja potwierdzona! Numer: SPA-4821. Wysłałam potwierdzenie na telefon."
    TTS->>Phone: synteza mowy
    Phone->>Gość: finalna odpowiedź Anny
```

---

## DIAGRAM 3 — Scenariusz eskalacji (Human Handoff)

```mermaid
flowchart TD
    START(["Gość: 'Mam ból w klatce piersiowej...'"])

    CLASSIFY{"Anna klasyfikuje:\nCzy to sytuacja\nmedyczna/awaryjna?"}

    RAG_OK["Pytanie\ninformacyjne\n→ odpowiedź z RAG"]

    SAFETY{"Protokół\nbezpieczeństwa:\nZabieg balneologiczny?\nPrzeciwwskazania?"}

    HANDOFF["⚠️ Wywołuje:\ntransfer_to_human\n(natywne transfer_to_number)"]

    ANNA_MSG["Anna mówi:\n'Łączę Pana z dyżurką\nmedyczną. Chwileczkę.'"]

    NURSE(["👩‍⚕️ Dyżurka pielęgniarska\n(lub Twój telefon na demo)"])

    START --> CLASSIFY
    CLASSIFY -->|"NIE — zwykłe pytanie"| RAG_OK
    CLASSIFY -->|"TAK — sytuacja awaryjna"| HANDOFF
    RAG_OK --> SAFETY
    SAFETY -->|"NIE — bezpieczne"| RAG_OK
    SAFETY -->|"TAK — przeciwwskazanie"| HANDOFF
    HANDOFF --> ANNA_MSG
    ANNA_MSG --> NURSE
```

---

## DIAGRAM 4 — Architektura multi-hotel (skalowanie, slajd Enterprise)

```mermaid
flowchart TB
    subgraph CENTRAL ["☁️ ElevenLabs — jeden agent 'Anna'"]
        AGENT["🤖 Agent Bukowy_Dwor_Anna\n(centralny, jeden dla całej sieci)"]
        KB1[("📚 Wspólna\nBaza RAG")]
        TOOLS1["🔧 Narzędzia\n(webhook)"]
    end

    subgraph HOTEL_A ["🏨 Hotel A — Bukowy Dwór, Krynica"]
        PBX_A["📞 Centrala PBX\n(SIP Trunk)"]
        INIT_A["conversation_initiation\n{hotel_name: 'Bukowy Dwór'\nlocation: 'Krynica-Zdrój'\npms_hotel_id: 'HOTEL_001'}"]
    end

    subgraph HOTEL_B ["🏨 Hotel B — Termy Górskie, Zakopane"]
        PBX_B["📞 Centrala PBX\n(SIP Trunk)"]
        INIT_B["conversation_initiation\n{hotel_name: 'Termy Górskie'\nlocation: 'Zakopane'\npms_hotel_id: 'HOTEL_002'}"]
    end

    subgraph HOTEL_C ["🌐 Widget webowy (dowolny hotel)"]
        WEB_C["Strona www\n(signed URL, 15 min)"]
        INIT_C["conversation_initiation\n{hotel_name: '...'\ndynamic variables}"]
    end

    PBX_A -->|"SIP + UUI (RFC 7433)\nmetadane hotelu"| AGENT
    INIT_A -.->|"nadpisanie prompta\ni zmiennych"| AGENT
    PBX_B -->|"SIP + UUI (RFC 7433)"| AGENT
    INIT_B -.->|"nadpisanie prompta"| AGENT
    WEB_C -->|"WebSocket\n(Signed URL)"| AGENT
    INIT_C -.->|"dynamic_variables"| AGENT

    AGENT <--> KB1
    AGENT <--> TOOLS1
```

---

## DIAGRAM 5 — Stos technologiczny (do slajdu „Stack")

```mermaid
block-beta
  columns 3

  block:ROW1:3
    A["🎙️ STT\nScribe v2 Realtime\nlatencja: ~150 ms\njęzyk: pl-PL + VAD"]
    B["🧠 LLM\nGPT-4o Mini\ntemp: 0.1\nstrict grounding"]
    C["🔊 TTS\nEleven v3 Conversational\nlatencja: ~280 ms\nspeed: 0.85x"]
  end

  block:ROW2:3
    D["📚 Knowledge Base (RAG)\n5 plików Markdown\ntryb: prompt + auto\nstrict grounding"]
    E["🔧 Tool Calling\n4 webhooki + transfer\nJSON Schema\nmock → PMS prod"]
    F["🔐 Security\nSigned URLs\nZero Retention Mode\nData Residency EU"]
  end
```
