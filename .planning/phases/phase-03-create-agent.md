# Phase 3 — `create_agent` „Anna"

## Cel
Stworzyć agenta głosowego „Anna" w ElevenLabs przez MCP, z poprawnym głosem, system promptem i parametrami senior-UX.

## Zależności
Phase 2 (realne `model_id` / `llm` / `voice_id`).

## Przygotowanie danych

### System prompt
Pełny tekst z `docs/anna_system_prompt_v3.md` — zawartość wewnątrz bloku kodu (między pierwszą linią ``` a domykającą ```, ok. linie 10–115). Wklej CAŁY tekst jako `system_prompt` (razem z sekcjami persona, strict grounding, protokoły rezerwacji, scenariusze specjalne).

### First message
```
Dzień dobry, tu Anna z recepcji Uzdrowiska Bukowy Dwór w Krynicy-Zdroju. W czym mogę Panu lub Pani dzisiaj pomóc?
```

## Wywołanie

```
tool_call: mcp__elevenlabs__create_agent, args:
{
  "name": "Bukowy_Dwor_Anna",
  "language": "pl",
  "first_message": "Dzień dobry, tu Anna z recepcji Uzdrowiska Bukowy Dwór w Krynicy-Zdroju. W czym mogę Panu lub Pani dzisiaj pomóc?",
  "system_prompt": "<CAŁY TEKST Z docs/anna_system_prompt_v3.md>",
  "voice_id": "cgSgspJ2msm6clMCkdW9",
  "llm": "<z Phase 2, domyślnie gemini-2.0-flash-001>",
  "temperature": 0.1,
  "model_id": "<z Phase 2, np. eleven_v3_conversational>",
  "stability": 0.8,
  "similarity_boost": 0.75,
  "turn_timeout": 3,
  "asr_quality": "high"
}
```

## Uwagi
- `turn_timeout` w MCP to liczba całkowita (sekundy) → `3`.
- `model_id` domyślny w MCP to `eleven_turbo_v2` — użyj wartości z Phase 2, o ile dostępna. Jeśli `eleven_v3_conversational` niedostępne, wybierz najbliższy v3 i zapisz.
- Zapisz zwrócony `agent_id` (wymagany w Phase 4 i Phase 6).

## DoD
- [ ] `agent_id` zwrócone i zapisane.
- [ ] `get_agent(agent_id)` potwierdza: nazwa, `language=pl`, voice_id i params.
- [ ] `first_message` i `system_prompt` zapisane poprawnie (brak obcięcia).

## Wynik przekazany do Phase 4
`agent_id` (string) + potwierdzenie konfiguracji.