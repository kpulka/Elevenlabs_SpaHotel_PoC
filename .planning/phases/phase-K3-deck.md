# Phase K3 — Deck: regeneracja i zgodność z kodem

## Cel
Doprowadzić oba decki (`Bukowy_Dwor_Case_Study.pptx`, `Bukowy_Dwor_Case_Study_EN.pptx`) do stanu
2026-11: 7 narzędzi (nie „4 webhooki”), port 8011 (nie 8000), brak `transfer_to_number`,
`gemini-3.5-flash-lite`, nowe ceny zabiegów.

**Stan wyjściowy:** źródła są poprawione (`prezentacja.html`, `presentation_en.html`,
`deck_spec*.json`, `generate_deck.py`), ale **binaria `.pptx` nie** — powstały w sierpniu i to one
mają stare liczby. `presentation/README.md` ma o tym ostrzeżenie.

## Zakres
- `presentation/generate_deck.py` → `Bukowy_Dwor_Case_Study.pptx` (generator PL działa).
- Decyzja dla EN: `presentation_en.html` → PPTX/PDF (np. Playwright print-to-PDF albo ręcznie).
- `presentation/assets/` — zrzuty demo, jeśli UI strony zmienił się po refaktorze frontendu.

## Kroki
1. `pip install python-pptx`, potem `python presentation/generate_deck.py` (nadpisze PL PPTX).
2. Otworzyć PL deck, sprawdzić slajd narzędzi (7 pozycji z cancel/reschedule), port 8011,
   `transfer_to_simulated_handoff`, brak `$15`.
3. Automatyczna kontrola treści bez otwierania PowerPointa:
   `unzip -p presentation/Bukowy_Dwor_Case_Study.pptx ppt/slides/*.xml | grep -c "transfer_to_number"`
   → 0; analogicznie `8000`, `4 webhook`.
4. EN: albo generator EN w `generate_deck.py` (parametr `--lang en`), albo konwersja
   `presentation_en.html` → PDF/PPTX; wybrać i **zapisać wybór w `presentation/README.md`**.
5. Odświeżyć zrzuty: strona główna, `/spa` (nowe ceny: 80/120/100/70/160/30), widget w rozmowie.
6. Usunąć z `presentation/README.md` ostrzeżenie o nieprzegenerowanych PPTX.

## Weryfikacja (DoD)
- [x] Oba PPTX otwierają się i mają 7 narzędzi + port 8011; `unzip -p` nie znajduje `transfer_to_number`,
      `8000`, `4 webhook`, `$15`.
- [x] Ceny na stronie `/spa` = 80/120/100/70/160/30 (`frontend/lib/generated/hotel-facts.ts`); zrzuty
      `anna_live_*` są archiwalne (patrz „Wynik”).
- [x] `presentation/README.md` opisuje realny sposób wygenerowania obu decków (PL i EN).
- [x] HTML-e i PPTX-y mówią to samo (sprawdzone na 3 slajdach: narzędzia, architektura, koszty).

## Kluczowe / ryzyka
- **Nie nadpisywać PPTX-a, jeśli był ręcznie poprawiany** — najpierw sprawdzić `git log`/datę pliku i
  porównać z zawartością; przy wątpliwości wygenerować do nowej nazwy i porównać.
- EN deck nie ma generatora — bez decyzji o konwersji faza jest „pół zrobiona”; dlatego krok 4 jest
  obowiązkowy, a nie opcjonalny.

## Wynik (2026-11-09, done)

**Wybór dla EN:** wariant z kroku 4 — `generate_deck.py` dostał `--lang pl|en|all`; teksty per język
w słowniku `TEXTS`, layout wspólny. Nie konwertujemy HTML→PDF.

**Dowód (skrypt `k3_verify.py`, czyta XML slajdów z `.pptx`):**

| miara | PL | EN |
|---|---|---|
| slajdy | 14 | 14 |
| `transfer_to_number` | 0 | 0 |
| `8000` | 0 | 0 |
| `4 webhook` | 0 | 0 |
| `$15` | 0 | 0 |
| narzędzia agenta | 7/7 | 7/7 |
| `8011` | 1 | 1 |

Stare binaria (backup `D:/Backups/Bukowy_Dwor_Case_Study*-pre-K3.pptx`) miały `transfer_to_number`=1,
`4 webhook`=1 i tylko 4/7 narzędzi.

**Zrzuty (`assets/`):** ceny na `/spa` zgadzają się z kodem (80/120/100/70/160/30 —
`frontend/lib/generated/hotel-facts.ts`), więc zrzuty nie wprowadzają w błąd faktograficznie.
`anna_live_homepage.png` / `anna_live_spa.png` nie trafiają na slajdy (tylko `deck_spec*.json`),
a `anna_widget_success.jpg` nie pokazuje kwot — nie ma tam czego dezaktualizować. Odświeżenie zrzutów
widgetu wymaga realnej rozmowy z agentem i zużywa kredyty (obecnie 10 000/10 000 — patrz K2),
więc robimy je przed pokazem, nie przy każdej zmianie decku. Opisane w `presentation/README.md`.

**Bramki po zmianie:** `mock_backend` 68 passed; `tsc --noEmit` OK; `check-i18n` 182 klucze;
`sync-data --check` 3 pokoje / 6 zabiegów; `next build` 11 stron statycznych + 1 route dynamiczny.
