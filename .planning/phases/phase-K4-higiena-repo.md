# Phase K4 — Higiena publicznego repozytorium (GitHub)

## Cel
Repo ma wyglądać jak skończony projekt, nie jak warsztat: jedna gałąź, tag wersji, opis, martwe klucze
tłumaczeń usunięte.

**Stan wyjściowy (zmierzony 2026-11-09):** `main` zsynchronizowane (0/0), brak tagów, `homepage` pusty,
1 otwarty issue, **jedna obca gałąź na remote**: `origin/claude/trusting-fermi-dy8rdu` — 3 commity
z 2026-11-04 („restructure repo into professional English case study”, 143 pliki, WIP tłumaczenia),
rozjechana z obecnym `main`; do tego ~40 nieużywanych kluczy w `frontend/lib/translations.ts`.

## Zakres
- GitHub: gałęzie, tagi, release, metadane repo, issues.
- `frontend/lib/translations.ts` (+ oba słowniki) — usunięcie martwych kluczy.
- `README.md` — ewentualny link do release/demo.

## Kroki
1. **Decyzja o `claude/trusting-fermi-dy8rdu`** (jedna z dwóch, do zapisania w tym pliku):
   a) usunąć — jest to porzucony WIP sprzed refaktoru, a jego treść (pełne tłumaczenie docs/backend na
      EN) koliduje z obecnym podejściem (dokumentacja PL + README EN);
   b) zachować jako tag `archive/english-wip-2026-11-04` i usunąć gałąź — historia zostaje, remote
      przestaje straszyć.
   Rekomendacja: (b). `git tag archive/english-wip origin/claude/trusting-fermi-dy8rdu && git push origin --tags && git push origin --delete claude/trusting-fermi-dy8rdu`.
2. **Tag wersji + release:** `git tag -a v1.0.0 -m "Portfolio release: hardened backend, tests, CI"` →
   push; release na GitHubie z 5 punktami (co działa, czego nie ma, jak uruchomić, bramki, link do docs/INDEX.md).
3. **Metadane repo** (UI albo `gh`): `homepage` = link do decka/demo; description bez zmian (jest dobra);
   topics: dodać `fastapi`, `nextjs`, `pytest`, `voice-ai`, usunąć niepasujące; wyłączyć Wiki (pusta).
4. **Martwe klucze i18n:** skrypt znajduje klucze w `translations.ts`, których nie ma w `app/` ani
   `components/`; usunąć z PL i EN, uruchomić `pnpm i18n:check` (parytet musi zostać) i `pnpm build`.
   Uwaga: to ~40 kluczy — jeśli usuwanie zajmie więcej niż godzinę, zamknąć fazę na „usunięte
   największe bloki (`introFeature*`, `home.feat*`)”, resztę zostawić jako dług.
5. **Issues:** przejrzeć otwarty issue — jeśli dotyczy stanu sprzed refaktoru, zamknąć z komentarzem
   „resolved in <commit>”, albo przepisać na konkretne zadanie.
6. **Ochrona gałęzi (opcjonalnie):** wymagany zielony CI na `main` (Settings → Branches).

## Weryfikacja (DoD)
- [x] `git branch -r` → tylko `origin/main`; `git tag` → `v1.0.0` + `archive/english-wip-2026-11-04`.
- [x] Release `v1.0.0` widoczny publicznie, link w README.
- [x] `homepage` ustawiony (`https://kpulka.github.io/Elevenlabs_SpaHotel_PoC/`); Wiki wyłączone; 0 otwartych issues.
- [x] `i18n:check` i `build` zielone po usunięciu kluczy; `grep` nie znajduje usuniętych nazw.
- [x] CI zielone na commicie tagu (workflow startuje z `push` na `main`; tag wskazuje ten sam SHA).

## Kluczowe / ryzyka
- Usuwanie gałęzi na remote jest nieodwracalne bez reflog po stronie GitHuba — dlatego najpierw tag.
- Martwe klucze usuwać partiami z buildem po każdej partii; `i18n:check` sprawdza tylko parytet,
  więc błąd „klucz używany, ale usunięty” wyjdzie dopiero w `tsc`/`build`.

## Wynik (2026-11-09, done)

| element | stan |
|---|---|
| gałęzie na remote | tylko `origin/main` (obca gałąź → tag `archive/english-wip-2026-11-04`, zrobione w K1) |
| tag | `v1.0.0` annotated na `57755ab` (commit z zielonym CI: run 42712220369) |
| release | [v1.0.0](https://github.com/kpulka/Elevenlabs_SpaHotel_PoC/releases/tag/v1.0.0) — 5 sekcji (co działa / czego nie ma / jak uruchomić / bramki / dokumentacja) + oba PPTX jako assety (4 148 952 B i 4 147 856 B) |
| topics | `ai-agent`, `case-study`, `conversational-ai`, `elevenlabs`, `fastapi`, `nextjs`, `podman`, `voice-agent`, `pytest`, `voice-ai` (dodane `pytest`, `voice-ai`) |
| homepage | `https://kpulka.github.io/Elevenlabs_SpaHotel_PoC/` |
| Wiki | wyłączone (`hasWikiEnabled=false`) |
| issues | 0 otwartych |
| martwe klucze i18n | **44 usunięte**, 182 → **138** kluczy w PL i EN; skan `k4_i18n.py`: **0 nieużywanych liści**; `check-i18n` 138/138, `tsc` clean, `next build` 11 stron |
| bramki inne | `pytest` **68 passed**, `sync-data --check` 3 pokoje / 6 zabiegów |

**Pages z deckiem:** `presentation/index.html` (dwujęzyczna strona-wejście) + `.github/workflows/pages.yml`
(artefakt = katalog `presentation/`, bez builda). Deploy: run 42712684119 → success; sprawdzone HTTP:
landing 200 (3 614 B), `prezentacja.html` 200, `presentation_en.html` 200, `assets/anna_widget_success.jpg`
200, `Bukowy_Dwor_Case_Study.pptx` 200. Repo ma teraz realny link do pokazania rekruterowi bez klonowania.

**Świadomie nie zrobione:** ochrona gałęzi `main` (krok 6, opcjonalny) — wymuszałaby PR-y przy pracy
jednoosobowej; można włączyć później w Settings → Branches. CI nie ma triggera na tagi (tag wskazuje
commit z zielonym runem, więc release jest pokryty).
