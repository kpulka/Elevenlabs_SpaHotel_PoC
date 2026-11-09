> **Status:** aktualny (2026-11) — źródło prawdy dla audytu konfiguracji live (guardrails, flow, zalecenia).

# Audyt Agenta „Anna" — Guardrails, Flow i Usprawnienia (2026-08)

**Agent:** Bukowy_Dwor_Anna — `agent_8401m0n03cggfgebhfh0cj96t7aj` (Creator $22/mies.)
**Źródło danych:** realna konfiguracja z live API (`GET /v1/convai/agents/{id}`) + dokumentacja w `docs/`.

---

## 1. CO JEST DOBRZE (stan faktyczny ✓)

- **Strict grounding** — twarde reguły w prompcie (nigdy nie wymyślaj cen/terminów/wyników medycznych) + `temperature 0.1`. Mocne guardrails anty-halucynacyjne.
- **KB poprawna** — 5 plików, `usage_mode` dobrze dobrane: 03_pokoje i 05_procedury = `prompt` (pełny kontekst), reszta = `auto` (RAG). Zgodnie z dokumentem.
- **Parame**: turn_timeout 3.0, turn_eagerness `patient`, stab 0.8, speed 0.85, sim 0.75, TTS `eleven_v3_conversational`, głos Jessica (`cgSgspJ2msm6clMCkdW9`). Wszystko ustawione zgodnie ze specją.
- **LLM:** `gemini-2.0-flash-001` (dobry wybór na koszty/PL), STT `scribe_realtime`.
- **4 webhooki** live na tunelu trycloudflare (sprawdzone — HTTP 200): check_spa_availability, book_spa_appointment, check_room_availability, send_sms_summary. Schematy POST poprawne.
- **Signed URL** w frontendzie (`/api/anna/signed-url`) — klucz nie wycieka do przeglądarki. Good practice.
- **Widget** ostylowany (navy/gold/cream), pełny variant, feedback rating. Wygląd pod brand.

## 2. ZNALEZIONE PROBLEMY WI

| # | Problem | Waga | Opis |
|---|---------|------|------|
| 1 | **Brak `transfer_to_number` (handoff)** | 🔴 Krytyczny | Prompt każe agentowi „wywołaj transfer_to_human" (8×: pkt 2, 4, 6; inne sekcje „KIEDY PRZEKAZAĆ"). **Ale taki system tool NIE istnieje** — żywa konfiguracja ma włączony tylko `end_call`. Agent nie ma żadnej fizycznej ścieżki przekazania do człowieka. Ścieżka demo C (eskalacja) nie może się realnie wykonać — agent „symuluje" przekazanie. |
| 2 | **Nazwa narzędzia** | 🟠 Wysoki | Dokument kazał `transfer_to_human`, a natywny ElevenLabs tool to `transfer_to_number`. Po aktywacji trzeba zsynchronizować nazwę w prompcie. |
| 3 | **max_duration 300s** | 🟡 Średni | 5 minut na rozmowę — OK na demo, krótko na real. Dla seniorów często za mało (powolne tempa). Podbić do 600-900s. |
| 4 | **brak `skip_turn` / warunek milczenia** | 🟡 Niski/średni | Cele mowy do ustalenia; przy seniorach OK, by „nie słychać nie jest", ale turn_eagerness patient już pilu. |
| 5 | **Tunel trycloudflare ulotny** | 🔴 Operacyjny | Webhook URL = nazwa domeny z ulotnym tunelu trycloudflare. Po restarcie tunelu adresy się zmieniają → wszystkie 4 webhooki padają. Potrzebny stały URL (ngrok stały / cloudflare tunnel stały .trycloudflare nie). Dla demo może być OK ale to pięta achillesowa. |

## 3. GUARDRAILS — OCENA

Warstwa promptowa (grounding + temperatura + retry-po-errorze + rozróżnianie „brak terminu" vs „błąd") jest dobra i wystarczająca dla PoC. Brakuje za to **warstwy wykonawczej handoffu** — prompt obiecuje agentowi eskalację, której nie ma. To luka w bezpieczeństwie: agent w sytuacji medycznej/awaryjnej nie ma realnego wyjścia „do człowieka", może się zapętlić lub udawać.

Dodatkowo brakuje (jeśli wymagane):
- **Conversation History Redaction / ZRM** — tylko na planie Enterprise; na Creator niem.
- **Monitoring** — wyłączony (`monitoring_enabled: false`). Wartościo włączyć dla statystyk.

## 3. PROPOZYCJE USPRA

1. **Aktywuj `transfer_to_number`** (built-in system tool) przez panel/API, podając numer recepcji. W prompcie zamień `transfer_to_human` → `transfer_to_number` (przygotowany plik `docs/archive/anna_system_prompt_v2.md` — 1:1, tylko zamiana nazwy).
2. **Podbij `max_duration_seconds`** 300 → 900 (15 min) dla spokojnych rozmów.
3. **Rozważ stały tunel** dla webhooków (cloudflared stały domeny / public DOMEN), żeby 4 narady nie padały po restarcie.
4. Opcjonalnie: włącz monitoring konwersacji, gdy będzie plan z tego wsparciem.
5. Prompt nie musi być rozbudowany if skracanie promontu nie jest pilne.

## 4. NIEZALECANE ZMIANY (świadomi)
- Nie zmieniać `usage_mode` KB — obecne dobrane na 5/5 pliki, zgodnie z planem.
- Nie podnosić temperatury — for senior grounding najważniejsza.

## 4. NEXT STEPS (decyzja użytkownika)
- [ ] Potwierdzić numer recepcji do `transfer_to_number`.
- [ ] Zastosować (ja mogę wykonać przez REST, bo MCP nie obsługuje built-in tools):
  - aktywać `transfer_to_number`,
  - wgrać prompura v2,
  - podbić max_duration.
- [ ] (opcjonalnie) zainicjować stały tunel na webhook.

---

## 5. AKTUALIZACJA (2026-08, wdrożono uproszczony handoff PoC)

Agent działa tylko jako **widget webowy** (`phone_numbers: []`), więc realny `transfer_to_number` (SIP/telefonia) w ogóle nie ma zastosowania na PoC. Zamiast tego:

- **Dodano endpoint** `POST /transfer_to_simulated_handoff` w `mock_backend/main.py` — loguje zdarzenie do konsoli + opcjonalny alert na Telegram (przez istniejącą integrację `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`). Przetestowany — zwraca `success:true`, `simulated:true`.
- **Prompt v3** (`docs/anna_system_prompt_v3.md`) — zamiast `transfer_to_human`/`transfer_to_number` agent wywołuje webhook `transfer_to_simulated_handoff` (schemat JSON w nagłówku pliku).
- **README mock_backend** zaktualizowany tabelą narzędzia.

> **Aby zadziałało w panelu:** zarejestruj w ElevenLabs narzędzie webhook `transfer_to_simulated_handoff` → URL = tunel + `/transfer_to_simulated_handoff`, i wgraj prompt v3. Opcjonalnie: ustaw zmienne Telegram dla alertu „na drugim ekranie".

---

## 6. WORKFLOW i PROCEDURES (Epik F, 2026-08)

### Co to jest
- **`procedures`** = nazwane, modułowe "skill'e" postępowania (osobno od promptu), które agent może uruchomić. Typy: `free_form` (naturalny język) | `deterministic` (sztywny flow). Referencjują narzędzia/KB/inne procedury.
- **`workflow`** = graf orchestratora (nodes/edges) jeśli chcesz rozgałęzionego agenta/sub-agentów. Węzły: start/end/tool/override_agent/phone_number/standalone_agent.

### Co zrobiono (a następnie oczyszczono)
Utworzono **4 procedury** u agenta (per-branch, NIE podpięte na żywo) do badań:
| Nazwa | type |
|---|---|
| przeprowadz_rezerwacje_zabiegu_spa | free_form |
| przeprowadz_zapytanie_o_pokoj | free_form |
| sprawdz_przeciwwskazania_zdrowotne | free_form |
| decyzja_o_transferze | deterministic |

> **AKTUALIZACJA (cleanup):** po ocenie badań procedury zostały **usunięte** (DELETE, `list_procedures` = `[]`). Nie są aktywne w agencie — były jedynie testowymi draftami do weryfikacji API. Stan agenta: `procedures: {}` (jak na start).

### Wynik badań podpięcia (F8 — odroczone)
Funkcja procedures jest w **stanie early/beta**:
- Tworzenie działa (POST create → draft, `has_draft=true`).
- **Podpięcie do agenta wymaga `version_id`** (PATCH `agent.procedures` = mapa `{id:{procedure_id,version_id}}`), ale procedury mają `version_id=None`, a **brak endpointu "publish/commit"** w OpenAPI → nie ma legalnego sposobu na wersjonowanie.
- `compile` na procedurach → 400 "Invalid JSON content" (błąd na `deterministic`).
- **Wniosek:** funkcja procedures w agents jest w **stanie early/beta** — tworzenie działa, ale podpięcie do agenta wymaga niemozliwego `version_id`. **Podpięcie ODROCZONE do dojrzałości funkcji.** Agent pozostał bezpieczny i niezmieniony (PATCH nie przeszedł — nic nie zmieniono); procedury testowe następnie usunięte.

### Rekomendacja na przyszłość
- Gdy ElevenLabs doda "publish version" / procedures dojrzałe — wtedy warto ponownie zbadać i (jeśli możliwe) podpiąć modularne procedury (dają jasny, testowalny flow rezerwacji SPA, pokoju, anty-medyczny, decyzji o transferze). Treści są zachowane w historii tego audytu.
- Nie używać `override_agent`/`phone_number` w workflow (brak telefonii dla tego PoC).
- Dokument odniesienia (decyzja + badania): usunięto po cleanup, wnioski w sekcji 6 niniejszego audytu.