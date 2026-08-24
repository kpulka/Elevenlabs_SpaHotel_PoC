# Phase G3 — Skrypt trwały startowy `start_anna.sh`

## Cel
Jedno polecenie podnoszące całość i **automatycznie naprawiające webhooki** po restarcie (bo trycloudflare zmienia URL).

## Plik: `mock_backend/tunnel/start_anna.sh`
Idempotentny skrypt bash. Co robi:
1. Znajduje cloudflared (lokalny w projekcie, potem systemowy).
2. Jeśli backend nie działa → uruchamia uvicorn na wolnym porcie (domyślnie 8011, argument `$1`).
3. Startuje tunel `cloudflared tunnel --url http://localhost:$PORT` do logu.
4. Wyłapuje nowy publiczny URL (regex `https://...trycloudflare.com`) z logu.
5. Zapisuje stan (`port`, `backend_pid`, `tunnel_pid`, `url`) do `tunnel/state.json`.
6. **Aktualizuje 5 narzędzi agenta** (PATCH `/v1/convai/tools/{id}`) na nowy URL — klucz z `frontend/.env.local`.

### Narzędzia aktualizowane
| tool_id (roszczek) | name |
|---|---|
| tool_4801m0ncs38tf8t93f45jfj992dt | check_spa_availability |
| tool_6001m0ncs38vf73v1zbaa9p5vdfv | book_spa_appointment |
| tool_6301m0ncs38wewt865sh99v1qkm8 | check_room_availability |
| tool_8101m0ncs38xe6tb29923tjt9045 | send_sms_summary |
| tool_6001m0ntyt8xefgsx1e8mcqnsw1n | transfer_to_simulated_handoff |

## Użycie
```bash
cd mock_backend/tunnel && ./start_anna.sh        # domyślnie 8011
# ./start_anna.sh 8012
```

## Weryfikacja (DoD)
- Po wywołaniu: backend :8011 żyje, nowy URL tunelu, 5× PATCH zwraca 200.
- `state.json` zawiera plik z `url`.
- Ponowne odpalenie nie duplikuje backendu (idempotencja).

## Kluczowe
- **auto-update webhooków to sedno** — bez niego ulotny URL trycloudflare znów zadłanie agenta po restarcie.