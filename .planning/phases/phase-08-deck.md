# Phase 8 — Zbuduj deck (PowerPoint / Google Slides)

## Cel
Zbudować 14-slajdową prezentację z materiałów w `presentation/`.

## Zależności
Phase 7 (screeny demo do slajdu 8/8b).

## Wejście (czytaj w tej kolejności)
1. `presentation/00_brief_prezentacja.md` — specyfikacja każdego slajdu + notatki prezentera.
2. `presentation/04_slajdy_outline.md` — outline (może być źródłem struktury).
3. `presentation/01_diagram_architektury.md` — 5 diagramów Mermaid → renderuj na obrazy (mermaid.live / mermaid-cli).
4. `presentation/assets/` — screeny widgetu + (dodane w Phase 7) screeny demo.

## Wykonanie
- **Deleguj do subagenta** (`delegate_task`) z pełnym kontekstem, LUB zbuduj sam z pomocą skill `powerpoint` / `google-workspace`.
- Styl: minimalistyczny, max 5 linii tekstu/slajd, notatki prezentera przy każdym slajdzie (z briefu).
- Diagramy: Mermaid → statyczne PNG/SVG.
- Nie używaj słowa „chatbot" (to agent głosowy).

## Struktura (14 slajdów)
1. Okładka → 2. Problem → 3. Persona (Zofia 72) → 4. Rozwiązanie „Anna" → 5. 3 decyzje architektoniczne / stack → 6. RAG + strict grounding → 7. Tool calling → 8. Demo (3 ścieżki + screeny) → 8b. Widget/UX → 9. RODO → 10. Skalowanie sieć → 11. Koszty/ROI → 12. Roadmapa (MVP→II→III) → 13. Pytania.

## DoD
- [ ] 14 slajdów (lub 12–14 z wariantem 8b).
- [ ] Każdy slajd ma notatki prezentera.
- [ ] Checklist z `00_brief_prezentacja.md` (sekcja CHECKLIST) zaliczona.
- [ ] Diagramy czytelne (widoczne z 2 m).
- [ ] Screeny demo z Phase 7 wstawione.

## Wynik przekazany do Phase 10
Plik `.pptx` (lub link Google Slides).