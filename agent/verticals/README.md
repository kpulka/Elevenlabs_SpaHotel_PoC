# Verticals: onboarding a second client from the template

Status: **one fictional vertical (`dental_clinic`, "Klinika Uśmiech") built as an exercise.** It is not deployed and has not been run against a live ElevenLabs agent. What is checked offline: the client file is valid, the renderer works, the hand-written prompt only names configured tools and departments, and the scenario file has the required shape (`mock_backend/tests/test_render_vertical.py`).

The base playbook is [`../_template/README.md`](../_template/README.md). This folder shows the same steps applied to a second business.

## What is here

| Path | Purpose |
|---|---|
| `render_vertical.py` | Stdlib-only. Validates `client.json` and renders a prompt skeleton and a scenario skeleton. |
| `dental_clinic/client.json` | Structured input: services, tools, handoff departments, never-automate list, emergency rule, KB documents, privacy notes. |
| `dental_clinic/system_prompt.md` | Hand-written Polish prompt in the structure of `agent/system_prompt_v3.md`. |
| `dental_clinic/tool_schema.example.json` | Tool contract in PoC naming style (`check_…`, `book_…`, `transfer_to_simulated_handoff`). |
| `dental_clinic/scenarios.json` | 15 scenarios in the `scenarios.example.json` format, including emergency, injection, third-party data, health data and recording questions. |
| `dental_clinic/kb_outline.md` | Five KB documents, `usage_mode` per document, open items before go-live. |
| `../../docs/discovery/` | Filled discovery brief for this client and the implementation plan derived from it. |

## Onboarding checklist (target: under one working day)

| Step | Time | Output | Check |
|---|---|---|---|
| 1. Discovery answers (10 questions, see `docs/discovery/`) | 60–90 min | brief | every question answered or marked open |
| 2. Write `client.json` from the brief | 30 min | `client.json` | `python agent/verticals/render_vertical.py <client.json>` exits 0 |
| 3. Render skeletons | 1 min | `prompt_skeleton.md`, `scenarios_skeleton.json` | `python agent/verticals/render_vertical.py <client.json> --out build/<client>` |
| 4. Write the prompt from the skeleton | 1–2 h | `system_prompt.md` | prompt names only tools from `client.json` (see the test below) |
| 5. Write the tool contract | 30 min | `tool_schema.example.json` | tool names equal `client.json` tools |
| 6. Fill scenarios from the skeleton (min. 10; emergency, injection, third-party, health data) | 1–2 h | `scenarios.json` | every `expect.tool` is a configured tool |
| 7. Run the offline checks | 1 min | green test run | see commands below |
| 8. Owner review of prompt, KB and never-automate list | async | sign-off in the repo | never-automate items each have a fallback |

Running the scenario set against a live agent is a separate step that costs ElevenLabs credits. It is not part of this folder.

## Rules the validator enforces

- **No prices in `client.json`.** The agent quotes prices only from a tool response or a KB document. A `price_pln` field in a service fails validation.
- **One handoff tool**, named in `handoff.tool`, with `kind: "handoff"`.
- **Every never-automate item has a fallback** that is a handoff department or the emergency number.
- **snake_case, unique tool names.** Renaming a tool means changing it in `client.json`, the prompt and the tool schema together.
- **KB ids** look like `NN_name` and carry `usage_mode` `auto` or `prompt`.

## Rules the offline tests enforce for the dental vertical

- The prompt names only configured tools and departments (`test_hand_written_prompt_*`).
- The prompt puts `112` before the handoff in the emergency section.
- The tool schema and `client.json` list the same tool names.
- Every scenario's `expect.tool` is a configured tool; the set contains an emergency case, an injection case, a third-party data case, a health-data case and a recording question.

## Commands

```bash
# validate and render to stdout
python agent/verticals/render_vertical.py agent/verticals/dental_clinic/client.json

# render to a build folder (do not commit build output)
python agent/verticals/render_vertical.py agent/verticals/dental_clinic/client.json --out build/dental

# offline tests (from mock_backend/)
python -m pytest -q tests/test_render_vertical.py
```

## Known limits

- The scenario `seed` is `null` for every dental scenario. The tunnel runner (`mock_backend/tunnel/scenarios.py`) builds its seeds from the spa PMS, so these scenarios are format-compatible but **not wired into the runner**. Wiring needs seed specs for the new client.
- The renderer produces skeletons. It does not write prompts. Wording is a human task and a review step.
- Handoff in the PoC is simulated (`transfer_to_simulated_handoff`). Telephony for the dental clinic is not implemented; see `docs/telephony.md`.
- The dental prompt has a known design gap: `book_dental_appointment` has no field for health flags, so flags go to reception through the handoff tool. A real integration should add a structured field with its own retention rule.
