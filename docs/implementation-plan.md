# Implementation Plan: AI Voice Receptionist "Anna" for the Bukowy Dwór Health Resort

> Defines the technical configuration, integrations, compliance controls and operating steps for the Anna voice receptionist on the ElevenLabs Agents platform.

This document is the canonical implementation plan for deploying the Anna voice assistant at the Uzdrowisko Termalne "Bukowy Dwór" health resort in Krynica-Zdrój. It combines the business requirements and the needs of the target audience (guests aged 60+) with the technical capabilities of the **ElevenLabs Agents** platform (Conversational AI).

The plan is designed for rapid deployment through the **ElevenLabs MCP (Model Context Protocol) agent**, which translates the instructions and JSON schemas into a ready configuration in the ElevenLabs workspace.

---

## 1. System Architecture and Conversation Flow

### 1.1. Design choice: native Conversational Agent
To eliminate the cumulative latency of traditional cascaded systems (STT → LLM → TTS), which exceeds 2 seconds and prevents natural dialogue, we use the integrated **ElevenLabs Agents** engine.

For the PoC phase and the target deployment we do not use external LLM pipelines. Instead we use the native ElevenLabs conversational model, which handles speech detection, reasoning and synthesis in a single, unified conversational loop.

### 1.2. Model selection and latency
* **Speech-to-Text (STT):** **Scribe v2 Realtime**. A speech transcription model with a latency of approximately **150 ms**, supporting Polish and automatic voice activity detection (VAD).
* **Language Model (LLM):** the language model integrated in the ElevenLabs workspace (for example GPT-4o Mini or Gemini 2.5 Flash, to reduce operating costs).
* **Text-to-Speech (TTS):** **Eleven v3 Conversational**. This model increases speech synthesis latency to approximately **280 ms** (compared with 75 ms for the Flash model), but provides **considerably higher emotional expressiveness, natural intonation and tonal depth**. This is essential for building trust, warmth and a sense of security among senior guests (60+).

---

## 2. UX and Acoustic Parameters Tailored to Seniors (60+)

Senior guests need a slower speaking pace, more time to formulate their thoughts and a stable voice without aggressive modulation. The agent configuration applies the following acoustic guidelines:

### 2.1. Turn-taking dynamics
* **turn_timeout (Take turn after silence):** set to **3.0 seconds** (the default is typically 1.0–1.5 seconds). This prevents the agent from interrupting senior guests and gives them time to breathe or to recall details (for example a date of birth or the name of a treatment).
* **turn_eagerness (Turn-taking eagerness):** configured in **`Patient`** mode. Ideal for collecting structured data (first name, last name, date), it avoids interrupting natural conversational pauses.

### 2.2. Voice character and TTS (the "Anna" voice)
The persona is named **Anna** and is given a warm, soothing female voice. For the PoC we recommend a professional, highly empathetic narrator voice, for example **Jessica: Playful, Bright, Warm** (premade voice, ID: `cgSgspJ2msm6clMCkdW9`), or a dedicated voice created in **Voice Design** from a text description.

* **Stability:** **0.80** (recommended range: 0.60–0.85). A high value prevents unnatural squeaks, whispering or emotional distortion, and ensures a consistent, calm tone.
* **Similarity Boost:** **0.75**. An optimal setting that ensures the highest clarity and fidelity to the reference voice.
* **Speed Control:** **0.85x**. Speech is slowed by 15% relative to the standard pace, so that senior guests can easily understand the instructions and prices the agent provides.

### 2.3. Pronunciation dictionary (PLS)
To prevent incorrect and unnatural pronunciation of proper names and medical terms, a PLS (XML) pronunciation dictionary is attached to the agent:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0" 
         xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.w3.org/2005/01/pronunciation-lexicon 
                             http://www.w3.org/TR/PRONUNCIATION-LEXICON/pls.xsd"
         alphabet="ipa" xml:lang="pl-PL">
         
  <lexeme>
    <grapheme>Bukowy Dwór</grapheme>
    <phoneme>buˈkɔvɨ dvuːr</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>Krynica-Zdrój</grapheme>
    <phoneme>krɨˈɲit͡sa zdruj</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>borowinowe</grapheme>
    <phoneme>bɔrɔvʲiˈnɔvɛ</phoneme>
  </lexeme>
</lexicon>
```

---

## 3. Knowledge Base (RAG) and Prevention of Hallucinations

The agent is grounded in five prepared Markdown files, stored in `agent/knowledge_base/`: general information and directions, SPA treatments, rooms and pricing, restaurant and diets, and procedures and policies. They are integrated into the ElevenLabs workspace according to their size and purpose:

### 3.1. Usage modes (`usage_mode`)
* **`prompt` mode (full context):** for small, critical files that must be available word for word in every turn of the conversation:
    * `05_procedures_and_policies.md` (cancellations, refund policy, SMS messages).
    * `03_rooms_and_pricing.md` (room prices, deposit rules).
    * *Rationale:* we avoid the risk that the RAG engine skips a critical procedure or price during retrieval. The combined size of these files must not exceed 300,000 characters.
* **`auto` mode (semantic search / RAG):** for extensive descriptive documents:
    * `01_general_info_and_directions.md`
    * `02_spa_treatments_and_health.md`
    * `04_restaurant_and_diets.md`
    * *Rationale:* the system dynamically injects only the best-matching fragments (chunks) into the system prompt, preserving the LLM context window.

### 3.2. Strict Grounding rules in the system prompt
To eliminate hallucinations completely (for example invented SPA prices or invented room availability), the agent's instructions, under the `system_prompt` key, define firm safety rules:

```text
ZASADY BEZWZGLĘDNE (STRICT GROUNDING):
1. Twoje odpowiedzi muszą być w 100% oparte na dostarczonej Bazie Wiedzy oraz wynikach wywołań narzędzi.
2. Jeśli gość pyta o ceny, pakiety, dostępność lub dojazd, a nie ma tych informacji w bazie wiedzy, odpowiedz dokładnie: „Przepraszam, ale nie mam w tej chwili dostępu do tych informacji. Połączę Państwa z Recepcją, gdzie otrzymają Państwo dokładną odpowiedź.” i natychmiast wywołaj narzędzie transfer_to_human.
3. Nigdy nie wymyślaj cen, terminów zabiegów, diet ani procedur. Uzdrowisko dba o zdrowie seniorów, więc informacje muszą być absolutnie precyzyjne.
```

*Translation of the rules:* (1) Responses must be based 100% on the knowledge base and tool results. (2) If a guest asks about prices, packages, availability or directions and the information is not in the knowledge base, the agent apologises, states that it does not currently have access to this information, says it will connect the guest to Reception for an exact answer, and immediately calls `transfer_to_human`. (3) Never invent prices, treatment times, diets or procedures. The resort looks after seniors' health, so information must be absolutely precise.

---

## 4. Tools and API Integrations (Canonical Set)

All tools are defined directly in the agent configuration using the standard **JSON Schema** format.

### 4.1. Webhook tools (simulated PMS integration)
During the demonstration the data is mocked, but the background call flow is fully realistic. The integration with a PMS (for example *KWHotel* or *Opera*) is implemented as a set of HTTP POST webhook requests, which send parameters and receive a response from a static JSON mock:

#### Tool 1: `check_spa_availability`
* **Role:** check free time slots for a selected SPA treatment.
* **JSON Schema:**
```json
{
  "name": "check_spa_availability",
  "description": "Sprawdza dostępność zabiegu SPA lub rehabilitacyjnego w wybranym dniu.",
  "parameters": {
    "type": "object",
    "properties": {
      "service_name": {
        "type": "string",
        "description": "Nazwa zabiegu (np. kąpiel borowinowa, masaż klasyczny)."
      },
      "date": {
        "type": "string",
        "description": "Data w formacie YYYY-MM-DD."
      }
    },
    "required": ["service_name", "date"]
  }
}
```

#### Tool 2: `book_spa_appointment`
* **Role:** book a treatment in the hotel system for a specific guest at a specific time.
* **JSON Schema:**
```json
{
  "name": "book_spa_appointment",
  "description": "Dokonuje rezerwacji zabiegu SPA dla gościa na konkretny termin.",
  "parameters": {
    "type": "object",
    "properties": {
      "service_name": { "type": "string" },
      "date": { "type": "string", "description": "YYYY-MM-DD" },
      "time": { "type": "string", "description": "Format HH:MM" },
      "guest_name": { "type": "string", "description": "Imię i nazwisko gościa." }
    },
    "required": ["service_name", "date", "time", "guest_name"]
  }
}
```

#### Tool 3: `check_room_availability`
* **Role:** query the PMS for rooms available in a selected period.
* **JSON Schema:**
```json
{
  "name": "check_room_availability",
  "description": "Sprawdza dostępność pokoi w wybranym przedziale czasowym.",
  "parameters": {
    "type": "object",
    "properties": {
      "room_type": { "type": "string", "enum": ["jednoosobowy", "dwuosobowy", "apartament"] },
      "check_in": { "type": "string", "description": "YYYY-MM-DD" },
      "check_out": { "type": "string", "description": "YYYY-MM-DD" }
    },
    "required": ["room_type", "check_in", "check_out"]
  }
}
```

---

### 4.2. Information / SMS gateway (PoC: Telegram / WhatsApp bot webhook)
To make a strong impression during the demonstration, the `send_sms_summary` tool is configured to send an HTTP request in the background to a **Telegram** or **WhatsApp** bot.

During a live conversation, when Anna says "*Właśnie wysłałam Panu podsumowanie na telefon*" (*"I have just sent you the summary on your phone"*), a formatted reservation message appears immediately in the Telegram channel shown on a secondary display or projector.

#### Tool 4: `send_sms_summary` (implemented via a Messenger webhook)
* **JSON Schema:**
```json
{
  "name": "send_sms_summary",
  "description": "Wysyła podsumowanie rezerwacji pokoju lub SPA bezpośrednio na telefon gościa.",
  "parameters": {
    "type": "object",
    "properties": {
      "phone_number": { "type": "string", "description": "Numer telefonu gościa (np. +48123456789)." },
      "summary_text": { "type": "string", "description": "Treść podsumowania (np. 'Rezerwacja kąpieli borowinowej: 25.08 o godz. 14:00. Zapraszamy!')" }
    },
    "required": ["phone_number", "summary_text"]
  }
}
```
* **Phase II target:** integration with the production **Twilio SMS** API.

---

### 4.3. Human Handoff (telephone call transfer)
The ElevenLabs platform supports native transfer of an active telephone call through the system tool **`transfer_to_number`**.

* **PoC / demonstration implementation:** the tool is configured with a designated staff mobile number used during the demonstration. When a call is escalated (for example for difficult medical questions or a report of feeling unwell), the agent says: "*Łączę z dyżurnym fizjoterapeutą...*" (*"I am connecting you with the on-duty physiotherapist..."*), and the designated phone rings immediately, taking over the call live.
* **System tool JSON schema:**
```json
{
  "name": "transfer_to_human",
  "description": "Natywne przekierowanie połączenia na zdefiniowany numer recepcji lub dyżurki medycznej.",
  "parameters": {
    "type": "object",
    "properties": {
      "department": { "type": "string", "enum": ["recepcja", "dyzurka_medyczna"] },
      "reason": { "type": "string", "description": "Powód przekazania rozmowy." }
    },
    "required": ["department", "reason"]
  }
}
```
* **Routing logic (Phase II):**
    * If `department == "recepcja"` → transfer to the hotel's main PBX number.
    * If `department == "dyzurka_medyczna"` → transfer to a dedicated medical line / nursing duty room.

---

## 5. Scaling Across a Hotel Network (Multi-Property)

To scale the solution across a network of SPA hotels without duplicating and maintaining dozens of independent agents, we implement an architecture based on **Dynamic Variables** and **Overrides**.

### 5.1. One parent agent with dynamic overrides
We create one central agent, "Anna". When a telephone call is established (through a SIP trunk from the PBX) or a WebSocket widget is opened, the system sends the initialisation payload `conversation_initiation_client_data`, which contains context variables specific to each property:

```json
{
  "type": "conversation_initiation_client_data",
  "conversation_config_override": {
    "agent": {
      "prompt": {
        "system_prompt": "Jesteś recepcjonistką w hotelu {{hotel_name}} w miejscowości {{location}}. Kontakt do nas to {{reception_phone}}."
      }
    }
  },
  "dynamic_variables": {
    "hotel_name": "Bukowy Dwór - Skrzydło Termalne",
    "location": "Krynica-Zdrój",
    "reception_phone": "+48 18 123 45 67",
    "pms_hotel_id": "HOTEL_001_A"
  }
}
```

*Translation of the `system_prompt` template:* "You are the receptionist at the {{hotel_name}} hotel in {{location}}. You can reach us at {{reception_phone}}."

### 5.2. Passing metadata in SIP signalling (RFC 7433)
For telephone calls, the hotel PBX passes the caller identifier and the hotel ID directly in the SIP signalling, using **UUI (User-to-User Information, RFC 7433)** headers. The ElevenLabs server reads this data (up to 256 bytes) and automatically applies the corresponding configuration overrides, matching the knowledge base and the assistant's behaviour in real time.

---

## 6. Enterprise Compliance, GDPR and Security

A key challenge in the health-resort sector is the processing of personal data (GDPR) and sensitive medical data (health status, contraindications for rehabilitation treatments).

### 6.1. Protecting API keys: Signed URLs
To embed the interactive widget on the resort's website, the client application must not communicate directly using the developer's main API key, because of the risk of key theft and unlimited costs.

* **Authorisation process:** the hotel server (a secure environment) sends a request to the ElevenLabs `/get_signed_url` API. In response it receives a signed token valid for **15 minutes**. The WebSocket connection is established using this temporary URL, which keeps the infrastructure secure.

### 6.2. GDPR position for stakeholder briefings (Enterprise Plan)
When presenting to client stakeholders, the team should explain how ElevenLabs protects guest data:

1.  **Zero Retention Mode (ZRM):** once this mode is activated on the Enterprise plan, audio files and generated transcripts are processed exclusively in RAM and are **never** written to ElevenLabs' hard disks.
2.  **Conversation History Redaction:** if the resort wants to keep conversation statistics and analyse trends, the history redaction mode is activated. The system automatically detects and masks sensitive personal data (surnames, phone numbers, reservation numbers) and medical terms with asterisks.
3.  **Data Residency:** a guarantee that data is processed within the European Union (servers in the EU region), for full compliance with the DPA and GDPR.

---

## 7. Cost and Operating Limits Analysis

| Parameter | PoC environment (tests and demo) | Production scale (Enterprise deployment) |
| :--- | :--- | :--- |
| **Recommended plan** | **Creator** ($22/month) | **Enterprise / Scale** ($299/month) |
| **Included minutes** | **275 minutes** | **3 738 minutes** |
| **Overage cost per minute** | $0.080 | $0.080 (negotiable at scale) |
| **Concurrent call limit** | **10 concurrent calls** | **30 concurrent calls** |
| **Peak traffic handling** | Standard limit | **Burst Pricing** (3x concurrency, up to 90 concurrent calls; additional calls billed at $0.160/min) |
| **Team access** | 1 account | 3 Workspace seats (Scale) / dedicated permission management |

---

## 8. Execution Guidelines for the MCP Agent

*Instructions for the MCP agent that configures the receptionist automatically in ElevenLabs.*

> **Correction (verified against the live ElevenLabs MCP server).** The MCP `create_agent` tool does NOT support: webhook tool calling, `turn_eagerness`, `speed`, or the knowledge base `usage_mode` settings. The split between what can be done through MCP and what requires the ElevenLabs workspace or the full API is described below.

### 8.1. What the MCP `create_agent` call does
1. **Create the agent** named `Bukowy_Dwor_Anna` (or `Anna`) with the following parameters:
   * `language: "pl"`
   * `temperature: 0.1` (strictness, minimised creativity)
   * `stability: 0.80`, `similarity_boost: 0.75`
   * `turn_timeout: 3` (in seconds; the MCP parameter is an integer)
   * `model_id: eleven_v3_conversational` (verify availability with `list_models`)
   * `voice_id: cgSgspJ2msm6clMCkdW9` (Jessica: Playful, Bright, Warm)
   * `first_message` and `system_prompt` = the content of `agent/system_prompt.md`

### 8.2. Knowledge base: conversion and constraints
* The MCP `add_knowledge_base_to_agent` tool accepts only **epub / pdf / docx / txt / html**, NOT `.md`.
* **Step 1:** convert the 5 files in `agent/knowledge_base/*.md` to `.txt` (UTF-8 encoding).
* **Step 2:** add them to the agent through MCP (one call per file; use the `text` or `input_file_path` field).
* **Constraint:** the split between `prompt` and `auto` modes (`usage_mode`) is NOT available through MCP. Set it in the ElevenLabs workspace (Knowledge Base → mode per file), if required.

### 8.3. What requires the ElevenLabs workspace or the full API (outside MCP)
* **Tool calling (4 webhooks + `transfer_to_number`):** register the tools from their JSON Schemas (§4) manually in the agent workspace → Tools section. Webhook URL: `http://localhost:8000/{endpoint}` (local PoC) or a public tunnel address (for example via ngrok). See `mock_backend/README.md`.
* **`turn_eagerness: Patient`:** set in the workspace (Conversation → Turn-taking); this parameter is not available through MCP.
* **`speed: 0.85`:** set in the agent's voice section in the workspace (not available through MCP).
* **Pronunciation dictionary (PLS, §2.3):** attach in the workspace (not through MCP).

### 8.4. Execution order
1. Convert the 5 files from `.md` to `.txt`.
2. MCP `create_agent` (voice, system prompt, acoustic parameters).
3. MCP `add_knowledge_base_to_agent` (5 `.txt` files).
4. Workspace / API: tool calling, `turn_eagerness`, `speed`, PLS.
5. Start the mock backend (`uvicorn main:app --port 8000`) and a public tunnel for the webhooks.
