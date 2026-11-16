# presentation/ — deck case study i materiał demo

Osobny deliverable: prezentacja case study „Wirtualny Recepcjonista AI — Bukowy Dwór" (portfolio: wdrożenie agenta głosowego ElevenLabs dla fikcyjnego uzdrowiska) plus surowce, z których powstała. Dokumentacja systemu jest w `docs/` (`docs/INDEX.md`).

**Co otworzyć pierwsze:**
- Online: [kpulka.github.io/anna-voice-agent](https://kpulka.github.io/anna-voice-agent/) — strona-wejście `index.html` z linkami do obu decków (GitHub Pages z tego katalogu, `.github/workflows/pages.yml`).
- `prezentacja.html` — wersja PL decku w przeglądarce, bez zależności (otwierasz ją podczas prezentacji). EN: `presentation_en.html`.
- `Bukowy_Dwor_Case_Study.pptx` / `Bukowy_Dwor_Case_Study_EN.pptx` — te same slajdy do edycji w PowerPoint/Google Slides.
- `content_pl.json` / `content_en.json` — **kanon treści decku** (teksty, tabele, notatki prelegenta; 69 kluczy, identyczne struktury w obu językach). To z nich generator buduje PPTX.
- `slides/` — układ: kolory, funkcje slajdów `slide_01_title` … `slide_14_qa`, lista `SLIDES` w kolejności.
- `deck_spec.json` / `deck_spec_en.json` — **historyczne, nieużywane przez generator**. Zostają, bo `verify_deck.py` je sprawdza (liczby). Nie są źródłem treści (patrz rozjazdy niżej).
- `verify_deck.py` — bramka liczb: arytmetyka planów, kanoniczne i wycofane figury we wszystkich artefaktach, 14 slajdów w obu PPTX, parytet kluczy `content_pl/en.json`. Bez zależności (PPTX czytany jako zip); uruchamiany w CI jako job `docs`.

**`generate_deck.py`** — generuje **oba** decki PPTX (PL i EN) z jednego wspólnego układu przez `python-pptx`. Treść czyta z `content_pl.json` / `content_en.json`, układ (kolory, slajdy) jest w `slides/`, grafiki z `assets/`. Slajdy są 16:9 w palecie navy/gold/cream. Uruchomienie:

```
pip install python-pptx
python presentation/generate_deck.py             # PL  → Bukowy_Dwor_Case_Study.pptx
python presentation/generate_deck.py --lang en   # EN  → Bukowy_Dwor_Case_Study_EN.pptx
python presentation/generate_deck.py --lang all  # oba
python presentation/generate_deck.py --lang all --out-dir DIR   # poza repo, np. do porównania
```

**Źródło vs widok (świadoma decyzja):**
- Źródłem treści PPTX są `content_*.json` (kanon). Zmiana tekstu slajdu = edycja JSON-a, potem regeneracja.
- `prezentacja.html` i `presentation_en.html` to **ręczne widoki** — nie ma dla nich generatora. Trzeba je uzgadniać z JSON-em ręcznie; spójność liczb pilnuje `verify_deck.py`.
- `deck_spec*.json` to **historyczna, inna wersja treści**, nieużywana przez generator. Nie edytować jako źródła.

**Rozjazdy z audytu (M5, 2026-11-13)** — `deck_spec*.json` vs `content_*.json`: z 131 stringów PL tylko 8 pasuje dosłownie (EN: 8 z 130). Najważniejsze różnice merytoryczne, których `content_*.json` nie ma:
- PL: podtytuł „Chętnie pogłębię swój token" (błąd językowy na slajdzie Pytania); „dostępny 8h/dobę".
- EN: „Sub-500ms" (kanon: ~430 ms); „Frankfurt / Dublin"; „15-min TTL"; „RFC 7433"; „Opera Cloud / Mews" (kanon: Opera/KWHotel); „Quick Reply Chips (PL, EN, DE, UK, ES)" (kanon: 6 opcji, DE/EN/UA).
- Kolejność: w `deck_spec*.json` demo jest przed kanałami (slajdy 8/9); w PPTX jest odwrotnie.
- Layouty i lokalne, bezwzględne ścieżki obrazów w JSON-ie nie mają odpowiednika w generatorze.

Różnice tez (np. Frankfurt, TTL, RFC) wymagają decyzji właściciela treści, zanim trafią do kanonu.

> **Stan liczb (2026-11-10):** decki, HTML-e, `deck_spec*.json` i `docs/business-case.md` mają jedną wspólną arytmetykę — $22 / 275 min i $299 / 3 738 min, czyli **$0,08/min**; $22 ≈ 3,5 h pracy recepcjonisty (25 PLN/h); 3 rezerwacje pokoju w nocy (3 × 500 PLN ≈ $375) pokrywają plan Scale ($299). Kurs 4,0 PLN/USD jest zapisany w notatkach prelegenta. Poprzednia wersja miała `~$0.027/min` (299 ÷ 3 738 = 0,08), „2 × 500 PLN pokrywa Scale" (pokrywało $250, nie $299) oraz „5 rezerwacji × $400–800 = $2 000–4 000 w 60 dni", na co repo nie ma danych. Przyczyna rozjazdu: HTML-e są utrzymywane ręcznie, a `presentation_en.html` był źródłem treści EN dla generatora.
>
> **Guard:** `python presentation/verify_deck.py` (bez zależności — PPTX czytany jako zip) sprawdza arytmetykę planów, obecność kanonicznych liczb i brak wycofanych, w obu PPTX, obu HTML-ach, obu `deck_spec*.json` i business case; liczy też 14 slajdów. Ten sam skrypt jest jobem `docs` w CI — liczby nie rozjadą się po cichu.

> **Stan plików `.pptx` (przegenerowane 2026-11-15 generatorem z `content_*.json`; treść planu Enterprise oznaczona jako projekt):** oba decki są przegenerowane z poprawionych źródeł i aktualne faktograficznie — 14 slajdów, 7/7 narzędzi agenta, backend na `:8011`, bez „4 webhooków", starego portu 8000 i `transfer_to_number`. PPTX, HTML i `deck_spec*.json` opisują ten sam system — teraz sprawdzane maszynowo, nie tylko przez brak zakazanych stringów.

**Notatki przygotowawcze** (brief, narracja demo, outline slajdów) są prywatne i nie są częścią publicznego repozytorium. Źródłem treści decku w repo są pliki `content_*.json`; `slides/` to tylko układ.

**`assets/`** — na slajdy produktowe trafiają `anna_widget_desktop.jpg` (agent w rozmowie), `anna_widget_chips.jpg` (chipy), `anna_widget_success.jpg` (potwierdzenie rezerwacji) oraz `anna_widget_rozmowa.jpg` (używany w głównym `README.md`); `diagram_architecture.png`, `diagram_multihotel.png`, `enterprise_security.png` na slajdy architektury/bezpieczeństwa; `persona_zofia.png` na slajd persony; `webhook_responses.json` to surowe odpowiedzi mock backendu użyte w przykładach. `anna_live_homepage.png` i `anna_live_spa.png` to pełnostronicowe zrzuty strony hotelu z sierpnia 2026 — materiał referencyjny, nie są wstawiane do decków (są tylko w `deck_spec*.json`). Zrzuty widgetu pochodzą z żywego demo; odświeżenie ich wymaga rozmowy z agentem (zużywa kredyty ElevenLabs), więc robimy to tylko przed pokazem, nie przy każdej zmianie decku.
