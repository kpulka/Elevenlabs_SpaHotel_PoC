# Mock Backend — Wirtualny Recepcjonista AI 🏨
## Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Mock backendu dla projektu PoC integracji Agenta ElevenLabs z systemem PMS (Property Management System).
Serwuje 4 endpointy POST jako webhooki dla agenta **Anna** — Wirtualnej Recepcjonistki AI.

---

## 💡 Start (rekomendowany — skrypt `tunnel/start_anna.sh`)
Backend + tunel + aktualizacja webhooków jednym poleceniem (odporne na restart — nowy URL tunelu automatycznie podpinany do agenta):
```bash
cd mock_backend/tunnel && ./start_anna.sh   # domyślny port 8011
# opcjonalnie: ./start_anna.sh 8012
```
Skrypt: uruchamia backend na wolnym porcie → cloudflared tunnel → łapie URL → aktualizuje 5 narzędzi agenta ElevenLabs → zapisuje stan do `tunnel/state.json`.

> ⚠️ **Port 8000 może być zajęty przez proces systemowy (svchost).** Dlatego domyślny port to 8011. Nie walcz z systemem — użyj wolnego portu.

> **Ulotny URL:** trycloudflare zmienia adres przy każdym restarcie (bez certyfikatu/domeny nie ma trwałego URL). Skrypt rozwiązuje to przez automatyczną aktualizację. Dla pełnej trwałości rozważ named tunnel (własna domena Cloudflare).

## 📦 Instalacja

```bash
# Przejdź do katalogu projektu
cd mock_backend

# Zainstaluj zależności
pip install -r requirements.txt
```

---

## 🚀 Uruchomienie

```bash
uvicorn main:app --reload --port 8000
```

Po uruchomieniu:
- **Serwer**: http://localhost:8000
- **Dokumentacja API (Swagger UI)**: http://localhost:8000/docs
- **Dokumentacja API (ReDoc)**: http://localhost:8000/redoc

---

## 📡 Endpointy API

ElevenLabs Agent powinien mieć skonfigurowany **Webhook URL** jako:
```
http://localhost:8000/{nazwa_endpointu}
```

### 1. `POST /check_spa_availability`
Sprawdza dostępność zabiegu SPA w danym dniu.

```bash
curl -X POST http://localhost:8000/check_spa_availability \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "masaż klasyczny",
    "date": "2026-08-25"
  }'
```

**Przykładowa odpowiedź (dostępny):**
```json
{
  "available": true,
  "slots": ["10:00", "11:00", "14:00", "14:30", "15:00", "16:00"],
  "service_name": "masaż klasyczny",
  "date": "2026-08-25"
}
```

---

### 2. `POST /book_spa_appointment`
Rezerwuje zabieg SPA dla gościa.

```bash
curl -X POST http://localhost:8000/book_spa_appointment \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "kąpiel borowinowa",
    "date": "2026-08-25",
    "time": "14:00",
    "guest_name": "Jan Kowalski"
  }'
```

**Przykładowa odpowiedź:**
```json
{
  "success": true,
  "confirmation_id": "SPA-4821",
  "service_name": "kąpiel borowinowa",
  "date": "2026-08-25",
  "time": "14:00",
  "guest_name": "Jan Kowalski",
  "message": "Rezerwacja potwierdzona."
}
```

---

### 3. `POST /check_room_availability`
Sprawdza dostępność pokoju i oblicza cenę pobytu.

```bash
curl -X POST http://localhost:8000/check_room_availability \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "dwuosobowy",
    "check_in": "2026-08-25",
    "check_out": "2026-08-28"
  }'
```

**Przykładowa odpowiedź (dostępny):**
```json
{
  "available": true,
  "room_type": "dwuosobowy",
  "price_per_night": 500,
  "check_in": "2026-08-25",
  "check_out": "2026-08-28",
  "total_nights": 3,
  "total_price": 1500,
  "message": "Pokój dostępny. Cena: 1500 PLN za 3 noc(y)."
}
```

> **Uwaga:** Weekend 30-31 sierpnia 2026 jest zablokowany (szczyt sezonu). Zapytanie o ten termin zwróci `"available": false`.

```bash
# Przykład — termin zajęty:
curl -X POST http://localhost:8000/check_room_availability \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "apartament",
    "check_in": "2026-08-30",
    "check_out": "2026-09-01"
  }'
```

---

### 4. `POST /send_sms_summary`
Wysyła podsumowanie rezerwacji na telefon gościa (demo: konsola + opcjonalnie Telegram).

```bash
curl -X POST http://localhost:8000/send_sms_summary \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+48123456789",
    "summary_text": "Bukowy Dwór: Rezerwacja kąpieli borowinowej potwierdzona na 25.08.2026 o godz. 14:00. Nr ref.: SPA-4821. Do zobaczenia!",
    "confirmation_id": "SPA-4821"
  }'
```

**Przykładowa odpowiedź:**
```json
{
  "success": true,
  "message": "Wiadomość wysłana.",
  "delivered_to": "+48123456789"
}
```

---

## 📲 Konfiguracja Telegram (opcjonalne)

Aby podczas demonstracji wiadomość pojawiała się **na żywo** na ekranie/rzutniku,
skonfiguruj bota Telegram ustawiając zmienne środowiskowe przed uruchomieniem serwera:

```bash
# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN = "1234567890:AABBCCDDEEFFaabbccddeeff1234567890ab"
$env:TELEGRAM_CHAT_ID   = "-1001234567890"
uvicorn main:app --reload --port 8000

# Linux / macOS
export TELEGRAM_BOT_TOKEN="1234567890:AABBCCDDEEFFaabbccddeeff1234567890ab"
export TELEGRAM_CHAT_ID="-1001234567890"
uvicorn main:app --reload --port 8000
```

### Jak uzyskać dane Telegram:
1. Utwórz bota przez [@BotFather](https://t.me/BotFather) → skopiuj token (`TELEGRAM_BOT_TOKEN`)
2. Dodaj bota do kanału/grupy jako Administrator
3. Wyślij wiadomość testową, następnie odwiedź:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   i skopiuj `chat.id` (`TELEGRAM_CHAT_ID`)

Jeśli zmienne nie są ustawione — wiadomość zostanie wydrukowana tylko do konsoli serwera (też działa świetnie na demo!).

---

## 🗂️ Struktura Projektu

```
mock_backend/
├── main.py              # Główna aplikacja FastAPI
├── requirements.txt     # Zależności Python
├── README.md            # Ta dokumentacja
└── data/
    ├── spa_schedule.json # Szkielet danych SPA (harmonogram generowany dynamicznie)
    └── rooms.json        # Dane pokoi i cennik
```

---

## 💡 Cennik (dane mock)

| Typ pokoju     | Cena / noc |
|----------------|------------|
| Jednoosobowy   | 350 PLN    |
| Dwuosobowy     | 500 PLN    |
| Apartament     | 750 PLN    |

## 🧖 Zabiegi SPA (dane mock)

| Zabieg                               | Dostępne godziny                          |
|--------------------------------------|------------------------------------------|
| kąpiel siarczkowa Ukojenie Stawów    | 10:00, 11:00, 14:00, 14:30, 15:00, 16:00 |
| masaż leczniczy pleców               | 10:00, 11:00, 14:00, 14:30, 15:00, 16:00 |
| kąpiel borowinowa                    | 10:00, 11:00, 14:00, 14:30, 15:00, 16:00 |
| jonoforeza                           | 10:00, 11:00, 14:00, 14:30, 15:00, 16:00 |
| masaż klasyczny                      | 10:00, 11:00, 14:00, 14:30, 15:00, 16:00 |

Harmonogram generowany dynamicznie dla **najbliższych 14 dni** od daty uruchomienia serwera.

---

## 🔗 Konfiguracja ElevenLabs Agent

W panelu ElevenLabs, przy konfiguracji narzędzi Webhook, ustaw:

| Narzędzie               | Webhook URL                                       | Metoda |
|-------------------------|---------------------------------------------------|--------|
| check_spa_availability  | `http://localhost:8000/check_spa_availability`    | POST   |
| book_spa_appointment    | `http://localhost:8000/book_spa_appointment`      | POST   |
| check_room_availability | `http://localhost:8000/check_room_availability`   | POST   |
| send_sms_summary        | `http://localhost:8000/send_sms_summary`          | POST   |
| transfer_to_simulated_handoff | `http://localhost:8000/transfer_to_simulated_handoff` | POST   |

> **Handoff (PoC):** agent zamiast realnego `transfer_to_number` (wymaga telefonii/SIP) wywołuje webhook `transfer_to_simulated_handoff` — backend loguje zdarzenie do konsoli i (jeśli skonfigurowany) wysyła alert na Telegram. Opis i schemat — sekcja „Handoff PoC" w `main.py`.

> **Wskazówka dla prezentacji:** Przy demo na żywo zostaw terminal z uruchomionym serwerem widoczny na bocznym ekranie — logi konsoli pokazują każde wywołanie narzędzia przez agenta Annę w czasie rzeczywistym! 🎤
