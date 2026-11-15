# Mock Backend — Wirtualny Recepcjonista AI 🏨
## Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Mock backendu PoC: symuluje PMS uzdrowiska i obsługuje **webhooki narzędzi agenta ElevenLabs Conversational AI** („Anna”, Wirtualna Recepcjonistka).

- **7 endpointów POST** (webhooki narzędzi agenta) + **3 endpointy GET** (`/health`, `/`, `/metrics`)
- **Port 8011** (8000 jest zajęty przez proces systemowy na hoście demo — nie walcz z systemem)
- Stan: rezerwacje i zajętość slotów SPA — w pamięci procesu (domyślnie) albo w SQLite (`ANNA_DB_PATH`)

---

## 📡 Endpointy (webhook tools agenta)

| Metoda | Ścieżka | Narzędzie agenta |
|--------|---------|------------------|
| POST | `/check_spa_availability` | `check_spa_availability` |
| POST | `/book_spa_appointment` | `book_spa_appointment` |
| POST | `/cancel_spa_appointment` | `cancel_spa_appointment` |
| POST | `/reschedule_spa_appointment` | `reschedule_spa_appointment` |
| POST | `/check_room_availability` | `check_room_availability` |
| POST | `/send_sms_summary` | `send_sms_summary` |
| POST | `/transfer_to_simulated_handoff` | `transfer_to_simulated_handoff` |
| GET | `/health` | health-check tunelu / monitoringu |
| GET | `/` | podsumowanie działania i katalog danych |
| GET | `/metrics` | liczniki i czasy odpowiedzi procesu (JSON, w pamięci) |

> **To nie jest publiczne API hotelu.** To atrapa PMS-a dla prezentacji PoC —
> patrz sekcja „Known limitations (PoC)”.

### Kontrakt pól (agent ElevenLabs polega na tych nazwach)

| Endpoint | Pola żądania | Pola odpowiedzi (zawsze obecne) |
|----------|--------------|---------------------------------|
| `check_spa_availability` | `service_name`, `date` | `available`, `service_name`, `date`, `message`, `available_services`, `price_pln`, `duration_min` (+ `slots` gdy w oknie rezerwacji, `ambiguous` przy niejednoznacznej nazwie) |
| `book_spa_appointment` | `service_name`, `date`, `time`, `guest_name` | `success`, `confirmation_id`, `service_name`, `date`, `time`, `guest_name`, `message` (+ `slots` / `ambiguous` przy odmowie) |
| `cancel_spa_appointment` | `confirmation_id`, `reason`, `medical_release`, `language`, **`appointment_datetime`** | `success`, `confirmation_id`, `cancelled`, `fee`, `medical_release`, `message`, `note`, `free_of_charge`, `fee_rule`, `found` |
| `reschedule_spa_appointment` | `confirmation_id`, `service_name`, `new_date`, `new_time`, `guest_name`, `language` | `success`, `confirmation_id`, `service_name`, `new_date`, `new_time`, `guest_name`, `found`, `message`, `note` (+ `previous_confirmation_id` przy sukcesie) |
| `check_room_availability` | `room_type`, `check_in`, `check_out` | `available`, `room_type`, `price_per_night`, `check_in`, `check_out`, `total_nights`, `total_price`, `message` (+ `available_room_types`, `available_room_type_names` przy nieznanym/niejednoznacznym typie) |
| `send_sms_summary` | `phone_number`, `summary_text`, `confirmation_id`, `language` | `success`, `message`, `delivered_to`, `language` |
| `transfer_to_simulated_handoff` | `department`, `reason`, `guest_name`, `language` | `success`, `simulated`, `message`, `department`, `reason`, `guest_name`, `language`, `note` |
| `GET /health` | — | `status`, `version`, `uptime_seconds` |

Pola **dodane** do kontraktu to wyłącznie rozszerzenia addytywne:

- `appointment_datetime` (opcjonalne, ISO 8601 z godziną) w `cancel_spa_appointment`
  — bez niego reguła opłat nie ma jak rozstrzygnąć „>2h / <2h”;
- `price_pln` i `duration_min` w `check_spa_availability` — cena i czas trwania
  zabiegu z katalogu (patrz „Ceny zabiegów” niżej);
- `found` w `cancel_spa_appointment` i `reschedule_spa_appointment` — czy numer
  potwierdzenia w ogóle istnieje; `false` ZAWSZE idzie w parze z `success: false`;
- `available_room_types` / `available_room_type_names` — kody i nazwy typów pokoi,
  gdy `room_type` jest nieznany lub niejednoznaczny.

---

## 🚦 Semantyka błędów (ważne dla agenta głosowego)

| Sytuacja | HTTP | Odpowiedź |
|----------|------|-----------|
| Zły format danych (np. `date="31/08/2026"`, `time="99:99"`, puste `guest_name`) | **422** | błąd walidacji Pydantic z czytelnym `msg` |
| Termin w przeszłości, poza 14-dniowym oknem, zajęty slot, nieznany/niejednoznaczny zabieg, nieznany typ pokoju | **200** | `available: false` / `success: false` + `message` (agent czyta to na głos) |
| Anulowanie lub przełożenie **nieistniejącego** numeru potwierdzenia | **200** | `success: false`, `cancelled: false`, `found: false` + prośba o sprawdzenie numeru (backend NIE tworzy przy tym nowej rezerwacji) |

Rozdzielenie jest celowe: agent głosowy dużo lepiej radzi sobie z 200 + wyjaśnieniem
niż z awarią narzędzia 4xx.

---

## 📦 Instalacja i uruchomienie (dev)

```bash
cd mock_backend
python -m pip install -r requirements-dev.txt     # runtime + pytest
# lub tylko runtime:
python -m pip install -r requirements.txt

uvicorn main:app --reload --port 8011
```

- API: <http://localhost:8011>
- Swagger UI: <http://localhost:8011/docs> · ReDoc: <http://localhost:8011/redoc>
- Health: <http://localhost:8011/health>

Wymagany Python: **3.12** (wersja z CI; obraz kontenera to `python:3.12-slim`).

### Testy

```bash
cd mock_backend
python -m pytest -q
python -m pytest -q --durations=5   # pięć najwolniejszych testów (regresja szybkości)
python -m mypy .                    # typy (mypy.ini); tests/ i skrypty tunelu poza bramką
```

The test suite uses `fastapi.testclient`, `httpx.ASGITransport` and `httpx.MockTransport`. It makes no
network calls, needs no Telegram or ElevenLabs credentials and writes no database files outside `tmp_path`.
The current number of tests is reported by CI (see the workflow in `.github/workflows/ci.yml`); to count them
locally run `python -m pytest --collect-only -q`.

Coverage (not enabled by default; CI passes `--cov`):

```bash
python -m pytest -q --cov=. --cov-report=term-missing   # configuration: mock_backend/.coveragerc
```

`.coveragerc` measures the backend code and the shared tunnel client. It omits `tests/` and the two CLI
scripts that call the live ElevenLabs API (`tunnel/sync_agent_tools.py`, `tunnel/run_simulations.py`); their
pure helpers are covered through `tunnel/_http.py` and `tests/test_run_simulations.py`.

### Kontrakt OpenAPI (snapshot)

`tests/test_openapi_contract.py` porównuje `app.openapi()` z zatwierdzonym plikiem
`tests/openapi.snapshot.json` (serializacja: posortowane klucze, `indent=2`, UTF-8,
końcowy `\n`). Zmiana nazwy lub typu pola w `schemas.py` to zmiana kontraktu, na
którym polegają narzędzia agenta ElevenLabs, więc test czerwienieje, dopóki nie
zaktualizujesz snapshotu świadomie:

```bash
cd mock_backend
UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest -q tests/test_openapi_contract.py
git diff tests/openapi.snapshot.json   # przejrzyj zmianę kontraktu
```

W PR, który zmienia kontrakt, opisz w opisie PR, które pola się zmieniły i czy
agent ElevenLabs (narzędzia `sync_agent_tools`) wymaga ponownej synchronizacji.

---

## 📲 Telegram (opcjonalnie, efekt „live” na demo)

```bash
# wartości trzymaj w mock_backend/.env (nie commitowane) lub w env procesu
export TELEGRAM_BOT_TOKEN="1234567890:***"
export TELEGRAM_CHAT_ID="-1001234567890"
```

Jak zdobyć dane: bot przez [@BotFather](https://t.me/BotFather) → dodaj bota do
kanału jako administratora → `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id`.

Bez tych zmiennych wiadomości są tylko drukowane w konsoli (demo nadal działa).
`tunnel/podman_start.sh` przekazuje zawartość `.env` do kontenera.

### Zmienne środowiskowe

| Zmienna | Domyślnie | Znaczenie |
|---------|-----------|-----------|
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | brak | wysyłka SMS/handoffu na Telegram |
| `CORS_ORIGINS` | `*` | lista originów po przecinku; przy `*` `allow_credentials=False` (wymóg specyfikacji CORS) |
| `ANNA_DEMO_LOGS` | `1` | `0` wyłącza logi demo na konsolę |
| `ANNA_ENV` | `dev` | `dev` = ostrzeżenia przy brakujących sekretach; `prod` = start odmawia bez `ANNA_WEBHOOK_SECRET` (fail-closed). Inna wartość kończy się błędem przy starcie |
| `ANNA_WEBHOOK_SECRET` | brak (auth wyłączona) | sekret webhooków: nagłówek `X-Webhook-Secret` albo podpis HMAC (patrz „Authentication”) |
| `ANNA_LOG_FORMAT` | `demo` | `json` — jeden obiekt JSON na linię (pola m.in. `request_id`, `conversation_id`), do log shipperów |
| `ANNA_DB_PATH` | `:memory:` | plik SQLite z kalendarzem SPA (rezerwacje, klucze idempotencji, numeracja); brak = stan w pamięci procesu. Patrz „Persistence” |
| `ANNA_EVENTS_WEBHOOK_URL` | brak (zdarzenia wyłączone) | adres odbiornika zdarzeń wychodzących (CRM / n8n). Działa tylko razem z `ANNA_EVENTS_SIGNING_SECRET`. Patrz „Outbound events” |
| `ANNA_EVENTS_SIGNING_SECRET` | brak | sekret HMAC podpisujący zdarzenia wychodzące |

### Authentication

Set `ANNA_WEBHOOK_SECRET` to protect the tool webhooks. Two modes are accepted, and both are rejected with
HTTP 401 when they do not verify. Both are disabled while the secret is empty (demo and tests).

* **Shared secret** (default): send `X-Webhook-Secret: <secret>`. The comparison is constant-time.
* **HMAC** (per request): send `X-Anna-Timestamp: <unix seconds>` and `X-Anna-Signature: sha256=<hex>`,
  where `hex = HMAC-SHA256(key=ANNA_WEBHOOK_SECRET, msg="<timestamp>.<raw request body>")`. The timestamp
  must be within 300 s of the server clock (replay window). When either HMAC header is present, only the
  HMAC is checked. The shared-secret header is then ignored, and both HMAC headers are required.

The HMAC uses the same `sign`/`verify` functions as the outbound events (`events.py`). A replay of the same
signed body is accepted during the 300 s window; the backend keeps no nonce store.

`ANNA_ENV=prod` makes startup fail with a clear error when `ANNA_WEBHOOK_SECRET` is empty. In `dev`, the
backend starts and logs a warning instead. The same secret must be configured in the ElevenLabs tool
definitions, otherwise their calls are rejected.

### Logi strukturalne i `/metrics`

- Logi: wpisy zawierają `request_id` żądania (i `conversation_id`, jeśli jest). W trybie
  `ANNA_LOG_FORMAT=json` każdy wpis to jeden obiekt JSON w linii; tryb `demo` zostaje domyślny.
- **Conversation id:** the agent (or a proxy) can send `X-Conversation-Id: <id>` as a header, or
  `?conversation_id=<id>` as a query parameter. The header wins when both are present. The id uses the same
  safe format as `X-Request-ID` (`[A-Za-z0-9._:-]`, at most 128 characters). Anything else is ignored. A valid
  id is echoed back in the `X-Conversation-Id` response header and written to every JSON log line of the
  request (access log, business rejections, errors, outbound events). This lets you follow one call from the
  conversation through each tool invocation.
- Personal data: phone numbers are masked to the last three digits (`********200`) in the console, the logs,
  the Telegram messages, the `delivered_to` field and the outbound events. Guest names are shortened to the
  first name and initials (`Jan K.`) in the Telegram handoff alert, the handoff logs and the handoff event.
  Phone-like numbers typed into free text (for example the handoff `reason`) are masked as well.
- `GET /metrics` zwraca liczniki i czasy odpowiedzi trzymane w pamięci procesu (JSON, bez zewnętrznych zależności).

---

## 📤 Outbound events (CRM / n8n)

When a booking is created, cancelled or rescheduled, and when a handoff is requested, the backend POSTs a
signed JSON event to `ANNA_EVENTS_WEBHOOK_URL`. Events are off unless both `ANNA_EVENTS_WEBHOOK_URL` and
`ANNA_EVENTS_SIGNING_SECRET` are set. Delivery happens after the tool response has been sent, so a failing
receiver never fails a tool call.

Contract (`events.py` is the reference implementation):

- Request: `POST <url>`, `Content-Type: application/json`.
- Body: compact JSON with sorted keys, UTF-8, for example
  `{"conversation_id":"conv_abc","data":{...},"event_id":"<uuid4>","event_type":"booking.created","occurred_at":"2026-11-15T10:00:00Z","request_id":"<id>"}`.
  `event_type` is one of `booking.created`, `booking.cancelled`, `booking.rescheduled`, `handoff.requested`.
  `conversation_id` and `request_id` are `null` when the call did not carry them.
- Headers: `X-Anna-Event-Id` (= `event_id`), `X-Anna-Timestamp` (unix seconds, decimal string) and
  `X-Anna-Signature: sha256=<hex>`, with `hex = HMAC-SHA256(key=ANNA_EVENTS_SIGNING_SECRET, msg="<timestamp>.<body>")`
  computed over the exact bytes sent.
- Delivery: up to 3 attempts (a pause of 0.5 s, then 1 s), 5 s timeout per attempt. Each attempt has a fresh
  timestamp and signature, but the body and `event_id` are the same across attempts. Receivers must
  de-duplicate on `event_id`. A final failure is logged as `events.dead_letter` (level `error`). There is no
  persistent queue: events still pending when the process stops are lost.
- `data` never contains a raw phone number. Booking events carry the full guest name, because a CRM record
  needs it. Handoff events carry the masked name and the masked reason.
- Metrics: `events.delivered` and `events.failed` (one count per event) in `GET /metrics`.
- Receiver checklist: recompute the signature over `"<timestamp>.<raw body>"`, compare in constant time, reject
  timestamps older than 300 s, and ignore an `event_id` you have already processed.

Signing test vector (also in `tests/test_events.py`):

```text
secret    = whsec_test_vector_0123
timestamp = 1767225600
body      = {"data":{"confirmation_id":"SPA-1001"},"event_id":"6f1c2b9e-0d4a-4c8e-9a51-2b7d3e4f5a6b","event_type":"booking.created"}
signature = sha256=e228d9d329e6d9898c0c0820487e48cff1279de3fc9468ca097ef1455672c7da
```

The same signature scheme protects inbound tool calls in HMAC mode (see "Authentication").

---

## 🗄️ Persistence (SQLite, optional)

By default the calendar lives in process memory, so it is lost on restart. Set `ANNA_DB_PATH` to a file path to
keep it in SQLite (standard library `sqlite3`, no ORM). The service rules do not change; only the storage does.

- **Migrations:** `sqlite_store.MIGRATIONS` is an ordered list of `(version, sql)` pairs. `migrate()` applies the
  pairs newer than the `schema_version` table, each in one transaction. Running it again is a no-op. Add a new
  pair for every schema change; never edit an applied one.
- **Tables:** `rezerwacje` (reservations), `klucze_idempotencji` (idempotency keys), `sekwencja` (confirmation
  numbers, which keep increasing across restarts), `schema_version`.
- **Slot exclusivity:** a UNIQUE index on `(klucz_slotu, godzina)` makes the second insert for a slot fail, even
  when two requests race past the service-level check.
- **Idempotency keys:** the key is the primary key of `klucze_idempotencji` and is written in the same
  transaction as its reservation. `purge_klucze(max_wiek)` deletes keys older than a TTL; it is a helper that
  nothing calls automatically. After a purge, a retry without its key falls back to the duplicate check (same
  service, date, time and guest), not to a second booking.
- **Concurrency:** one connection (`check_same_thread=False`) guarded by a lock, WAL journal mode, 5 s busy
  timeout. See the single-worker constraint below.
- **Files:** the test suite never creates a database inside the repository (it uses `tmp_path`). `*.db`,
  `*.sqlite`, `*.sqlite3` and their `-wal` / `-shm` companions are git-ignored.

Example:

```bash
ANNA_DB_PATH=./data/anna.db uvicorn main:app --port 8011   # the parent directory is created if missing
```

### Single-worker constraint

Run **one** uvicorn worker (the default). Two limits follow from this:

- With the in-memory store, every worker has its own calendar. Bookings made on one worker are invisible to the
  others, so no process-wide guarantee exists.
- With SQLite, the UNIQUE index keeps slot exclusivity across processes, but the service layer reads and then
  writes in separate statements. Without a process-wide lock, two workers can still race on the idempotency
  path. Multi-worker deployments are therefore not supported.

`tests/test_concurrency.py` fires 20 concurrent bookings for one slot through the ASGI app, for both stores,
and expects exactly one winner. This shows correctness within one process only.

---

## 🐳 Podman / Docker

Dockerfile leży w `mock_backend/Dockerfile`, a **kontekstem builda jest `mock_backend/`**
(ścieżki `COPY` są względne wobec kontekstu). Nazwa obrazu musi brzmieć
`bukowy-dwor-backend`, bo tak uruchamia go `tunnel/podman_start.sh`.

```bash
cd mock_backend
podman build -t bukowy-dwor-backend -f Dockerfile .
podman run -d --name bukowy-dwor-backend -p 8011:8011 \
  -e TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  -e TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" \
  -e ANNA_WEBHOOK_SECRET="$ANNA_WEBHOOK_SECRET" \
  localhost/bukowy-dwor-backend
curl -s localhost:8011/health
```

Obraz działa jako nieuprzywilejowany użytkownik `app` (UID 10001), ma `TZ=Europe/Warsaw`
(tzdata w obrazie) i `HEALTHCHECK` odpytujący `/health` (stdlib Pythona, bez curl).

Zatrzymanie: `podman stop bukowy-dwor-backend` (albo `tunnel/podman_stop.sh`, który
sprząta też tunel). `.containerignore` i `.dockerignore` wykluczają z kontekstu `tunnel/`,
`tests/`, cache (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`) i `.env`.

## 🌐 Tunel + webhooki (demo end-to-end)

```bash
cd mock_backend/tunnel && ./start_anna.sh      # backend + cloudflared + update 5 webhooków
cd mock_backend/tunnel && ./podman_start.sh    # wariant kontenerowy
```

Skrypt łapie publiczny URL trycloudflare, aktualizuje narzędzia agenta i zapisuje
stan w `tunnel/state.json`. Port 8000 bywa zajęty przez `svchost` — dlatego 8011.

---

## 💡 Dane demo

### Pokoje — cennik z `data/rooms.json` (jedyne źródło dla backendu)

| Kod | Nazwa | Cena / noc |
|-----|-------|------------|
| `jednoosobowy` | Pokój Jednoosobowy „Spokojny Sen” | 350 PLN |
| `dwuosobowy` | Pokój Dwuosobowy „Komfort Plus” | 500 PLN |
| `apartament` | Apartament | 750 PLN |

Ceny są zgodne z `frontend/lib/hotel-data.ts` (350 / 500 / 750) — zmiana musi
nastąpić w obu miejscach, bo frontend ma własną kopię danych marketingowych.

Zablokowane terminy (`zajete_terminy` w `rooms.json`): **28–29.12.2026**,
przerwa świąteczno-noworoczna (blokada dotyczy wszystkich typów pokoi).

Zasada (żeby demo „wszystko zajęte” działało):

- okno blokady MUSI leżeć w przyszłości — inaczej kolizja nigdy nie wystąpi,
  a jedyną odmową zostanie „data w przeszłości”; test
  `test_blocked_window_dates_are_in_the_future` pilnuje tego i podpowiada,
  że trzeba przesunąć okno w `rooms.json`;
- wpis blokady ma tylko `opis` (etykieta) i `daty` (ISO 8601) — **zakres dat
  w odpowiedzi jest generowany** z `daty` przez `KatalogPokoi.opis_blokady()`
  (`28-29.12.2026`). Nie wpisuj gotowego zakresu obok dat; test
  `test_blocked_description_is_generated_from_json` dowodzi, że opis idzie
  za danymi.

### SPA — katalog z `data/spa_schedule.json` (seed przy starcie)

| Kod | Nazwa (wyświetlana) | Cena | Czas | Źródło ceny | Aliasy |
|-----|---------------------|------|------|-------------|--------|
| `kapiel_siarczkowa` | kąpiel siarczkowa Ukojenie Stawów | 80 PLN | 20 min | baza wiedzy | kąpiel siarczkowa, ukojenie stawów, siarczkowa, sulphur bath, sulfur bath |
| `masaz_leczniczy` | masaż leczniczy pleców | 120 PLN | 30 min | baza wiedzy | masaż leczniczy, masaz leczniczy plecow, leczniczy pleców, masaż pleców, back massage, therapeutic massage |
| `kapiel_borowinowa` | kąpiel borowinowa | 100 PLN | 25 min | baza wiedzy | borowinowa, borowina, peat bath, mud bath |
| `jonoforeza` | jonoforeza | 70 PLN | 20 min | baza wiedzy | ionoforeza, jonoforeza zabieg, iontophoresis |
| `masaz_klasyczny` | masaż klasyczny | 160 PLN | 50 min | baza wiedzy | masaz klasyczny, klasyczny, masaż relaksacyjny, classic massage, swedish massage |
| `gimnastyka_lecznicza` | gimnastyka lecznicza (grupowa) | 30 PLN | 45 min | strona www | gimnastyka lecznicza, gimnastyka, gimnastyka grupowa, gimnastyka dla seniorów, ćwiczenia grupowe, therapeutic gymnastics, group gymnastics |

Godziny zabiegów (dla każdego zabiegu): `10:00, 11:00, 14:00, 14:30, 15:00, 16:00`.
Okno rezerwacji: **najbliższe 14 dni** liczone od dnia bieżącego (przewijane).

Dopasowanie nazwy: **dokładne (bez diakrytyków) → alias → podciąg**.
Podciąg pasujący do kilku zabiegów (np. „masaż”) zwraca `available: false`
z listą `ambiguous` i `available_services` — agent ma dopytać gościa.

Katalog jest **zamknięty**: każde `service_name`, które nie trafia w żaden wpis,
dostaje `available: false` + `available_services`. Nowy zabieg dodaje się
wyłącznie w `data/spa_schedule.json` (kod, nazwa, aliasy, `price_pln`,
`duration_min`, `zrodlo_ceny`) — brak ceny/czasu w seedzie to `ValueError`
przy starcie, a nie cichy katalog bez cennika.

**Baseny termalne (32°C i 34°C) nie są w katalogu zabiegów.** Strona pokazuje je
jako część oferty, ale to udogodnienia strefy basenowej w cenie pobytu, a nie
usługa do rezerwacji — nie mają ceny jednostkowej ani slotów, więc agent nie
powinien ich „rezerwować”. Decyzja jest zapisana w `_baseny` w seedzie.

### Ceny zabiegów — jedno źródło prawdy

Ceny i czasy trzyma **wyłącznie** `data/spa_schedule.json`, w polach
`price_pln` i `duration_min`; `check_spa_availability` zwraca je jako
`price_pln` / `duration_min`, więc frontend da się wygenerować z tych samych liczb.

Wartości kanoniczne = **baza wiedzy agenta**
(`agent/knowledge_base/02_katalog_zabiegow_spa_i_zdrowie.md`):
80 / 120 / 100 / 70 / 160 PLN. To te liczby Anna wypowiada gościowi na głos —
nie wolno ich zmieniać po cichu tylko dlatego, że inny plik podaje inne.
`gimnastyka_lecznicza` (30 PLN / 45 min) też jest w bazie wiedzy — doszła tam razem
z porządkami 2026-11, więc wszystkie sześć pozycji ma `zrodlo_ceny: "baza_wiedzy"`.

Strona nie trzyma własnej kopii cen: `frontend/scripts/sync-data.mjs` generuje
`frontend/lib/generated/hotel-facts.ts` z tego pliku i z `rooms.json`, a `pnpm data:check`
(w CI) wywala build, jeśli wygenerowany plik rozjedzie się z backendem. Po zmianie ceny
w seedzie wystarczy `pnpm data:sync`.

### Model zasobu dla slotów (świadome ograniczenie)

Zajętość trzymana jest jako `{data: {godzina, ...}}` — **bez kodu zabiegu**.
Założenie: na daną godzinę dostępny jest **jeden gabinet / jeden fizjoterapeuta
wspólny dla wszystkich zabiegów**. Konsekwencje:

- nie da się sprzedać 14:00 dwóm gościom na dwa różne zabiegi (to był realny
  defekt: klucz `(zabieg, data)` pozwalał na podwójną sprzedaż tego samego
  człowieka);
- kalendarz jest bardziej restrykcyjny niż realne SPA z kilkoma gabinetami —
  jeśli kiedyś będzie ich więcej, klucz trzeba rozszerzyć do
  `(gabinet, data)` i przypisać zabiegi do gabinetów;
- testy: `test_same_hour_cannot_be_sold_twice_for_different_treatments`
  oraz `test_double_booking_same_slot_fails_with_remaining_slots`.

### Reguła opłat przy anulacji SPA

| Warunek | `fee` | `free_of_charge` |
|---------|-------|------------------|
| `appointment_datetime` > 2h przed zabiegiem | `0.0` | `true` |
| `appointment_datetime` < 2h przed zabiegiem | `0.5` | `false` |
| `medical_release: true` (dowolny timing) | `0.0` | `true` |
| brak `appointment_datetime` | `0.5` | `false` (`fee_rule`: „Brak godziny zabiegu…”) |

`fee` pozostaje **ułamkiem** ceny zabiegu (0.0 / 0.5) dla zgodności z agentem;
`fee_rule` mówi wprost, która reguła zadziałała (PL/EN wg `language`).

---

## 🗂️ Struktura

```
mock_backend/
├── main.py              # aplikacja FastAPI: konfiguracja, CORS, /health, / + include_router (app = main:app)
├── routers/
│   ├── security.py      # uwierzytelnianie webhooków: X-Webhook-Secret albo HMAC
│   ├── spa.py           # trasy SPA: check/book/cancel/reschedule_spa_appointment
│   ├── rooms.py         # trasa dostępności pokoi: check_room_availability
│   └── comms.py         # trasy komunikacyjne: send_sms_summary, transfer_to_simulated_handoff
├── config.py            # konfiguracja ze zmiennych środowiskowych (Settings: env, webhook_secret, log_format, db_path, events_*)
├── logs.py              # logi: tryb demo / json, request/conversation id, maskowanie PII (log_event, log_demo)
├── events.py            # zdarzenia wychodzące (podpisane POST, retry, dead letter) + sign/verify (HMAC)
├── metrics.py           # liczniki i czasy odpowiedzi dla GET /metrics
├── data.py              # dane demo (singletony: USLUGI, SPA_STORE, POKOJE, NAZWY_USLUG); SPA_STORE = pamięć lub SQLite
├── i18n.py              # obsługa języka odpowiedzi (pick, lang_of, is_en)
├── schemas.py           # modele Pydantic + walidacja formatów (422)
├── services/spa.py     # reguły biznesowe SPA (bez FastAPI)
├── responses/           # pakiet odpowiedzi/odmów (kontrakt z promptem agenta): availability, booking, cancel, reschedule, _common
├── catalog.py           # katalog zabiegów, normalizacja, resolver+aliasy
├── store.py             # kalendarz SPA w pamięci procesu (SpaStore) + katalog pokoi
├── sqlite_store.py      # SqliteSpaStore: ten sam interfejs w SQLite, migracje, klucze idempotencji z TTL
├── telegram.py          # jeden wspólny helper wysyłki na Telegram
├── requirements.txt     # runtime, wersje przypięte
├── requirements-dev.txt # runtime + pytest + pytest-cov + mypy
├── pytest.ini           # pythonpath + testpaths (bez --cov; CI dodaje)
├── .coveragerc          # zakres pomiaru pokrycia (bez tests/ i skryptów CLI tunelu)
├── tests/
│   ├── conftest.py      # fixture: czysty stan, cisza w konsoli
│   ├── helpers.py       # stałe URL i helpery wspólne dla testów
│   ├── test_spa_*.py    # rezerwacja / anulowanie / przełożenie (HTTP)
│   ├── test_spa_service.py, test_spa_service_errors.py # reguły SPA bez TestClient
│   ├── test_sqlite_store.py # migracje, restart, idempotencja, TTL, wątki (SQLite)
│   ├── test_concurrency.py  # 20 równoległych rezerwacji, pamięć i SQLite
│   ├── test_events.py       # podpis (wektor testowy), retry, dead letter, PII w zdarzeniach
│   ├── test_auth.py         # X-Webhook-Secret, HMAC, fail-closed w prod
│   ├── test_observability.py, test_logs.py # request/conversation id, JSON, maskowanie
│   ├── test_schemas.py, test_telegram.py
│   ├── test_rooms.py, test_comms.py, test_app.py
│   └── test_http_client.py, test_run_simulations.py # narzędzia tunelu (retry tylko dla idempotentnych)
├── data/
│   ├── rooms.json       # typy pokoi, ceny, terminy zablokowane (jedyne źródło)
│   └── spa_schedule.json# seed zabiegów/aliasów/godzin/cen (nie jest nadpisywany)
└── tunnel/
    ├── Dockerfile       # obraz kontenera (kontekst builda = mock_backend/)
    ├── podman_start.sh  # start kontenera + tunel + update webhooków
    └── start_anna.sh    # start backendu z hosta + tunel + update webhooków
```

---

## ⚠️ Known limitations (PoC)

- **Stan domyślnie w pamięci** — bez `ANNA_DB_PATH` rezerwacje i zajętość slotów znikają po restarcie procesu. Z `ANNA_DB_PATH` stan jest w SQLite, ale tylko dla jednego workera (patrz „Single-worker constraint”).
- **Autoryzacja webhooków jest opcjonalna w dev** — bez `ANNA_WEBHOOK_SECRET` każdy, kto zna URL tunelu, może wywołać dowolne narzędzie. `ANNA_ENV=prod` wymusza sekret przy starcie. Brak ochrony przed powtórzeniem podpisanego żądania w oknie 300 s (brak magazynu nonce).
- **Zdarzenia wychodzące bez trwałej kolejki** — po wyczerpaniu prób zdarzenie trafia tylko do logu `events.dead_letter`; zdarzenia oczekujące w chwili zatrzymania procesu przepadają.
- **Ulotny URL trycloudflare** — adres zmienia się przy każdym restarcie tunelu (skrypty aktualizują webhooki, ale nie ma trwałej domeny).
- **Brak rzeczywistego PMS/SMS** — „SMS” to wydruk w konsoli + opcjonalny Telegram; brak integracji z systemem hotelowym.
- **Telefon/handoff tylko symulowany** — bez telefonii (SIP) nie ma prawdziwego przekierowania do człowieka.
- **Dane demo są statyczne** — cennik, godziny i blokada świąteczna to wartości z plików JSON, nie żywy kalendarz.
- **Jeden gabinet na godzinę** — wszystkie zabiegi dzielą jeden kalendarz (patrz „Model zasobu dla slotów”); realne SPA z kilkoma gabinetami wymaga klucza `(gabinet, data)`.
- **Ceny poza backendem są nieaktualne** — `frontend/lib/hotel-data.ts` nadal ma 65/70/45/90/30 PLN; kanoniczne są wartości z `data/spa_schedule.json`.
- **Brak limitów zapytań** — nie wystawiaj tego backendu publicznie poza czasem demo.

> **Wskazówka na prezentację:** zostaw terminal z serwerem na bocznym ekranie —
> logi demo (`ANNA_DEMO_LOGS`, domyślnie włączone) pokazują każde wywołanie
> narzędzia przez Annę w czasie rzeczywistym.
