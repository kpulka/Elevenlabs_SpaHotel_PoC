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

Wymagany Python: **3.13+** (testowane na 3.13/3.14; obraz kontenera to `python:3.13-slim`).

### Testy

```bash
cd mock_backend
python -m pytest -q
```

Testy używają `fastapi.testclient`, nie wymagają sieci ani danych Telegrama
(68 przypadków: walidacja 422, daty przeszłe, zajmowanie/zwalnianie slotów
z wspólnym kalendarzem, reguły opłat, reschedule, nieistniejące numery
potwierdzenia, ceny pokoi, blokada terminów, katalog/aliasy, cennik zabiegów,
`/health`, kontrakt pól).

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
(`docs/baza_wiedzy_rag_bukowy_dwor/02_katalog_zabiegow_spa_i_zdrowie.md`):
80 / 120 / 100 / 70 / 160 PLN. To te liczby Anna wypowiada gościowi na głos —
nie wolno ich zmieniać po cichu tylko dlatego, że inny plik podaje inne.
Jedyny wyjątek: `gimnastyka_lecznicza` nie występuje w bazie wiedzy, więc jej
30 PLN / 45 min pochodzi ze strony (`frontend/lib/hotel-data.ts`) i jest
oznaczone jako `zrodlo_ceny: "strona_www"`.

Pliki, które nadal wiozą **nieaktualne ceny** i muszą zostać przegenerowane
z backendu (poza zakresem tego repo-backendu — nie ruszamy `frontend/`):
`frontend/lib/hotel-data.ts` (`treatmentCopy`: 65 / 70 / 45 / 90 / 30 PLN,
brak wpisu dla masażu klasycznego; czasy też się różnią: borowinowa 20 vs 25 min,
jonoforeza 15 vs 20 min). Po zmianie ceny w seedzie trzeba je odtworzyć
z `/` (sekcja `catalog.uslugi`) albo z `check_spa_availability`.

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
│   └── test_api.py      # 68 testów API
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

- **Stan tylko w pamięci** — rezerwacje i zajętość slotów znikają po restarcie procesu (brak bazy danych).
- **Brak autoryzacji na webhookach** — każdy, kto zna URL tunelu, może wywołać dowolne narzędzie.
- **Ulotny URL trycloudflare** — adres zmienia się przy każdym restarcie tunelu (skrypty aktualizują webhooki, ale nie ma trwałej domeny).
- **Brak rzeczywistego PMS/SMS** — „SMS” to wydruk w konsoli + opcjonalny Telegram; brak integracji z systemem hotelowym.
- **Telefon/handoff tylko symulowany** — bez telefonii (SIP) nie ma prawdziwego przekierowania do człowieka.
- **Dane demo są statyczne** — cennik, godziny i blokada świąteczna to wartości z plików JSON, nie żywy kalendarz.
- **Jeden gabinet na godzinę** — wszystkie zabiegi dzielą jeden kalendarz (patrz „Model zasobu dla slotów”); realne SPA z kilkoma gabinetami wymaga klucza `(gabinet, data)`.
- **Ceny poza backendem są nieaktualne** — `frontend/lib/hotel-data.ts` nadal ma 65/70/45/90/30 PLN; kanoniczne są wartości z `data/spa_schedule.json`.
- **Brak uwierzytelniania i limitów** — nie wystawiaj tego backendu publicznie poza czasem demo.

> **Wskazówka na prezentację:** zostaw terminal z serwerem na bocznym ekranie —
> logi demo (`ANNA_DEMO_LOGS`, domyślnie włączone) pokazują każde wywołanie
> narzędzia przez Annę w czasie rzeczywistym.
