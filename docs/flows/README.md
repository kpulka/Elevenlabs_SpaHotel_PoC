# Booking flows: state diagrams

Status: **derived from the repository, verified offline.** Each transition in these diagrams is exercised by `mock_backend/tests/test_flow_transitions.py` through the real HTTP routes of the mock backend. The live ElevenLabs agent is **not** tested by these files.

| Document | Covers | Sources |
|---|---|---|
| [cancellation.md](cancellation.md) | `cancel_spa_appointment`: fee rule, slot release, unknown-number rejection | `agent/procedures/procedures_7.md` (procedure 1), `mock_backend/services/spa.py` (`anuluj_rezerwacje`, `oblicz_oplate_anulowania`) |
| [reschedule.md](reschedule.md) | `check_spa_availability` → `reschedule_spa_appointment`: new number, slot move, rejections | `agent/procedures/procedures_7.md` (procedure 2), `mock_backend/services/spa.py` (`przenies_rezerwacje`) |

## Conventions

- Diagrams use Mermaid `stateDiagram-v2`. They render on GitHub.
- A "state" is what the **backend** knows about a confirmation number. The agent's conversation state is not modelled.
- Business rejections (`success: false`, HTTP 200) are shown as transitions that change nothing. They are not errors.
- Scope: the mock backend keeps bookings in memory. A restart clears them. Persistence (SQLite) is planned, not implemented.

## Known gaps (as of this commit)

| Gap | Effect |
|---|---|
| The cancel tool takes no guest name (`AnulowanieSPA` has no `guest_name`) | Identity check before cancel depends on the agent following procedure 1; the backend cannot enforce it. |
| Reschedule is free in the backend (`note: Zmiana terminu jest bezpłatna`) | Fee rules for later reschedules are not modelled; the prompt's "first change is free" is not enforced. |
| No idempotency on reschedule | Retrying a reschedule after a timeout can move the booking twice. Book has an idempotency key; reschedule does not. |
