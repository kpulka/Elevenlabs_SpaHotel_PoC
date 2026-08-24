# Phase F5 — Research & weryfikacja API (workflow / procedures)

## Cel
Zweryfikować, co dokładnie robią `workflow` i `procedures` w agents ElevenLabs, na podstawie **oficjalnego OpenAPI** (`openapi.json`), i potwierdzić dostępne endpointy, zanim cokolwiek utworzymy. To faza "zero ryzyka" — tylko czytanie/schematy.

## Zależności
- Agent `Bukowy_Dwor_Anna` (`agent_8401m0n03cggfgebhfh0cj96t7aj`) — Phase 3.
- Zapasowy `_openapi.json` w `.planning/` (jeśli istnieje) lub pobrany na nowo:
  `curl -s https://api.elevenlabs.io/openapi.json -o openapi.json`.

## Krok 1 — Zidentyfikuj schematy
Przeszukaj `components/schemas` OpenAPI:
- `ProcedureType` → enum: `['free_form','deterministic']`.
- `CreateProcedureRequestModel` → `{name (max200), content, trigger, type}`.
- `ProcedureRefResponseModel` → zwraca `procedure_id, version_id, name, type, trigger, referenced_tool_ids, referenced_kb_ids, referenced_procedure_ids, referenced_dynamic_variables`.

## Krok 2 — Potwierdź endpointy procedures
```
POST   /v1/convai/agents/{agent_id}/branches/{branch_id}/procedures          # create
GET    /v1/convai/agents/{agent_id}/branches/{branch_id}/procedures          # list
POST   /v1/convai/agents/{agent_id}/branches/{branch_id}/procedures/compile  # compile (dry-run)
GET    /v1/convai/agents/{agent_id}/branches/{branch_id}/procedures/{procedure_id}          # get
PATCH  /v1/convai/agents/{agent_id}/branches/{branch_id}/procedures/{procedure_id}/draft    # update draft
```

## Krok 3 — Potwierdź workflow node types
Węzły `AgentWorkflowResponseModel`: `start`, `end`, `tool` (wykonaj narzędzia równolegle), `override_agent` (subagent z własnym promptem/KB), `phone_number` (transfer do numeru), `standalone_agent`. Edges: `edges` (mapa id → `WorkflowEdgeModel`). `prevent_subagent_loops` bool.

## Krok 4 — Zanotuj ID
Z `GET /v1/convai/agents/{id}` zapisz: `agent_id`, `branch_id`, `main_branch_id`, `version_id`. Bez nich nie utworzysz procedury.

## Krok 5 — `compile` dry-run (bez podpinania)
Spróbuj `POST .../procedures/compile` z minimalną przykładową procedurą (np. nazwą i krotką treścią). Celem jest potwierdzenie, że struktura/walidacja przechodzi **bez modyfikacji żywego agenta**.

## DoD
- Zanotowana wiedza o `workflow` i `procedures` (schematy + znaczenie).
- Potwierdzone endpointy branches/procedures/compile + workflow node types.
- Zapisan `agent_id`/`branch_id`/`main_branch_id`/`version_id`.
- `compile` dry-run zakończony (green lub udokumentowany błąd).
- Model „Anna" niezmieniony w tej fazie.