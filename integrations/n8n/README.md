# n8n integration: signed Anna events

**Status: design / example, not deployed.** What is verified and what is not:

| Part | File | Status |
|---|---|---|
| Reference receiver (signature, replay window, dedupe, HTTP) | `receiver_example.py` | **Verified** offline: 48 pytest tests in `test_receiver.py` |
| Code node logic (same verification, in JavaScript) | `verify_signature.js` | **Verified** by executing it with Node.js against the same vectors (`test_receiver.py`) |
| n8n workflow JSON | `anna_events_workflow.example.json` | **Structure checked** (JSON, node graph, no secrets). **Not imported or executed in a live n8n instance.** |
| Emitter in the Anna backend | `mock_backend/` | Out of scope here. This folder only consumes the contract below; confirm the emitter is merged before relying on it. |

Nothing in this folder talks to a real CRM or calendar. All targets are placeholders (`*.example.invalid`, env vars).

## Files

| File | Purpose |
|---|---|
| `anna_events_workflow.example.json` | Importable n8n workflow (Webhook, Code, IF, Switch, HTTP Request, Respond to Webhook). Inactive. |
| `verify_signature.js` | Source of the workflow's Code node (kept as a file so it can be tested). |
| `receiver_example.py` | Stdlib-only reference receiver. Same checks as the workflow. Runs locally. |
| `test_receiver.py` | Offline tests: fixed test vector, tampering, stale timestamps, HTTP round-trip, workflow checks, Node cross-check. |

## Contract (what the emitter sends)

`POST` with a JSON body. The signature covers the **raw bytes** on the wire.

Body: compact JSON with sorted keys (`separators=(",", ":")`).

| Field | Type | Notes |
|---|---|---|
| `event_id` | string | Unique per event. Use it to dedupe retries. Also sent as header `X-Anna-Event-Id`. |
| `event_type` | string | `booking.created`, `booking.cancelled`, `booking.rescheduled`, `handoff.requested` |
| `occurred_at` | string | ISO 8601, UTC |
| `request_id` | string | Correlates with the backend request log |
| `conversation_id` | string or null | Conversation identifier when the emitter has one |
| `data` | object | Event payload, already masked (guest names, phone numbers). Field names inside `data` are defined by the emitter; the example assumes `confirmation_id` for reschedule/cancel routes. Confirm before use. |

Headers:

| Header | Value |
|---|---|
| `X-Anna-Event-Id` | same as body `event_id` |
| `X-Anna-Timestamp` | unix seconds, integer |
| `X-Anna-Signature` | `sha256=` + hex(HMAC-SHA256(secret, `"{timestamp}.{body}"`)) |

Replay tolerance: **300 s** either side of the receiver clock. Outside that window the request is rejected.

Response codes from the receiver/workflow:

| Code | When |
|---|---|
| 200 | Signature and timestamp valid (`duplicate: true` if the `event_id` was already seen) |
| 400 | Valid signature but malformed: invalid JSON, `event_id` header/body mismatch, unknown `event_type` |
| 401 | Missing or invalid headers, stale timestamp, bad signature. The body is always `{"error":"unauthorized"}`, so the caller cannot tell which check failed. |
| 404 | Wrong path (receiver only) |
| 413 | Body over 64 KiB (receiver only) |

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `ANNA_EVENTS_WEBHOOK_URL` | Anna backend (emitter) | Target URL, e.g. `http://<n8n-host>:5678/webhook/anna/events` |
| `ANNA_EVENTS_SIGNING_SECRET` | Anna backend **and** n8n / receiver | Shared HMAC key. Must be identical on both sides. Never commit it. |
| `ANNA_CRM_URL` | n8n | CRM base URL (placeholder in the example) |
| `ANNA_CALENDAR_URL` | n8n | Calendar base URL (placeholder in the example) |
| `NODE_FUNCTION_ALLOW_BUILTIN=crypto` | n8n | Lets the Code node `require('crypto')`. Check the variable name against your n8n version docs. |
| `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` | n8n | Lets the Code node and expressions read `$env`. Needed for the secret and the URLs. Only do this on a host you control. |

Credentials: the CRM auth header is an n8n credential (`httpHeaderAuth`), not an env var. The workflow references it by placeholder id only.

## Run the reference receiver locally (no n8n needed)

```bash
cd integrations/n8n
export ANNA_EVENTS_SIGNING_SECRET=local-dev-secret   # any value, local only
python receiver_example.py --port 8787 &
python receiver_example.py --print-sample            # prints a signed sample request
```

Send the printed headers and body with curl, using `--data-binary` so the bytes are not altered:

```bash
curl -s -X POST http://127.0.0.1:8787/webhook/anna/events \
  -H "Content-Type: application/json" \
  -H "X-Anna-Event-Id: evt_sample_0001" \
  -H "X-Anna-Timestamp: <timestamp from --print-sample>" \
  -H "X-Anna-Signature: <signature from --print-sample>" \
  --data-binary @sample_body.json
```

Note: `--print-sample` signs with the current time, so it must be sent within 300 s.

## Run the tests

From the repository root (no n8n, no network):

```bash
python -m pytest -q integrations/n8n/test_receiver.py
```

The test vector is `secret="test-secret"`, `timestamp="1700000000"`, `body='{"event_id":"e1"}'`, expected signature `sha256=18a2df74eba88d0ed4b4033fc9f3860558e826c9e5d1b77dc702b5da0d0cefe6` (computed with Python's `hmac` module and hardcoded in the test). The Node cross-check runs only if `node` is on PATH.

## Set up n8n (example)

1. Start n8n in Docker. Keep secrets in an env file, not on the command line (`-e KEY=value` is visible in the process list). The `*.env` pattern is git-ignored in this repo.

   ```bash
   # anna-n8n.env (local, never committed)
   ANNA_EVENTS_SIGNING_SECRET=<generate a long random value>
   ANNA_CRM_URL=https://crm.example.invalid/api/v1
   ANNA_CALENDAR_URL=https://calendar.example.invalid/api/v1
   NODE_FUNCTION_ALLOW_BUILTIN=crypto
   N8N_BLOCK_ENV_ACCESS_IN_NODE=false
   ```

   ```bash
   docker run -it --rm -p 5678:5678 --env-file anna-n8n.env -v n8n_data:/home/node/.n8n n8nio/n8n
   ```

2. Open `http://localhost:5678`, then **Import from File** and choose `anna_events_workflow.example.json`.
3. Create an `httpHeaderAuth` credential for the CRM and calendar placeholder nodes, then attach it to each HTTP node.
4. In the Webhook node, confirm **Raw Body** is on. Check where the raw body appears in your n8n version (binary `data` or `rawBody`); `verify_signature.js` handles both shapes, but this is the first thing to check if every request returns 401.
5. Send a test request with the receiver's `--print-sample` output and check the execution in the **Executions** tab.
6. Activate the workflow only after step 5 works.

## Gotchas

- **Verify the raw bytes.** If n8n parses the JSON and you re-serialize it, key order, whitespace and non-ASCII escaping change, and the signature no longer matches. The test `test_signature_covers_raw_bytes_not_reserialized_json` covers this on the Python side.
- **200 means "accepted", not "processed".** The example responds 200 in parallel with the routing, so a failing CRM or calendar call is not reported back to the emitter. Retries and dead-letter handling belong to the emitter; a production workflow should respond after the downstream calls succeed.
- **No dedupe store in the example.** The receiver keeps seen `event_id`s in memory only. A production consumer needs a durable store (for example n8n's data store or a database) with a TTL.
- **Clock skew.** A host clock more than 300 s off rejects every event. Keep NTP running.

## GDPR note

The payload carries personal data of guests (names, confirmation numbers, sometimes health-related reasons for handoff). Rules this example follows, and rules a real deployment must still meet:

- The emitter must send masked data only (guest names and phone numbers masked, no free-text health notes). The example workflow does not add data; it forwards what the emitter sent.
- The CRM and calendar are processors or recipients of that data. Their contracts, retention and location must be settled before live use. See `docs/gdpr/ropa.md`.
- Keep n8n execution data retention short (n8n settings: execution data pruning). Stored executions contain the payload.
- Not legal advice. Confirm the legal basis with your data protection officer.

## Limitations

- Not run in a live n8n instance (no Docker in the verification environment). Node-level checks cover the Code node logic only.
- The Switch routes only the four contract event types; anything else goes to a NoOp node.
- CRM and calendar calls are placeholders: field names and endpoints are invented for illustration and must be replaced with the real API.
