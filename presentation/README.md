# presentation/ — deck rekrutacyjny i materiał demo

Osobny deliverable: prezentacja case study „Wirtualny Recepcjonista AI — Bukowy Dwór" (ElevenLabs Deployment Strategist) plus surowce, z których powstała. Dokumentacja systemu jest w `docs/` (`docs/INDEX.md`).

**Co otworzyć pierwsze:**
- `prezentacja.html` — wersja PL decku w przeglądarce, bez zależności (to pokazujesz na rozmowie). EN: `presentation_en.html`.
- `Bukowy_Dwor_Case_Study.pptx` / `Bukowy_Dwor_Case_Study_EN.pptx` — te same slajdy do edycji w PowerPoint/Google Slides.
- `deck_spec.json` / `deck_spec_en.json` — specyfikacja slajdów (layout, teksty, notatki prelegenta). To źródło treści, nie do prezentowania.

**`generate_deck.py`** — generuje `Bukowy_Dwor_Case_Study.pptx` (PL) z Pythona przez `python-pptx`; grafiki bierze z `assets/`, skrypt buduje slajdy 16:9 w palecie navy/gold/cream. Uruchomienie:

```
pip install python-pptx
python presentation/generate_deck.py
```

Uwaga: skrypt odtwarza wyłącznie deck PL — wersja `_EN.pptx` i oba HTML-e nie mają generatora w repo, więc zmiany w nich wprowadzaj ręcznie.

**Pliki `.md`** to materiał wejściowy i przygotowanie do rozmów, w kolejności procesu: `00_brief_prezentacja.md` (co ma osiągnąć deck), `01_diagram_architektury.md` + `01_architecture_diagrams_en.md` (diagramy Mermaid), `02/03/04` (tok myślenia V1, narracja demo, outline slajdów), `05/06/09` (materiały V2: pytania, Excalidraw, przygotowanie do Hiring Managera), `07` (UX), `08` (wytyczne UI strony hotelu).

**`assets/`** — zrzuty żywego demo (`anna_live_homepage.png`, `anna_live_spa.png`, `anna_widget_*.jpg`) trafiają na slajdy produktowe; `diagram_architecture.png`, `diagram_multihotel.png`, `enterprise_security.png` na slajdy architektury/bezpieczeństwa; `persona_zofia.png` na slajd persony; `webhook_responses.json` to surowe odpowiedzi mock backendu użyte w przykładach.
