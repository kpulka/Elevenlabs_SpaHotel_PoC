# Konfiguracja agenta Anna (config-as-code)

`anna_v3.json` to **eksport opisowy** ustawień agenta ElevenLabs, zapisany w repo, żeby zmiany były wersjonowane w git i dało się je porównać z panelem. Nie jest to plik, który ElevenLabs czyta automatycznie.

## Jak to się łączy z żywym agentem

| Co | Gdzie jest prawda | Jak trafia do ElevenLabs |
|---|---|---|
| Treść promptu | `agent/system_prompt_v3.md` (wklejana do panelu) | ręcznie w panelu / PATCH agenta |
| Baza wiedzy (5 dokumentów) | `agent/knowledge_base_txt/*.txt` | `python scripts/deploy_kb_and_tools.py` (REST) |
| `rag`, `turn_eagerness`, `speed`, `timezone` | `scripts/deploy_kb_and_tools.py` | ten sam skrypt (PATCH) |
| Model LLM, temperatura, TTS, głos, STT | `anna_v3.json` (opis) | panel ElevenLabs |
| Narzędzia (webhooki) | `anna_v3.json` + `mock_backend/tunnel/tool_schemas.py` | `mock_backend/tunnel/sync_agent_tools.py` |
| Procedury | `agent/procedures/procedure_ids.json` | panel / API procedur |
| ID agenta | nie jest w pliku | zmienna `ELEVENLABS_AGENT_ID` |

Źródłem prawdy dla wartości liczbowych jest live agent. Gdy zmienisz coś w panelu, zaktualizuj JSON w tym samym commicie. Nie ma automatycznej synchronizacji w obu kierunkach.

## Zasady

- Brak sekretów: klucze API tylko w env (`ELEVENLABS_API_KEY`), ID agenta w env (`ELEVENLABS_AGENT_ID`).
- Pola z wartością `PLACEHOLDER` (np. `tool_base_url`) trzeba uzupełnić lokalnie; nie commituj adresów tuneli.
- Wartości pochodzą z repo: `docs/architecture.md`, `docs/pl/plan_implementacji_recepcjonisty.md`, `docs/pl/audyt_agenta_2026-08.md` (addendum), `scripts/deploy_kb_and_tools.py`. Jeśli dokument źródłowy się zmieni, zmień JSON.
- Stan live nie był odczytywany przy tworzeniu pliku (brak połączenia w czasie pisania). Przed uznaniem za zgodne porównaj z `get_agent` / panelem.

## Walidacja

```
python -c "import json; json.load(open('agent/config/anna_v3.json', encoding='utf-8')); print('ok')"
```
