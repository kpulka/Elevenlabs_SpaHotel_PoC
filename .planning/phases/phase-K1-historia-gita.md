# Phase K1 — Historia gita i rozmiar repozytorium

## Cel
Usunąć z historii 53 MB blobu `cloudflared.exe` (usunięty z drzewa w commicie `c2f9824`, ale nadal
siedzi w historii), żeby klon publicznego repo ważył kilka MB, a nie ~58 MB.

**Stan wyjściowy (zmierzony):** `.git` = 55 MB, `git rev-list --objects --all` pokazuje blob
`54893480 B` dla `mock_backend/tunnel/cloudflared.exe`; GitHub `size` = 58 126 KB.

## Zakres
- Historia gita (`main`), `.gitignore`, `.gitattributes` (bez zmian treści).
- **Nie dotyka kodu** — po fazie drzewo robocze ma być bajtowo identyczne.

## Kroki
1. Backup przed operacją (poza repo): `git bundle create D:/Backups/spahotels-pre-filter-$(date +%F).bundle --all`.
2. Narzędzie: `pip install git-filter-repo` (BFG jako alternatywa).
3. Usunięcie ścieżki z całej historii:
   `git filter-repo --path mock_backend/tunnel/cloudflared.exe --invert-paths`
4. Porządki: `git reflog expire --expire=now --all`, `git gc --prune=now --aggressive`.
5. Weryfikacja **przed** push-em:
   - `git rev-list --objects --all | grep -i cloudflared` → pusto
   - `git count-objects -vH` → `size-pack` < 6 MB
   - `git fsck --strict` → bez błędów
   - `git log --oneline origin/main..HEAD` → pusto (historia tylko skrócona, nie zmieniona treściowo)
6. Force-push: `git push --force origin main` (branch `main` jest jedynym, który zostaje).
7. Kontrola po pushu: świeży klon do katalogu tymczasowego → `du -sh .git`, `pytest`, `pnpm typecheck`,
   uruchomienie CI.
8. Na laptopie: **usunąć stary klon i sklonować od nowa** (stary będzie próbował scalać nieistniejące
   commity).

## Weryfikacja (DoD)
- [ ] `git count-objects -vH` w repo i w świeżym klonie: `size-pack` < 6 MB.
- [ ] `git rev-list --objects --all | grep cloudflared` → 0 trafień.
- [ ] `git fsck` czyste; CI zielone na nowym HEAD.
- [ ] README/obrazy/dokumentacja nietknięte (diff drzewa względem backupu = 0).
- [ ] Bundle backupu istnieje i daje się odtworzyć (`git clone backup.bundle`).

## Kluczowe / ryzyka
- **Force-push psuje każdy istniejący klon** (drugi laptop, ewentualne fork-i). To jest świadoma cena;
  bez tego repo zostaje 15× większe niż treść.
- Nie robić tego, gdy inna sesja agenta pracuje w tym drzewie (sprawdzić `git status`, `git log`, mtime).
- `filter-repo` usuwa `origin` — trzeba go dodać z powrotem przed push-em
  (`git remote add origin https://github.com/kpulka/Elevenlabs_SpaHotel_PoC.git`).
- Nie usuwać `.gitattributes` (wpisy `binary` na `*.exe` zapobiegają powtórce).
