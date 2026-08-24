# Phase F8 — Implementacja wybranego wariantu (na żywo, iteracyjnie i przywracalnie)

## Cel
Podłączyć wybrane procedury (F7) do żywego agenta `Bukowy_Dwor_Anna` przez API — iteracyjnie, z backupem i możliwością rollbacku. Jeśli wybrano workflow: zbudować minimalny graf i zwalidować.

## Zależności
- F7 (wybrany wariant + mechanizm podpięcia).
- `agent_id`, `branch_id`, `main_branch_id`, `version_id` (F5).
- Backup aktualnej konfiguracji agenta (prompt + tool_ids) zapisany w tej fazie przed zmianą.

## Krok 1 — Backup / rollback (BEZPIECZEŃSTWO)
- Pobierz `GET /v1/convai/agents/{id}` → zapisz pełny JSON do `.planning/_agent_backup_pre_procedures.json`.
- Zanotuj aktualny `prompt` i `tool_ids` oraz `workflow` (szkielet start_node).

## Krok 2 — Podpięcie procedures
- W zależności od mechanizmu (F7):
  - jeśli agent ma pole referencji do procedur — ustaw je;
  - jeśli procedures podpinają się przez workflow/toole — skonfiguruj.
- Uruchom `POST .../compile` (jeśli wymagane) by aktywować.
- Zachowaj minimalność: NIE ruszaj głosu, parametrów akustycznych, KB, tool_IDS poza koniecznymi.

## Krok 3 — (Opcjonalnie) minimalny workflow
- Jeśli wybrano wariant B: zbuduj graf np. `start → (tool decyzja_o_transferze) → end` albo `start → tool node → phone_number`.
- NODES: `start`, `tool`, `end`; EDGES: porządek ewaluacji (`edge_order`).
- Waliduj przez `POST .../compile` przed zapisem na żywo.

## Krok 4 — Weryfikacja na żywo
- `GET /v1/convai/agents/{id}` → potwierdź, że procedury/workflow są widoczne; prompt/tool_ids zgodne z oczekiwaniem.
- `GET .../procedures` (lub workflow) → lista zwiera procedury.
- Zapisz `version_id` po zmianie.

## DoD
- Agent zawiera utworzone procedury (lub działający minimalny workflow).
- `get_agent`/`list_procedures` potwierdza zmianę.
- Backup istnieje → możliwy pełny rollback do stanu sprzed.
- Brak regresji w głosie, parametrach, KB.