# Inwentaryzacja dokumentów + niespójności do ujednolicenia

## 1. Inwentaryzacja

| Plik | Typ | Rola | Status |
|---|---|---|---|
| `ElevenLabs_Etap_V1.md` | Wytyczne | Rozmowa + case study (Deployment Strategist) | Źródło celu |
| `ElevenLabs_Etap_V2.md` | Wytyczne | Product design + wireframing + system design + HM | Źródło celu |
| `specyfikacja_poc_recepcjonista_ai.md` | Spec (PoC) | Prototyp demo z mockupami (3 ścieżki) | Do scalenia |
| `specyfikacja_recepcjonista_ai.md` | Spec (pełna) | Docelowy produkt (5 obszarów + architektura) | Do scalenia |
| `01_informacje_ogolne_i_dojazd.md` | RAG | Dojazd, architektura, parking | Spójny |
| `02_katalog_zabiegow_spa_i_zdrowie.md` | RAG | Basen, zabiegi, opieka medyczna | Spójny |
| `03_pokoje_i_cennik.md` | RAG | Pokoje, ceny, zaliczki | Spójny |
| `04_restauracja_i_diety.md` | RAG | Gastro, diety, room service | Spójny |
| `05_procedury_i_polityki.md` | RAG | Anulacje, SMS, zwierzęta | Spójny |

## 2. Relacje między dokumentami

- **Spec PoC** = wersja „demo", mockupy (`rooms.json`, `spa_schedule.json`), nacisk na SPA + 3 ścieżki pokazowe.
- **Pełna spec** = stan docelowy, rozbudowana architektura (PMS, bramka SMS, PBX), senior UX, roadmapa MVP/Faza II.
- **RAG (5 plików)** = baza wiedzy hotelu „Bukowy Dwór" — zasila scenariusz informacyjny i kontekst agenta.
- **Etap V1/V2** = brief rekrutacyjny; case study to najpewniej *ten* recepcjonista AI.

## 3. Niespójności do rozstrzygnięcia

### 3.1 Persona agenta
- PoC: „Pani Anna" (lub bezosobowy żeński głos).
- Pełna spec: „Wirtualna Recepcjonistka **Danuta**".
- **Decyzja:** jedna nazwa w całej prezentacji.

### 3.2 Zestaw narzędzi (tool calling)
| PoC | Pełna spec |
|---|---|
| `check_spa_availability(service, date)` | `check_room_availability(...)`, `send_sms_summary` |
| `book_spa_appointment(...)` | — |
| `trigger_sms(...)` | `send_sms_summary(...)` |
| `transfer_to_human(reason)` | `transfer_to_human(department, reason)` |
- **Decyzja:** jedna kanoniczna tabela narzędzi z JSON Schema (pokoje + SPA + SMS + handoff).

### 3.3 Głos (voice)
- PoC: Rachel/Nicole, model **Turbo v2.5**.
- Pełna spec: ciepły, spokojny głos (brak konkretnego modelu).
- **Decyzja:** jeden wybór głosu + modelu do prezentacji.

### 3.4 Zakres / dojrzałość
- PoC = tylko ścieżki demo (mockupy, „sztywne terminy").
- Pełna spec = pełne wdrożenie (PMS, RODO, roadmapa).
- **Decyzja:** co prezentujemy — czysty PoC, czy „PoC → wizja docelowa" (zalecane: to drugie, bo pokazuje myślenie architektoniczne zgodnie z V1/V2).

### 3.5 Grupa docelowa / cel
- Oba zgodne: seniorzy 60+, hotele uzdrowiskowe SPA. (Brak konfliktu.)

## 4. Co NIE wymaga zmian
- Pliki RAG (5 plików) są wewnętrznie spójne i dobrze ustrukturyzowane.
- Wytyczne V1/V2 pozostają bez zmian (to brief).

## 5. Wynik ujednolicenia (ZREALIZOWANE ✅)

Dodano nowy, bardziej szczegółowy dokument **`docs/plan_implementacji_recepcjonisty.md`** (od agenta znającego ElevenLabs) — stał się źródłem prawdy technicznej. Rozstrzyga wszystkie 5 niespójności powyżej:

1. **Persona** → **Anna** ✅
2. **Narzędzia** → kanoniczny zestaw: `check_spa_availability`, `book_spa_appointment`, `check_room_availability`, `send_sms_summary`, `transfer_to_human` ✅
3. **Głos** → Jessica — Playful, Bright, Warm (`cgSgspJ2msm6clMCkdW9`), Eleven v3 Conversational, stability 0.80 / similarity 0.75 / speed 0.85 ✅
4. **Zakres** → „PoC → wizja docelowa" ✅
5. **RAG** → tryby `prompt` (05, 03) vs `auto` (01, 02, 04) + strict grounding ✅

W wyniku scalenia:
- **`specyfikacja_recepcjonista_ai.md`** = kanoniczna spec funkcjonalna (scalona, spójna z planem).
- **`specyfikacja_poc_recepcjonista_ai.md`** = oznaczony **ZDEPRECJONOWANY** (archiwum).
- **`plan_implementacji_recepcjonisty.md`** = źródło prawdy technicznej (modele, parametry, JSON Schema, koszty).