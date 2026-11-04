# Agent artifacts

Everything deployed to the ElevenLabs agent "Anna".

| Path | Content |
|---|---|
| `system_prompt.md` | Persona, grounding rules, escalation rules, procedure references |
| `knowledge_base/` | Five curated RAG documents. `03` and `05` are injected in-context (`prompt`), the rest are retrieved (`auto`) |
| `workflow/workflow.json` | Workflow graph (start → main agent → end) |
| `workflow/procedures.md` | The seven operating procedures (cancellation, rescheduling, deposit refund, early/late check-in, diets, transport, complaints) |
| `deploy_agent.py` | Uploads the knowledge base and applies agent settings via the REST API (`--dry-run` to preview) |

**Language note.** Prompt, knowledge base and procedures are in Polish on purpose: they are the runtime content spoken to Polish-speaking guests. Design documentation around them is in English (see `../docs`).
