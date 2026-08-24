# Phase G4 — Autostart (on-logon, user-level)

## Cel
Uruchamiać `start_anna.sh` samoczynnie przy logowaniu użytkownika, bez ręki i bez potrzeby admina. To eliminuje pierwotną przyczynę awarii (webhooki wymagały ręcznego startu).

## Plik: `…\Startup\anna_backend_start.cmd`
Lokalizacja: `C:\Users\jakub\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\anna_backend_start.cmd`

Treść (wywołuje bash przez pełną ścieżkę MSYS — Tu MSYS Git jest pod `L:\Program Files\Git\`):
```cmd
start "" "L:\Program Files\Git\usr\bin\bash.exe" -c "cd /d/Projects/Elevenlabs/SpaHotels/mock_backend/tunnel && bash start_anna.sh >/d/Projects/Elevenlabs/SpaHotels/mock_backend/tunnel/autostart.log 2>&1"
```

## Dlaczego user-level/on-logon (nie at-start)
- Folder Startup użytkownika działa **bez admina** (schtasks /update by wymagał admina).
- On-logon startuje gdy masz sesję — tam gdzie pracujesz; at-start bez zalogowanego użytkownika może nie podnieść procesów poprawnie.

## Weryfikacja (DoD)
- Plik istnieje w folder Startup.
- `bash` z pełnej ścieżki (`L:\...\bash.exe`) działa (test: `pwd`, `whoami`).
- `start_anna.sh` idempotentny — na logon nie duplikuje już działającego backendu.
- Przy restarcie: backend + tunel + webhooki same wracają.

## Uwagi / rozszerzenie
- **Start przy starcie systemu** (bez logowania) wymaga Task Scheduler `at startup` z uprawnieniami admina — opcjonalnie.
- **Podman Desktop**: platforma kontaner, nie tuneler; backend-w-kontaner to opcjonal — dla PoC bieżący Windows-autostart wystarcza.