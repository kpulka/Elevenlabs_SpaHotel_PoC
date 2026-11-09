# presentation/ — deck rekrutacyjny i materiał demo

Osobny deliverable: prezentacja case study „Wirtualny Recepcjonista AI — Bukowy Dwór" (ElevenLabs Deployment Strategist) plus surowce, z których powstała. Dokumentacja systemu jest w `docs/` (`docs/INDEX.md`).

**Co otworzyć pierwsze:**
- Online: [kpulka.github.io/Elevenlabs_SpaHotel_PoC](https://kpulka.github.io/Elevenlabs_SpaHotel_PoC/) — strona-wejście `index.html` z linkami do obu decków (GitHub Pages z tego katalogu, `.github/workflows/pages.yml`).
- `prezentacja.html` — wersja PL decku w przeglądarce, bez zależności (to pokazujesz na rozmowie). EN: `presentation_en.html`.
- `Bukowy_Dwor_Case_Study.pptx` / `Bukowy_Dwor_Case_Study_EN.pptx` — te same slajdy do edycji w PowerPoint/Google Slides.
- `deck_spec.json` / `deck_spec_en.json` — specyfikacja slajdów (layout, teksty, notatki prelegenta). To źródło treści, nie do prezentowania.

**`generate_deck.py`** — generuje **oba** decki PPTX (PL i EN) z jednego wspólnego layoutu przez `python-pptx`. Teksty per język siedzą w słowniku `TEXTS`, grafiki skrypt bierze z `assets/`, slajdy są 16:9 w palecie navy/gold/cream. Uruchomienie:

```
pip install python-pptx
python presentation/generate_deck.py             # PL  → Bukowy_Dwor_Case_Study.pptx
python presentation/generate_deck.py --lang en   # EN  → Bukowy_Dwor_Case_Study_EN.pptx
python presentation/generate_deck.py --lang all  # oba
```

Uwaga: oba HTML-e (`prezentacja.html`, `presentation_en.html`) nie mają generatora w repo — utrzymywane ręcznie; `presentation_en.html` jest źródłem treści EN dla decku.

> **Stan plików `.pptx` (2026-11-09):** oba decki są przegenerowane z poprawionych źródeł i aktualne faktograficznie — 14 slajdów, 7/7 narzędzi agenta, backend na `:8011`, bez „4 webhooków", starego portu 8000 i `transfer_to_number`. Weryfikacja treści: brak zakazanych stringów w XML slajdów (`k3_verify.py` / `unzip -p`). PPTX, HTML i `deck_spec*.json` opisują ten sam system.

**Pliki `.md`** to materiał wejściowy i przygotowanie do rozmów, w kolejności procesu: `00_brief_prezentacja.md` (co ma osiągnąć deck), `01_diagram_architektury.md` + `01_architecture_diagrams_en.md` (diagramy Mermaid), `02/03/04` (tok myślenia V1, narracja demo, outline slajdów), `05/06/09` (materiały V2: pytania, Excalidraw, przygotowanie do Hiring Managera), `07` (UX), `08` (wytyczne UI strony hotelu).

**`assets/`** — na slajdy produktowe trafiają `anna_widget_desktop.jpg` (agent w rozmowie), `anna_widget_chips.jpg` (chipy), `anna_widget_success.jpg` (potwierdzenie rezerwacji) oraz `anna_widget_rozmowa.jpg` (używany w głównym `README.md`); `diagram_architecture.png`, `diagram_multihotel.png`, `enterprise_security.png` na slajdy architektury/bezpieczeństwa; `persona_zofia.png` na slajd persony; `webhook_responses.json` to surowe odpowiedzi mock backendu użyte w przykładach. `anna_live_homepage.png` i `anna_live_spa.png` to pełnostronicowe zrzuty strony hotelu z sierpnia 2026 — materiał referencyjny, nie są wstawiane do decków (są tylko w `deck_spec*.json`). Zrzuty widgetu pochodzą z żywego demo; odświeżenie ich wymaga rozmowy z agentem (zużywa kredyty ElevenLabs), więc robimy to tylko przed pokazem, nie przy każdej zmianie decku.
