# Phase G1 — Diagnoza awarii (check_room + handoff padły)

## Cel
Ustalić, dlaczego w rozmowie z Anną padły i `check_room_availability`, i handoff (`transfer_to_simulated_handoff`) — pozornie „agent zawiódł", w rzeczywistości nie działał żaden webhook.

## Krok 1 — Sprawdzenie żywotności
```bash
curl -s -o /dev/null -w "%{http_code}" <public tunnel URL>/ 
curl -s -m 8 http://localhost:8000/   # czy backend odpowiada
```

## Krok 2 — Ustalenia (fakt)
- **Port 8000 zajęty przez systemowy `svchost.exe`** (PID 5248) — mock backend nie ma jak tam startować (bind error 10048).
- Tunel trycloudflare **martwy / nieuruchomiony** → publiczny URL nie odpowiada.
- Konsekwencja: wszystkie 5 webhooków agenta bez celu; `check_room` → timeout/retry (Anna zrobiła retry zgodnie z promptem ✓), potem chciała handoff → też padł → „problem z połączeniem z recepcją".

## Krok 3 — DoD
- Zdiagnozowano źródło (backend+tunel, NIE prompt).
- Zanotowano, że 8000 nie jest dostępny (systemowy proces).
- Żadnych zmian — faza czysto badawcza.

## Wnioski
Problem to **nie zachowanie Anny, a operacyjna martwa infrastruktura webhooków.** Rozwiązanie: wolny port + trwały start + autostart (G2–G4).