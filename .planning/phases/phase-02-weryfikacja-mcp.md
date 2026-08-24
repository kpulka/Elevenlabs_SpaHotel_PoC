# Phase 2 — Weryfikacja środowiska MCP

## Cel
Potwierdzić realne wartości (model TTS, LLM, głos, plan), zanim stworzymy agenta. Wykluczyć rozbieżności między planem a rzeczywistością.

## Zależności
Brak (można równolegle z Phase 1).

## Kroki — wywołania MCP (Hermes `tool_call`)

1. **Głos** — potwierdź dostępność:
```
tool_call: mcp__elevenlabs__get_voice, args: {"voice_id": "cgSgspJ2msm6clMCkdW9"}
```
Oczekiwany: głos „Jessica - Playful, Bright, Warm" (premade).

2. **Modele TTS** — spisz dostępne `model_id`:
```
tool_call: mcp__elevenlabs__list_models
```
Szukaj `eleven_v3_conversational` (lub `eleven_turbo_v2.x` / `eleven_flash_v2_5`). Zanotuj dokładny identyfikator do użycia w Phase 3.

3. **Plan / subskrypcja** — czy conversational agent jest dostępny:
```
tool_call: mcp__elevenlabs__check_subscription
```
Zanotuj `tier` (free/creator/...), `voice_limit`, limity minut/znaków.

4. **Istniejące głosy (opcjonalnie)** — jeśli chcesz porównać:
```
tool_call: mcp__elevenlabs__search_voices, args: {"search": ""}
```

## Rekord decyzji (uzupełnij i zapisz tu)
| Parametr | Wartość z planu | Wartość realna | Decyzja |
|---|---|---|---|
| voice_id | `cgSgspJ2msm6clMCkdW9` | | |
| model_id (TTS) | `eleven_v3_conversational` | | |
| llm | `gemini-2.0-flash-001` (domyślny MCP) | | |
| plan/tier | (nieznane) | | |
| language | `pl` | | |

## DoD
- [ ] Głos `cgSgspJ2msm6clMCkdW9` potwierdzony.
- [ ] Realne `model_id` TTS zapisane (nadpisz jeśli różne od `eleven_v3_conversational`).
- [ ] Realne `llm` zapisane.
- [ ] Znany `tier` (czy agent da się utworzyć).
- [ ] Tabela decyzji uzupełniona i zapisana w tym pliku.

## Wynik przekazany do Phase 3
Uzupełniona tabela decyzji (konkretne stringi `model_id` / `llm` / `voice_id`).