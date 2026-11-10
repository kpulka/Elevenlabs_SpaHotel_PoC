# presentation/ — deck rekrutacyjny i materiał demo

Osobny deliverable: prezentacja case study „Wirtualny Recepcjonista AI — Bukowy Dwór" (ElevenLabs Deployment Strategist) plus surowce, z których powstała. Dokumentacja systemu jest w `docs/` (`docs/INDEX.md`).

**Co otworzyć pierwsze:**
- Online: [kpulka.github.io/Elevenlabs_SpaHotel_PoC](https://kpulka.github.io/Elevenlabs_SpaHotel_PoC/) — strona-wejście `index.html` z linkami do obu decków (GitHub Pages z tego katalogu, `.github/workflows/pages.yml`).
- `prezentacja.html` — wersja PL decku w przeglądarce, bez zależności (to pokazujesz na rozmowie). EN: `presentation_en.html`.
- `Bukowy_Dwor_Case_Study.pptx` / `Bukowy_Dwor_Case_Study_EN.pptx` — te same slajdy do edycji w PowerPoint/Google Slides.
- `deck_spec.json` / `deck_spec_en.json` — specyfikacja slajdów (layout, teksty, notatki prelegenta). To źródło treści, nie do prezentowania.
- `verify_deck.py` — bramka liczb: arytmetyka planów, kanoniczne i wycofane figury we wszystkich artefaktach, 14 slajdów w obu PPTX. Bez zależności (PPTX czytany jako zip); uruchamiany w CI jako job `docs`.

**`generate_deck.py`** — generuje **oba** decki PPTX (PL i EN) z jednego wspólnego layoutu przez `python-pptx`. Teksty per język siedzą w słowniku `TEXTS`, grafiki skrypt bierze z `assets/`, slajdy są 16:9 w palecie navy/gold/cream. Uruchomienie:

```
pip install python-pptx
python presentation/generate_deck.py             # PL  → Bukowy_Dwor_Case_Study.pptx
python presentation/generate_deck.py --lang en   # EN  → Bukowy_Dwor_Case_Study_EN.pptx
python presentation/generate_deck.py --lang all  # oba
```

Uwaga: oba HTML-e (`prezentacja.html`, `presentation_en.html`) nie mają generatora w repo — utrzymywane ręcznie, niezależnie od `TEXTS` w `generate_deck.py`. Kanonem treści decku jest `TEXTS`; HTML-e są osobną powierzchnią i trzeba je uzgadniać ręcznie (wcześniej `presentation_en.html` uchodził za źródło EN, choć generator go nie czyta — stąd cichy rozjazd liczb). Różnice wyłapuje `verify_deck.py`.

> **Stan liczb (2026-11-10):** decki, HTML-e, `deck_spec*.json` i `docs/business-case.md` mają jedną wspólną arytmetykę — $22 / 275 min i $299 / 3 738 min, czyli **$0,08/min**; $22 ≈ 3,5 h pracy recepcjonisty (25 PLN/h); 3 rezerwacje pokoju w nocy (3 × 500 PLN ≈ $375) pokrywają plan Scale ($299). Kurs 4,0 PLN/USD jest zapisany w notatkach prelegenta. Poprzednia wersja miała `~$0.027/min` (299 ÷ 3 738 = 0,08), „2 × 500 PLN pokrywa Scale" (pokrywało $250, nie $299) oraz „5 rezerwacji × $400–800 = $2 000–4 000 w 60 dni", na co repo nie ma danych. Przyczyna rozjazdu: HTML-e są utrzymywane ręcznie, a `presentation_en.html` był źródłem treści EN dla generatora.
>
> **Guard:** `python presentation/verify_deck.py` (bez zależności — PPTX czytany jako zip) sprawdza arytmetykę planów, obecność kanonicznych liczb i brak wycofanych, w obu PPTX, obu HTML-ach, obu `deck_spec*.json` i business case; liczy też 14 slajdów. Ten sam skrypt jest jobem `docs` w CI — liczby nie rozjadą się po cichu.

> **Stan plików `.pptx` (2026-11-09, przegenerowane 2026-11-10):** oba decki są przegenerowane z poprawionych źródeł i aktualne faktograficznie — 14 slajdów, 7/7 narzędzi agenta, backend na `:8011`, bez „4 webhooków", starego portu 8000 i `transfer_to_number`. PPTX, HTML i `deck_spec*.json` opisują ten sam system — teraz sprawdzane maszynowo, nie tylko przez brak zakazanych stringów.

**Pliki `.md`** to materiał wejściowy i przygotowanie do rozmów, w kolejności procesu: `00_brief_prezentacja.md` (co ma osiągnąć deck), `01_diagram_architektury.md` + `01_architecture_diagrams_en.md` (diagramy Mermaid), `02/03/04` (tok myślenia V1, narracja demo, outline slajdów), `05/06/09` (materiały V2: pytania, Excalidraw, przygotowanie do Hiring Managera), `07` (UX), `08` (wytyczne UI strony hotelu).

**`assets/`** — na slajdy produktowe trafiają `anna_widget_desktop.jpg` (agent w rozmowie), `anna_widget_chips.jpg` (chipy), `anna_widget_success.jpg` (potwierdzenie rezerwacji) oraz `anna_widget_rozmowa.jpg` (używany w głównym `README.md`); `diagram_architecture.png`, `diagram_multihotel.png`, `enterprise_security.png` na slajdy architektury/bezpieczeństwa; `persona_zofia.png` na slajd persony; `webhook_responses.json` to surowe odpowiedzi mock backendu użyte w przykładach. `anna_live_homepage.png` i `anna_live_spa.png` to pełnostronicowe zrzuty strony hotelu z sierpnia 2026 — materiał referencyjny, nie są wstawiane do decków (są tylko w `deck_spec*.json`). Zrzuty widgetu pochodzą z żywego demo; odświeżenie ich wymaga rozmowy z agentem (zużywa kredyty ElevenLabs), więc robimy to tylko przed pokazem, nie przy każdej zmianie decku.
