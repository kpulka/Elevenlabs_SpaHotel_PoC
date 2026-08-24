# Prompt: Wytyczne UI dla Strony Internetowej Hotelu „Bukowy Dwór"

> **Jak używać tego pliku:**
> Skopiuj sekcję „PROMPT" i wklej ją do wybranego AI (ChatGPT, Claude, Gemini itp.).
> Prompt jest samodzielny — AI nie potrzebuje żadnych dodatkowych plików.

---

## PROMPT

---

Jesteś ekspertem UI/UX i design systems. Masz stworzyć kompletne wytyczne UI (design guidelines) dla strony internetowej luksusowego polskiego uzdrowiska termalnego.

---

### KONTEKST — Kim jest klient i kto odwiedza stronę

**Hotel:** Uzdrowisko Termalne „Bukowy Dwór"
**Lokalizacja:** ul. Zdrojowa 15, Krynica-Zdrój (południe Polski, region górski)
**Charakter:** Resort medyczno-wypoczynkowy klasy premium. Nie jest to typowy hotel — to miejsce leczenia, regeneracji i spokoju. Goście przyjeżdżają na kilkudniowe lub kilkutygodniowe pobyty sanatoryjne.
**Oferta:** Pokoje (jednoosobowy 350 PLN/noc, dwuosobowy 500 PLN/noc, apartament 750 PLN/noc), strefa SPA z basenami termalnymi (32°C i 34°C), zabiegi balneologiczne (kąpiele siarczkowe, borowinowe, jonoforeza, masaże lecznicze), restauracja z dietami leczniczymi (cukrzycowa, lekkostrawna, bezglutenowa).

**Główna grupa docelowa: seniorzy 60+**
- Wolą telefon od aplikacji, ale korzystają z internetu żeby się zapoznać z ofertą przed zadzwonieniem
- Mają obniżoną precyzję dotyku i gorzej widzą małe fonty
- Szukają konkretnych informacji: ceny, zabiegi, dojazd, dostępność architektoniczna
- Podejmują decyzje wolniej — potrzebują poczucia bezpieczeństwa i zaufania, nie presji sprzedażowej
- Często korzystają ze strony razem z dorosłymi dziećmi (córka/syn pomaga zarezerwować)

**Druga grupa: opiekunowie i rodziny** (30–55 lat) — szukają miejsca dla rodzica, ważna jest dla nich wiarygodność i bezpieczeństwo medyczne.

---

### OSOBOWOŚĆ MARKI — Tone & Feel

Bukowy Dwór to nie spa w modnym hotelu miejskim. To:
- **Ciepłe** — jak rozmowa z doświadczoną pielęgniarką, nie z concierge'em
- **Spokojne** — zero flashowych animacji, zero pop-upów z odliczaniem
- **Wiarygodne** — zdjęcia prawdziwych przestrzeni, konkretne informacje, nie marketingowy bełkot
- **Dostępne** — dosłownie (architektonicznie) i wizualnie (czytelność)
- **Luksusowe, ale nie ostentacyjne** — premium przez materiały i przestrzeń, nie przez logo

Słowa które opisują markę: **spokój, leczenie, natura, zaufanie, ciepło, regeneracja**
Słowa których unikamy: dynamiczny, innowacyjny, trendy, nowoczesny, premium (jako pusty przymiotnik)

---

### SYSTEM KOLORÓW — Ustalona paleta (obowiązkowa, nie zmieniaj)

Paleta została ustalona podczas projektowania widgetu głosowego Anny i musi być spójna ze stroną:

**Kolory podstawowe:**
| Nazwa | Hex | Zastosowanie |
|---|---|---|
| Navy (granat) | `#1B2A4A` | Nagłówki, header strony, stopka, przyciski CTA |
| Cream (krem) | `#F5F0E8` | Tło główne strony, tło kart |
| Gold (złoto) | `#C9A84C` | Akcenty, obramowania kart, ikony, dekoracyjne linie |
| Sage Green (szałwia) | `#7A9E7E` | Potwierdzenia, elementy pozytywne, ikona „aktywny" widgetu |

**Kolory pomocnicze:**
| Nazwa | Hex | Zastosowanie |
|---|---|---|
| Warm White | `#FDFAF5` | Tło sekcji jasnych, karty |
| Lavender Grey | `#C4C4D4` | Bańki czatu Anny, elementy drugorzędne |
| Warm Beige | `#E8DCC8` | Bańki czatu gościa, hover state |
| Deep Charcoal | `#2C2C2C` | Tekst główny (nie czarny — zbyt twardy) |
| Muted Grey | `#8A8A8A` | Tekst drugorzędny, timestamps, etykiety |
| Error Red | `#C0392B` | Tylko błędy — nigdzie indziej |

**Reguły kolorów:**
- Tło strony: Cream (`#F5F0E8`), nie białe
- Tekst na jasnym tle: Deep Charcoal (`#2C2C2C`) — kontrast min. WCAG AA (4.5:1)
- Tekst na Navy: biały (`#FFFFFF`)
- Gold jako akcent — używaj oszczędnie (max 10% powierzchni), nie jako tło tekstu
- Nigdy nie używaj czystego czarnego `#000000` — zbyt agresywny dla tej marki

---

### TYPOGRAFIA

**Zasada nadrzędna: czytelność > estetyka. Zawsze.**

**Font główny (body):** Serif o humanistycznym charakterze — sugestia: **Lora**, **Merriweather** lub **Playfair Display** dla nagłówków + **Source Serif 4** lub **Georgia** dla treści. Alternatywa: **Inter** (sans-serif) jeśli czytelność ma absolutny priorytet.

**Font pomocniczy (UI, przyciski, etykiety):** Sans-serif — **Inter**, **Nunito** lub **DM Sans**

**Skala typograficzna (minimalna — możesz zwiększyć, nie zmniejszaj):**

| Element | Rozmiar | Weight | Line-height |
|---|---|---|---|
| H1 (hero) | 48–64px desktop / 32px mobile | 700 | 1.2 |
| H2 (sekcja) | 36–40px / 26px | 600 | 1.3 |
| H3 (karta, podsekcja) | 24–28px / 20px | 600 | 1.4 |
| Body (treść) | **18px** / **16px** | 400 | **1.7** |
| Body small (opisy, meta) | **16px** / 14px | 400 | 1.6 |
| Label (przyciski, etykiety) | 15–16px / 14px | 500–600 | 1.4 |
| Caption (timestampy, footnotes) | 13–14px | 400 | 1.5 |

**Zasady:**
- Minimum 18px dla treści głównej — senior musi czytać bez powiększania
- Line-height minimum 1.6 dla bloków tekstowych
- Maksymalna szerokość kolumny tekstu: 680px (nie rozciągaj na pełną szerokość)
- Letter-spacing dla nagłówków: lekko rozstrzelony (+0.02em) dla czytelności
- Nigdy nie używaj `font-weight: 100` ani `200` — zbyt cienkie dla seniorów

---

### KOMPONENTY UI

#### 1. NAWIGACJA (Header)

**Desktop:**
- Pełna szerokość, sticky (przylepia się przy scrollowaniu)
- Tło: Navy `#1B2A4A`
- Logo: lewo, białe
- Menu: środek lub prawo, białe linki, 16px, letter-spacing: 0.05em
- CTA przycisk: „Zarezerwuj pobyt" — Gold obramowanie, biały tekst, hover: Gold fill
- Pozycje menu: Pokoje | SPA & Zabiegi | Restauracja | Dojazd & Dostępność | Kontakt
- Bez mega-menu — prosta, płaska nawigacja

**Mobile:**
- Hamburger menu (3 poziome linie, nie X)
- Po otwarciu: pełnoekranowe overlay, Navy tło, duże pozycje menu (min 48px touch target)
- Telefon recepcji widoczny bez otwierania menu: `+48 18 123 45 67` (klikalne)

#### 2. HERO SECTION

- Pełna szerokość, wysokość: 85vh desktop / 60vh mobile
- Tło: zdjęcie basenu termalnego lub strefy SPA — ciepłe, naturalne oświetlenie (jantarowe, mgła nad wodą, kamień i zieleń)
- Overlay gradient: Navy semi-transparentny od dołu (góra przezroczysta → dół 60% opacity)
- Treść wycentrowana lub lewa kolumna:
  - Mały tag: „Uzdrowisko Termalne · Krynica-Zdrój" (Gold, 14px, uppercase, letter-spacing)
  - H1: „Miejsce, gdzie ciało wraca do równowagi" (biały, Playfair/Serif)
  - Podnagłówek: krótki, konkretny (biały, 18px, nie slogan marketingowy)
  - Dwa przyciski: [Zarezerwuj pobyt] (Gold fill) + [Poznaj zabiegi SPA] (biały outline)
- Bez karuzeli / sliderów — jeden statyczny kadr, spokój

#### 3. KARTY (pokoje, zabiegi, oferty)

- Tło: Warm White `#FDFAF5`
- Zaokrąglone rogi: `border-radius: 16px`
- Obramowanie: 1px solid Gold `#C9A84C` z opacity 0.3
- Cień: `box-shadow: 0 4px 24px rgba(27,42,74,0.08)` — subtelny, nie dramatyczny
- Struktura karty:
  - Zdjęcie (górna część, 60% karty, object-fit: cover)
  - Treść (dolna część, padding 24px):
    - Kategoria: mały tag (Gold text, 12px uppercase)
    - Tytuł (H3, Navy)
    - Opis (Body, Deep Charcoal, max 3 linie + „Czytaj więcej")
    - Cena (jeśli dotyczy): duża, Navy bold + „/ noc" lub „/ zabieg" small
    - CTA: [Szczegóły] lub [Zarezerwuj] — Navy fill lub Gold outline
- Hover: karta lekko unosi się (`transform: translateY(-4px)`), cień się wzmacnia — płynnie, 200ms

#### 4. PRZYCISKI

| Typ | Styl | Użycie |
|---|---|---|
| Primary | Navy fill, biały tekst, `border-radius: 8px` | Główne CTA: „Zarezerwuj" |
| Secondary | Gold obramowanie 2px, Navy tekst | Drugorzędne: „Szczegóły", „Dowiedz się więcej" |
| Ghost | Biały obramowanie, biały tekst | Na ciemnych tłach (hero) |
| Danger | Error Red fill | Tylko anulowanie, błędy |

**Wymiary:** min `height: 52px`, padding `16px 32px`, font 16px medium
**Touch target:** min `48×48px` — senior z mniej precyzyjnym dotykiem
**Hover:** jaśnienie o 10%, cursor: pointer, transition 150ms
**Disabled:** opacity 0.4, cursor: not-allowed — ale unikaj disabled buttonów, lepiej wyjaśnij dlaczego akcja jest niemożliwa

#### 5. FORMULARZE (rezerwacja, kontakt)

- Input height: min 52px (nie standardowe 40px)
- Label: zawsze nad polem, nigdy placeholder zamiast labela
- Placeholder: tylko przykład formatu (np. „np. 15.09.2026"), nie nazwa pola
- Focus state: Gold obramowanie 2px, subtelny cień
- Error state: Error Red obramowanie, komunikat błędu poniżej pola (tekst, nie tylko kolor)
- Pola obowiązkowe: oznaczone tekstem „(wymagane)", nie tylko gwiazdką
- Układ: jeden kolumna na mobile, max dwie kolumny na desktop — nie przeładowuj
- Przycisk submit: szerokość 100% na mobile, min 200px na desktop

#### 6. SEKCJA DOSTĘPNOŚCI ARCHITEKTONICZNEJ

To sekcja krytyczna dla grupy docelowej — wyróżnij ją wizualnie.
- Dedykowana sekcja na stronie głównej i stronie „Dojazd"
- Tło: lekko różne od reszty (Cream z delikatną granicą lub Gold strip po lewej)
- Ikony: proste, jednoliniowe (brak barier, winda, poręcze, parking)
- Tekst konkretny: „Brak progów w całym obiekcie", „4 windy z komunikatami głosowymi", „10 szerokich miejsc parkingowych dla osób z niepełnosprawnościami"
- Nie używaj eufemizmów — „dostępność" to funkcja, nie wstydliwy temat

#### 7. WIDGET GŁOSOWY ANNY (integracja na stronie)

Na wszystkich podstronach (nie tylko głównej) w prawym dolnym rogu:

**Floating button (stan zamknięty):**
- Kształt: zaokrąglona pigułka lub okrąg, min 56px
- Kolor: Gold `#C9A84C` lub Navy z Gold akcentem
- Ikona: mikrofon (nie dymek czatu — to agent głosowy, nie chatbot)
- Tekst: „Porozmawiaj z Anną" (widoczny na desktop, tylko ikona na mobile)
- Po 45 sekundach na stronie: jeden subtelny puls animacji (nie powtarzać)
- Pozycja: `position: fixed; bottom: 24px; right: 24px; z-index: 1000`

**Panel widgetu (stan otwarty) — spójność z istniejącym designem:**
- Rozmiar desktop: 380×560px floating panel
- Rozmiar mobile: fullscreen (100vw × 100vh)
- Header: Navy, avatar Anny (okrągłe zdjęcie/ilustracja), „Anna · Recepcja", ikony minimize + close
- Tło panelu: Cream `#F5F0E8`
- Bańki czatu Anny: Lavender Grey `#C4C4D4`, lewa strona
- Bańki czatu gościa: Warm Beige `#E8DCC8`, prawa strona
- Quick reply chips: Warm White tło, Gold obramowanie 1px, Navy tekst, `border-radius: 24px`
- Chip specjalny „... Inny": przerywaną linią, Muted Grey tekst
- Progress bar: 4 kroki (Język → Temat → Szczegóły → Potwierdzenie), Gold fill dla aktywnych
- Action bar: trzy przyciski — [Napisz] grey outline / [🎙️ Mów] Sage Green fill aktywny / [Zadzwoń] grey outline
- Success screen: zielony check, Gold border karta z danymi rezerwacji

**Inline banner (na stronie SPA i Rezerwacje):**
- Nad formularzem lub listą zabiegów
- Tło: Warm White, Gold lewa krawędź 3px
- Tekst: „🎙️ Wolisz zapytać głosowo? Anna pomoże Ci zarezerwować zabieg."
- Przycisk: [Porozmawiaj z Anną] — Navy fill

#### 8. STOPKA (Footer)

- Tło: Navy `#1B2A4A`
- Tekst: biały, Gold akcenty na linkach hover
- Struktura 4 kolumny desktop / 2 kolumny tablet / 1 kolumna mobile:
  - Kolumna 1: Logo + krótki opis + ikony social media
  - Kolumna 2: Szybkie linki (Pokoje, SPA, Restauracja, Kontakt)
  - Kolumna 3: Kontakt (adres, telefon klikalny, email, godziny recepcji)
  - Kolumna 4: Dojazd + mapa (miniatura Google Maps)
- Subfooter: „© 2026 Bukowy Dwór · Polityka prywatności · RODO"
- Telefon recepcji: duży, klikalny, wyróżniony — senior musi go znaleźć bez szukania

---

### STRONY DO ZAPROJEKTOWANIA

Wygeneruj wytyczne dla następujących widoków:

1. **Strona główna** — hero, sekcja wyróżnionych cech (dostępność, 24/7, lokalizacja), karty pokoi, karty SPA, sekcja restauracji (mini), sekcja dostępności architektonicznej, CTA kontaktowe, stopka
2. **Pokoje** — lista kart pokoi z filtrem (typ, termin), szczegóły pokoju (galeria, wyposażenie, cena, formularz rezerwacji)
3. **SPA & Zabiegi** — lista zabiegów z cenami i czasem trwania, info o basenach, sekcja opieki medycznej, inline widget Anny
4. **Restauracja** — godziny posiłków, diety lecznicze (tablety/karty), room service
5. **Dojazd & Dostępność** — mapa, adres, transport meleksem, parking, lista udogodnień dla osób z niepełnosprawnościami
6. **Kontakt / Rezerwacja** — formularz kontaktowy, formularz rezerwacji pokoju, inline widget Anny, telefon i email

---

### ZASADY LAYOUTU I SIATKI

- **Siatka:** 12-kolumnowa, max-width kontenera: `1280px`, guttery: `32px` desktop / `16px` mobile
- **Sekcje:** padding pionowy `96px` desktop / `64px` mobile — dużo przestrzeni, nie upychaj
- **Obrazy:** zawsze z `alt` opisem, lazy-loading, format WebP z fallback JPEG
- **Animacje:** tylko `transition` i `transform`, max 300ms, `prefers-reduced-motion` — wyłącz dla tych co tego potrzebują
- **Scroll:** płynny, nie podrygujący. Unikaj parallax — dezorientuje seniorów

---

### DOSTĘPNOŚĆ (WCAG AA — obowiązkowe)

- Kontrast tekstu: min **4.5:1** dla tekstu normalnego, **3:1** dla dużego (>18px bold lub >24px)
- Focus visible: wyraźny focus ring (Gold `2px solid #C9A84C` lub Navy) — nie usuwaj outline CSS
- Nawigacja klawiaturą: cała strona obsługiwalna Tab/Shift-Tab/Enter/Space
- Skip link: „Przejdź do treści" jako pierwszy element strony (widoczny przy focus)
- Obrazy dekoracyjne: `alt=""`, obrazy treściowe: opisowy alt
- Formularze: każde pole z `<label>`, błędy powiązane przez `aria-describedby`
- Przyciski: zawsze z czytelną etykietą (nie tylko ikoną)
- Język strony: `<html lang="pl">`

---

### CZEGO UNIKAĆ

❌ **Pop-upy i overlaye** przy wejściu na stronę — senior się denerwuje i zamyka zakładkę
❌ **Animacje autoplay** (wideo, slidery) — dekoncentrują i dezorientują
❌ **Odliczanie i „ostatnie wolne miejsca"** — presja sprzedażowa niszczy zaufanie tej grupy
❌ **Małe fonty jako „elegancja"** — poniżej 16px to wykluczenie, nie styl
❌ **Zbyt wiele kolorów** — trzymaj się palety, Gold używaj oszczędnie
❌ **Zdjęcia stockowe ze sztucznymi uśmiechami** — używaj autentycznych zdjęć przestrzeni i natury
❌ **Chatbot-owy język dla Anny** — widget to recepcjonistka, nie bot. Nigdzie słowo „chatbot"
❌ **Wyskakujące okna cookie consent bez możliwości odrzucenia** — RODO i UX
❌ **Hamburger menu na desktop** — seniorzy lubią widzieć wszystkie opcje naraz
❌ **Ceny ukryte za „zapytaj o ofertę"** — podaj konkretne ceny. Brak cen = brak zaufania

---

### FORMAT ODPOWIEDZI

Wygeneruj:

1. **Design Tokens** — kompletna lista zmiennych CSS (kolory, typografia, spacing, border-radius, shadows) w formacie `:root { --zmienna: wartość; }`

2. **Wytyczne dla każdej strony** — dla każdej z 6 stron: układ sekcji, które komponenty, kolejność treści, szczególne uwagi UX

3. **Component Checklist** — lista wszystkich komponentów UI z ich stanami (default, hover, focus, active, disabled, error)

4. **Accessibility Checklist** — lista rzeczy do sprawdzenia przed publikacją

5. **Do/Don't lista** — 10 konkretnych par „rób to / nie rób tego" specyficznych dla tej marki i grupy docelowej

Odpowiadaj po polsku. Bądź konkretny — podawaj wartości px, hex, nazwy właściwości CSS. Unikaj ogólników.
