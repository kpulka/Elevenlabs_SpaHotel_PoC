# Lessons Learned

> Real problems hit while building and testing this PoC, how they were diagnosed, and what changed. Each one maps to a production concern.

## 1. "The agent failed" was actually dead infrastructure

**Symptom.** In a test conversation, room availability and the human handoff both failed. The agent retried (as instructed) and then apologised about a "connection problem".

**Diagnosis.** The prompt and model behaved correctly. The mock backend could not bind its default port (already used by a system service) and the public tunnel was down, so **every** webhook was unreachable.

**Fix.** Moved to a free port; wrote a start script that launches the backend and tunnel, captures the new public URL, and re-points all agent tools to it; added autostart and a containerised variant.

**Takeaway.** Blame the integration layer before the model. In production this becomes a stable endpoint, health checks, and alerting on tool error rate (see [playbook §5](deployment-playbook.md#5-failure-modes-and-runbook)).

## 2. The prompt promised an escalation that did not exist

**Symptom.** The audit of the live agent found that the prompt told the model to call a "transfer to human" tool, but the deployed configuration had no such tool — only `end_call`.

**Fix.** Implemented a handoff tool (simulated on web because there is no telephony in the PoC) that notifies staff with conversation context, and aligned prompt and configuration. Documented the production path (`transfer_to_number` via SIP).

**Takeaway.** Safety rules need an executable path. Audit prompt ↔ configuration consistency as a release step. Details: [agent-audit.md](agent-audit.md).

## 3. The widget silently did nothing

**Symptom.** The "Talk to Anna" button did not start a conversation; the console showed failed requests.

**Diagnosis.** Several red herrings (dev-server hot-reload WebSocket, static asset 403s that did not reproduce with `curl`). The real cause: the custom element is only defined after a script from a public CDN loads; where that CDN was blocked, the element never existed and nothing could be clicked.

**Fix.** Self-hosted the widget script and made the trigger resilient to the element not being ready yet.

**Takeaway.** A third-party script on the critical path is an availability risk. Self-host or provide a fallback (phone number) and test in locked-down networks.

## 4. Ephemeral tunnel URLs break webhooks after every restart

**Fix for the PoC.** The start scripts discover the new URL and update the agent's tools automatically.
**Production answer.** A fixed domain, named tunnel or hosted service with authenticated webhooks.

## 5. Choosing the voice model for the audience, not the benchmark

A faster "flash" voice model saves roughly 200 ms but sounds less natural. For 70+ guests, expressiveness and pace (speed 0.85×, patient turn-taking) increased perceived trust more than the latency saved. Measure with your audience.

## 6. Policies belong in procedures, not in one giant prompt

Cancellation windows, deposit refunds, early/late check-in, dietary handling, transport and complaints were moved from the prompt into discrete operating procedures. This shortens the prompt, makes policies auditable, and lets business owners review them independently of prompt engineering. See [operating-procedures.md](operating-procedures.md).

## 7. Tooling bugs happen — keep a REST fallback

The management tool used to attach the knowledge base to the agent returned a server-side error. The deployment script [`agent/deploy_agent.py`](../agent/deploy_agent.py) talks to the REST API directly, so deployment never depends on a single tool being healthy. It also makes the KB deployment reproducible and reviewable.
