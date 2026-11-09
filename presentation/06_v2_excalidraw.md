# V2 — Wireframing w Excalidraw: Co i Jak Rysować

> **Zasada Excalidraw wg briefu ElevenLabs V2:**
> „Prostokąty i tekst." Nic więcej. Rekruter ocenia TOK MYŚLENIA, nie estetykę.
> Zły wireframe narysowany pewnie i z komentarzem bije dobry narysowany w ciszy.
>
> **Jak działać:**
> Rysuj i mów jednocześnie. Każdy prostokąt który rysujesz — powiedz co to jest i dlaczego tu jest.

---

## CO RYSOWAĆ — 3 szkice w kolejności

Podczas sesji V2 prawdopodobnie będziesz mieć ~20-30 minut na wireframing.
Zaplanuj: **2 szkice obowiązkowe + 1 opcjonalny** jeśli zostanie czas.

---

## SZKIC 1 — Architektura Systemu (zacznij od tego, ~8 minut)

**Co to jest:** High-level diagram jak dane przepływają przez system.
**Dlaczego od tego:** Pokazuje że rozumiesz cały system zanim przejdziesz do UI.

### Co narysować (od lewej do prawej):

```
[ GOŚĆ / TELEFON ]  →→→  [ ELEVENLABS AGENT ]  →→→  [ MOCK / PMS ]
                               ↕           ↕
                          [ RAG / KB ]   [ SMS / TELEGRAM ]
                               ↕
                          [ RECEPCJA (human) ]
```

**Jak to rysować krok po kroku:**

1. **Zacznij od użytkownika** (lewy skraj): prostokąt z napisem „👴 Gość / Telefon (SIP)"
   - Powiedz: *„Zaczynam od użytkownika — senior dzwoni przez telefon."*

2. **Centralny blok** (środek): duży prostokąt „☁️ ElevenLabs Agent" z 3 małymi w środku: „STT | LLM | TTS"
   - Powiedz: *„To jest serce systemu — jedna zunifikowana pętla, nie trzy osobne serwisy."*

3. **Strzałka z opóźnieniem**: nad strzałką napisz „~430ms"
   - Powiedz: *„Latencja to kluczowy parametr dla seniorów."*

4. **Baza wiedzy** (pod centrum): prostokąt „📚 RAG / Knowledge Base" ze strzałką do agenta
   - Powiedz: *„Agent nigdy nie odpowiada z pamięci — zawsze odpytuje bazę wiedzy."*

5. **Narzędzia** (prawa strona): prostokąty „PMS / Rezerwacje", „SMS / Telegram", strzałki oznaczone „webhook"
   - Powiedz: *„Tool calling — agent może działać, nie tylko mówić."*

6. **Człowiek** (dolny prawy): prostokąt „👤 Recepcja / Dyżurka" ze strzałką „transfer_to_simulated_handoff"
   - Powiedz: *„Zawsze musi być opcja wyjścia do człowieka — szczególnie w kontekście medycznym."*

**Zamknij szkic zdaniem:** *„To jest MVP. Zanim przejdę do UI — czy ta architektura odpowiada na problem który zdefiniowaliśmy?"*

---

## SZKIC 2 — Przepływ Konwersacji (obowiązkowy, ~10 minut)

**Co to jest:** Diagram stanów rozmowy — co się dzieje po każdym kroku.
**Dlaczego:** Pokazuje że myślisz o edge cases i UX, nie tylko happy path.

### Co narysować:

```
[ START: Anna odbiera ]
         ↓
[ Rozpoznanie intencji ]
    ↙         ↘
[ Pytanie    [ Rezerwacja ]
  info ]          ↓
    ↓       [ Zbieranie danych
[ RAG ]       krok po kroku ]
    ↓              ↓
[ Odpowiedź ] [ Potwierdzenie ]
                   ↓
              [ Tool: book() ]
                   ↓
              [ Sukces / Błąd ]
                   ↓
              [ SMS wysyłka ]
```

**Jak rysować — szczegółowo:**

1. **Góra centrum:** „👋 Anna odbiera — First Message" (zaokrąglony prostokąt = start)

2. **Diament decyzyjny** (lub prostokąt z napisem „Klasyfikacja intencji"):
   - Napisz 3 wyjścia: „Pytanie informacyjne | Rezerwacja | Eskalacja"
   - Powiedz: *„LLM klasyfikuje intencję. Na podstawie tego wybiera ścieżkę."*

3. **Ścieżka lewa — RAG:**
   - „Semantic search w KB" → „Odpowiedź" → „Koniec lub dalej?"
   - Powiedz: *„Strict grounding — jeśli info nie ma w bazie, nie wymyśla."*

4. **Ścieżka środkowa — Rezerwacja:**
   - Kilka prostokątów połączonych strzałkami: „Jaki zabieg?" → „Jaka data?" → `check_availability()` → „Która godzina?" → „Imię i nazwisko?" → **Parafrazowanie** → `book()` → „SMS?"
   - Przy „Parafrazowanie" napisz ★ i powiedz: *„To jest kluczowy krok — Anna zawsze powtarza ustalenia zanim zarezerwuje."*

5. **Ścieżka prawa — Eskalacja:**
   - „Wykryto: sytuacja awaryjna / brak info / prośba o człowieka" → `transfer_to_simulated_handoff()` → „Recepcja przejmuje (symulacja)"
   - Powiedz: *„Zawsze deterministyczna — żaden warunek nie omija tej ścieżki."*

6. **Na dole dodaj notatkę:** „turn_timeout: 3s | turn_eagerness: Patient | speed: 0.85x"
   - Powiedz: *„Te parametry to UX decisions, nie techniczne detale — wynikają z persony seniora."*

**Zamknij:** *„Czy mam też pokazać jak wygląda panel konfiguracyjny dla managera hotelu?"*

---

## SZKIC 3 — Panel Zarządzania dla Hotelu (opcjonalny, ~8 minut)

**Co to jest:** Prosty mockup UI dla managera hotelu — jak konfiguruje i monitoruje Annę.
**Dlaczego wartościowy:** Pokazuje myślenie o operacyjnej stronie produktu, nie tylko o rozmowie.
**Kiedy rysować:** Jeśli rekruter pyta o „co widzi hotel od strony managementu" lub masz czas.

### Co narysować:

```
┌─────────────────────────────────────────────────────┐
│  BUKOWY DWÓR — Panel Zarządzania Anną               │
├────────────┬────────────────────────────────────────┤
│ NAWIGACJA  │  DASHBOARD — dzisiaj                   │
│            │  ┌──────────┐ ┌──────────┐ ┌────────┐ │
│ Dashboard  │  │ 47 rozmów│ │ 38 samo- │ │ 9 do  │ │
│ Rozmowy    │  │ dziś     │ │ obsłużo- │ │ czło- │ │
│ Baza wiedzy│  │          │ │ nych 81% │ │ wieka │ │
│ Narzędzia  │  └──────────┘ └──────────┘ └────────┘ │
│ Ustawienia │                                        │
│            │  OSTATNIE ROZMOWY                      │
│            │  ┌────────────────────────────────────┐│
│            │  │ 14:22 | Jan K. | Masaż | ✅ SPA-4821││
│            │  │ 14:05 | [red.] | Info  | ✅         ││
│            │  │ 13:47 | [red.] | Eskal.| → Recepcja││
│            │  └────────────────────────────────────┘│
└────────────┴────────────────────────────────────────┘
```

**Co narysować jako prostokąty:**

1. **Pasek boczny (sidebar):** prostokąt z listą: Dashboard / Rozmowy / Baza Wiedzy / Ustawienia

2. **3 karty KPI (top):**
   - „Rozmowy dziś: 47"
   - „Obsłużone bez człowieka: 81%"
   - „Przekazane do recepcji: 9"
   - Powiedz: *„To są KPI które uzgodniliśmy na początku — % obsługi bez człowieka."*

3. **Tabela ostatnich rozmów:**
   - Kolumny: Godzina | Gość | Typ | Status
   - Przy Gość: *„[red.]"* — powiedz: *„Imiona są zamaskowane automatycznie — Conversation History Redaction, RODO."*

4. **Sekcja Baza Wiedzy (osobny ekran, opcjonalnie):**
   - Lista plików z przyciskiem „Aktualizuj" i datą ostatniej modyfikacji
   - Powiedz: *„Manager hotelu może sam aktualizować cennik bez angażowania developera."*

**Zamknij:** *„To jest warstwa operacyjna — hotel widzi co Anna robi i może reagować. Bez tego narzędzia wdrożenie jest czarną skrzynką dla klienta."*

---

## ZASADY RYSOWANIA W EXCALIDRAW

### Techniczne
- Używaj tylko prostokątów, strzałek i tekstu — dosłownie zgodnie z briefem V2
- Strzałki mają etykiety (co przepływa: „audio", „JSON", „webhook", „transfer")
- Grupuj powiązane elementy w ramki (zaznaczenie grupy = jeden większy prostokąt)
- Zaokrąglone rogi = start/koniec przepływu; ostre = środkowe kroki

### Zachowanie podczas rysowania
- **Mów cały czas** — cisza podczas rysowania to stracona szansa
- **Pytaj** co 2-3 minuty: „Czy to kierunek który Cię interesuje, czy wolisz żebym pokazał [coś innego]?"
- **Nie mazgaj i nie przepraszaj** za estetykę — *„To jest świadomy szkic, nie projekt końcowy"*
- Jeśli zmienisz zdanie podczas rysowania — powiedz: *„Właśnie widzę że lepiej to zorganizować tak..."* — to jest PLUS, nie minus

### Timing (orientacyjny)
| Etap | Czas |
|---|---|
| Pytania (problem understanding) | 8–12 min |
| Szkic 1 — architektura | 7–10 min |
| Szkic 2 — przepływ konwersacji | 8–12 min |
| Szkic 3 — panel (opcjonalny) | 5–8 min |
| Dyskusja / doprecyzowanie | do końca |

---

## ZDANIA DO ZAPAMIĘTANIA

Na start rysowania:
> *„Zacznę od architektury wysokopoziomowej — chcę upewnić się, że mamy wspólne rozumienie systemu, zanim przejdę do konkretnych ekranów."*

Gdy pytają „dlaczego tak, nie inaczej?":
> *„Tę decyzję podjąłem z powodu [persony / kanału / ograniczenia] które ustaliliśmy na początku."*

Gdy nie wiesz jak coś narysować:
> *„Nie jestem pewien jak to najlepiej zwizualizować — czy wolisz żebym pokazał to jako diagram przepływu danych, czy jako makietę ekranu?"*

Gdy kończysz:
> *„To jest wersja MVP. Gdybyśmy mieli drugi sprint — dodałbym [X]. Ale celowo zostawiłem to poza zakresem żeby nie komplikować pierwszego wdrożenia."*
