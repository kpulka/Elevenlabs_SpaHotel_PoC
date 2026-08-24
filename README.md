# ElevenLabs — Deployment Strategist: Repozytorium Case Study

## Cel nadrzędny
Stworzenie **prezentacji** zgodnej z wytycznymi rekrutacyjnymi z `ElevenLabs_Etap_V1.md` oraz `ElevenLabs_Etap_V2.md`.
Case study = **Wirtualny Recepcjonista AI dla hotelu & SPA** (Uzdrowisko Termalne „Bukowy Dwór").

## Architektura (aktualna)

**Platforma:** ElevenLabs Conversational AI — natywny agent (STT + LLM orchestrator + TTS w jednej pętli, bez zewnętrznego backendu LLM).  
**Persona:** Anna (głos: Jessica — Playful, Bright, Warm `cgSgspJ2msm6clMCkdW9`, model: `eleven_v3_conversational`).  
**RAG:** 5 plików Markdown — procedury i cennik w trybie `prompt`, reszta w trybie `auto` (semantic search).  
**Tool calling:** 4 webhooki (check_spa_availability, book_spa_appointment, check_room_availability, send_sms_summary) + natywne `transfer_to_number`.  
**Mock backend (PoC):** FastAPI (`mock_backend/`) — lokalne endpointy HTTP symulujące PMS i bramkę SMS.  
**Odbiorca końcowy:** seniorzy 60+ (wolne tempo, parafrazowanie, turn_timeout 3.0s, speed 0.85x).

## Mapa repozytorium

```
SpaHotels/
├── ElevenLabs_Etap_V1.md                              # Wytyczne etap 1 (rozmowa + case study)
├── ElevenLabs_Etap_V2.md                              # Wytyczne etap 2 (product/system design + HM)
│
├── .planning/                                          # ← GSD: plan implementacji
│   ├── PROJECT.md                                      # Kontekst, decyzje, epiki, konwencje
│   └── ROADMAP.md                                      # 10 faz (Epiki A-D) z DoD
│
├── mock_backend/                                       # ← Mock backend PoC (FastAPI)
│   ├── main.py                                         # 4 endpointy webhook
│   ├── requirements.txt
│   ├── README.md                                       # Instrukcja uruchomienia + curl + ngrok
│   └── data/
│       ├── spa_schedule.json
│       └── rooms.json
│
├── plan/                                               # Plan pracy (meta)
│   ├── 00_roadmapa.md                                  # ← ZACZNIJ TUTAJ — fazy + mapa plików
│   ├── 01_inwentaryzacja.md
│   └── 02_brief_dla_agenta.md
│
├── docs/                                               # Dokumentacja produktu
│   ├── architecture_and_tech_stack_en.md               # ← [EN] ENTERPRISE ARCHITECTURE & TECH STACK
│   ├── agent_workflows_and_procedures_en.md           # ← [EN] AGENT WORKFLOWS & PROCEDURES (SOP)
│   ├── plan_implementacji_recepcjonisty.md             # ← ŹRÓDŁO PRAWDY technicznej
│   ├── specyfikacja_recepcjonista_ai.md                # ← KANONICZNA spec funkcjonalna
│   ├── architektura_stack_technologiczny.md            # ← ARCHITEKTURA & STACK TECHNOLOGICZNY (Mermaid)
│   ├── elevenlabs_agent_workflow.md                    # ← WORKFLOW AGENTA (Graf stanów & Mermaid)
│   ├── elevenlabs_agent_procedures.md                  # ← PROCEDURY OPERACYJNE (SOP & Reguły biznesowe)
│   ├── anna_system_prompt.md                           # ← SYSTEM PROMPT (wklej w ElevenLabs)
│   ├── specyfikacja_poc_recepcjonista_ai.md            # ZDEPRECJONOWANY (archiwum)
│   └── baza_wiedzy_rag_bukowy_dwor/                    # 5 plików RAG
│       ├── 01_informacje_ogolne_i_dojazd.md
│       ├── 02_katalog_zabiegow_spa_i_zdrowie.md        # ← UZUPEŁNIONY (5 zabiegów)
│       ├── 03_pokoje_i_cennik.md                       # ← UZUPEŁNIONY (apartament)
│       ├── 04_restauracja_i_diety.md
│       └── 05_procedury_i_polityki.md
│
└── presentation/                                       # ← Materiały prezentacyjne
    ├── Bukowy_Dwor_Case_Study_EN.pptx                  # ← [EN] POWERPOINT PRESENTATION (14 SLIDES)
    ├── presentation_en.html                            # ← [EN] INTERACTIVE WEB PRESENTATION DECK
    ├── 01_architecture_diagrams_en.md                  # ← [EN] 5 MERMAID DIAGRAMS IN ENGLISH
    ├── 02_v1_interview_thought_process_en.md           # ← [EN] V1 INTERVIEW THOUGHT PROCESS & ROI
    ├── 00_brief_prezentacja.md                         # Brief dla AI/człowieka do zbudowania slajdów
    ├── 01_diagram_architektury.md                      # 5 diagramów Mermaid
    ├── 02_tok_myslenia_v1.md                           # V1: tok myślenia, ROI, pytania do rekrutera
    ├── 03_narracja_demo.md                             # Skrypt 3 ścieżek demo + fallbacki
    ├── 04_slajdy_outline.md                            # Outline 14 slajdów
    ├── 05_v2_problem_understanding.md                  # V2: pytania problem understanding
    ├── 06_v2_excalidraw.md                             # V2: guide Excalidraw (3 szkice)
    ├── 07_ux_design.md                                 # UX: journey map + widget + chips + błędy
    └── assets/                                         # UI mockupy & diagramy
```

## Następny krok
Otwórz plan implementacji GSD: `.planning/ROADMAP.md` (10 faz, Epiki A–D). Start od Phase 1.

## Kluczowe linki konfiguracyjne
- **System prompt gotowy:** `docs/anna_system_prompt.md`
- **Mock backend:** uruchom `uvicorn main:app --reload --port 8000` w folderze `mock_backend/`
- **Webhook URL w panelu ElevenLabs:** `http://localhost:8000/{nazwa_endpointu}` (PoC lokalny) lub publiczny URL z ngrok
