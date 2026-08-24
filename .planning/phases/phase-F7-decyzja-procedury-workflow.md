# Phase F7 — Decyzja projektowa: co podpiąć (procedury vs workflow)

## Cel
Na podstawie badań (F5) i utworzonych procedur (F6) podejmij świadomą decyzję, **co podłączyć do żywego agenta** i w jakiej kolejności, z zachowaniem bezpieczeństwa (zero regresji wobec działającego „Anny").

## Zależności
- F5 (znaczenie obu pól) + F6 (4 utworzone procedury).

## Krok 1 — Opcje
| Wariant | Opis | Kiedy ma sens |
|---|---|---|
| **A. Tylko procedures** | Podpiąć nazwane procedury do agenta/knowledge + referencje do tooli. Prompt może zostać przycięty. | Najmniejsza ingerencja; flow jawne i testowalne. |
| **B. Procedures + prosty workflow** | Do tego zbudować minimalny graf (np. eskalacja → node `phone_number`/`end`). | Gdy chcemy rozgałęzienie/podskrypt bez pełnej przebudowy. |
| **C. Pełny workflow** | Graf orchestratora z subagentami (`override_agent`), tools nodes, routowanie warunkowe. | Faza docelowa/na produkcję; duża zmiana — nie dla PoC. |

## Krok 2 — Kryteria
- **Ryzyko regresji:** każda opcja, która zmienia prompt/schemat agenta, wymaga backupu i rollback.
- **Testowalność:** procedures łatwe do weryfikacji przez `simulate_conversation`.
- **MVP:** najmniejsza zmiana, która przynosi wartość (jawne flow, mniej promptu, lepsze testowanie).
- **ElevenLabs-specific:** procedures to reużywalne "skill'e"; pełny workflow to duży, wizualny orchestrator.

## Krok 3 — Zalecenie (do potwierdzenia z userem)
- Start: **opcja A (procedures)** — najbezpieczniejsza, testowalna, realny benefit (flow jawne).
- `decyzja_o_transferze` można uczynić `deterministic` (sztywna reguła) — naturalnie nadaje się do workflow.
- Pełny workflow (C) — **odroczony** na fazę produkcyjną; NIE dotykać teraz na żywym agencie bez wyczerpania A.

## Krok 4 — Określ, jak podpiąć procedures do agenta
- Sprawdzić w OpenAPI, czy agent `conversation_config` posiada pole referencji do procedur (np. `procedures` id / w workflow node), oraz czy potrzebny jest `POST .../compile` zanim staną się aktywne.
- Zanotować konkretny payload/iście zmian.

## DoD
- Wybrano wariant (A/B/C) z uzasadnieniem.
- Odnotowano czego NIE ruszamy (np. pełny workflow) i dlaczego.
- Zidentyfikowany mechanizm podpięcia procedures do agenta (endpoint/pole).