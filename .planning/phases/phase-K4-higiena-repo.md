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
- [ ] `git branch -r` → tylko `origin/main`; `git tag` → `v1.0.0` (+ ewentualny tag archiwalny).
- [ ] Release `v1.0.0` widoczny publicznie, link w README opcjonalnie.
- [ ] `homepage` ustawiony; Wiki wyłączone; 0 otwartych issues nieaktualnych.
- [ ] `pnpm i18n:check` i `pnpm build` zielone po usunięciu kluczy; `grep` nie znajduje usuniętych nazw.
- [ ] CI zielone na tagu (workflow działa też dla tagów albo release nie wymaga runu).

## Kluczowe / ryzyka
- Usuwanie gałęzi na remote jest nieodwracalne bez reflog po stronie GitHuba — dlatego najpierw tag.
- Martwe klucze usuwać partiami z buildem po każdej partii; `i18n:check` sprawdza tylko parytet,
  więc błąd „klucz używany, ale usunięty” wyjdzie dopiero w `tsc`/`build`.
