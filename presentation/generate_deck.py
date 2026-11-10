"""Generator decku rekrutacyjnego (PL i EN) — python-pptx.

Użycie:
    python presentation/generate_deck.py            # tylko PL
    python presentation/generate_deck.py --lang en  # tylko EN
    python presentation/generate_deck.py --lang all # oba decki

Wyjście:
    Bukowy_Dwor_Case_Study.pptx     (PL)
    Bukowy_Dwor_Case_Study_EN.pptx  (EN)

Teksty trzymamy w słowniku `TEXTS` (jeden wpis na język), a kod slajdów jest
wspólny — dzięki temu oba decki mają identyczny layout i te same liczby.
Źródłem treści EN jest `presentation_en.html` (utrzymywany ręcznie).
"""

import argparse
import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

NAVY = RGBColor(27, 42, 74)       # #1B2A4A
GOLD = RGBColor(201, 168, 76)     # #C9A84C
CREAM = RGBColor(245, 240, 232)   # #F5F0E8
WHITE = RGBColor(255, 255, 255)
CHARCOAL = RGBColor(44, 44, 44)   # #2C2C2C
SAGE = RGBColor(122, 158, 126)    # #7A9E7E
MUTED = RGBColor(138, 138, 138)

BRAND_LINE = "ELEVENLABS DEPLOYMENT STRATEGIST CASE STUDY"


TEXTS = {
    "pl": {
        "file": "Bukowy_Dwor_Case_Study.pptx",
        # 1 — title
        "s1_title": "Wirtualny Recepcjonista AI",
        "s1_sub": "Uzdrowisko Termalne „Bukowy Dwór” × ElevenLabs",
        "s1_tagline": "\nWdrożenie natywnego agenta konwersacyjnego dla wymagającej grupy seniorów 60+ w sieci resortów SPA.",
        "s1_badge": "Etap V1 & V2: Case Study, Product Design & System Architecture | 2026",
        "s1_notes": "Zacznij od 30 sekund kontekstu biznesowego: dlaczego uzdrowisko i dlaczego seniorzy, zanim wejdziesz w technikę.",
        # 2 — problem
        "s2_title": "Senior czeka. Recepcja nie odbiera.",
        "s2_cat": "WYZWANIE BIZNESOWE",
        "s2_cards": [
            ("60–70% Gości to Seniorzy", "Grupa 60+ preferuje tradycyjny kontakt telefoniczny ponad aplikacje i formularze webowe.", "📞"),
            ("Szczyt Ruchu = Utracone Połączenia", "Kumulacja telefonów w godzinach 8:00–10:00 i 16:00–18:00 generuje zajęte linie i frustrację.", "⏰"),
            ("Utracony Przychód ze SPA", "Niedoczekany telefon to brak rezerwacji zabiegu (80–160 PLN) lub pokoju (350–750 PLN).", "💰"),
            ("Brak Proaktywności Recepcji", "Personel jest przeciążony meldowaniem i nie wykonuje telefonów outbound przed przyjazdem.", "👥"),
        ],
        "s2_notes": "To slajd o problemie biznesowym. Zanim powiesz jak to rozwiązałeś — zapytaj rekrutera, jakie mają pytania do problemu.",
        # 3 — persona
        "s3_title": "Kto dzwoni? Pani Zofia, 72 lata.",
        "s3_cat": "USER PERSONA & EMPATHY",
        "s3_points": [
            ("Profil i Mowa:", "Mówi spokojnie, robi naturalne pauzy w środku zdania, zastanawia się nad odpowiedziami."),
            ("Bariery Pamięciowe:", "Nie pamięta nazw medycznych zabiegów — pyta o „ten masaż co pomaga na lędźwie”."),
            ("Niska Tolerancja na Błędy:", "Gdy bot wchodzi w słowo lub nie rozumie 2 razy — senior natychmiast odkłada słuchawkę."),
            ("Potrzeba Potwierdzenia:", "Oczekuje przejrzystego SMS-a z podsumowaniem, często z prośbą o wysyłkę do córki."),
            ("Wniosek Projektowy:", "Każdy parametr techniczny (timeout 3s, tempo 0.85x, parafrazowanie) wynika wprost z tej persony."),
        ],
        "s3_notes": "Podkreśl: to nie jest abstrakcyjna persona. To prototyp pacjenta sanatoryjnego w Polsce.",
        # 4 — architecture
        "s4_title": "Natywna pętla konwersacyjna ElevenLabs",
        "s4_cat": "SYSTEM ARCHITECTURE (HIGH LEVEL)",
        "s4_panel_title": "Pojedynczy silnik vs Kaskada",
        "s4_panel_body": "\n• Zintegrowana pętla: STT + LLM + TTS w jednym kanale WebRTC/SIP\n\n• Czas reakcji: ~430 ms zamiast >2.0s w klasycznym kaskadowym backendzie\n\n• Strict Grounding: Odpowiedzi wyłącznie w oparciu o 5 plików RAG\n\n• Tool Calling: Natywne webhooki do systemu hotelowego PMS\n\n• Deterministic Handoff: Przełączanie na recepcję w razie wątpliwości",
        "s4_notes": "Dlaczego natywny ElevenLabs? Eliminacja latencji. Kaskada 3 osobnych serwisów gubi seniora przez 2-sekundową ciszę.",
        # 5 — decisions
        "s5_title": "3 kluczowe decyzje architektoniczne",
        "s5_cat": "STRATEGIC TRADE-OFFS",
        "s5_decisions": [
            ("1. Natywny Agent (vs Custom LLM)", "Kaskadowy pipeline (STT -> zewnętrzny LLM -> TTS) generuje ponad 2s opóźnienia. Natywna pętla ElevenLabs schodzi do ~430ms. Dla seniora każda sekunda ciszy to utrata zaufania."),
            ("2. Eleven v3 (vs Flash 75ms)", "Flash jest ultra-szybki, ale brzmi technicznie. Eleven v3 Conversational (280ms) oferuje ciepło, intonację i empatię. Dla gościa 70+ naturalność głosu jest ważniejsza niż 100ms."),
            ("3. UX Parametry: 3.0s & Patient", "Domyślny timeout 1.2s powoduje wchodzenie w słowo, gdy senior bierze oddech. Ustawienie turn_timeout: 3.0s, turn_eagerness: Patient i speed: 0.85x eliminuje stres."),
        ],
        "s5_notes": "Podkreśl, że jesteś świadom kosztu i trade-offów: wiesz kiedy wybrać Flash, a dlaczego w sanatorium wygrywa v3.",
        # 6 — RAG
        "s6_title": "Baza Wiedzy (RAG) i Strict Grounding",
        "s6_cat": "KNOWLEDGE BASE & ZERO HALUCYNACJI",
        "s6_left_title": "Struktura 5 Plików Markdown",
        "s6_left_body": "\n• 01_dojazd.md — parking, meleks, brak barier\n• 02_katalog_spa.md — 7 zabiegów i baseny\n• 03_pokoje_i_cennik.md — 3 typy pokoi\n• 04_restauracja.md — diety cukrzycowa, lekkostrawna\n• 05_procedury.md — regulamin i bezpieczeństwo\n\nPodział trybów RAG:\n• Prompt Mode (w kontekście): cennik + procedury\n• Auto Mode (semantic search): opisy i dojazd",
        "s6_right_title": "Protokół Medyczny i Bezpieczeństwo",
        "s6_right_body": "\n• Strict Grounding:\nBrak informacji w bazie = natychmiastowe przekazanie do recepcji. Zakaz zgadywania cen i terminów.\n\n• Wywiad Balneologiczny:\nPrzed zapisem na kąpiel siarczkową lub borowinową agent pyta o przeciwwskazania sercowo-naczyniowe.\n\n• Natychmiastowa Eskalacja:\nSymptomy awaryjne (ból w klatce, duszność) uruchamiają transfer do dyżurki medycznej.",
        "s6_notes": "W sanatorium błąd w cenie to problem handlowy, ale halucynacja o zabiegu to zagrożenie zdrowotne.",
        # 7 — tools
        "s7_title": "Anna nie tylko rozmawia — działa w systemie PMS",
        "s7_cat": "TOOL CALLING & INTEGRACJA",
        "s7_headers": ["Narzędzie (Function)", "Rola Biznesowa / Przepływ", "Typ Integracji"],
        "s7_rows": [
            ("check_spa_availability", "Weryfikacja wolnych slotów na zabiegi w kalendarzu", "POST Webhook (FastAPI/PMS)"),
            ("book_spa_appointment", "Zapis gościa na zabieg, wygenerowanie ID (np. SPA-4821)", "POST Webhook (FastAPI/PMS)"),
            ("cancel_spa_appointment", "Anulowanie zabiegu (bezpłatnie >2 h, 50% <2 h, 0% przy zwolnieniu medycznym)", "POST Webhook (FastAPI/PMS)"),
            ("reschedule_spa_appointment", "Zmiana terminu zabiegu (bezpłatna, nowy kod SPA)", "POST Webhook (FastAPI/PMS)"),
            ("check_room_availability", "Sprawdzenie terminów pokoi i kalkulacja ceny pobytu", "POST Webhook (FastAPI/PMS)"),
            ("send_sms_summary", "Wysyłka SMS / Telegram z numerem rezerwacji i wskazówkami", "POST Webhook (Bramka SMS)"),
            ("transfer_to_simulated_handoff", "Przekazanie do recepcji / dyżurki (log + alert Telegram)", "POST Webhook (handoff symulowany — brak SIP)"),
        ],
        "s7_notes": "Zwróć uwagę, że handoff do człowieka jest w PoC symulowany webhookiem (log + alert Telegram), bo nie ma telefonii/SIP — docelowo zastąpi go natywne SIP REFER.",
        # 8 — omnichannel
        "s8_title": "Dwa kanały, jeden zunifikowany asystent",
        "s8_cat": "OMNICHANNEL DEPLOYMENT",
        "s8_ch1_title": "Kanał 1: Tradycyjna Telefonia (SIP Trunk) — ścieżka docelowa",
        "s8_ch1_body": "• Ten sam agent i prompt po podpięciu SIP Trunk (Faza II — telefonii nie ma w PoC)\n• Bezpośredni numer do recepcji hotelu\n• Dostępność 24/7 bez oczekiwania w kolejce\n• Turn timeout 3.0s, parafrazowanie ustaleń, wysyłka SMS po zakończeniu\n",
        "s8_ch2_title": "Kanał 2: Interaktywny Widget Webowy na Stronie Hotelu",
        "s8_ch2_body": "• Quick Reply Chips: Szybki wybór języka (6 opcji) i tematów rozmowy\n• Live Transkrypcja: Wizualne śledzenie rozmowy w czasie rzeczywistym\n• Karta Sukcesu: Natychmiastowe potwierdzenie rezerwacji z opcją wysyłki do opiekuna\n• Signed URL: 15-minutowy bezpieczny token WebSocket bez ekspozycji API key",
        "s8_notes": "W PoC agent działa wyłącznie jako widget webowy; kanał telefoniczny przez SIP Trunk to ścieżka docelowa — ta sama konfiguracja agenta.",
        # 9 — demo
        "s9_title": "Demo: 3 ścieżki walidacji",
        "s9_cat": "LIVE SCENARIOS",
        "s9_scenarios": [
            ("Ścieżka A: Rezerwacja Zabiegu SPA (Happy Path)", "Gość pyta o masaż leczniczy -> Anna sprawdza kalendarz -> proponuje 14:30 -> parafrazuje dane -> potwierdza rezerwację SPA-4821 -> wysyła SMS."),
            ("Ścieżka B: Zapytanie Informacyjne z RAG", "Pytanie o godziny posiłków dietetycznych i dojazd meleksem -> precyzyjna odpowiedź z bazy wiedzy bez halucynacji."),
            ("Ścieżka C: Eskalacja Medyczna / Przeciwwskazanie", "Gość zgłasza dolegliwości kardiologiczne przy kąpieli siarczkowej -> Anna natychmiast przełącza na dyżurkę medyczną."),
        ],
        "s9_notes": "Miej przygotowany fallback: jeśli internet padnie, pokaż logi z FastAPI lub nagrania audio.",
        # 10 — security
        "s10_title": "Enterprise Ready: RODO i ochrona danych medycznych",
        "s10_cat": "SECURITY & COMPLIANCE",
        "s10_items": [
            ("Zero Retention Mode (ZRM):", "Audio i transkrypcje przetwarzane wyłącznie w pamięci RAM — brak zapisu na dyskach ElevenLabs."),
            ("Data Redaction:", "Automatyczne maskowanie danych osobowych (PII) i medycznych w logach."),
            ("Data Residency EU:", "Przetwarzanie danych na terenie Unii Europejskiej, pełna zgodność z RODO / DPA."),
            ("Signed URLs:", "Bezpieczne tokeny jednorazowe eliminujące wyciek klucza API do przeglądarki."),
        ],
        "s10_notes": "Dla zarządu sieci hoteli compliance medyczne to warunek sine qua non.",
        # 11 — multi-hotel
        "s11_title": "Jeden agent, dziesięć hoteli — skalowanie sieciowe",
        "s11_cat": "MULTI-TENANT ARCHITECTURE",
        "s11_panel_title": "Architektura Multi-Hotel",
        "s11_panel_body": "• 1 Centralny Agent: Zamiast 10 osobnych botów utrzymujemy jeden rdzeń system promptu.\n\n• Dynamic Variables: Przy inicjacji połączenia wstrzykujemy parametry:\n  - hotel_name, location\n  - reception_phone\n  - pms_hotel_id\n\n• Sygnalizacja SIP UUI: Przekazywanie ID hotelu w nagłówkach centrali PBX.\n\n• Skalowalność: Dodanie 11. obiektu to 5 minut konfiguracji zmiennych.",
        "s11_notes": "Pokaż, jak myślisz jako Deployment Strategist: optymalizacja kosztów utrzymania i zarządzania agentami.",
        # 12 — costs
        "s12_title": "Koszty wdrożenia i twardy zwrot z inwestycji (ROI)",
        "s12_cat": "BUSINESS CASE & FINANCIALS",
        "s12_headers": ["Parametr", "Faza Pilotażu / PoC (Creator)", "Faza Skalowania (Scale)"],
        "s12_rows": [
            ("Koszt platformy", "$22 / miesiąc", "$299 / miesiąc"),
            ("Minuty w pakiecie", "275 minut rozmów", "3 738 minut rozmów (≈ 0,08 USD/min)"),
            ("Jednoczesne połączenia (Concurrency)", "10 kanałów", "30 kanałów (+Burst do 90)"),
        ],
        "s12_roi_title": "Kalkulacja ROI (Return on Investment):",
        "s12_roi_body": "• Koszt 275 min AI ($22 ≈ 88 PLN) odpowiada 3,5 godzinom pracy recepcjonisty (~25 PLN/h).\n• Ochrona Przychodów: 3 rezerwacje pokoju w nocy (3 × 500 PLN = 1 500 PLN ≈ $375) pokrywają miesięczny abonament Scale ($299).\n• Wartość dla Personelu: Zero wypalenia zawodowego i możliwość skupienia się na gościach obecnych fizycznie w obiekcie.",
        "s12_notes": "Nie pozycjonujemy AI jako redukcji personelu. To ochrona przed utraconym przychodem w nocy i w szczytach. Kurs w kalkulacji: 4,0 PLN/USD; cennik platformy według stanu z 2026-11.",
        # 13 — roadmap
        "s13_title": "Roadmapa wdrożenia: od PoC do proaktywnego AI",
        "s13_cat": "IMPLEMENTATION TIMELINE",
        "s13_phases": [
            ("Faza I: PoC & Walidacja (Obecnie)", "• Baza wiedzy RAG (5 plików)\n• Mock backend (FastAPI, 7 narzędzi webhook, :8011)\n• Widget webowy z Quick Reply Chips\n• Testy czasu reakcji i promptu", SAGE),
            ("Faza II: Integracja Produkcyjna (Miesiąc 1-2)", "• Bezpośrednie API do PMS (Opera/KWHotel)\n• Bramka Twilio SMS (potwierdzenia)\n• Wpięcie w centralę telefoniczną SIP PBX\n• Wielojęzyczność (DE, EN, UA)", GOLD),
            ("Faza III: Proaktywny Outbound AI (Miesiąc 3+)", "• Automatyczne telefony przed przyjazdem\n• Potwierdzanie transportu meleksem\n• Spersonalizowane rekomendacje zabiegów\n• Zaawansowana analityka intencji i CSAT", NAVY),
        ],
        "s13_notes": "Faza III to przejście od reaktywnej infolinii do proaktywnego generatora przychodów.",
        # 14 — Q&A
        "s14_title": "Dziękuję za uwagę.",
        "s14_sub": "\nCzas na dyskusję, pytania i sesję System Design (V2).",
        "s14_notes": "Otwórz dyskusję i przejdź do warsztatu projektowego.",
    },
    "en": {
        "file": "Bukowy_Dwor_Case_Study_EN.pptx",
        # 1 — title
        "s1_title": "Virtual AI Receptionist",
        "s1_sub": "Bukowy Dwór — Thermal Spa & Health Resort × ElevenLabs",
        "s1_tagline": "\nNative conversational agent deployment for a demanding 60+ guest base across a spa resort chain.",
        "s1_badge": "Phase V1 & V2: Case Study, Product Design & System Architecture | 2026",
        "s1_notes": "Start with 30 seconds of business context: why a health resort and why seniors, before touching the technology.",
        # 2 — problem
        "s2_title": "Senior Guests Wait. Front Desk Can't Keep Up.",
        "s2_cat": "BUSINESS CHALLENGE",
        "s2_cards": [
            ("60–70% Senior Guests", "The 60+ demographic strongly prefers voice calls over mobile apps and web forms.", "📞"),
            ("Peak Call Spikes", "Call surges at 8:00–10:00 and 16:00–18:00 create busy lines and guest frustration.", "⏰"),
            ("Lost High-Margin Revenue", "An unanswered call is a lost treatment ($30–$80) or room booking ($100–$250).", "💰"),
            ("Front Desk Bottlenecks", "Staff are overloaded with check-ins and have no bandwidth for pre-arrival outbound calls.", "👥"),
        ],
        "s2_notes": "This is the business problem slide. Before explaining your solution, ask the interviewer what questions the problem raises for them.",
        # 3 — persona
        "s3_title": "Who Is Calling? Mrs. Sophia, 72 Years Old.",
        "s3_cat": "USER PERSONA & EMPATHY",
        "s3_points": [
            ("Profile & Speech:", "Speaks slowly, pauses naturally mid-sentence, takes time to think before answering."),
            ("Vocabulary Gaps:", "Does not recall clinical treatment names — asks for “that massage that helps my lower back”."),
            ("Zero Error Tolerance:", "If the bot interrupts or fails to understand twice, a senior hangs up immediately."),
            ("Confirmation Need:", "Expects a clear SMS summary, often asked to be sent to her daughter."),
            ("Engineering Rule:", "Every technical parameter (3.0s timeout, 0.85x pace, paraphrasing) stems directly from this persona."),
        ],
        "s3_notes": "Stress that this is not an abstract persona — it is the archetype of a health-resort patient.",
        # 4 — architecture
        "s4_title": "Unified ElevenLabs Conversational Loop",
        "s4_cat": "SYSTEM ARCHITECTURE (HIGH LEVEL)",
        "s4_panel_title": "Single Loop vs Cascade",
        "s4_panel_body": "\n• Integrated loop: STT + LLM + TTS in a single WebRTC/SIP channel\n\n• Response time: ~430 ms instead of >2.0 s in a classic cascaded backend\n\n• Strict grounding: answers come only from the 5 RAG files\n\n• Tool calling: native webhooks into the hotel PMS\n\n• Deterministic handoff: transfer to reception whenever in doubt",
        "s4_notes": "Why a native ElevenLabs loop? Latency elimination. A cascade of three services loses a senior guest inside two seconds of silence.",
        # 5 — decisions
        "s5_title": "3 Core Architectural Decisions",
        "s5_cat": "STRATEGIC TRADE-OFFS",
        "s5_decisions": [
            ("1. Native Agent (vs Custom LLM)", "A cascaded pipeline (STT -> external LLM -> TTS) adds more than 2 s of latency. The native ElevenLabs loop drops to ~430 ms. For a senior, every second of silence erodes trust."),
            ("2. Eleven v3 (vs Flash 75 ms)", "Flash is ultra-fast but sounds technical. Eleven v3 Conversational (280 ms) delivers warmth, intonation and empathy. For a 70+ guest, a natural voice matters more than 100 ms."),
            ("3. UX Parameters: 3.0 s & Patient", "The default 1.2 s timeout cuts in while a senior takes a breath. turn_timeout: 3.0 s, turn_eagerness: Patient and speed: 0.85x remove the stress."),
        ],
        "s5_notes": "Show that you know the cost and the trade-offs: when to pick Flash, and why v3 wins in a health resort.",
        # 6 — RAG
        "s6_title": "Knowledge Base (RAG) & Strict Grounding",
        "s6_cat": "KNOWLEDGE BASE & ZERO HALLUCINATION",
        "s6_left_title": "Structure of the 5 Markdown Files",
        "s6_left_body": "\n• 01_access.md — parking, shuttle, step-free access\n• 02_spa_catalogue.md — 7 treatments and pools\n• 03_rooms_and_pricing.md — 3 room types\n• 04_restaurant.md — diabetic and light diets\n• 05_procedures.md — house rules and safety\n\nRAG mode split:\n• Prompt Mode (in context): pricing + procedures\n• Auto Mode (semantic search): descriptions and access",
        "s6_right_title": "Medical Protocol & Safety",
        "s6_right_body": "\n• Strict grounding:\nNo information in the knowledge base = immediate transfer to reception. Never guess prices or availability.\n\n• Balneological screening:\nBefore booking a sulphur or peat bath the agent asks about cardiovascular contraindications.\n\n• Immediate escalation:\nEmergency symptoms (chest pain, shortness of breath) trigger a transfer to the on-duty nurse station.",
        "s6_notes": "In a health resort a wrong price is a commercial issue, but a hallucinated treatment is a health risk.",
        # 7 — tools
        "s7_title": "Anna Doesn't Just Chat — She Acts in the PMS",
        "s7_cat": "TOOL CALLING & INTEGRATION",
        "s7_headers": ["Tool (Function)", "Business Role / Flow", "Integration Type"],
        "s7_rows": [
            ("check_spa_availability", "Checks free treatment slots in the calendar", "POST Webhook (FastAPI/PMS)"),
            ("book_spa_appointment", "Books the guest and returns an ID (e.g. SPA-4821)", "POST Webhook (FastAPI/PMS)"),
            ("cancel_spa_appointment", "Cancels a treatment (free >2 h, 50% <2 h, 0% with medical release)", "POST Webhook (FastAPI/PMS)"),
            ("reschedule_spa_appointment", "Moves a treatment to a new slot (free, new SPA code)", "POST Webhook (FastAPI/PMS)"),
            ("check_room_availability", "Checks room availability and calculates the total stay price", "POST Webhook (FastAPI/PMS)"),
            ("send_sms_summary", "Sends an SMS / Telegram summary with the booking ID and directions", "POST Webhook (SMS gateway)"),
            ("transfer_to_simulated_handoff", "Hands off to reception / nurse station (log + Telegram alert)", "POST Webhook (simulated handoff — no SIP)"),
        ],
        "s7_notes": "Point out that the human handoff is simulated by a webhook in the PoC (log + Telegram alert) because there is no telephony/SIP — a native SIP REFER will replace it in production.",
        # 8 — omnichannel
        "s8_title": "Two Channels, One Unified Assistant",
        "s8_cat": "OMNICHANNEL DEPLOYMENT",
        "s8_ch1_title": "Channel 1: Traditional Telephony (SIP Trunk) — target state",
        "s8_ch1_body": "• Same agent and prompt once SIP Trunk is connected (Phase II — no telephony in the PoC)\n• Direct number to the hotel reception\n• 24/7 availability with no queueing\n• Turn timeout 3.0 s, paraphrased confirmations, SMS after the call\n",
        "s8_ch2_title": "Channel 2: Interactive Web Widget on the Hotel Website",
        "s8_ch2_body": "• Quick Reply Chips: pick a language (6 options) and a topic\n• Live Transcript: follow the conversation in real time\n• Success Card: instant booking confirmation with an option to send it to a carer\n• Signed URL: 15-minute secure WebSocket token without exposing the API key",
        "s8_notes": "In the PoC the agent runs only as a web widget; the SIP Trunk phone channel is the target state with the very same agent configuration.",
        # 9 — demo
        "s9_title": "Demo: 3 Validation Paths",
        "s9_cat": "LIVE SCENARIOS",
        "s9_scenarios": [
            ("Path A: SPA Treatment Booking (Happy Path)", "Guest asks about a therapeutic massage -> Anna checks the calendar -> proposes 14:30 -> paraphrases the details -> confirms booking SPA-4821 -> sends the SMS."),
            ("Path B: Grounded Knowledge Question (RAG)", "Question about diabetic meal times and the shuttle -> a precise answer from the knowledge base with no hallucination."),
            ("Path C: Medical Escalation / Contraindication", "Guest reports cardiac symptoms before a sulphur bath -> Anna transfers to the nurse station immediately."),
        ],
        "s9_notes": "Have a fallback ready: if the network drops, show the FastAPI logs or the audio recordings.",
        # 10 — security
        "s10_title": "Enterprise Ready: GDPR & Medical Data Protection",
        "s10_cat": "SECURITY & COMPLIANCE",
        "s10_items": [
            ("Zero Retention Mode (ZRM):", "Audio and transcripts are processed in RAM only — nothing is written to ElevenLabs disks."),
            ("Data Redaction:", "Automatic masking of personal (PII) and medical data in logs."),
            ("Data Residency EU:", "Data processed inside the European Union, full GDPR / DPA compliance."),
            ("Signed URLs:", "Secure one-time tokens that keep the API key out of the browser."),
        ],
        "s10_notes": "For a hotel-chain board, medical compliance is a sine qua non condition.",
        # 11 — multi-hotel
        "s11_title": "One Agent, Ten Hotels — Network Scaling",
        "s11_cat": "MULTI-TENANT ARCHITECTURE",
        "s11_panel_title": "Multi-Hotel Architecture",
        "s11_panel_body": "• 1 Central Agent: instead of 10 separate bots we maintain a single system-prompt core.\n\n• Dynamic Variables: injected when the call starts:\n  - hotel_name, location\n  - reception_phone\n  - pms_hotel_id\n\n• SIP UUI signalling: the PBX passes the hotel ID in the call headers.\n\n• Scalability: adding an 11th property is 5 minutes of variable configuration.",
        "s11_notes": "Show how you think as a Deployment Strategist: maintenance cost and agent governance optimisation.",
        # 12 — costs
        "s12_title": "Deployment Cost & Hard Return on Investment (ROI)",
        "s12_cat": "BUSINESS CASE & FINANCIALS",
        "s12_headers": ["Parameter", "Pilot / PoC Phase (Creator)", "Scaling Phase (Scale)"],
        "s12_rows": [
            ("Platform cost", "$22 / month", "$299 / month"),
            ("Included minutes", "275 call minutes", "3,738 call minutes (≈ $0.08/min)"),
            ("Concurrent calls (Concurrency)", "10 channels", "30 channels (+burst to 90)"),
        ],
        "s12_roi_title": "ROI calculation:",
        "s12_roi_body": "• 275 min of AI ($22 ≈ 88 PLN) costs as much as 3.5 hours of a receptionist (~25 PLN/h).\n• Revenue protection: three night room bookings (3 × 500 PLN = 1,500 PLN ≈ $375) cover the monthly Scale plan ($299).\n• Value for staff: no burnout and full focus on guests physically present at the property.",
        "s12_notes": "Do not position AI as headcount reduction. It protects revenue at night and during call peaks. FX rate used: 4.0 PLN/USD; platform pricing as of 2026-11.",
        # 13 — roadmap
        "s13_title": "Implementation Roadmap: from PoC to Proactive AI",
        "s13_cat": "IMPLEMENTATION TIMELINE",
        "s13_phases": [
            ("Phase I: PoC & Validation (Now)", "• RAG knowledge base (5 files)\n• Mock backend (FastAPI, 7 webhook tools, :8011)\n• Web widget with Quick Reply Chips\n• Latency and prompt testing", SAGE),
            ("Phase II: Production Integration (Month 1-2)", "• Direct PMS API (Opera/KWHotel)\n• Twilio SMS gateway (confirmations)\n• SIP PBX telephony integration\n• Multilingual (DE, EN, UA)", GOLD),
            ("Phase III: Proactive Outbound AI (Month 3+)", "• Automated pre-arrival calls\n• Shuttle confirmation\n• Personalised treatment recommendations\n• Advanced intent and CSAT analytics", NAVY),
        ],
        "s13_notes": "Phase III moves the agent from a reactive hotline to a proactive revenue generator.",
        # 14 — Q&A
        "s14_title": "Thank you.",
        "s14_sub": "\nTime for discussion, questions and the System Design session (V2).",
        "s14_notes": "Open the discussion and move into the design workshop.",
    },
}


def create_presentation(lang="pl"):
    t = TEXTS[lang]
    prs = Presentation()
    # 16:9 widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

    def add_bg(slide, color=NAVY):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category_text=BRAND_LINE, dark_theme=True):
        # Category tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = GOLD
        p_cat.font.name = 'Arial'

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.9))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(28)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE if dark_theme else NAVY
        p_title.font.name = 'Georgia'

    def add_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # ----------------------------------------------------
    # SLIDE 1: Title
    # ----------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    add_bg(s1, NAVY)

    # Decorative gold line
    line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(1.5), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = GOLD
    line.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(7.5), Inches(3.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = t["s1_title"]
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.font.name = 'Georgia'

    p2 = tf.add_paragraph()
    p2.text = t["s1_sub"]
    p2.font.size = Pt(22)
    p2.font.color.rgb = GOLD
    p2.font.name = 'Georgia'

    p3 = tf.add_paragraph()
    p3.text = t["s1_tagline"]
    p3.font.size = Pt(14)
    p3.font.color.rgb = CREAM

    # Bottom badge
    bb = s1.shapes.add_textbox(Inches(0.8), Inches(6.2), Inches(10), Inches(0.6))
    p_b = bb.text_frame.paragraphs[0]
    p_b.text = t["s1_badge"]
    p_b.font.size = Pt(12)
    p_b.font.color.rgb = SAGE

    # Right side image
    img1 = os.path.join(assets_dir, 'anna_widget_desktop.jpg')
    if os.path.exists(img1):
        s1.shapes.add_picture(img1, Inches(8.0), Inches(1.4), Inches(4.7))

    add_notes(s1, t["s1_notes"])

    # ----------------------------------------------------
    # SLIDE 2: Problem
    # ----------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_bg(s2, CREAM)
    add_header(s2, t["s2_title"], t["s2_cat"], dark_theme=False)

    # 4 Cards for pain points
    cards_data = t["s2_cards"]

    for i, (head, desc, icon) in enumerate(cards_data):
        row = i // 2
        col = i % 2
        left = Inches(0.8 + col * 5.9)
        top = Inches(1.9 + row * 2.5)

        box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.6), Inches(2.2))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = GOLD
        box.line.width = Pt(1)

        tb = s2.shapes.add_textbox(left + Inches(0.3), top + Inches(0.2), Inches(5.0), Inches(1.8))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{icon}  {head}"
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = NAVY
        p.font.name = 'Georgia'

        p_desc = tf.add_paragraph()
        p_desc.text = f"\n{desc}"
        p_desc.font.size = Pt(13)
        p_desc.font.color.rgb = CHARCOAL

    add_notes(s2, t["s2_notes"])

    # ----------------------------------------------------
    # SLIDE 3: Persona
    # ----------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_bg(s3, NAVY)
    add_header(s3, t["s3_title"], t["s3_cat"], dark_theme=True)

    img_zofia = os.path.join(assets_dir, 'persona_zofia.png')
    if os.path.exists(img_zofia):
        s3.shapes.add_picture(img_zofia, Inches(0.8), Inches(1.9), Inches(4.2))

    tb3 = s3.shapes.add_textbox(Inches(5.3), Inches(1.8), Inches(7.2), Inches(5.0))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    persona_points = t["s3_points"]

    for i, (title_p, body_p) in enumerate(persona_points):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.text = f"• {title_p} "
        p.font.bold = True
        p.font.size = Pt(14)
        p.font.color.rgb = GOLD

        # Add normal text
        run = p.add_run()
        run.text = body_p
        run.font.bold = False
        run.font.color.rgb = WHITE
        run.font.size = Pt(14)

    add_notes(s3, t["s3_notes"])

    # ----------------------------------------------------
    # SLIDE 4: Architecture & Loop
    # ----------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    add_bg(s4, NAVY)
    add_header(s4, t["s4_title"], t["s4_cat"], dark_theme=True)

    img_arch = os.path.join(assets_dir, 'diagram_architecture.png')
    if os.path.exists(img_arch):
        s4.shapes.add_picture(img_arch, Inches(0.8), Inches(1.8), Inches(7.5))

    tb4 = s4.shapes.add_textbox(Inches(8.5), Inches(1.8), Inches(4.3), Inches(5.0))
    tf4 = tb4.text_frame
    tf4.word_wrap = True

    p4_1 = tf4.paragraphs[0]
    p4_1.text = t["s4_panel_title"]
    p4_1.font.size = Pt(18)
    p4_1.font.bold = True
    p4_1.font.color.rgb = GOLD

    p4_desc = tf4.add_paragraph()
    p4_desc.text = t["s4_panel_body"]
    p4_desc.font.size = Pt(13)
    p4_desc.font.color.rgb = WHITE

    add_notes(s4, t["s4_notes"])

    # ----------------------------------------------------
    # SLIDE 5: 3 Decisions
    # ----------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_bg(s5, CREAM)
    add_header(s5, t["s5_title"], t["s5_cat"], dark_theme=False)

    decisions = t["s5_decisions"]

    for i, (d_title, d_desc) in enumerate(decisions):
        top = Inches(1.9 + i * 1.7)
        box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.7), Inches(1.5))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = GOLD

        tb = s5.shapes.add_textbox(Inches(1.1), top + Inches(0.15), Inches(11.1), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = d_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf.add_paragraph()
        p_b.text = d_desc
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s5, t["s5_notes"])

    # ----------------------------------------------------
    # SLIDE 6: Baza Wiedzy (RAG)
    # ----------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_bg(s6, NAVY)
    add_header(s6, t["s6_title"], t["s6_cat"], dark_theme=True)

    # Two columns
    box_l = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.9), Inches(5.6), Inches(5.0))
    box_l.fill.solid()
    box_l.fill.fore_color.rgb = RGBColor(35, 52, 88)
    box_l.line.color.rgb = GOLD

    tb_l = s6.shapes.add_textbox(Inches(1.1), Inches(2.1), Inches(5.0), Inches(4.5))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = t["s6_left_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p2 = tf_l.add_paragraph()
    p2.text = t["s6_left_body"]
    p2.font.size = Pt(13)
    p2.font.color.rgb = WHITE

    box_r = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.9), Inches(5.6), Inches(5.0))
    box_r.fill.solid()
    box_r.fill.fore_color.rgb = RGBColor(35, 52, 88)
    box_r.line.color.rgb = SAGE

    tb_r = s6.shapes.add_textbox(Inches(7.2), Inches(2.1), Inches(5.0), Inches(4.5))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = t["s6_right_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SAGE

    p2 = tf_r.add_paragraph()
    p2.text = t["s6_right_body"]
    p2.font.size = Pt(13)
    p2.font.color.rgb = WHITE

    add_notes(s6, t["s6_notes"])

    # ----------------------------------------------------
    # SLIDE 7: Tools (Table)
    # ----------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_bg(s7, CREAM)
    add_header(s7, t["s7_title"], t["s7_cat"], dark_theme=False)

    # Table
    rows = 8
    cols = 3
    table_shape = s7.shapes.add_table(rows, cols, Inches(0.8), Inches(1.9), Inches(11.7), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(5.5)
    table.columns[2].width = Inches(3.0)

    headers = t["s7_headers"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.color.rgb = GOLD
        p.font.size = Pt(13)

    data = t["s7_rows"]

    for row_idx, (c1, c2, c3) in enumerate(data, start=1):
        for col_idx, val in enumerate([c1, c2, c3]):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 1 else RGBColor(250, 246, 240)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(12)
            p.font.color.rgb = CHARCOAL

    add_notes(s7, t["s7_notes"])

    # ----------------------------------------------------
    # SLIDE 8: Omnichannel (Phone + Web)
    # ----------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    add_bg(s8, NAVY)
    add_header(s8, t["s8_title"], t["s8_cat"], dark_theme=True)

    img_chips = os.path.join(assets_dir, 'anna_widget_chips.jpg')
    if os.path.exists(img_chips):
        s8.shapes.add_picture(img_chips, Inches(0.8), Inches(1.8), Inches(3.2))

    tb8 = s8.shapes.add_textbox(Inches(4.3), Inches(1.8), Inches(8.2), Inches(5.0))
    tf8 = tb8.text_frame
    tf8.word_wrap = True

    p = tf8.paragraphs[0]
    p.text = t["s8_ch1_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p_t = tf8.add_paragraph()
    p_t.text = t["s8_ch1_body"]
    p_t.font.size = Pt(13)
    p_t.font.color.rgb = WHITE

    p2 = tf8.add_paragraph()
    p2.text = t["s8_ch2_title"]
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = SAGE

    p_w = tf8.add_paragraph()
    p_w.text = t["s8_ch2_body"]
    p_w.font.size = Pt(13)
    p_w.font.color.rgb = WHITE

    add_notes(s8, t["s8_notes"])

    # ----------------------------------------------------
    # SLIDE 9: Live Demo Paths
    # ----------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    add_bg(s9, CREAM)
    add_header(s9, t["s9_title"], t["s9_cat"], dark_theme=False)

    img_succ = os.path.join(assets_dir, 'anna_widget_success.jpg')
    if os.path.exists(img_succ):
        s9.shapes.add_picture(img_succ, Inches(0.8), Inches(1.8), Inches(3.2))

    tb9 = s9.shapes.add_textbox(Inches(4.4), Inches(1.8), Inches(8.1), Inches(5.0))
    tf9 = tb9.text_frame
    tf9.word_wrap = True

    scenarios = t["s9_scenarios"]

    for i, (sc_title, sc_desc) in enumerate(scenarios):
        p = tf9.paragraphs[0] if i == 0 else tf9.add_paragraph()
        p.text = f"{sc_title}"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf9.add_paragraph()
        p_b.text = f"{sc_desc}\n"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s9, t["s9_notes"])

    # ----------------------------------------------------
    # SLIDE 10: Security & Compliance
    # ----------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    add_bg(s10, NAVY)
    add_header(s10, t["s10_title"], t["s10_cat"], dark_theme=True)

    img_sec = os.path.join(assets_dir, 'enterprise_security.png')
    if os.path.exists(img_sec):
        s10.shapes.add_picture(img_sec, Inches(0.8), Inches(1.8), Inches(6.8))

    tb10 = s10.shapes.add_textbox(Inches(7.9), Inches(1.8), Inches(4.7), Inches(5.0))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    sec_items = t["s10_items"]

    for i, (it_title, it_desc) in enumerate(sec_items):
        p = tf10.paragraphs[0] if i == 0 else tf10.add_paragraph()
        p.text = f"🔒 {it_title}"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = GOLD

        p_b = tf10.add_paragraph()
        p_b.text = f"{it_desc}\n"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = WHITE

    add_notes(s10, t["s10_notes"])

    # ----------------------------------------------------
    # SLIDE 11: Multi-Hotel Architecture
    # ----------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    add_bg(s11, NAVY)
    add_header(s11, t["s11_title"], t["s11_cat"], dark_theme=True)

    img_multi = os.path.join(assets_dir, 'diagram_multihotel.png')
    if os.path.exists(img_multi):
        s11.shapes.add_picture(img_multi, Inches(0.8), Inches(1.8), Inches(6.8))

    tb11 = s11.shapes.add_textbox(Inches(7.9), Inches(1.8), Inches(4.7), Inches(5.0))
    tf11 = tb11.text_frame
    tf11.word_wrap = True

    p = tf11.paragraphs[0]
    p.text = t["s11_panel_title"]
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD

    p_body = tf11.add_paragraph()
    p_body.text = t["s11_panel_body"]
    p_body.font.size = Pt(12)
    p_body.font.color.rgb = WHITE

    add_notes(s11, t["s11_notes"])

    # ----------------------------------------------------
    # SLIDE 12: Costs & ROI
    # ----------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    add_bg(s12, CREAM)
    add_header(s12, t["s12_title"], t["s12_cat"], dark_theme=False)

    # Cost table
    table_shape = s12.shapes.add_table(4, 3, Inches(0.8), Inches(1.9), Inches(11.7), Inches(2.3))
    table = table_shape.table
    table.columns[0].width = Inches(3.9)
    table.columns[1].width = Inches(3.9)
    table.columns[2].width = Inches(3.9)

    c_headers = t["s12_headers"]
    for idx, h in enumerate(c_headers):
        cell = table.cell(0, idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.color.rgb = GOLD
        p.font.size = Pt(13)

    c_data = t["s12_rows"]

    for row_idx, (c1, c2, c3) in enumerate(c_data, start=1):
        for col_idx, val in enumerate([c1, c2, c3]):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 1 else RGBColor(250, 246, 240)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(12)
            p.font.color.rgb = CHARCOAL

    tb12 = s12.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(11.7), Inches(2.4))
    tf12 = tb12.text_frame
    tf12.word_wrap = True

    p = tf12.paragraphs[0]
    p.text = t["s12_roi_title"]
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY

    p_roi = tf12.add_paragraph()
    p_roi.text = t["s12_roi_body"]
    p_roi.font.size = Pt(13)
    p_roi.font.color.rgb = CHARCOAL

    add_notes(s12, t["s12_notes"])

    # ----------------------------------------------------
    # SLIDE 13: Roadmap
    # ----------------------------------------------------
    s13 = prs.slides.add_slide(blank_layout)
    add_bg(s13, CREAM)
    add_header(s13, t["s13_title"], t["s13_cat"], dark_theme=False)

    phases = t["s13_phases"]

    for i, (ph_title, ph_desc, col_accent) in enumerate(phases):
        left = Inches(0.8 + i * 4.0)
        box = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.9), Inches(3.7), Inches(5.0))
        box.fill.solid()
        box.fill.fore_color.rgb = WHITE
        box.line.color.rgb = col_accent
        box.line.width = Pt(2)

        tb = s13.shapes.add_textbox(left + Inches(0.2), Inches(2.1), Inches(3.3), Inches(4.5))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = ph_title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = NAVY

        p_b = tf.add_paragraph()
        p_b.text = f"\n{ph_desc}"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = CHARCOAL

    add_notes(s13, t["s13_notes"])

    # ----------------------------------------------------
    # SLIDE 14: Q&A
    # ----------------------------------------------------
    s14 = prs.slides.add_slide(blank_layout)
    add_bg(s14, NAVY)

    tb14 = s14.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10.3), Inches(3.0))
    tf14 = tb14.text_frame
    tf14.word_wrap = True
    p = tf14.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = t["s14_title"]
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = GOLD
    p.font.name = 'Georgia'

    p2 = tf14.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = t["s14_sub"]
    p2.font.size = Pt(22)
    p2.font.color.rgb = WHITE

    add_notes(s14, t["s14_notes"])

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), t["file"])
    prs.save(out_path)
    print(f"[{lang}] deck generated: {out_path}")
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate the Bukowy Dwor case-study deck (PL/EN).")
    parser.add_argument(
        "--lang",
        choices=["pl", "en", "all"],
        default="pl",
        help="which deck to build (default: pl)",
    )
    args = parser.parse_args(argv)

    langs = ["pl", "en"] if args.lang == "all" else [args.lang]
    return [create_presentation(lang) for lang in langs]


if __name__ == '__main__':
    main()
