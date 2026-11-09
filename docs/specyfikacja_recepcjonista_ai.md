> **Status:** aktualny (2026-11) — źródło prawdy dla zakresu funkcjonalnego (CO robi produkt).

# Specyfikacja Funkcjonalna: Wirtualny Recepcjonista Głosowy AI „Anna" — Sieć Hoteli & SPA

> **Dokument kanoniczny.** Łączy wymagania biznesowe + specyfikę grupy docelowej (seniorzy 60+) z możliwościami platformy **ElevenLabs Agents (Conversational AI)**.
> Szczegóły techniczne (modele, parametry akustyczne, schematy JSON, koszty) znajdują się w **`plan_implementacji_recepcjonisty.md`** — to on jest źródłem prawdy technicznej.
> Niniejsza spec definiuje CO robi produkt; plan implementacji definiuje JAK jest skonfigurowany.

**Platforma:** ElevenLabs Agents (Conversational AI)
**Persona:** Anna
**Profil gościa:** seniorzy 60+, osoby ceniące spokój, goście z potrzebami medyczno-rehabilitacyjnymi
**Środowisko:** hotele wielooddziałowe, ośrodki uzdrowiskowe, resorty termalne
**Pilot:** Uzdrowisko Termalne „Bukowy Dwór", Krynica-Zdrój

---

## 1. Koncepcja Systemu

System realizuje zadania recepcjonisty hotelowego w kanale głosowym. Na platformie ElevenLabs łączy:
- natywny silnik konwersacyjny (**ElevenLabs Agents**) — STT + LLM orchestrator + TTS w jednej pętli konwersacyjnej,
- bazę wiedzy (**RAG** — 5 plików Markdown),
- narzędzia (**Tool Calling / Webhook**) do PMS/SPA/bramki SMS,
- natywne przekierowanie połączeń (**Human Handoff**).

### Stack modeli (szczegóły w planie implementacji §1.2)
| Warstwa | Wybór |
|---|---|
| STT | Scribe v2 Realtime (~150 ms) |
| LLM | GPT-4o Mini lub Gemini 2.5 Flash |
| TTS | Eleven v3 Conversational (~280 ms, wysoka ekspresja) |

> Cel: zminimalizować latencję przy zachowaniu naturalnej, ciepłej barwy głosu — kluczowej dla seniorów.

---

## 2. Persona i Głos („Anna")

- **Imię:** Anna.
- **Głos (PoC):** głos premade **Jessica — Playful, Bright, Warm** (ID: `cgSgspJ2msm6clMCkdW9`), albo dedykowany głos z **Voice Design**.
- **Parametry głosu:** stability `0.80`, similarity_boost `0.75`, speed `0.85x`.
- **Styl:** empatyczny, niespieszny, bardzo uprzejmy; zero żargonu („wiadomość tekstowa na telefon" zamiast „SMS z linkiem płatności").

### Parametry akustyczne dla seniora (turn-taking)
- `turn_timeout` = **3.0 s** (dłuższe okno ciszy — rozmówca mówi wolniej),
- `turn_eagerness` = **Patient** (nie przerywa, cierpliwie czeka na dane).

---

## 3. Zakres Funkcjonalny

### 3.1. Rezerwacje i dostępność
- Weryfikacja dostępności pokoi (preferencja parter/winda dla seniorów).
- Kalkulacja cen (pakiety lecznicze, zniżki sanatoryjne/lojalnościowe).
- Rezerwacje pokoi i zabiegów SPA; polityka zadatków (30%) i anulacji (14 dni).

### 3.2. Usługi medyczne, SPA i wellness
- Zapisy na zabiegi balneologiczne, masaże, konsultacje.
- Pytania przesiewowe o przeciwwskazania zdrowotne przed potwierdzeniem zabiegu.
- Infrastruktura basenowa (temperatury wód, łagodne wejścia, podnośniki).

### 3.3. Gastronomia i diety
- Diety lecznicze (cukrzycowa, lekkostrawna, bezglutenowa/bezmleczna) → karta gościa.
- Godziny posiłków, pomoc kelnerska, bezpłatny room service przy niedyspozycji.

### 3.4. Informacje praktyczne i dojazd
- Nawigacja punktowa („obok starej pijalni wód", „droga płaska").
- Bezpłatny transfer meleksem z dworca (zgłoszenie min. 24 h).
- Dostępność architektoniczna (brak progów, windy z komunikatami głosowymi).

### 3.5. Reklamacje, pomoc i zgłoszenia awaryjne
- Zgłoszenia usterki/potrzeby (poduszkę ortopedyczną, krzesełko pod prysznic).
- Awaria zdrowotna → natychmiastowe łączenie z dyżurką (gabinet 101) / numerem alarmowym.

---

## 4. Scenariusze Demonstracyjne (PoC)

Na potrzeby prezentacji agent płynnie obsłuży 3 ścieżki (dane z mockupów):

**A. Rezerwacja SPA** — gość pyta o masaż; agent sprawdza terminy (mock), proponuje godziny, zbiera dane (krok po kroku), parafrazuje ustalenia, potwierdza i wysyła „SMS" (webhook Telegram/WhatsApp).

**B. Informacyjna (RAG)** — gość pyta o godziny posiłków / czy basen wymaga czepka; agent odpowiada wyłącznie z bazy wiedzy.

**C. Eskalacja (Human Handoff)** — nietypowa prośba / skarga / wymogi medyczne → agent rozpoznaje brak kompetencji i przekierowuje do „prawdziwej recepcji" (transfer do numeru).

---

## 5. KANONICZNY Zestaw Narzędzi (Tool Calling)

Pełne schematy JSON — w planie implementacji §4. Lista spójna dla PoC i wersji docelowej:

| Narzędzie | Rola | Typ |
|---|---|---|
| `check_spa_availability` | wolne godziny zabiegu SPA | Webhook (mock PMS) |
| `book_spa_appointment` | zapis zabiegu SPA | Webhook (mock PMS) |
| `check_room_availability` | wolne pokoje w terminie | Webhook (mock PMS) |
| `send_sms_summary` | podsumowanie rezerwacji na telefon | Webhook (Telegram/WhatsApp PoC → Twilio Faza II) |
| `transfer_to_human` | przekierowanie do recepcji/dyżurki | natywne `transfer_to_number` |

---

## 6. Baza Wiedzy (RAG)

Pięć plików Markdown (Bukowy Dwór). Przypisanie trybów (`usage_mode`):

| Tryb | Pliki | Uzasadnienie |
|---|---|---|
| `prompt` (pełny kontekst, zawsze w promptcie) | `05_procedury_i_polityki.md`, `03_pokoje_i_cennik.md` | krytyczne ceny i procedury nie mogą zostać pominięte przez RAG |
| `auto` (semantic search / RAG) | `01_informacje_ogolne_i_dojazd.md`, `02_katalog_zabiegow_spa_i_zdrowie.md`, `04_restauracja_i_diety.md` | obszerne opisy, wstrzykujemy tylko dopasowane fragmenty |

### Strict Grounding (eliminacja halucynacji)
Agent odpowiada w 100% w oparciu o bazę wiedzy i wyniki narzędzi. Brak informacji → uprzejma odmowa + `transfer_to_human`. Nigdy nie wymyśla cen, terminów ani diet.

---

## 7. Komunikacja SMS / Asystent Pobytu

- Agent pyta, na jaki numer wysyłać powiadomienia (gość lub opiekun — córka/syn).
- Rodzaje wiadomości: potwierdzenie + zaliczka, przypomnienie 3 dni przed przyjazdem (+transport), harmonogram zabiegów wieczorem.
- **PoC:** Telegram/WhatsApp webhook (efekt „wow" na drugim monitorze).
- **Faza II:** produkcyjne API Twilio SMS.

---

## 8. Skalowanie na Sieć Hoteli (Multi-obiektowość)

Jeden nadrzędny agent „Anna" + **Dynamic Variables / Overrides**: pakiet inicjalizacyjny `conversation_initiation_client_data` nadpisuje nazwę hotelu, lokalizację, telefon recepcji i ID hotelu. Dla telefonii: metadane w sygnalizacji SIP (**UUI, RFC 7433**). → jeden agent, wiele obiektów, bez powielania konfiguracji. (Szczegóły: plan implementacji §5.)

---

## 9. Bezpieczeństwo i RODO

1. **Signed URLs** (`/get_signed_url`, ważność 15 min) — widget nie używa głównego klucza API.
2. **Zero Retention Mode (ZRM)** — audio + transkrypcje tylko w RAM, bez zapisu na dyskach (Enterprise).
3. **Conversation History Redaction** — automatyczne maskowanie danych osobowych/medycznych.
4. **Data Residency** — przetwarzanie w UE (DPA/RODO).
5. **Minimalizacja danych** — tylko imię, nazwisko, telefon, preferencje; zgoda ustna na dane wrażliwe.

---

## 10. Koszty i Limity (skrót)

| | PoC (demo) | Produkcja (Enterprise) |
|---|---|---|
| Plan | Creator (~$22/mies.) | Scale/Enterprise (~$299/mies.) |
| Minuty | 275 | 3 738 |
| Concurrent calls | 10 | 30 (+Burst Pricing do 90) |

Pełna tabela — plan implementacji §7.

---

## 11. Roadmapa Wdrożenia

### MVP / PoC (Faza 1)
1. RAG z kompletną bazą wiedzy (5 plików, tryby `prompt`/`auto`).
2. Narzędzia availability/booking na mockupach PMS.
3. Rezerwacje wstępne + SMS (webhook Telegram/WhatsApp).
4. Płynny transfer do żywego recepcjonisty (`transfer_to_number`).

### Faza II (rozszerzenie)
1. Integracja z systemem rozliczeń medycznych i e-kartoteką SPA.
2. Wielojęzyczność (DE/EN) z tym samym standardem empatii.
3. Outbound Voice AI — połączenia wychodzące przed przyjazdem (potwierdzenie + transport).
4. Produkcyjny Twilio SMS + routing PBX (recepcja vs dyżurka medyczna).

---

## 12. Odniesienia

- **Plan techniczny (źródło prawdy):** `plan_implementacji_recepcjonisty.md`
- **Baza wiedzy RAG:** `baza_wiedzy_rag_bukowy_dwor/` (5 plików)
- **Wytyczne rekrutacyjne:** `archive/ElevenLabs_Etap_V1.md`, `archive/ElevenLabs_Etap_V2.md` (archiwum)