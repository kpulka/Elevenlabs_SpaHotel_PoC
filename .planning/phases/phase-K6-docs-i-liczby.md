# Phase K6 — dokumentacja wdrożeniowa i audyt liczb

**Cel:** domknąć to, co po K1–K5 nadal brakowało pod rozmowę o roli wdrożeniowej, bez kredytów i bez
ruszania działającego demo: dokumenty o wdrożeniu (biznes, playbook, wnioski) oraz rozstrzygnięcie
rozbieżnych liczb ROI.

**Kontekst:** 2026-11-09 inny agent zrobił refactoring i wypchnął go na `claude/trusting-fermi-dy8rdu`.
W K1 ta gałąź została **zarchiwizowana** (tag `archive/english-wip-2026-11-04` = `86ddeff`, usunięta
z remote), nie zmergowana. Stan zmierzony 2026-11-10: gałąź **3 commity przed / 25 za** `main`,
wspólny przodek `c98b730`. Czyli: nic z refactoringu nie ma na `main` i nigdy nie było.

**Decyzja:** nie merge'ujemy (to nie scalenie, a powtórka K1–K5: inny układ katalogów, brak `.planning/`,
polskie nazwy plików, brak runbooka). Zamiast tego **zebrane selektywnie** trzy dokumenty, przepisane pod
strukturę `main` i zweryfikowane twierdzenie po twierdzeniu.

## Co weszło do repo

| plik | źródło | co zmieniono względem gałęzi |
|---|---|---|
| `docs/business-case.md` | `docs/business-case.md` z gałęzi | ekonomia przeliczona na polskie realia (25 PLN/h ≈ $6/h, nie $15–25/h); $0,08/min wyliczone z planów; „parytet pracy, nie oszczędność" zamiast obietnicy oszczędności; linki tylko do plików, które istnieją na `main` |
| `docs/deployment-playbook.md` | `docs/deployment-playbook.md` | fazy z bramkami spięte z realnym procesem repo (`.planning/`, CI); runbook awarii wskazuje `run_simulations.py --check`; port `8000`/`8011` wyjaśniony; architektura docelowa bez obiecywania funkcji, których PoC nie ma |
| `docs/lessons-learned.md` | `docs/lessons-learned.md` | 8. incydentów, każdy sprawdzony w repo (m.in. `transfer_to_human` z audytu 2026-08, port 8000 zajęty przez system, widget z CDN → self-host, `PATCH` KB zwracający 200 i ignorujący treść); usunięte twierdzenia bez dowodu |

## Co poprawiono w liczbach (audyt)

| gdzie | było | jest |
|---|---|---|
| `presentation/presentation_en.html` | `3,738 min (~$0.027/min)` | `3,738 min (≈ $0.08/min)` |
| `presentation/presentation_en.html` | `Replaces 1 FTE night shift` / `Saves 3 FTEs` | „Covers the night-shift routine load" / „Same core agent, KB per hotel" — twierdzenie o redukcji zatrudnienia było nie do obrony i sprzeczne z notatką prelegenta na tym samym slajdzie |
| `presentation/presentation_en.html` | `$400–800 × 5 = $2,000–4,000`, „annual contract in <60 days" | jedna rezerwacja ≈ 500 PLN (≈ $125); 3 × 500 PLN ≈ $375 pokrywa plan Scale ($299) |
| `presentation/prezentacja.html`, `generate_deck.py` (PL/EN) | „2 × 500 PLN pokrywa abonament Scale" | 3 × 500 PLN = 1 500 PLN ≈ $375 (−$76 zapasu); kurs 4,0 PLN/USD w notatkach |
| `presentation/deck_spec*.json`, `04_slajdy_outline.md`, `00_brief_prezentacja.md`, `02_tok_myslenia_v1.md` | „275 min ≈ 1 h pracy recepcjonisty" | $22 ≈ 88 PLN ≈ **3,5 h** przy 25 PLN/h |
| `presentation/02_v1_interview_thought_process_en.md` | `$0.027/min`, `$400–800`, „1 hour wage" | liczby jak wyżej + nota historyczna, że to poprawka z 2026-11-10 |

Arytmetyka: 22 ÷ 275 = 0,080 i 299 ÷ 3 738 = 0,080 — ten sam kurs, więc $0,08/min jest jedyną liczbą
obronioną. Wcześniejsze `$0.027` było błędem rachunkowym, nie innym cennikiem.

**Dlaczego to umknęło:** bramki sprawdzały typy, parytet i18n i zakazane stringi, ale **nic nie porównywało
liczb między artefaktami**. HTML-e są utrzymywane ręcznie, a `presentation_en.html` był źródłem treści EN
dla generatora — więc rozjechały się po cichu.

## Nowa bramka

`presentation/verify_deck.py` (stdlib; PPTX czytany jako zip): sprawdza arytmetykę planów, obecność liczb
kanonicznych i brak wycofanych w obu PPTX, obu HTML-ach, obu `deck_spec*.json` i `docs/business-case.md`,
oraz 14 slajdów w obu deckach. Uruchamiany jako job `docs` w CI — bez nowych zależności, kilka sekund.

## Dowody (2026-11-10)

| co | wynik |
|---|---|
| `python presentation/verify_deck.py` | OK — 7 artefaktów, 14/14 slajdów, kurs 0,080, pokrycie $375 |
| PPTX po regeneracji | 14 slajdów PL i EN, nowe liczby obecne, wycofane nieobecne (XML slajdów + notatki) |
| `pytest -q` | 76 passed |
| `tsc --noEmit` / `check-i18n` / `sync-data --check` | 0 / 138 kluczy / 3 pokoje, 6 zabiegów |
| `next build` | OK |
| YAML `ci.yml` | parsuje się (`yaml.safe_load`) |

## Odrzucone z raportu poprzedniego agenta (sprawdzone, nieprawdziwe na `main`)

| twierdzenie | stan faktyczny |
|---|---|
| „`mock_backend/data/*.json` nie są czytane przez `main.py`" | czytane: `store.py:147` (`rooms.json`), `catalog.py:77` (`spa_schedule.json`) |
| „ID agenta na sztywno w widgecie, `ELEVENLABS_AGENT_ID` nic nie zmieni" | `NEXT_PUBLIC_ELEVENLABS_AGENT_ID ?? fallback` — env nadpisuje, literał to fallback dla dev (`anna-embed-widget.tsx:10,70,167`) |
| „brak CI / trzeba dodać workflow" | `ci.yml` + `pages.yml` działają, runy zielone |
| „brak LICENSE, brak zrzutów w README" | MIT w repo, dwa zrzuty w README, opis i 10 tematów na GitHubie |

## Domknięte 2026-11-10 (decyzja agenta, właściciel nie miał preferencji)

- **Release:** `v1.0.1` (release utworzony ponownie, tag wskazuje **`0aecd33`** = `main`, czyli commit,
  w którym `README.md` linkuje do `v1.0.1`; pierwsze wydanie stało na `d4facb6` sprzed tej poprawki).
  Nota wymienia poprawki liczb i bramki (76 testów, run CI `42794822592`). Assety **obu** release'ów są
  identyczne — w `v1.0.0` podmieniono oba PPTX na przegenerowane
  (SHA256 `1e1062db…` / `1bf6dcfe…`, porównane z plikami lokalnymi i przez API), a w jego notatkach jest
  blok „Assets replaced 2026-11-10" nad treścią z 2026-11-09. **Sam tag `v1.0.0` (`57755ab`) i jego
  historia są nietknięte.** Link w `README.md` wskazuje `v1.0.1`.
- **Lokalny ref:** `git branch -D claude/trusting-fermi-dy8rdu` (był `86ddeff`). Treść nietknięta —
  tag `archive/english-wip-2026-11-04` (annotated, na origin) wskazuje ten sam commit; sprawdzone
  `git rev-parse "archive/english-wip-2026-11-04^{commit}"` → `86ddeff`. Lokalnie zostaje tylko `main`.
- **Higiena:** `git gc` po nowych commitach z PPTX — `.git` 46,7 MB → **30,7 MB** (`size-pack` 30,67 MiB).
  Każdy commit z dwoma PPTX dodaje ~8 MB luźnych obiektów, dopóki nie przejdzie gc.
