# Agent Audit: "Anna" — Guardrails, Flow and Improvements (2026-08)

> Review of the live Anna agent configuration against the design documentation, covering guardrails, conversation flow, operational risks and recommended changes.

**Agent:** Bukowy_Dwor_Anna — `agent_8401m0n03cggfgebhfh0cj96t7aj` (Creator, $22/month)
**Data source:** live configuration retrieved from the ElevenLabs API (`GET /v1/convai/agents/{id}`) and the documentation in `docs/`.

---

## 1. What Is Working Well (verified state ✓)

- **Strict grounding:** hard rules in the prompt (never invent prices, availability or medical results) plus `temperature 0.1`. Strong anti-hallucination guardrails.
- **Knowledge base is correct:** 5 files, with `usage_mode` set as intended. 03_rooms and 05_procedures are set to `prompt` (full context); the remaining files are set to `auto` (RAG). This matches the functional specification.
- **Parameters:** turn_timeout 3.0, turn_eagerness `patient`, stability 0.8, speed 0.85, similarity 0.75, TTS `eleven_v3_conversational`, voice Jessica (`cgSgspJ2msm6clMCkdW9`). All settings match the specification.
- **LLM:** `gemini-2.0-flash-001` (a good choice for cost and Polish-language performance); STT `scribe_realtime`.
- **Four webhooks** are live through a temporary quick tunnel and verified (HTTP 200): check_spa_availability, book_spa_appointment, check_room_availability, send_sms_summary. POST schemas are correct.
- **Signed URL** in the front end (`/api/anna/signed-url`): the API key is not exposed to the browser. Good practice.
- **Widget** styled to the brand palette (navy / gold / cream), full variant, with feedback rating.

## 2. Issues Found

| # | Issue | Severity | Description |
|---|-------|----------|-------------|
| 1 | **No `transfer_to_number` (handoff) configured** | Critical | The prompt instructs the agent to "call transfer_to_human" (8 times: points 2, 4, 6, and other sections under "WHEN TO TRANSFER"). **However, no such system tool exists**: the live configuration has only `end_call` enabled. The agent has no working path to hand over to a person. Demo path C (escalation) cannot actually be executed; the agent would be simulating a transfer. |
| 2 | **Tool name mismatch** | High | The document specified `transfer_to_human`, while the native ElevenLabs tool is `transfer_to_number`. The name in the prompt must be synchronised once the tool is activated. |
| 3 | **max_duration 300 s** | Medium | Five minutes per call is acceptable for a demo but short for real use. Senior callers often speak more slowly. Increase to 600–900 s. |
| 4 | **No `skip_turn` / silence condition** | Low / medium | Speech goals still to be defined. For senior guests this is acceptable, so the agent does not appear to "ignore" them, but turn_eagerness `patient` already covers most of this. |
| 5 | **Ephemeral quick tunnel** | Critical (operational) | Webhook URLs are tied to the hostname of an ephemeral quick tunnel. After a tunnel restart the addresses change and all four webhooks fail. A stable URL is required (a reserved ngrok domain or a named Cloudflare tunnel; quick tunnels are not stable). Acceptable for a demo, but it is the single point of failure. |

## 3. Guardrails Assessment

The prompt-level layer (grounding, low temperature, retry-after-error, and distinguishing "no appointment available" from "system error") is sound and sufficient for the PoC. What is missing is the **execution layer of the handoff**: the prompt promises an escalation that does not exist. This is a safety gap. In a medical or emergency situation the agent has no real way to reach a person, and it may loop or simulate a transfer.

Additionally, the following are missing (if required):
- **Conversation History Redaction / ZRM:** available only on the Enterprise plan; not available on Creator.
- **Monitoring:** disabled (`monitoring_enabled: false`). Enabling it is valuable for statistics.

## 4. Recommended Improvements

1. **Activate `transfer_to_number`** (built-in system tool) through the workspace or API, providing the reception number. In the prompt, replace `transfer_to_human` with `transfer_to_number`. The change is a one-to-one substitution of the tool name.
2. **Increase `max_duration_seconds`** from 300 to 900 (15 minutes) for calmer conversations.
3. **Use a stable tunnel** for the webhooks (a reserved tunnel domain or a named tunnel), so that the four webhooks do not fail after a restart.
4. Optional: enable conversation monitoring once the plan supports it.
5. The prompt does not need to be expanded. Shortening it is not urgent.

## 5. Changes Deliberately Not Recommended
- Do not change the knowledge base `usage_mode` settings. The current assignment (5 of 5 files) matches the plan.
- Do not increase the temperature. For grounding with senior guests, low temperature is the most important control.

## 6. Next Steps (decision for the client team)
- [ ] Confirm the reception number for `transfer_to_number`.
- [ ] Apply the following changes (the REST API is required, because the MCP does not support built-in tools):
  - activate `transfer_to_number`,
  - upload the updated prompt,
  - increase max_duration.
- [ ] (Optional) set up a stable tunnel for the webhooks.

---

## 7. Update (2026-08): Simplified PoC Handoff Deployed

The agent runs only as a **web widget** (`phone_numbers: []`), so a real `transfer_to_number` (SIP / telephony) is not applicable to the PoC. Instead:

- **Endpoint added:** `POST /transfer_to_simulated_handoff` in `mock_backend/main.py`. It logs the event to the console and optionally sends an alert to Telegram (through the existing `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` integration). Tested: returns `success: true` and `simulated: true`.
- **System prompt:** `agent/system_prompt.md` instructs the agent to call the webhook `transfer_to_simulated_handoff` instead of `transfer_to_human` / `transfer_to_number`. The JSON schema is in the header of the file.
- **Mock backend README** updated with a table entry for the tool (`mock_backend/README.md`).

> **To make this work in the workspace:** register the webhook tool `transfer_to_simulated_handoff` in ElevenLabs, with URL = tunnel address + `/transfer_to_simulated_handoff`, and upload the system prompt from `agent/system_prompt.md`. Optionally, set the Telegram variables to send the "second screen" alert.

---

## 8. Workflow and Procedures (Epic F, 2026-08)

### What these are
- **`procedures`** are named, modular "skills" for handling a situation, separate from the main prompt, which the agent can run. Types: `free_form` (natural language) or `deterministic` (rigid flow). They reference tools, knowledge base files or other procedures.
- **`workflow`** is the orchestrator graph (nodes and edges), used if you want a branching agent or sub-agents. Node types: start / end / tool / override_agent / phone_number / standalone_agent.

### What was done (and then cleaned up)
Four procedures were created on the agent (per branch, NOT attached live) for research purposes:

| Name | Type |
|---|---|
| przeprowadz_rezerwacje_zabiegu_spa | free_form |
| przeprowadz_zapytanie_o_pokoj | free_form |
| sprawdz_przeciwwskazania_zdrowotne | free_form |
| decyzja_o_transferze | deterministic |

> **Update (cleanup):** after evaluating the research, the procedures were **deleted** (DELETE; `list_procedures` returns `[]`). They are not active on the agent and were only test drafts used to verify the API. Agent state: `procedures: {}` (the initial state).

### Result of the attachment investigation (F8: deferred)
The procedures feature is in an **early / beta** state:
- Creation works (POST create → draft, `has_draft=true`).
- **Attaching to an agent requires a `version_id`** (PATCH `agent.procedures` as a map `{id: {procedure_id, version_id}}`), but the procedures have `version_id=None`, and the OpenAPI specification has **no publish / commit endpoint**, so there is no supported way to version them.
- `compile` on the procedures returns 400 "Invalid JSON content" (an error for `deterministic`).
- **Conclusion:** the procedures feature in agents is in an **early / beta** state. Creation works, but attaching to an agent requires a `version_id` that cannot be obtained. **Attachment is DEFERRED until the feature matures.** The agent remains safe and unchanged (the PATCH was not applied, so nothing was modified). The test procedures were subsequently deleted.

### Recommendation for the future
- When ElevenLabs adds a "publish version" capability or the procedures feature matures, re-evaluate and, where feasible, attach the modular procedures. They would provide clear, testable flows for SPA booking, room requests, medical screening and transfer decisions. The content is preserved in the history of this audit.
- Do not use `override_agent` or `phone_number` nodes in the workflow (there is no telephony for this PoC).
- Reference document (decision and research): removed during cleanup; the conclusions are in section 8 of this audit.
