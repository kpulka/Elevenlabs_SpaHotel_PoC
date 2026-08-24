# Phase 5 — Uruchom mock backend

## Cel
Uruchomić lokalny FastAPI (mock PMS) i potwierdzić 4 endpointy webhook.

## Zależności
Brak (można równolegle z Phase 2–4).

## Kroki

1. Zainstaluj zależności:
```bash
cd mock_backend
pip install -r requirements.txt
```

2. Uruchom serwer (background):
```bash
uvicorn main:app --port 8000
```
(W Hermes: `terminal(background=true)` albo osobny proces.)

3. Zdrowie (GET):
```bash
curl -s http://localhost:8000/ | head
```
Oczekiwane: `{"status":"OK","projekt":"Wirtualny Recepcjonista AI — Bukowy Dwór",...}`.

4. Test 4 endpointów (POST):

```bash
# 1. availability SPA
curl -s -X POST http://localhost:8000/check_spa_availability \
  -H "Content-Type: application/json" \
  -d '{"service_name":"masaż klasyczny","date":"2026-08-25"}'

# 2. book SPA
curl -s -X POST http://localhost:8000/book_spa_appointment \
  -H "Content-Type: application/json" \
  -d '{"service_name":"kąpiel borowinowa","date":"2026-08-25","time":"14:00","guest_name":"Jan Kowalski"}'

# 3. room availability
curl -s -X POST http://localhost:8000/check_room_availability \
  -H "Content-Type: application/json" \
  -d '{"room_type":"dwuosobowy","check_in":"2026-08-25","check_out":"2026-08-28"}'

# 4. sms summary
curl -s -X POST http://localhost:8000/send_sms_summary \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+48123456789","summary_text":"Test","confirmation_id":"SPA-1234"}'
```

## Oczekiwane odpowiedzi
1. `{"available":true,"slots":[...],"service_name":...,"date":...}`
2. `{"success":true,"confirmation_id":"SPA-XXXX",...}`
3. `{"available":true,"price_per_night":500,"total_price":1500,...}` (weekend 30–31.08 → `"available":false`)
4. `{"success":true,"message":"Wiadomość wysłana.","delivered_to":...}`

## DoD
- [ ] Serwer działa na `localhost:8000`.
- [ ] 4 endpointy zwracają poprawne JSON (sprawdź pola: `available`, `slots`, `confirmation_id`, `total_price`).
- [ ] Weekend 30–31.08.2026 zwraca `available:false` (logika zajętych dat działa).

## Wynik przekazany do Phase 6
Działający backend na `localhost:8000` + mapa endpointów.