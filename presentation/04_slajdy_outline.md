# Outline Slajdów — Wirtualny Recepcjonista AI „Bukowy Dwór"

> Struktura prezentacji do przełożenia na PowerPoint / Google Slides.
> Format: Tytuł slajdu | Treść | Diagram/visual | Uwagi dla prezentera

---

## SLAJD 1 — Okładka
**Tytuł:** Wirtualny Recepcjonista AI — Bukowy Dwór & Spa  
**Podtytuł:** Case study: wdrożenie ElevenLabs Conversational AI w sieci hoteli uzdrowiskowych  
**Visual:** Zdjęcie uzdrowiska / spa + logo ElevenLabs  
**Uwaga:** Zacznij od: „Zanim przejdę do architektury — 30 sekund kontekstu biznesowego."

---

## SLAJD 2 — Problem (biznesowy, nie techniczny)
**Tytuł:** Problem: senior czeka, recepcja nie odbiera  
**Treść (bullet):**
- Recepcja uzdrowiska: 60% gości to seniorzy 60+
- Szczyt ruchu telefonicznego: 8:00-10:00 i 16:00-18:00 — kolejka, oczekiwanie
- Gość nie rezerwuje zabiegu jeśli „trudno się dodzwonić"
- Recepcjonista: ~$20/h, dostępny 8 godz./dobę

**Visual:** Prosty wykres: godziny połączeń vs. obsadzone dyżury  
**Uwaga:** „Zanim powiem jak to rozwiązałem — jakie pytania macie do problemu?"

---

## SLAJD 3 — Persona Użytkownika
**Tytuł:** Kto dzwoni? — Pani Zofia, 72 lata  
**Treść:**
- Mówi wolno, robi pauzy w środku zdania
- Nie pamięta nazw zabiegów, pyta „ten masaż co na kręgosłup"
- Nie lubi gdy coś się powtarza — frustracja = rozłączenie
- Oczekuje potwierdzenia SMS (wysyła córce)

**Visual:** Prosta persona card (imię, wiek, pain points, goals)  
**Uwaga:** „Każda decyzja architektoniczna którą zaraz pokażę wynika z tej persony."

---

## SLAJD 4 — Rozwiązanie (1 zdanie)
**Tytuł:** Anna — wirtualna recepcjonistka dostępna 24/7  
**Treść:** ElevenLabs Conversational AI: natywna pętla STT + LLM + TTS, latencja < 500ms, ciepły głos, cierpliwe tempo  
**Visual:** Diagram 1 (główny przepływ — uproszczony, bez szczegółów technicznych)  
**Uwaga:** „Za chwilę pokażę to na żywo. Najpierw architektura."

---

## SLAJD 5 — Stack Technologiczny
**Tytuł:** Jak to działa — 3 warstwy  
**Treść:**

| Warstwa | Wybór | Dlaczego |
|---|---|---|
| STT | Scribe v2 Realtime | ~150ms, VAD, pl-PL |
| LLM | Gemini 3.5 Flash Lite | niska temperatura, RAG grounding |
| TTS | Eleven v3 Conversational | ekspresja > latencja dla seniorów |

**Visual:** Diagram 5 (block diagram stacku)  
**Uwaga:** „Pytanie które zawsze pada: dlaczego v3 a nie Flash który jest 4x szybszy? [odpowiedź z toku myślenia]"

---

## SLAJD 6 — UX dla Seniorów (parametry)
**Tytuł:** Architektura konwersacyjna dostosowana do odbiorcy  
**Treść:**
- `turn_timeout: 3.0s` — 3× dłuższe okno ciszy niż default
- `turn_eagerness: Patient` — Anna nie przerywa
- `speed: 0.85x` — 15% wolniej od standardu
- Jeden krok = jedno pytanie. Zawsze parafrazowanie przed potwierdzeniem.

**Visual:** Porównanie timeline'u: standard agent vs Anna  
**Uwaga:** „To nie jest 'konfiguracja'. To jest UX research przełożony na parametry."

---

## SLAJD 7 — Baza Wiedzy (RAG)
**Tytuł:** Baza wiedzy — bez halucynacji  
**Treść:**
- 5 plików Markdown (dojazd, SPA, pokoje, restauracja, procedury)
- Tryb `prompt` (zawsze w kontekście): procedury + cennik
- Tryb `auto` (semantic search): opisy zabiegów, dojazd
- Strict grounding: brak info = transfer do człowieka, nigdy zmyślanie

**Visual:** Schemat: dokument → chunking → semantic search → inject  
**Uwaga:** „Dlaczego nie wrzucić wszystkiego do prompta? [odpowiedź o tokenach i skalowalności]"

---

## SLAJD 8 — Narzędzia (Tool Calling)
**Tytuł:** Anna potrafi działać, nie tylko mówić  
**Treść (tabela):**

| Narzędzie | Akcja |
|---|---|
| `check_spa_availability` | Sprawdza wolne terminy |
| `book_spa_appointment` | Rezerwuje zabieg |
| `check_room_availability` | Sprawdza pokoje |
| `send_sms_summary` | Wysyła potwierdzenie |
| `cancel_spa_appointment` | Anuluje zabieg (50% <2 h, 0% medycznie) |
| `reschedule_spa_appointment` | Zmienia termin zabiegu |
| `transfer_to_simulated_handoff` | Symulowane przekazanie do recepcji (brak SIP) |

**Uwaga:** razem 7 narzędzi webhook + wbudowane `end_call`.

**Visual:** Diagram 2 (sequence diagram — uproszczony do 3-4 kroków)  
**Uwaga:** „Webhooki trafiają do backendu który symuluje PMS. Pokażę to za chwilę."

---

## SLAJD 9 — DEMO (live)
**Tytuł:** Demo — 3 minuty, 3 ścieżki  
**Treść:** (minimal — tu mówisz, nie czytasz)
- Ścieżka A: Rezerwacja masażu + SMS
- Ścieżka B: Pytanie informacyjne (RAG)
- Ścieżka C: Eskalacja przy przeciwwskazaniu medycznym

**Visual:** QR code do widgetu lub zdjęcie panelu ElevenLabs  
**Uwaga:** Miej gotowy fallback (screeny + diagram) jeśli demo padnie.

---

## SLAJD 10 — Bezpieczeństwo i RODO
**Tytuł:** Enterprise ready — dane medyczne, RODO, skala  
**Treść:**
- **Zero Retention Mode** — audio i transkrypcje tylko w RAM
- **Conversation History Redaction** — automatyczne maskowanie PII
- **Data Residency EU** — serwery w regionie UE, DPA
- **Signed URLs** — widget bez exposowania klucza API

**Visual:** Ikony (lock, EU flag, shield)  
**Uwaga:** „Dla zarządu uzdrowiska to często decydujący argument."

---

## SLAJD 11 — Skalowanie na Sieć Hoteli
**Tytuł:** Jeden agent, dziesięć hoteli  
**Treść:**
- Dynamic Variables + Overrides: jeden centralny agent
- `conversation_initiation_client_data` — pakiet inicjalizacyjny per hotel
- SIP UUI (RFC 7433) — metadane hotelu w sygnalizacji telefonicznej
- Dodanie nowego hotelu = konfiguracja zmiennych, nie nowy agent

**Visual:** Diagram 4 (multi-hotel architecture)  
**Uwaga:** „Tu jest realna oszczędność kosztów utrzymania. Zamiast 10 agentów do zarządzania — jeden."

---

## SLAJD 12 — Koszty i ROI
**Tytuł:** Koszty — PoC za cenę kawy, skala za cenę etatu  
**Treść:**

| | PoC | Produkcja |
|---|---|---|
| Plan | Creator ($22/mies) | Scale ($299/mies) |
| Minuty | 275 min | 3 738 min |
| Concurrent calls | 10 | 30 (+Burst 3x) |

- **Break-even:** 275 min = $22 ≈ 3,5 h pracy recepcjonisty (~25 PLN/h) — parytet kosztu, nie oszczędność
- **24/7 bez chorobowego** — recepcjonista AI nie bierze urlopu

**Visual:** Prosta kalkulacja: koszt miesięczny AI vs. 0.5 etatu recepcjonisty  
**Uwaga:** „ROI nie jest w minutach. Jest w tym że hotel może zaoferować rezerwację o 2 w nocy."

---

## SLAJD 13 — Roadmapa
**Tytuł:** Co dalej — MVP → Faza II → Faza III  
**Treść:**
- **MVP (teraz):** RAG + mockupy, 3 ścieżki, demo działa
- **Faza II:** PMS integracja (KWHotel/Opera), Twilio SMS, PBX routing, DE/EN
- **Faza III:** Outbound AI — dzwoni do gości przed przyjazdem, potwierdza transport

**Visual:** Oś czasu lub 3-kolumnowa tabela  
**Uwaga:** „Faza III to zmiana roli — agent przestaje tylko odpowiadać, zaczyna inicjować kontakt."

---

## SLAJD 14 — Pytania
**Tytuł:** Pytania?  
**Visual:** Kontakt + link do repo / dokumentacji  
**Uwaga:** Miej pod ręką: `02_tok_myslenia_v1.md` z odpowiedziami na trudne pytania.
