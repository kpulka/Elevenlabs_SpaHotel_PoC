# Lessons Learned

> Seven-plus real problems hit while building and testing this PoC, how each was diagnosed, and what changed.
> Every entry is verifiable in this repository; each one maps to a production concern in
> [deployment-playbook.md](deployment-playbook.md).

## 1. "The agent failed" was actually dead infrastructure

**Symptom.** In a test conversation, room availability and the human handoff both failed. The agent retried
as instructed, then apologised about a "connection problem" — which reads like a model defect.

**Diagnosis.** The prompt and the model behaved correctly. The mock backend could not bind its default port
(`8000` is taken by a system process on the demo host) and the public tunnel was down, so **every** webhook
was unreachable at once.

**Fix.** Moved the backend to `8011` and documented why; wrote a start script that launches the backend and
the tunnel, captures the new public URL and re-points all agent tools to it; added `--check` preflight that
probes every webhook host before a session is spent.

**Takeaway.** Blame the integration layer before the model. In production this becomes a stable endpoint,
health checks and alerting on tool error rate.

## 2. The prompt promised a tool that did not exist

**Symptom.** The audit of the live agent found the prompt instructing the model to "call `transfer_to_human`"
in eight places. Nothing by that name was configured on the agent.

**Diagnosis.** Beyond the wrong name, the built-in ElevenLabs transfer tool (`transfer_to_number`) needs a
real PBX trunk, which a PoC does not have. The safety rule was therefore unexecutable: the agent was told to
escalate through a path that did not exist.

**Fix.** v3 of the prompt routes escalation through `transfer_to_simulated_handoff`, a webhook on the mock
backend that notifies staff with the conversation context. Prompt and configuration were aligned, and the
production path (SIP transfer) is documented separately instead of being implied.

**Takeaway.** Safety rules need an executable path. Audit prompt ↔ configuration consistency as a release
step; the artifact of that audit is [audyt_agenta_2026-08.md](audyt_agenta_2026-08.md).

## 3. The widget silently did nothing

**Symptom.** The "Talk to Anna" button did not start a conversation; the console showed failed requests.

**Diagnosis.** Several red herrings (dev-server hot-reload noise, static 403s that did not reproduce with
`curl`). The real cause: the custom element is only defined after a script from a public CDN loads. Where
that CDN was blocked, the element never existed and nothing could be clicked.

**Fix.** Self-hosted the widget script at `/widget/convai-widget-embed.js` and made the trigger resilient to
the element not being ready yet.

**Takeaway.** A third-party script on the critical path is an availability risk. Self-host or provide a
fallback (a phone number) and test on locked-down networks.

## 4. Ephemeral tunnel URLs break webhooks after every restart

**Symptom.** After restarting the tunnel, one or two procedures started failing mid-call while the rest
worked — the signature of a half-updated configuration.

**Diagnosis.** A quick tunnel gets a new hostname on every start, while each tool has the URL baked into its
schema. Some tools had been updated by an old inline script that knew only five of the seven tools.

**Fix.** `sync_agent_tools.py` is now the single place that rewrites webhook URLs: it resolves tools **by
name** (so re-created tools keep working), covers all seven, and is called by the start scripts.

**Takeaway.** Treat endpoint discovery as code, not as a manual step. In production this disappears behind a
fixed domain — but the "re-point everything, verify every tool" habit is what makes that transition safe.

## 5. Choosing the voice for the audience, not for the benchmark

A faster "flash" voice model saves roughly 200 ms but sounds less natural. For 70+ guests, expressiveness and
pace mattered more than the latency: `eleven_v3_conversational` at 0.85× speed with patient turn-taking.
Reasoning stays at temperature 0.1 with `gemini-3.5-flash-lite`, because grounding matters more than fluency
for prices and medical boundaries. Measure with your actual audience — latency benchmarks do not hear a
90-year-old repeat a question.

## 6. Policies belong in procedures, not in one giant prompt

Cancellation windows, deposit refunds, early check-in / late check-out, dietary handling, transport and
complaints were moved out of the prompt into **seven discrete published procedures**. The prompt got shorter,
policies became auditable line by line, and the business owner can review them without reading prompt
engineering. A procedure also gives the model an explicit trigger condition, which is exactly what stops it
from improvising.

## 7. A `200 OK` is not proof that anything changed

**Symptom.** Uploading a corrected knowledge-base file returned `200`, and the agent kept answering from the
old text.

**Diagnosis.** `PATCH /v1/convai/knowledge-base/{id}` accepts the multipart upload and **ignores the content**.
The same class of trap exists for the hosted prompt: the live agent can hold a different version than the
file in the repository.

**Fix.** A KB change means: create a new document → re-point the agent's `knowledge_base` list (preserving
each entry's `usage_mode`) → delete the old document → verify by searching for a marker string in
`extracted_inner_html`. For deployments the repository uses a REST script (`deploy_kb_and_tools.py`) rather
than a UI, so the change is reproducible and reviewable.

**Takeaway.** Verify state, never the status code. Any "deploy" step needs an assertion that reads the
result back.

## 8. The deck lied about its own arithmetic

**Symptom.** Found while merging review notes from an abandoned branch: the online English deck claimed
`3,738 minutes (~$0.027/min)` and "5 bookings × $400–800 pays for the annual contract in under 60 days",
while the deck generator said `$22 / 275 min` and `$299 / 3,738 min` — which is **$0.08/min**, three times
higher. The Polish deck claimed two 500 PLN bookings cover a $299 plan (they cover $250), and the same
"275 min ≈ 1 hour of receptionist wage" error appeared in four more files.

**Diagnosis.** Nothing checked arithmetic. The gates verified type-safety, i18n parity and forbidden strings,
but no gate compared numbers **between** artifacts (generator, HTML deck, spec JSON, notes).

**Fix.** One canonical set of figures (FX 4.0 PLN/USD, $0.08/min, 3 × 500 PLN ≈ $375 > $299), applied to the
generator, both HTML decks, both spec files and the historical notes; the PPTX files were regenerated and
verified for 14 slides, the new figures and the absence of the old ones.

**Takeaway.** A claim repeated in six files is not six times more true. Cross-artifact assertions belong in
the same gate as the tests — and a "no invented numbers" rule beats a persuasive slide.
