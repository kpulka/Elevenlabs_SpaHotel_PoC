# Mock Backend — Wirtualny Recepcjonista AI 🏨
## Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Mock backendu PoC: symuluje PMS uzdrowiska i obsługuje **webhooki narzędzi agenta ElevenLabs Conversational AI** („Anna”, Wirtualna Recepcjonistka).

- **7 endpointów POST** (webhooki narzędzi agenta) + **2 endpointy GET** (`/health`, `/`)
- **Port 8011** (8000 jest zajęty przez proces systemowy na hoście demo — nie walcz z systemem)
- Stan w pamięci procesu: rezerwacje i zajętość slotów SPA (bez bazy danych)

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

> **To nie jest publiczne API hotelu.** To atrapa PMS-a dla prezentacji PoC —
> patrz sekcja „Known limitations (PoC)”.

### Kontrakt pól (agent ElevenLabs polega na tych nazwach)

| Endpoint | Pola żądania | Pola odpowiedzi (zawsze obecne) |
|----------|--------------|---------------------------------|
| `check_spa_availability` | `service_name`, `date` | `available`, `service_name`, `date`, `message`, `available_services` (+ `slots` gdy w oknie rezerwacji, `ambiguous` przy niejednoznacznej nazwie) |
| `book_spa_appointment` | `service_name`, `date`, `time`, `guest_name` | `success`, `confirmation_id`, `service_name`, `date`, `time`, `guest_name`, `message` (+ `slots` / `ambiguous` przy odmowie) |
| `cancel_spa_appointment` | `confirmation_id`, `reason`, `medical_release`, `language`, **`appointment_datetime`** | `success`, `confirmation_id`, `cancelled`, `fee`, `medical_release`, `message`, `note`, `free_of_charge`, `fee_rule`, `found` |
| `reschedule_spa_appointment` | `confirmation_id`, `service_name`, `new_date`, `new_time`, `guest_name`, `language` | `success`, `confirmation_id`, `service_name`, `new_date`, `new_time`, `guest_name`, `message`, `note` |
| `check_room_availability` | `room_type`, `check_in`, `check_out` | `available`, `room_type`, `price_per_night`, `check_in`, `check_out`, `total_nights`, `total_price`, `message` |
| `send_sms_summary` | `phone_number`, `summary_text`, `confirmation_id`, `language` | `success`, `message`, `delivered_to`, `language` |
| `transfer_to_simulated_handoff` | `department`, `reason`, `guest_name`, `language` | `success`, `simulated`, `message`, `department`, `reason`, `guest_name`, `language`, `note` |
| `GET /health` | — | `status`, `version`, `uptime_seconds` |

Jedynym polem **dodanym** do kontraktu jest opcjonalne `appointment_datetime`
(ISO 8601, z godziną) w `cancel_spa_appointment` — bez niego reguła opłat nie
ma jak rozstrzygnąć „>2h / <2h”; szczegóły niżej.

---

## 🚦 Semantyka błędów (ważne dla agenta głosowego)

| Sytuacja | HTTP | Odpowiedź |
|----------|------|-----------|
| Zły format danych (np. `date="31/08/2026"`, `time="99:99"`, puste `guest_name`) | **422** | błąd walidacji Pydantic z czytelnym `msg` |
| Termin w przeszłości, poza 14-dniowym oknem, zajęty slot, nieznany/niejednoznaczny zabieg, nieznany typ pokoju | **200** | `available: false` / `success: false` + `message` (agent czyta to na głos) |

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

Wymagany Python: **3.13+** (testowane na 3.13/3.14; obraz kontenera to `python:3.13-slim`).

### Testy

```bash
cd mock_backend
python -m pytest -q
```

Testy używają `fastapi.testclient`, nie wymagają sieci ani danych Telegrama
(49 przypadków: walidacja 422, daty przeszłe, zajmowanie/zwalnianie slotów,
reguły opłat, reschedule, ceny pokoi, katalog/aliasy, `/health`, kontrakt pól).

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

---

## 🐳 Podman / Docker

Dockerfile leży w `tunnel/Dockerfile`, ale **kontekstem builda jest `mock_backend/`**
(ścieżki `COPY` są względne wobec kontekstu). Nazwa obrazu musi brzmieć
`bukowy-dwor-backend`, bo tak uruchamia go `tunnel/podman_start.sh`.

```bash
cd mock_backend
podman build -t bukowy-dwor-backend -f tunnel/Dockerfile .
podman run -d --name bukowy-dwor-backend -p 8011:8011 \
  -e TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
  -e TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" \
  localhost/bukowy-dwor-backend
curl -s localhost:8011/health
```

Zatrzymanie: `podman stop bukowy-dwor-backend` (albo `tunnel/podman_stop.sh`, który
sprząta też tunel). `.containerignore` wyklucza z kontekstu `tunnel/`, `tests/`,
`__pycache__` i `.env`.

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

Zablokowane terminy (`zajete_terminy` w `rooms.json`): weekend **30–31.08.2026**.
To dane statyczne — gdy wypadną w przeszłości, blokada jest nieaktywna
(przeszłe terminy odrzuca osobna reguła).

### SPA — katalog z `data/spa_schedule.json` (seed przy starcie)

| Kod | Nazwa (wyświetlana) | Aliasy |
|-----|---------------------|--------|
| `kapiel_siarczkowa` | kąpiel siarczkowa Ukojenie Stawów | kąpiel siarczkowa, ukojenie stawów, siarczkowa, sulphur bath, sulfur bath |
| `masaz_leczniczy` | masaż leczniczy pleców | masaż leczniczy, masaz leczniczy plecow, leczniczy pleców, masaż pleców, back massage, therapeutic massage |
| `kapiel_borowinowa` | kąpiel borowinowa | borowinowa, borowina, peat bath, mud bath |
| `jonoforeza` | jonoforeza | ionoforeza, jonoforeza zabieg, iontophoresis |
| `masaz_klasyczny` | masaż klasyczny | masaz klasyczny, klasyczny, masaż relaksacyjny, classic massage, swedish massage |

Godziny zabiegów (dla każdego zabiegu): `10:00, 11:00, 14:00, 14:30, 15:00, 16:00`.
Okno rezerwacji: **najbliższe 14 dni** liczone od dnia bieżącego (przewijane).

Dopasowanie nazwy: **dokładne (bez diakrytyków) → alias → podciąg**.
Podciąg pasujący do kilku zabiegów (np. „masaż”) zwraca `available: false`
z listą `ambiguous` i `available_services` — agent ma dopytać gościa.

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
├── main.py              # aplikacja FastAPI + wszystkie trasy (app = main:app)
├── schemas.py           # modele Pydantic + walidacja formatów (422)
├── catalog.py           # katalog zabiegów, normalizacja, resolver+aliasy
├── store.py             # stan slotów/rezerwacji (in-memory) + katalog pokoi
├── telegram.py          # jeden wspólny helper wysyłki na Telegram
├── requirements.txt     # runtime, wersje przypięte
├── requirements-dev.txt # runtime + pytest
├── pytest.ini           # pythonpath + testpaths
├── tests/
│   ├── conftest.py      # fixture: czysty stan, cisza w konsoli
│   └── test_api.py      # 49 testów API
├── data/
│   ├── rooms.json       # typy pokoi, ceny, terminy zablokowane (jedyne źródło)
│   └── spa_schedule.json# seed zabiegów/aliasów/godzin (nie jest nadpisywany)
└── tunnel/
    ├── Dockerfile       # obraz kontenera (kontekst builda = mock_backend/)
    ├── podman_start.sh  # start kontenera + tunel + update webhooków
    └── start_anna.sh    # start backendu z hosta + tunel + update webhooków
```

---

## ⚠️ Known limitations (PoC)

- **Stan tylko w pamięci** — rezerwacje i zajętość slotów znikają po restarcie procesu (brak bazy danych).
- **Brak autoryzacji na webhookach** — każdy, kto zna URL tunelu, może wywołać dowolne narzędzie.
- **Ulotny URL trycloudflare** — adres zmienia się przy każdym restarcie tunelu (skrypty aktualizują webhooki, ale nie ma trwałej domeny).
- **Brak rzeczywistego PMS/SMS** — „SMS” to wydruk w konsoli + opcjonalny Telegram; brak integracji z systemem hotelowym.
- **Telefon/handoff tylko symulowany** — bez telefonii (SIP) nie ma prawdziwego przekierowania do człowieka.
- **Dane demo są statyczne** — cennik, godziny i blokada weekendu to wartości z plików JSON, nie żywy kalendarz.
- **Brak uwierzytelniania i limitów** — nie wystawiaj tego backendu publicznie poza czasem demo.

> **Wskazówka na prezentację:** zostaw terminal z serwerem na bocznym ekranie —
> logi demo (`ANNA_DEMO_LOGS`, domyślnie włączone) pokazują każde wywołanie
> narzędzia przez Annę w czasie rzeczywistym.
