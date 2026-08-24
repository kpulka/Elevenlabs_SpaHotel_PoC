# Phase 6 — Tunel + tool calling + parametry panelowe

## Cel
Wystawić mock backend publicznie i podpiąć narzędzia do agenta (webhooki + transfer), oraz ustawić parametry niedostępne w MCP.

## Zależności
Phase 5 (backend działa) + Phase 3 (`agent_id`).

## Krok 1 — Tunel
```bash
ngrok http 8000
# lub:
cloudflared tunnel --url http://localhost:8000
```
Zanotuj publiczny URL (np. `https://abcd1234.ngrok.io`) → **BASE_URL**.

## Krok 2 — Tool calling (panel ElevenLabs → Agent → Tools)

MCP `create_agent` nie obsługuje tool calling; zrób to w panelu. Zarejestruj 4 webhook tools (JSON Schema poniżej, Webhook URL = `BASE_URL + endpoint`) + natywne `transfer_to_number`.

### Narzędzie 1: `check_spa_availability` → `BASE_URL/check_spa_availability`
```json
{
  "name": "check_spa_availability",
  "description": "Sprawdza wolne godziny dla wybranego zabiegu SPA w danym dniu.",
  "parameters": {
    "type": "object",
    "properties": {
      "service_name": { "type": "string", "description": "Nazwa zabiegu (np. masaż klasyczny, kąpiel borowinowa)." },
      "date": { "type": "string", "description": "Data YYYY-MM-DD." }
    },
    "required": ["service_name", "date"]
  }
}
```

### Narzędzie 2: `book_spa_appointment` → `BASE_URL/book_spa_appointment`
```json
{
  "name": "book_spa_appointment",
  "description": "Rezerwuje zabieg SPA dla gościa na konkretny termin.",
  "parameters": {
    "type": "object",
    "properties": {
      "service_name": { "type": "string" },
      "date": { "type": "string", "description": "YYYY-MM-DD" },
      "time": { "type": "string", "description": "HH:MM" },
      "guest_name": { "type": "string", "description": "Imię i nazwisko gościa." }
    },
    "required": ["service_name", "date", "time", "guest_name"]
  }
}
```

### Narzędzie 3: `check_room_availability` → `BASE_URL/check_room_availability`
```json
{
  "name": "check_room_availability",
  "description": "Sprawdza dostępność i cenę pokoju w wybranym terminie.",
  "parameters": {
    "type": "object",
    "properties": {
      "room_type": { "type": "string", "enum": ["jednoosobowy", "dwuosobowy", "apartament"] },
      "check_in": { "type": "string", "description": "YYYY-MM-DD" },
      "check_out": { "type": "string", "description": "YYYY-MM-DD" }
    },
    "required": ["room_type", "check_in", "check_out"]
  }
}
```

### Narzędzie 4: `send_sms_summary` → `BASE_URL/send_sms_summary`
```json
{
  "name": "send_sms_summary",
  "description": "Wysyła podsumowanie rezerwacji na telefon gościa.",
  "parameters": {
    "type": "object",
    "properties": {
      "phone_number": { "type": "string", "description": "Numer telefonu np. +48123456789." },
      "summary_text": { "type": "string", "description": "Treść podsumowania rezerwacji." },
      "confirmation_id": { "type": "string", "description": "ID potwierdzenia (opcjonalne)." }
    },
    "required": ["phone_number", "summary_text"]
  }
}
```

### Narzędzie 5 (natywne): `transfer_to_number`
- W panelu dodaj systemowy tool `transfer_to_number` (human handoff) → numer recepcji/dyżurki.

## Krok 3 — Parametry panelowe (niedostępne w MCP)
- `turn_eagerness` → `Patient` (Conversation → Turn-taking).
- `speed` → `0.85` (sekcja głosu).
- Słownik wymowy PLS → wklej z `docs/plan_implementacji_recepcjonisty.md` §2.3 (Bukowy Dwór, Krynica-Zdrój, borowinowe).
- (opcjonalnie) tryby `usage_mode` KB: cennik+procedury → `prompt`, reszta → `auto`.

## DoD
- [ ] Tunel daje publiczny `BASE_URL`.
- [ ] 4 webhook tools + `transfer_to_number` zarejestrowane w agencie.
- [ ] Webhook URL osiągalny (curl na `BASE_URL/check_spa_availability` przez tunel).
- [ ] `turn_eagerness: Patient`, `speed: 0.85`, PLS ustawione.

## Wynik przekazany do Phase 7
Agent z kompletnym tool callingiem + działającym tunelem.