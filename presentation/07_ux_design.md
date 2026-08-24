# UX Design — Wirtualny Recepcjonista Anna

Dwa kanały, dwa UX. Ten dokument pokrywa oba.

---

## KANAŁ 1 — TELEFON (SIP / Infolinia)

W tym kanale nie ma żadnego UI. UX = wyłącznie projektowanie konwersacji.

---

### User Journey Map — Telefon

#### Faza 0: Przed połączeniem

| Etap | Co robi gość | Stan emocjonalny | Punkt styku |
|---|---|---|---|
| Decyzja o zadzwonieniu | Szuka numeru w folderze / na kartce przy telefonie w pokoju | Neutralny, lekko niepewny technologii | Numer na materiałach drukowanych hotelu |
| Wybieranie numeru | Dzwoni na recepcję | Oczekiwanie — czy odbiorą? | Sygnał oczekiwania |

**Ryzyko UX:** Jeśli gość czeka dłużej niż 4 sygnały → odkłada słuchawkę. Anna musi odebrać natychmiast.

---

#### Faza 1: Pierwsze sekundy (krytyczne)

| Etap | Anna mówi | Cel UX | Czego unikać |
|---|---|---|---|
| Odebranie | „Dzień dobry, tu Anna z recepcji Bukowego Dworu. W czym mogę Panu/Pani pomóc?" | Ciepłe przywitanie, jasna tożsamość | Długie intro, wymienienie godzin pracy, IVR-owy ton |
| Identyfikacja problemu | Słucha. Nie przerywa. | Gość musi poczuć że jest słyszany | Natychmiastowe pytanie zwrotne zanim gość skończy |

**Parametry techniczne które realizują ten UX:**
- `turn_timeout: 3.0s` — Anna czeka 3 sekundy ciszy zanim odpowie
- `turn_eagerness: Patient` — nie wchodzi w słowo przy naturalnych pauzach
- `first_message` wypowiadane spokojnie, `speed: 0.85x`

---

#### Faza 2: Obsługa (happy path — rezerwacja zabiegu)

```
Gość: "Chciałbym zarezerwować masaż."
         ↓
Anna: "Chętnie. Jaki rodzaj masażu Pana interesuje?"   ← 1 pytanie
         ↓
Gość: "Ten... na kręgosłup."
         ↓
Anna: "Rozumiem — masaż leczniczy pleców. Na który dzień?"   ← parafrazuje + 1 pytanie
         ↓
Gość: [cisza 2 sekundy] "No... może na środę."
         ↓                  ↑
         |         turn_timeout: 3s — Anna czeka, nie przerywa
Anna: [wywołuje narzędzie] "Sprawdzam... Mam wolne: 10:00, 14:30 i 15:00. Która godzina?"
         ↓
Gość: "14:30."
         ↓
Anna: "Jak się Pan nazywa?"
         ↓
Gość: "Kowalski, Jan."
         ↓
Anna: "Świetnie. Rezerwuję masaż leczniczy pleców
       na środę 27 sierpnia o 14:30 dla Pana Jana Kowalskiego.
       Czy zgadza się?"   ← PARAFRAZOWANIE przed potwierdzeniem
         ↓
Gość: "Tak."
         ↓
Anna: [book()] "Gotowe! Numer rezerwacji: SPA-4821.
       Na jaki numer wysłać potwierdzenie?
       Możemy też wysłać do córki lub syna."   ← opcja dla opiekuna
```

**Zasady UX konwersacji (telefon):**
- **Jeden krok, jedno pytanie** — nigdy „Kiedy i na jaki zabieg?"
- **Zawsze parafrazuj** przed potwierdzeniem akcji — eliminuje błędy i buduje zaufanie
- **Podaj numer potwierdzenia głosowo** — senior go nie zapisze, ale poczuje bezpieczeństwo
- **Zaoferuj SMS do opiekuna** — wiele seniorów woli żeby córka/syn miała potwierdzenie

---

#### Faza 3: Stany błędów i edge cases

**Błąd 1 — Anna nie rozumie (1× nierozumienie):**
```
Anna: "Przepraszam, nie dosłyszałam. Czy mógłby Pan powtórzyć?"
```
Spokojnie, bez słów „błąd" lub „problem".

**Błąd 2 — Anna nie rozumie (2× z rzędu):**
```
Anna: "Przepraszam za kłopot. Żeby ułatwić — czy chodzi o zabieg SPA,
       informację o hotelu, czy coś innego?"
```
Upraszcza — daje opcje zamiast pytania otwartego.

**Błąd 3 — Anna nie rozumie (3× z rzędu):**
```
Anna: "Przepraszam za niedogodność. Połączę Pana teraz z recepcją,
       gdzie na pewno uzyska Pan pomoc."
       → transfer_to_human()
```
Po 3 nieudanych próbach — zawsze eskalacja. Bez dalszych prób.

**Błąd 4 — Webhook nie odpowiada (PMS timeout):**
```
Anna: "Chwileczkę, sprawdzam dostępność..."
      [jeśli timeout po 5s]
      "Przepraszam, mam chwilową przerwę w połączeniu z systemem rezerwacji.
       Połączę Pana z recepcją, która sprawdzi to bezpośrednio."
       → transfer_to_human()
```

**Błąd 5 — Brak dostępności:**
```
Anna: "Niestety o 14:30 nie ma wolnego miejsca.
       Mam dostępne: 10:00 lub 16:00 — która godzina bardziej Panu odpowiada?"
```
Zawsze podaje alternatywę, nigdy nie kończy na „brak".

---

#### Faza 4: Zakończenie rozmowy

| Sytuacja | Anna mówi |
|---|---|
| Pomyślna rezerwacja | „Dziękuję za kontakt. Do zobaczenia w środę! Życzę miłego dnia." |
| Tylko informacja | „Cieszę się, że mogłam pomóc. Gdyby miał Pan więcej pytań — proszę dzwonić. Do usłyszenia!" |
| Po eskalacji | „Łączę z recepcją. Chwileczkę proszę." [cisza / muzyka → recepcja przejmuje] |
| Gość się żegna | „Do widzenia, życzę przyjemnego pobytu!" |

---

#### Faza 5: Po rozmowie (SMS)

```
SMS / Telegram:

🏨 Bukowy Dwór — Potwierdzenie

Panie Janie,
rezerwacja przyjęta ✅

📋 Masaż leczniczy pleców
📅 Środa, 27 sierpnia 2026
🕑 14:30
🔑 Nr rezerwacji: SPA-4821

Centrum SPA — parter, prawa strona od recepcji.
Prosimy o przybycie 5 minut wcześniej.

W razie pytań: tel. +48 18 123 45 67
```

**Zasady UX SMS:**
- Krótki, emoji jako wizualne anchory (senior skanuje, nie czyta)
- Numer rezerwacji widoczny od razu
- Instrukcja gdzie się stawić (senior nie pamięta)
- Numer telefonu na wypadek pytań

---

---

## KANAŁ 2 — WIDGET WEBOWY (strona hotelu)

Tu mamy pełne UI. Projektujemy je od zera.

---

### Kontekst użycia

Gość przegląda stronę hotelu (często na komputerze, czasem na tablecie).
Widzi stronę → pojawia się subtelna opcja rozmowy → klika → zaczyna rozmawiać z Anną.

**Kluczowa różnica vs telefon:**
- Gość ma ekran — może czytać i słuchać jednocześnie
- Możemy pokazywać transkrypcję na żywo
- Możemy wyświetlić potwierdzenie na ekranie (nie tylko SMS)
- Gość może kliknąć zamiast mówić (dla tych co nie chcą mówić)

---

### Trigger — jak pojawia się widget

**Opcja A (rekomendowana): Floating button**

W prawym dolnym rogu strony, zawsze widoczny:

```
┌──────────────────────────────────┐
│                                  │
│         [treść strony]           │
│                                  │
│                    ╔═══════════╗ │
│                    ║ 💬 Porozmawiaj ║ │
│                    ║   z Anną  ║ │
│                    ╚═══════════╝ │
└──────────────────────────────────┘
```

- Kolor: ciepły, kontrastowy (nie agresywny czerwony)
- Tekst: „Porozmawiaj z Anną" — nie „Chatbot", nie „AI Assistant"
- Po 45 sekundach na stronie: delikatna animacja pulsowania przycisku (raz)

**Opcja B: Inline banner na stronie rezerwacji**

Na podstronie „Rezerwacje" lub „SPA", nad formularzem:
```
╔══════════════════════════════════════════════╗
║ 🎙️ Wolisz zapytać głosowo?                   ║
║ Anna pomoże Ci zarezerwować zabieg.  [Zadzwoń] ║
╚══════════════════════════════════════════════╝
```

---

### UI Widgetu — anatomia okna rozmowy

Po kliknięciu przycisku pojawia się panel rozmowy. Oto jego pełna specyfikacja:

```
╔═══════════════════════════════════════╗
║  🏨 Anna — Recepcja Bukowego Dworu  ✕ ║  ← HEADER
╠═══════════════════════════════════════╣
║                                       ║
║         ┌─────────────────┐           ║
║         │   AVATAR ANNY   │           ║  ← AVATAR ZONE
║         │  (animowany     │           ║
║         │   podczas mowy) │           ║
║         └─────────────────┘           ║
║         🟢 Anna słucha...             ║  ← STATUS
║                                       ║
╠═══════════════════════════════════════╣
║  TRANSKRYPCJA (live):                 ║  ← TRANSCRIPT ZONE
║  ┌─────────────────────────────────┐  ║
║  │ Anna: Dzień dobry! W czym mogę  │  ║
║  │       Panu/Pani pomóc?          │  ║
║  │                                 │  ║
║  │ Ty: Chciałbym zarezerwować...   │  ║  ← live, pojawia się
║  │                                 │  ║     w trakcie mówienia
║  └─────────────────────────────────┘  ║
╠═══════════════════════════════════════╣
║  [🎙️ Mów]   [⌨️ Napisz]   [📞 Zadzwoń] ║  ← ACTION BAR
╚═══════════════════════════════════════╝
```

---

### Szczegółowa specyfikacja elementów UI

#### HEADER
- Lewa strona: avatar Anny (małe kółko, ciepłe zdjęcie/ilustracja) + „Anna · Recepcja"
- Prawa strona: przycisk ✕ (zamknij) — zawsze widoczny
- Kolor tła: ciemny granat lub biel — spójny z brandem hotelu
- Wysokość: 56px

#### AVATAR ZONE
- Środek panelu, dominujący element
- Stany animacji:
  - **Idle (czeka):** subtelne oddychanie / delikatny puls obrysu
  - **Słucha (gość mówi):** fale dźwiękowe wokół avatara, kolor zielony
  - **Mówi (Anna odpowiada):** usta (jeśli ilustracja) się ruszają LUB intensywniejsza animacja fal, kolor niebieski
  - **Myśli (wywołuje narzędzie):** spinner / delikatny obrót, kolor szary
- Opcje realizacji: animated SVG illustration (prosto) LUB Lottie animation (bogato) LUB D-ID / HeyGen avatar wideo (premium)
- Rozmiar: 120×120px w widoku desktop, 80×80px mobile

#### STATUS BAR (pod avatarem)
Dynamiczny tekst jednej linii:
- `🟢 Anna słucha...` — gdy gość mówi
- `🔵 Anna odpowiada...` — gdy TTS gra
- `⚪ Anna sprawdza dostępność...` — gdy tool calling w toku
- `🟡 Łączę z recepcją...` — podczas transferu

#### TRANSCRIPT ZONE
- Scrollowalna, max 40% wysokości panelu
- Bańki konwersacji: prawa (gość) / lewa (Anna) — klasyczny chat bubble layout
- Transkrypcja gościa pojawia się na żywo (streaming, słowo po słowie)
- Transkrypcja Anny pojawia się po zakończeniu wypowiedzi (nie w trakcie TTS)
- Można wyłączyć / schować (checkbox „Pokaż transkrypcję" dla tych co nie chcą czytać)
- Czcionka: min 16px (senior), line-height: 1.6

#### ACTION BAR (dolny pasek)
Trzy przyciski:

**[🎙️ Mów]** — główny CTA, największy
- Domyślnie aktywny (mikrofon włączony automatycznie po otwarciu widgetu)
- Stan aktywny: podświetlony, animacja fali
- Stan wyciszony: szary, ikona przekreślonego mikrofonu
- Kliknięcie: toggle mikrofonu (dla tych co chcą pauzować)

**[⌨️ Napisz]** — fallback dla tych co nie chcą mówić
- Kliknięcie: transcript zone zamienia się w pole tekstowe + przycisk „Wyślij"
- Anna odpowiada głosowo (TTS) na wpisany tekst
- Powód istnienia: goście w głośnym miejscu, goście z problemami z mową, preferencje

**[📞 Zadzwoń]** — opcjonalny, dla tych co wolą zwykły telefon
- Kliknięcie: otwiera `tel:+48181234567` (na mobile dzwoni bezpośrednio)
- Powód istnienia: zawsze dawaj opcję wyjścia do klasycznego telefonu

---

### Stany ekranu widgetu

**Stan 1 — Inicjalizacja (pierwsze 1-2 sekundy):**
```
╔═══════════════════════╗
║  🏨 Anna — Bukowy...  ║
╠═══════════════════════╣
║     [ładowanie...]    ║
║    ⠋ Łączę z Anną    ║
╚═══════════════════════╝
```

**Stan 2 — Aktywna rozmowa:** (opisany wyżej — główny widok)

**Stan 3 — Potwierdzenie rezerwacji (po book()):**
```
╔═══════════════════════════════════════╗
║  🏨 Anna — Bukowy Dwór             ✕ ║
╠═══════════════════════════════════════╣
║                                       ║
║         ✅ Rezerwacja potwierdzona!   ║
║                                       ║
║  📋 Masaż leczniczy pleców            ║
║  📅 Środa, 27 sierpnia · 14:30        ║
║  🔑 SPA-4821                          ║
║                                       ║
║  [📱 Wyślij potwierdzenie SMS]        ║
║  [💬 Zadaj kolejne pytanie]           ║
║  [✕ Zamknij]                          ║
╚═══════════════════════════════════════╝
```
- Zielone tło potwierdzenia — jasny sygnał sukcesu
- Trzy akcje: SMS, dalej rozmawiaj, zamknij

**Stan 4 — Transfer do człowieka:**
```
╔═══════════════════════════════════════╗
║  🏨 Anna — Bukowy Dwór             ✕ ║
╠═══════════════════════════════════════╣
║                                       ║
║    👤 Łączę z recepcją...             ║
║    Proszę pozostać na linii.          ║
║                                       ║
║    Lub zadzwoń bezpośrednio:          ║
║    📞 +48 18 123 45 67                ║
║                                       ║
╚═══════════════════════════════════════╝
```

**Stan 5 — Błąd połączenia:**
```
╔═══════════════════════════════════════╗
║  🏨 Anna — Bukowy Dwór             ✕ ║
╠═══════════════════════════════════════╣
║                                       ║
║    ⚠️ Problem z połączeniem           ║
║                                       ║
║    [🔄 Spróbuj ponownie]              ║
║    [📞 Zadzwoń: +48 18 123 45 67]     ║
║                                       ║
╚═══════════════════════════════════════╝
```
Zawsze dawaj numer telefonu jako fallback — nigdy nie zostawiaj gościa bez wyjścia.

---

### Responsywność

| Urządzenie | Zachowanie widgetu |
|---|---|
| Desktop | Floating panel 380×560px, prawy dolny róg |
| Tablet | Floating panel 340×500px lub fullscreen modal |
| Mobile | Fullscreen (100vw × 100vh), dolny pasek z przyciskami |

---

### Dostępność (Accessibility — ważne dla grupy 60+)

- **Czcionka min. 16px**, nagłówki 20px+ — nie zmniejszaj dla estetyki
- **Kontrast min. WCAG AA** (4.5:1) — ciemny tekst na jasnym tle lub odwrotnie
- **Przyciski min. 48×48px** touch target — senior ma mniej precyzji dotykową
- **Aria-labels** na wszystkich elementach interaktywnych
- **Nie autoplay audio bez zgody** — zapytaj mikrofon przy pierwszym otwarciu przez przeglądarkę (Web Audio API wymaga user gesture)
- **Widoczny focus indicator** — dla użytkowników klawiatury / czytników ekranu

---

## PORÓWNANIE — TELEFON vs WIDGET

| Aspekt | Telefon | Widget webowy |
|---|---|---|
| UI | Brak (czysty głos) | Pełne UI (avatar, transkrypcja) |
| Dostęp | Numer na materiałach hotelu | Floating button na stronie |
| Profil gościa | Senior, comfort zone | Każdy wiek, aktywnie przeglądający |
| Transkrypcja | Niedostępna | Live, scrollowalna |
| Potwierdzenie | SMS po rozmowie | Na ekranie + opcjonalny SMS |
| Fallback przy błędzie | Transfer do człowieka | Transfer + numer telefonu na ekranie |
| Implementacja | ElevenLabs SIP Trunk + PBX | ElevenLabs SDK (WebSocket) + Signed URL |
| Czas wdrożenia (PoC) | 1 dzień (natywna integracja) | 2-3 dni (frontend + backend Signed URL) |

---

## CO DODAĆ DO PREZENTACJI

Na slajd UX (po slajdzie z personą):

**Slajd „Dwa kanały, jeden głos":**
- Lewa kolumna: ikona telefonu + „Telefon (SIP)" + kluczowe zasady UX (3 bullet)
- Prawa kolumna: mockup widgetu webowego (stan aktywnej rozmowy)
- Pod spodem: „Ten sam agent, ta sama Anna — inne UI, ta sama jakość obsługi"

Wireframe widgetu (Szkic 4 do Excalidraw — opcjonalny, jeśli rekruter zapyta o web UX).
