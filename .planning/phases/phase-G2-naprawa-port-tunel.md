# Phase G2 — Naprawa (wolny port + cloudflared)

## Cel
Przywrócić działający mock backend i publiczny tunel, nie konfliktując z systemowym portem 8000.

## Krok 1 — Backend na wolnym porcie 8011
```bash
cd mock_backend && python -m uvicorn main:app --host 0.0.0.0 --port 8011
```
> Nie walczymy z `svchost.exe` na 8000 — wybrano wolny port 8011.

## Krok 2 — cloudflared (lokalny w projekcie)
Pobierz binary Windows amd64 (ostatni release cloudflared):
```bash
mkdir -p mock_backend/tunnel
curl -sL -o mock_backend/tunnel/cloudflared.exe \
  "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
```
- Instalacja **lokalna w projekcie** (nie systemowo).

## Krok 3 — Tunel + weryfikacja
```bash
./cloudflared.exe tunnel --url http://localhost:8011 --no-autoupdate
```
Wylap nowy publiczny URL (trycloudflare) z logu. Potwierdź publiczne endpointy:
```bash
curl -X POST <URL>/check_room_availability -H "Content-Type: application/json" -d '{"room_type":"dwuosobowy","check_in":"2026-09-10","check_out":"2026-09-13"}'
# -> {"available":true,...,"total_price":1500,...}
```

## DoD
- Backend działa na :8011 (`"status":"OK"`).
- Publiczny tunel odpowiada (check_room → available:true).
- cloudflared w projekcie, uruchomiony.

## Uwaga
Trycloudflare URL **zmienia się przy restarcie** → wymaga auto-update webhooków (G3/G4).