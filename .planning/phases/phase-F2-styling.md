# Phase F2 — Ostyluj widget tak, by pasował do brandingu strony

## Cel
Dopasować wygląd oficjalnego widgeta do motywu strony (kolory navy/gold/cream, zaokrąglenia, krój, pozycja). Podpiąć UI pod config z `_agent_widget.json`.

## Zależności
Phase F1 (widget działa).

## Kroki
1. Z widget_config (świetne dla brandu) przenieś kolory: `bg_color`, `btn_color`, `btn_text_color`, `border_color`, `focus_color`, `avatar` (orb navy/gold), `text_color`; ustaw spójnie z istniejącymi `bg-navy`, `bg-gold`, `bg-cream`.
2. Ustaw położenie: `placement: bottom-right`, kompensuj z FAB. Rozważ mniejszą pozycje / rozmiar jeśli koliduje.
3. Polskie teksty (main_label, start_call, input_placeholder) — z `text_contents`; upewnij się że nie duplikują się z własnym nagłówkiem.
4. Jeśli chcesz szybkie pytania/proponowane (zamiast kroków Język/Temat) — ElevenLabs ma `suggested_questions` w nowych versi; dodaj w `ConvaiWidget` wartość.

## DoD
- [ ] Widget wizualnie spójny (kolory/radii/font) ze stroną.
- [ ] Pozycja prawy-dolny nie koliduje z innymi elementami.
- [ ] Polskie etykiety z bazy widgetu.

## Wynik
Widget estetycznie dopasowany i funkcjonalny.