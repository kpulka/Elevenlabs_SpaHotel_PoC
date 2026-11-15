# Tunel demo (trycloudflare) — webhooki agenta

`sync_agent_tools.py` to jedyne miejsce, które przepina webhooki agenta ElevenLabs
na aktualny adres tunelu. Narzędzia znajduje **po nazwie** (nie po ID) i obsługuje
**wszystkie 7** narzędzi spa: `check_spa_availability`, `book_spa_appointment`,
`check_room_availability`, `send_sms_summary`, `transfer_to_simulated_handoff`,
`cancel_spa_appointment`, `reschedule_spa_appointment`.

Klucz API bierze z `--api-key`, potem `$ELEVENLABS_API_KEY`, a na końcu z
`frontend/.env.local` (nigdy go nie wypisuje).

```bash
# 1. po każdym restarcie tunelu — nowy URL (robią to podman_start.sh i start_anna.sh)
python mock_backend/tunnel/sync_agent_tools.py --base-url https://xxx.trycloudflare.com

# 2. podejrzenie stanu (tylko odczyt — dobre do debugowania demo)
python mock_backend/tunnel/sync_agent_tools.py --list

# 3. podgląd uzupełnienia brakujących pól schematu (bez zapisu)
python mock_backend/tunnel/sync_agent_tools.py --ensure-schema --dry-run
```

⚠️ URL tunelu jest **efemeryczny** — zmienia się przy każdym starcie cloudflared.
Jeśli webhooki nie zostaną zsynchronizowane, agent dzwoni pod martwy adres i
procedury (rezerwacja, anulowanie, przełożenie, SMS, handoff) milcząco padają.
Synchronizacja musi więc wykonać się **po każdym** uruchomieniu tunelu.

`--ensure-schema` (bez `--dry-run`) dopisuje tylko brakujące **opcjonalne** pola
body: `appointment_datetime` w anulowaniu oraz `language` w SMS i handoffie.
Nigdy nie usuwa ani nie zmienia istniejących pól i jest idempotentny.

## `run_simulations.py` — dowód z żywych symulacji (K2)

Symulacje agenta (rezerwacja niejednoznacznego zabiegu, anulowanie >2 h = 0%, <2 h = 50%, zmiana terminu,
zadatek, wczesny przyjazd/późny wyjazd, dieta, transport, reklamacja, dostępność z datą przeszłą oraz dwa
ataki: prompt injection i anulowanie ze złym nazwiskiem). Scenariusze to dane w `scenarios.py`; każdy ma
`procedure` (nazwa z `agent/procedures/procedure_ids.json`) i `tags`. Transkrypty trafiają do
`evals/transcripts/` (nadpisanie: `ANNA_TRANSCRIPTS_DIR`); są maskowane z danych osobowych gości.
Instrukcja pełna: `evals/README.md`.

```bash
python mock_backend/tunnel/run_simulations.py --check      # kredyty ElevenLabs + /health + gałąź
python mock_backend/tunnel/run_simulations.py --dry-run    # payloady scenariuszy, zero wywołań płatnych
python mock_backend/tunnel/run_simulations.py --only 02,16 # tylko wybrane (ogranicza koszt)
python mock_backend/tunnel/run_simulations.py              # pełny przebieg
```

Skrypt sam seeduje rezerwacje potrzebne scenariuszom i wplata ich numery `SPA-XXXX` w treść (backend liczy
opłatę z `appointment_datetime` vs `now`, więc daty są liczone w momencie uruchomienia). Przed startem
sprawdza też, czy **hosty webhooków siedmiu narzędzi Anny** odpowiadają na `/health` (filtruje po
`TOOL_PATHS`, więc obce narzędzia z workspace'u nie zaśmiecają wyniku) — martwy tunel kończy się
exit 2 zamiast nieudanych symulacji. Exit codes: `0` wszystko przeszło, `1` test nie przeszedł,
`2` konfiguracja/backend, `3` brak kredytów, `4` timeout. Scenariusz <2 h wymaga wolnego slotu
w najbliższych 2 h — uruchom między 08:00 a 16:00 albo dodaj `--skip-scenario3`.

ID agenta: `--agent-id`, a domyślnie `$ELEVENLABS_AGENT_ID` (brak = błąd, kod wyjścia 2; w `--dry-run` nie jest potrzebny).

Sekwencję wywołań narzędzi i zakazane frazy sprawdza `sequence_check.py` (także offline, w testach).
