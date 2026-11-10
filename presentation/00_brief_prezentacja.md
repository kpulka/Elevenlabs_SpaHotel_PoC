# Brief: Prezentacja „Wirtualny Recepcjonista AI — Bukowy Dwór"

> **Dla kogo jest ten dokument:**
> Dla AI lub człowieka, który ma zbudować prezentację PowerPoint/Google Slides.
> Zawiera pełną specyfikację — co ma być na każdym slajdzie, w jakiej formie i dlaczego.
>
> **Pliki źródłowe (przeczytaj przed tworzeniem):**
> - `docs/plan_implementacji_recepcjonisty.md` — źródło prawdy technicznej
> - `docs/specyfikacja_recepcjonista_ai.md` — spec funkcjonalna
> - `docs/anna_system_prompt_v3.md` — system prompt gotowy do wklejenia
> - `presentation/01_diagram_architektury.md` — 5 diagramów Mermaid (architektura, sequence, multi-hotel…)
> - `presentation/02_tok_myslenia_v1.md` — tok myślenia V1, odpowiedzi na trudne pytania, liczby ROI
> - `presentation/03_narracja_demo.md` — skrypt 3 ścieżek demo + fallbacki
> - `presentation/04_slajdy_outline.md` — outline 14 slajdów
> - `presentation/05_v2_problem_understanding.md` — pytania do problem understanding (V2)
> - `presentation/06_v2_excalidraw.md` — co rysować w Excalidraw i jak (V2)
> - `presentation/07_ux_design.md` — UX: journey map + widget spec + stany błędów + quick reply chips

---

## KONTEKST — po co ta prezentacja istnieje

Rekrutacja na stanowisko **Deployment Strategist w ElevenLabs** — firma tworząca AI do głosu.
Dwa etapy wymagają materiałów:

- **V1 (Etap 1):** Rozmowa + interaktywne case study. Rekruter chce zobaczyć jak kandydat myśli, łączy technikę z biznesem, pcha projekt do przodu.
- **V2 (Etap 2):** Product design + wireframing (Excalidraw) + system design + rozmowa z Hiring Managerem.

**Prezentacja służy do obu etapów** — jako materiał przygotowawczy i jako artefakt do pokazania podczas sesji.

---

## WYMAGANIA FORMALNE

- **Format:** PowerPoint (.pptx) lub Google Slides (preferowany, łatwiejszy do udostępnienia)
- **Liczba slajdów:** 12–14 (bez okładki i slajdu Q&A: 10–12 merytorycznych)
- **Język:** Polski
- **Styl wizualny:** Minimalistyczny, ciemny lub jasny motyw (nie korporacyjny clipart). Priorytet: czytelność i profesjonalizm. Dużo białej przestrzeni, mała liczba bullet pointów.
- **Reguła:** Max 5 linii tekstu na slajd. Reszta — w notatce prezentera.
- **Diagramy:** Mermaid z pliku `01_diagram_architektury.md` do przełożenia na statyczne obrazy lub zachowania jako kod (jeśli narzędzie to obsługuje).

---

## WYMAGANIA MERYTORYCZNE — czego szuka rekruter

### V1 sprawdza:
1. Czy kandydat rozumie **platformę ElevenLabs** (STT, LLM, TTS, tool calling, RAG, handoff)?
2. Czy potrafi **przełożyć architekturę na wartość biznesową**?
3. Czy myśli o **wdrożeniu u dużego klienta** (skalowanie, RODO, failover, metryki)?
4. Czy pokazuje **tok myślenia** a nie gotowy produkt?

### V2 sprawdza:
1. Czy kandydat umie **zdekompozycja problemu** (pytania zanim odpowiedź)?
2. Czy potrafi **wireframować** (prosto, prostokąty i tekst)?
3. Czy rozumie **system design** (diagram integracji, wzorce architektoniczne)?
4. Czy jest **otwarty na współpracę** podczas sesji (nie monologuje)?

**Prezentacja powinna to wszystko demonstrować — przez strukturę, nie przez deklaracje.**

---

## SPECYFIKACJA SLAJDÓW

---

### SLAJD 1 — Okładka

**Tytuł (duży):** Wirtualny Recepcjonista AI  
**Podtytuł:** Case study: ElevenLabs Conversational AI × Uzdrowisko Termalne „Bukowy Dwór"  
**Visual:** Jeden element graficzny — np. fala dźwiękowa lub mikrofon; absolutne minimum tekstu  
**Dolny pasek:** [Twoje imię i nazwisko] · Deployment Strategist Case Study · [data]  
**Notatka prezentera:** „Zacznam od 30 sekund kontekstu biznesowego — nie od architektury."

---

### SLAJD 2 — Problem (biznesowy, nie techniczny)

**Tytuł:** Senior czeka. Recepcja nie odbiera.

**Treść (max 4 bullet):**
- Uzdrowiska i hotele SPA: 60–70% gości to seniorzy 60+ — wolą telefon od aplikacji
- Szczyt połączeń: 8:00–10:00 i 16:00–18:00 — kolejka, oczekiwanie, frustracja
- Niezrealizowana rezerwacja = utracony przychód (zabieg SPA: 80–160 zł)
- Recepcjonista: ~25 zł/h, dostępny 8h/dobę, nie dzwoni do gości przed przyjazdem

**Visual:** Prosty wykres słupkowy — „Godziny połączeń vs. godziny dyżuru" lub ilustracja: stary telefon z zegarem  
**Czego NIE robić:** Nie pisać słowa „AI" ani „chatbot" na tym slajdzie — to slajd o problemie, nie rozwiązaniu  
**Notatka prezentera:** „Zanim powiem jak to rozwiązałem — jakie pytania macie do problemu? [pauza]"

---

### SLAJD 3 — Persona użytkownika

**Tytuł:** Kto dzwoni? Pani Zofia, 72 lata.

**Layout:** Dwie kolumny — lewa: avatar/ilustracja; prawa: 4 cechy  
**Treść (prawa kolumna):**
- Mówi wolno, robi pauzy w środku zdania
- Nie pamięta nazw zabiegów — pyta „ten masaż co na kręgosłup"
- Jeśli agent jej przerwie lub się myli — rozłącza się
- Chce potwierdzenie na SMS — najlepiej do córki, nie do siebie

**Pod tabelką (1 zdanie, wyróżnione):** „Każda decyzja architektoniczna w tym projekcie wynika z tej persony."

**Notatka prezentera:** „To nie jest wymyślona persona. To jest prototyp gościa sanatoryjnego. Wszystko co zaraz pokażę — od tempa mowy, przez timeout ciszy, po parafrazowanie — wynika z tej jednej kartki."

---

### SLAJD 4 — Rozwiązanie (1 zdanie + diagram wysokopoziomowy)

**Tytuł:** Anna — recepcjonistka dostępna 24/7

**Treść (środek slajdu, duże):**
> ElevenLabs Conversational AI: natywna pętla STT + LLM + TTS  
> Latencja: ~430 ms · Głos: ciepły, zwolniony · Dostępny: całą dobę

**Visual:** Diagram 1 z `01_diagram_architektury.md` — główny przepływ (uproszczony: Gość → ElevenLabs → Narzędzia → Gość)  
**Czego NIE robić:** Nie wyjaśniać tu szczegółów — to slajd „co", nie „jak"  
**Notatka prezentera:** „Za chwilę pokażę to na żywo. Najpierw powiem dlaczego wybrałem taką architekturę — a nie łatwiejszą."

---

### SLAJD 5 — Dlaczego taka architektura? (decyzje projektowe)

**Tytuł:** 3 decyzje architektoniczne — i ich uzasadnienie

**Layout:** Tabela 3 wiersze

| Decyzja | Dlaczego |
|---|---|
| Natywny agent ElevenLabs, nie Custom LLM | Kaskadowy pipeline (STT→LLM→TTS): >2s opóźnienie. Natywna pętla: ~430ms. Dla seniora każda sekunda ciszy = utrata zaufania. |
| TTS: Eleven v3 Conversational (nie Flash) | Flash: 75ms, ale robotyczny ton. v3: 280ms, ale ekspresja emocjonalna. Dla 70-latka ciepło głosu > prędkość. |
| `turn_timeout 3s`, `speed 0.85x`, `Patient` | Default: 1–1.5s. Senior robi pauzy w środku zdania. 1.5s → agent wchodzi w słowo → gość się rozłącza. |

**Notatka prezentera:** „Każda z tych decyzji to trade-off. Pokażę co wybrałem i dlaczego — ale jeśli macie inne zdanie, chętnie porozmawiam."

---

### SLAJD 6 — Baza Wiedzy (RAG) + Strict Grounding

**Tytuł:** Co Anna wie — i jak wie, że nie wie

**Treść lewa kolumna (RAG):**
- 5 plików Markdown: dojazd, SPA, pokoje, restauracja, procedury
- Tryb `prompt` (zawsze w kontekście): cennik + procedury
- Tryb `auto` (semantic search): opisy zabiegów i dojazd
- Powód: skalowanie do setek dokumentów bez zmiany kodu

**Treść prawa kolumna (Strict Grounding):**
- Brak informacji w bazie = **transfer do recepcji** (nigdy zmyślanie)
- Protokół bezpieczeństwa: przed zabiegiem balneologicznym → pytanie o przeciwwskazania
- Powód: zmyślona cena = problem sprzedażowy; zmyślone przeciwwskazanie = ryzyko prawne

**Visual:** Ikona dokumentu → strzałka → ikona magnifiera (RAG) lub ikona tarczy (grounding)  
**Notatka prezentera:** „To jest najważniejszy slajd. W branży medycznej AI która zmyśla jest gorsze niż brak AI."

---

### SLAJD 7 — Tool Calling (co Anna potrafi zrobić)

**Tytuł:** Anna nie tylko mówi — działa

**Tabela (5 wierszy):**

| Narzędzie | Co robi | Typ |
|---|---|---|
| `check_spa_availability` | Sprawdza wolne terminy zabiegu | Webhook → mock PMS |
| `book_spa_appointment` | Rezerwuje zabieg | Webhook → mock PMS |
| `check_room_availability` | Sprawdza dostępność pokoi | Webhook → mock PMS |
| `send_sms_summary` | Wysyła potwierdzenie SMS / Telegram | Webhook → bramka |
| `transfer_to_simulated_handoff` | Symulowane przekazanie do recepcji / dyżurki (log + alert Telegram) | Webhook (brak SIP w PoC) |

**Visual:** Mały sequence diagram (Diagram 2 — 3-4 kroki, nie pełny)  
**Notatka prezentera:** „Webhooki trafiają do backendu który na PoC symuluje PMS. Pokażę to za chwilę."

---

### SLAJD 8 — Demo (live lub screeny)

**Tytuł:** Demo — 3 ścieżki, 3 minuty

**Treść (minimal — tu prezentujesz, nie czytasz):**
- **A.** Rezerwacja zabiegu SPA + potwierdzenie Telegram
- **B.** Pytanie informacyjne (baza wiedzy, bez halucynacji)
- **C.** Eskalacja — gość zgłasza przeciwwskazanie medyczne → transfer LIVE

**Visual:** Screenshoty panelu ElevenLabs (lista narzędzi, system prompt, baza wiedzy) LUB QR code do widżetu  
**Notatka prezentera:** Pełny skrypt w `presentation/03_narracja_demo.md`. Miej fallback (screeny odpowiedzi JSON) jeśli coś padnie.

---

### SLAJD 8b — UX i Widget Webowy

**Tytuł:** Dwa kanały, jeden głos

**Layout:** Dwie kolumny

**Lewa kolumna — Telefon (SIP):**
- Odbiór natychmiastowy, 24/7
- turn_timeout 3s — Anna nie przerywa
- Parafrazowanie przed każdym potwierdzeniem
- SMS potwierdzający (opcja: do opiekuna)

**Prawa kolumna — Widget na stronie www:**
- Floating button „Porozmawiaj z Anną"
- Avatar z animacją stanu (słucha / mówi / czeka)
- Quick reply chips przy pytaniach zamkniętych
- Transkrypcja live + success card z danymi rezerwacji

**Visual:** Mockup widgetu (stan aktywnej rozmowy z chipami językowymi) — plik z `presentation/assets/`  
**Notatka prezentera:** „Ten sam agent, ta sama Anna. Dwa kanały — telefon dla seniorów którzy wolą dzwonić, widget dla gości którzy przeglądają stronę. Zero duplikacji konfiguracji."

---

### SLAJD 9 — Bezpieczeństwo i RODO

**Tytuł:** Enterprise ready — dane medyczne, RODO

**4 bullet (z ikonami):**
- 🔒 **Zero Retention Mode** — audio i transkrypcje tylko w RAM, nie na dyskach ElevenLabs
- 🕶️ **Conversation History Redaction** — automatyczne maskowanie nazwisk, telefonów, danych medycznych
- 🇪🇺 **Data Residency EU** — przetwarzanie w regionie UE, pełne DPA
- 🔑 **Signed URLs** — widget nie eksponuje głównego klucza API (ważność tokenu: 15 min)

**Jedno zdanie podsumowujące (wyróżnione):** „Dla zarządu uzdrowiska to często decydujący argument — nie funkcje, lecz compliance."  
**Notatka prezentera:** „ZRM i Redaction to plan Enterprise. Na PoC wyjaśniam jak to działa i co klient musi zamówić."

---

### SLAJD 10 — Skalowanie na sieć hoteli

**Tytuł:** Jeden agent, dziesięć hoteli — bez powielania

**Treść lewa (problem bez Dynamic Variables):**
- 10 hoteli → 10 osobnych agentów
- 10 baz wiedzy do aktualizowania
- 10 konfiguracji do utrzymania

**Treść prawa (rozwiązanie):**
- Jeden centralny agent „Anna"
- Pakiet inicjalizacyjny per hotel: `hotel_name`, `location`, `reception_phone`, `pms_id`
- Telefonia: metadane w sygnalizacji SIP (RFC 7433, UUI header)
- Dodanie hotelu = zmiana konfiguracji zmiennych, nie nowy agent

**Visual:** Diagram 4 z `01_diagram_architektury.md` (multi-hotel)  
**Notatka prezentera:** „To jest kluczowy argument biznesowy dla sieci. ROI z wdrożenia na 10 hoteli jest prawie identyczny jak na 1."

---

### SLAJD 11 — Koszty i ROI

**Tytuł:** Koszty — PoC za $22, skala za $299

**Tabela:**

| | PoC / Demo | Produkcja |
|---|---|---|
| Plan | Creator ($22/mies.) | Scale ($299/mies.) |
| Minuty w pakiecie | 275 min | 3 738 min |
| Jednoczesne połączenia | 10 | 30 (+Burst: 90) |

**Kalkulacja ROI (poniżej tabeli):**
- 275 minut = ok. 4,5h obsługi; $22 odpowiada ok. 3,5 h pracy recepcjonisty (~25 PLN/h ≈ $6/h)
- Agent AI: 24/7, zero zwolnień, zero „już nie odbieram"
- Dodatkowy przychód: rezerwacja zabiegów o 22:00 — niemożliwa bez AI

**Wyróżnione zdanie:** „ROI nie jest w minutach. Jest w rezerwacjach które trafiają o 23:00."  
**Notatka prezentera:** „Nie sprzedaję oszczędności — sprzedaję nowy kanał przychodu."

---

### SLAJD 12 — Roadmapa

**Tytuł:** Co dalej — MVP → Faza II → Faza III

**Oś czasu lub 3 kolumny:**

| MVP (gotowe) | Faza II | Faza III |
|---|---|---|
| RAG + mockupy | Integracja PMS (Opera/KWHotel) | Outbound AI |
| 3 ścieżki demo | Twilio SMS (produkcja) | Dzwoni do gości przed przyjazdem |
| Transfer do człowieka | PBX routing (recepcja vs dyżurka) | Potwierdza transport |
| — | Wielojęzyczność (DE/EN) | Personalizacja historyczna |

**Notatka prezentera:** „Faza III to zmiana roli — agent przestaje odpowiadać, zaczyna inicjować. To jest produkt outbound dla sieci hoteli, nie tylko infolinia."

---

### SLAJD 13 — Pytania / Dyskusja

**Tytuł:** Pytania?

**Treść:** absolutne minimum — nazwa/logo, ewentualnie kontakt  
**Visual:** Nic lub prosta ilustracja  
**Notatka prezentera:** Otwórz dyskusję aktywnie: „Chętnie pogłębię dowolny wątek — architekturę, koszty, UX seniorów, RODO. Co Was interesuje najbardziej?"

---

## NOTATKI DLA BUDOWNICZEGO SLAJDÓW

### Styl i tone of voice
- **Nie piszemy** „rozwiązanie zapewnia", „system umożliwia", „platforma oferuje" — to korporacyjny bełkot
- **Piszemy** aktywnie: „Anna sprawdza", „gość słyszy", „zabieg zostaje zarezerwowany"
- Slajdy mówią językiem **wartości biznesowej**, notatki prezentera — językiem technicznym
- Żadnych skrótów bez rozwinięcia przy pierwszym użyciu (STT = Speech-to-Text, itp.)

### Wizualizacje
- Diagramy Mermaid z `01_diagram_architektury.md` — przekształć w statyczne obrazy (mermaid.live lub podobne)
- Ikony: Font Awesome lub podobny zestaw — spójny styl przez całą prezentację
- Paleta kolorów: 2-3 kolory max. Sugestia: ciemnogranatowy + pomarańczowy akcent + biały tekst

### Co NIE powinno być na slajdach (zostaje w notatkach)
- Dokładne wartości parametrów (`turn_timeout: 3.0`, `stability: 0.80`) — do notatek lub osobnego slajdu technicznego jeśli rekruter poprosi
- Pełne schematy JSON — do notatek lub aneksu
- Szczegóły mock backendu — wystarczy wzmianka że „backend symuluje PMS"

### Aneks (opcjonalny, nie prezentować jeśli nie zapytają)
- Slajd A1: Pełny stack technologiczny (Diagram 5 z `01_diagram_architektury.md`)
- Slajd A2: Sequence diagram rezerwacji krok po kroku (Diagram 2)
- Slajd A3: JSON Schema narzędzi (copy-paste z planu implementacji)
- Slajd A4: System prompt Anny (fragment — `docs/anna_system_prompt_v3.md`)

---

## CHECKLIST — przed wysłaniem prezentacji

- [ ] Każdy slajd ma max 5 linii tekstu
- [ ] Każdy slajd ma notatki prezentera (co powiedzieć, czego nie czytać)
- [ ] Diagramy są czytelne w skali slajdu (test: czy widać z 2 metrów?)
- [ ] Nie ma słowa „chatbot" — to agent głosowy, nie bot
- [ ] Sekcja RODO jest na osobnym slajdzie (nie schowana w bullet)
- [ ] Roadmapa pokazuje Fazę III (outbound) — to „wow" na koniec
- [ ] Slajd z kosztami zawiera kalkulację ROI, nie tylko tabelkę cennika
- [ ] Deck działa jako samodzielny dokument (można przesłać emailem bez prezentera)
