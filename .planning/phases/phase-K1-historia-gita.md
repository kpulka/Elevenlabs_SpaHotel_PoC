# Phase K1 — Historia gita i rozmiar repozytorium

## Cel
Usunąć z historii dwa nieaktualne, duże bloby: `cloudflared.exe` (usunięty z drzewa w commicie
`c2f9824`, ale nadal w historii) oraz starą wersję decku PL (8,94 MiB, wyparta przez obecne 3,96 MiB).
Dzięki temu klon publicznego repo jest mniejszy, a historia nie zawiera binariów, których nikt już nie
potrzebuje.

> **Decyzja właściciela (2026-11-09):** zakres = `cloudflared.exe` **+ stara wersja decku**; zgoda na
> `force-push` po backupie bundle; backup do `D:/Backups`, tylko ten klon; gałąź
> `origin/claude/trusting-fermi-dy8rdu` → tag archiwalny **po** przepisaniu + usunięcie gałęzi.
> **Cel „< 6 MB” odrzucony:** bieżące drzewo waży 34,18 MiB, więc jest nieosiągalny bez usunięcia
> decków i zrzutów z repo. Nowy cel: `.git` < 35 MB i brak blobu > 10 MB.

**Stan wyjściowy (zmierzony 2026-11-09):** `.git` = 64 MB; reachable blobs = 99,19 MiB, w tym
`cloudflared.exe` = 52,35 MiB i stara wersja `presentation/Bukowy_Dwor_Case_Study.pptx` = 8,94 MiB;
bieżące drzewo HEAD = 34,18 MiB. GitHub `size` = 58 523 KB (wartość API, odświeżana asynchronicznie).

## Zakres
- Historia gita (`main`), `.gitignore`, `.gitattributes` (bez zmian treści).
- **Nie dotyka kodu** — po fazie drzewo robocze ma być bajtowo identyczne.

## Kroki (wykonane)
1. Backup przed operacją (poza repo): `git bundle create D:/Backups/spahotels-pre-filter-2026-11-09.bundle --all`
   → 57 MB, `git bundle verify` OK, klon z bundle przetestowany.
2. Narzędzie: `python -m pip install --user git-filter-repo` (2.47.0; skrypt nie był na PATH, wołane jako moduł).
3. Usunięcie **konkretnych blobów** z całej historii (nie ścieżek):
   `python -m git_filter_repo --strip-blobs-with-ids strip-blobs.txt --force`
   — plik zawierał SHA `cloudflared.exe` i starej wersji decku.
4. Porządki: `git reflog expire --expire=now --all`, `git gc --prune=now --aggressive`
   (kolejność: `gc` + `reflog expire` **przed** filter-repo, bo inaczej narzędzie odmawia jako „nie świeży klon”).
5. Weryfikacja **przed** push-em:
   - `git rev-list --objects --all | grep -i cloudflared` → pusto
   - `git count-objects -vH` → `size-pack` **30,57 MiB** (nowy cel < 35 MB; stare „< 6 MB” odrzucone)
   - `git fsck --strict` → bez błędów
   - `HEAD tree` identyczny przed/po (`2f184d8`), tematy 20 commitów identyczne
6. Force-push: `git push --force-with-lease=main:<stary-SHA> origin main` (bezpieczniej niż goły `--force`),
   potem tag archiwalny i `git push origin --delete claude/trusting-fermi-dy8rdu`.
7. Kontrola po pushu: świeży klon → `.git` **31 MB**, `size-pack` **30,74 MiB**, 0 trafień `cloudflared`,
   `pytest` **68 passed**; CI na `fc22c74`: **success** (run 42698787091).
8. Ten klon jest jedynym klonem właściciela — nie ma drugiego laptopa do re-klonu (decyzja 2026-11-09).

## Weryfikacja (DoD) — wykonana 2026-11-09
- [x] `git count-objects -vH` w repo: `size-pack` **30,57 MiB**; świeży klon: **30,74 MiB** (`.git` 31 MB).
- [x] `git rev-list --objects --all | grep cloudflared` → 0 trafień (także w świeżym klonie).
- [x] `git fsck --strict` czyste; CI na `fc22c74`: **success** (run 42698787091).
- [x] Treść nietknięta: 20 commitów, identyczne tematy, **HEAD tree `2f184d8` identyczny przed/po**;
      `git diff <stary-tree> HEAD` pusty.
- [x] Bundle backupu `D:/Backups/spahotels-pre-filter-2026-11-09.bundle` (57 MB, 5 refów) — `git bundle verify` OK, klon z bundle działa.
- [x] Tag archiwalny `archive/english-wip-2026-11-04` (commit `86ddeff`) wypchnięty **po** filter-repo,
      więc nie wskrzesza usuniętych blobów; gałąź `origin/claude/trusting-fermi-dy8rdu` usunięta.
- [x] Remote po operacji: tylko `refs/heads/main` (`fc22c74`) + tag archiwalny.

## Wynik (dowód)
| miara | przed | po |
|---|---|---|
| `.git` | 64 MB | **31 MB** |
| `size-pack` | 9,10 MiB (luźne 52,76 MiB) | **30,57 MiB** (wszystko w jednym packu) |
| reachable blobs | 99,19 MiB | **46,84 MiB** (bez cloudflared i starego decku) |
| blob `cloudflared.exe` | 52,35 MiB | **brak** |
| stara wersja decku | 8,94 MiB | **brak** |
| HEAD tree | `2f184d8` | `2f184d8` (bez zmian) |
| świeży klon | ~58 MB (GitHub) | **31 MB**, 0 trafień `cloudflared` |
| testy w świeżym klonie | — | **68 passed** |

## Kluczowe / ryzyka
- **Force-push unieważnił wszystkie istniejące klony** — świadoma cena; backup bundle pozwala odtworzyć starą historię.
- `filter-repo` wymagał `--force` (ignorowane pliki buildowe typu `.next/`, `__pycache__` są liczone jako
  „untracked”); przed operacją wykonano `git gc` i `git reflog expire`, a backup był zweryfikowany.
- `--strip-blobs-with-ids` usuwa **konkretne bloby**, nie ścieżki — dzięki temu bieżący deck i drzewo
  robocze pozostały nietknięte (inaczej `--path` usunąłby też aktualny plik).
- Tag archiwalny utworzono **po** filter-repo; utworzony wcześniej wskrzesiłby 52 MB blobu przez tag.
- Nie usuwać `.gitattributes` (wpisy `binary` na `*.exe` zapobiegają powtórce).
- GitHub `size` w API (58 523 KB) odświeża się asynchronicznie — miarodajny jest świeży klon.
