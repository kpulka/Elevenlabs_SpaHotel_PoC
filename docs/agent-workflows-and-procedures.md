> **Status:** aktualny (2026-11) — tłumaczenie EN dokumentów `docs/elevenlabs_agent_workflow.md` i `docs/elevenlabs_agent_procedures.md` (wersja źródłowa: PL).
>
> **Graph scope (read this first):** the Mermaid graph in §1 describes the **designed** conversational graph (target state, ~30 states). The graph **actually deployed and live** on the agent is a minimal **workflow v3: 3 nodes** (`start` → `main_agent` → `end`) and **2 edges**, defined in `.planning/workflow/workflow_v3.json`. §2 lists the 7 procedures that are published on the live agent.

# Agent Workflows & Standard Operating Procedures (SOP) — Virtual AI Receptionist "Bukowy Dwór"

> Complete technical specification for conversation flow graphs (**ElevenLabs Agent Workflows**) and dynamic standard operating procedures (**ElevenLabs Agent Procedures**) translated to English.

---

## 1. Conversational Graph Workflow (Mermaid.js)

```mermaid
flowchart TD
    %% STYLING DEFINITIONS
    classDef startNode fill:#1B2A4A,stroke:#C9A84C,stroke-width:3px,color:#FFFFFF,font-weight:bold;
    classDef routerNode fill:#233458,stroke:#C9A84C,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef stateNode fill:#FDFAF5,stroke:#1B2A4A,stroke-width:2px,color:#1B2A4A;
    classDef toolNode fill:#E8DCC8,stroke:#C9A84C,stroke-width:2px,color:#1B2A4A,font-weight:bold;
    classDef guardNode fill:#FFF3CD,stroke:#856404,stroke-width:2px,color:#856404,font-weight:bold;
    classDef handoffNode fill:#F8D7DA,stroke:#721C24,stroke-width:2px,color:#721C24,font-weight:bold;
    classDef endNode fill:#7A9E7E,stroke:#1B2A4A,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef ragNode fill:#EBF3EB,stroke:#7A9E7E,stroke-width:2px,color:#1B2A4A;

    %% 1. START & GREETING
    START(["📞 Inbound Call / WebRTC Init\n(Inject dynamic variables: hotel_name, location)"]):::startNode
    GREETING["🗣️ Anna Greeting:\n'Good day, this is Anna, receptionist at Bukowy Dwór.\nHow may I assist you today?'"]:::stateNode
    
    START --> GREETING
    GREETING --> ROUTER{"🧠 Intent Router Node\n(NLU Classification of Guest Speech)"}:::routerNode

    %% 2. ROUTER BRANCHES
    ROUTER -->|"1. SPA / Treatment Booking"| SPA_IDENTIFY["Identify Requested Treatment:\n(e.g., sulphur bath, mud therapy, massage)"]:::stateNode
    ROUTER -->|"2. Room / Stay Booking"| ROOM_PARAMS["Collect Stay Parameters:\n(dates, party size, room tier, mobility needs)"]:::stateNode
    ROUTER -->|"3. General Inquiries (RAG)"| RAG_SEARCH["🔍 Semantic Vector Search (RAG):\n(Access, dietary menus, resort rules)"]:::ragNode
    ROUTER -->|"4. Request Human Agent"| HANDOFF_HUMAN["👤 Speak to Human Front Desk"]:::handoffNode
    ROUTER -->|"5. Medical Emergency / Distress"| EMERGENCY["🚨 Urgent Medical Distress / Pain"]:::handoffNode

    %% 3. SPA SUBSYSTEM (WITH BALNEOLOGICAL SAFETY GUARDRAIL)
    subgraph SUB_SPA ["🧖‍♀️ SPA & MEDICAL WELLNESS SUBSYSTEM"]
        SPA_IDENTIFY --> SPA_CHECK_GUARD{"Is treatment thermal or balneological?"}:::guardNode
        
        SPA_CHECK_GUARD -->|"YES (Sulphur/Mud bath)"| SPA_TRIAGE["⚠️ Medical Safety Check:\n'Do you have any acute heart conditions,\ncirculatory issues, or skin inflammation?'"]:::guardNode
        SPA_CHECK_GUARD -->|"NO (Standard massage)"| SPA_DATE_TIME["Determine Preferred Date & Time of Day"]:::stateNode
        
        SPA_TRIAGE -->|"Contraindication Detected"| SPA_REJECT["Explain Clinical Risk\n+ Recommend Doctor Consultation"]:::guardNode
        SPA_REJECT --> SPA_ALT{"Guest selects alternative?"}:::routerNode
        SPA_ALT -->|"YES"| SPA_IDENTIFY
        SPA_ALT -->|"NO (Wants Medical Staff)"| EMERGENCY

        SPA_TRIAGE -->|"No Contraindications (Safe)"| SPA_DATE_TIME
        
        SPA_DATE_TIME --> SPA_CALL_AVAIL[["🔧 TOOL: check_spa_availability(service, date)"]]:::toolNode
        SPA_CALL_AVAIL --> SPA_AVAIL_RES{"Available slots in PMS?"}:::routerNode
        
        SPA_AVAIL_RES -->|"No Open Slots"| SPA_NO_SLOTS["Propose Alternative Day or Time Window"]:::stateNode
        SPA_NO_SLOTS --> SPA_DATE_TIME

        SPA_AVAIL_RES -->|"Slots Found"| SPA_PROPOSE["Present 2-3 Concrete Options:\n'I have 10:00 AM, 2:30 PM, and 3:00 PM available. Which suits you best?'"]:::stateNode
        SPA_PROPOSE --> SPA_COLLECT["Capture Selection + Guest Full Name"]:::stateNode
        
        SPA_COLLECT --> SPA_PARAPHRASE["🗣️ Paraphrased Confirmation Gate:\n'To confirm: Sulphur Bath on August 27th at 2:30 PM for Mr. John Smith. Is that correct?'"]:::stateNode
        SPA_PARAPHRASE --> SPA_CONFIRM_CHECK{"Guest explicit agreement?"}:::routerNode
        
        SPA_CONFIRM_CHECK -->|"Correction Requested"| SPA_DATE_TIME
        SPA_CONFIRM_CHECK -->|"YES, confirmed"| SPA_BOOK_EXEC[["🔧 TOOL: book_spa_appointment(service, date, time, guest)"]]:::toolNode
        
        SPA_BOOK_EXEC --> SPA_SEND_SMS[["🔧 TOOL: send_sms_summary(phone, summary, confirmation_id)"]]:::toolNode
        SPA_SEND_SMS --> SPA_SUCCESS["🗣️ Spoken Confirmation with Booking ID:\n'Booked! Your confirmation number is SPA-4821. I have sent an SMS summary.'"]:::stateNode
    end

    %% 4. ROOMS SUBSYSTEM
    subgraph SUB_ROOMS ["🛏️ ROOM & STAY RESERVATIONS"]
        ROOM_PARAMS --> ROOM_AVAIL_EXEC[["🔧 TOOL: check_room_availability(room_type, check_in, check_out)"]]:::toolNode
        ROOM_AVAIL_EXEC --> ROOM_RES{"Inventory available?"}:::routerNode
        ROOM_RES -->|"Sold Out"| ROOM_NO_AVAIL["Propose Alternative Dates or Room Categories"]:::stateNode
        ROOM_NO_AVAIL --> ROOM_PARAMS

        ROOM_RES -->|"Available"| ROOM_PRICE_QUOTE["Quote Total Stay Price & Amenities:\n(Elevator access, step-free shower, orthopedic bed)"]:::stateNode
        ROOM_PRICE_QUOTE --> ROOM_GUEST_DATA["Collect Guest Contact & Confirmation Phone"]:::stateNode
        ROOM_GUEST_DATA --> ROOM_SMS[["🔧 TOOL: send_sms_summary(Provisional Booking ID)"]]:::toolNode
        ROOM_SMS --> ROOM_SUCCESS["🗣️ Confirm Provisional Room Reservation"]:::stateNode
    end

    %% 5. RAG KNOWLEDGE BASE
    subgraph SUB_RAG ["📚 GROUNDED KNOWLEDGE RETRIEVAL"]
        RAG_SEARCH --> RAG_EVAL{"Information verified in KB?"}:::routerNode
        RAG_EVAL -->|"YES"| RAG_ANSWER["🗣️ Calm, factual, grounded response"]:::ragNode
        RAG_EVAL -->|"NO (Missing in KB)"| RAG_UNKNOWN["'I do not have this information in my system.\nLet me connect you with the front desk to assist you.'"]:::stateNode
        RAG_UNKNOWN --> HANDOFF_HUMAN
    end

    %% 6. ESCALATIONS
    subgraph SUB_HANDOFF ["🚨 HUMAN HANDOFF & ESCALATIONS"]
        EMERGENCY --> CALL_NURSE["🗣️ 'Your health is our top priority. I am immediately connecting you to the on-duty nurse station.'"]:::handoffNode
        CALL_NURSE --> EXEC_TRANSFER_NURSE[["🔧 TOOL: transfer_to_simulated_handoff(department='dyzurka_medyczna')"]]:::handoffNode

        HANDOFF_HUMAN --> CALL_RECEPTION["🗣️ 'Certainly, I am transferring you to a receptionist now. Please hold a moment.'"]:::handoffNode
        CALL_RECEPTION --> EXEC_TRANSFER_REC[["🔧 TOOL: transfer_to_simulated_handoff(department='recepcja')"]]:::handoffNode
    end

    %% 7. WRAP-UP & TERMINATION
    SPA_SUCCESS --> WRAP_UP{"May I help with anything else?"}:::routerNode
    ROOM_SUCCESS --> WRAP_UP
    RAG_ANSWER --> WRAP_UP

    WRAP_UP -->|"YES — additional inquiry"| ROUTER
    WRAP_UP -->|"NO — that is all, thank you"| GOODBYE["🗣️ Warm Closing:\n'Thank you very much for calling. Have a wonderful day, and we look forward to welcoming you to Bukowy Dwór!'"]:::endNode
    GOODBYE --> END_SESSION(["🔴 End Call Session"]):::endNode
```

---

## 2. Catalog of 7 Enterprise Standard Operating Procedures (SOP)

| # | Procedure (published name) | Procedure ID | Trigger Condition | Business Logic & Operational Steps |
|---|---|---|---|---|
| **1** | **`procedura_anulowania_rezerwacji_spa`** | `agtprc_5301m0r0e03mfy5b2se1afbye78z` | Guest requests to cancel a scheduled spa treatment or massage. | **>2h before:** free cancellation, releases the slot in the PMS calendar.<br>**<2h before:** **50%** fee, **EXCEPT** for a sudden medical condition/pain or doctor's release (`medical_release: true`) → **0%**. Dispatches SMS summary. |
| **2** | **`procedura_zmiany_terminu_zabiegu`** | `agtprc_9001m0r0e0a5f4fv2j88e8ewz9t1` | Guest requests to move a treatment to a different hour or day. | Queries PMS slots (`check_spa_availability`) → offers 2-3 concrete options → rebooks → sends SMS with the new appointment time. Rescheduling is free of charge. |
| **3** | **`procedura_odwolania_pobytu_i_zwrotu_zadatku`** | `agtprc_0701m0r0e0gre1ra8jhh51xm1pan` | Guest cancels a room stay and asks about the 30% deposit refund. | **>14 days before:** 100% refund OR **110% Future Stay Voucher**.<br>**7–14 days before:** 50% refund OR **100% voucher** (12 months).<br>**<7 days:** non-refundable (exception: medical hospitalization → handoff to the Manager). |
| **4** | **`procedura_wczesnego_przyjazdu_i_poznego_wyjazdu`** | `agtprc_3701m0r0e0qnfpf9ysz2g5a62trs` | Arriving before 3:00 PM (e.g. morning train) or departing after 11:00 AM. | **Early check-in:** free luggage storage + free access to thermal pools and dining from 9:00 AM; room early for free if already cleaned.<br>**Late check-out:** until 2:00 PM — **50 PLN**; until 6:00 PM — **100 PLN** (subject to availability). |
| **5** | **`procedura_zgloszenia_diety_leczniczej`** | `agtprc_8001m0r0e0yff679gj7sxvdgd1sk` | Guest reports diabetes, a light/easily digestible diet, or a gluten- and dairy-free diet. | Three medical diets are included in the stay at no extra charge under clinical dietitian supervision. The gluten- and dairy-free menu must be registered at least 3 days before arrival. Communicates meal times. |
| **6** | **`procedura_zamowienia_transportu_i_meleksa`** | `agtprc_7001m0r0e15kfv28bnc9x9x3p11t` | Guest requests pickup from the Krynica-Zdrój train/bus station or an electric golf cart on premises. | Free dedicated electric shuttle (melex) for resort guests, available 24h. Logs arrival time, luggage count, wheelchair/mobility aid details → sends SMS with the driver's direct contact. |
| **7** | **`procedura_reklamacji_i_trudnego_goscia`** | `agtprc_1801m0r0e1c1enmvsrcttyh36jq7` | Guest is dissatisfied, reports a technical defect, noise, or a service issue. | Active listening without interrupting → genuine institutional apology → immediate service ticket dispatched → complimentary herbal tea / salt cave pass and handoff to the Duty Manager. |

> IDs are the published procedure IDs stored in `.planning/workflow/procedure_ids.json`.
