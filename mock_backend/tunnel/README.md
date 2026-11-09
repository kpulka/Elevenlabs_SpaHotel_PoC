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
