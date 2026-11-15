# Security policy

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private vulnerability reporting for this
repository (the **Security** tab → **Report a vulnerability**). Include what you found, the steps to reproduce it,
and the commit or release you tested.

This is a portfolio project maintained by one person. Only the `main` branch is supported. I aim to acknowledge a
report within a week and to fix or document a confirmed issue as soon as practical. There is no bug bounty and no
service-level commitment.

## Scope

In scope:

- The mock backend (`mock_backend/`): request validation, business-rule enforcement, webhook authentication
  (`mock_backend/routers/security.py`), error handling, and the tunnel and start scripts (`mock_backend/tunnel/`).
- The website (`frontend/`): the signed-URL proxy (`/api/anna/signed-url`), the contact form, dependencies and
  headers.
- Secrets handling in the repository and its CI workflows (`.github/workflows/`).

Out of scope:

- ElevenLabs Agents, Cloudflare and GitHub platforms themselves. Report those to the vendor.
- Demo-mode behaviour that is documented and intentional: with `ANNA_WEBHOOK_SECRET` empty the tool endpoints accept
  unauthenticated requests (see below), and the in-memory state resets on restart unless a database path is set.
- Findings that need a leaked API key or webhook secret of the repository owner.

## What this project is, and what it is not

- **The hotel is fictional.** "Uzdrowisko Termalne Bukowy Dwór" does not exist. Prices, staff, contact details and
  photographs are invented or AI-generated placeholders (see [NOTICE.md](NOTICE.md)).
- **No real guest data.** This repository is a demonstration. Do not send real personal or health data to the demo,
  the tunnel URL or the widget.
- **The demo may be public while it runs.** The Cloudflare quick tunnel exposes the mock backend to the internet for
  as long as the start script runs. Treat it as a demonstration, not as a production endpoint.

## Secrets handling

- API keys and webhook secrets live only in local `.env` / `.env.local` files, which are gitignored. Every `*.example`
  file lists the variables it needs, without values.
- The ElevenLabs API key is used server-side only. The browser requests a short-lived signed URL from
  `/api/anna/signed-url` and never receives the key.
- Tunnel state (`state.json`, logs, backups) is gitignored because it contains addresses and process IDs.
- If you find a secret in the history, report it through the channel above. The key must be rotated; removing it
  from a later commit is not enough.

## Webhook authentication

The seven tool endpoints of the mock backend (`POST /check_spa_availability`, `/book_spa_appointment`,
`/cancel_spa_appointment`, `/reschedule_spa_appointment`, `/check_room_availability`, `/send_sms_summary`,
`/transfer_to_simulated_handoff`) are checked by `mock_backend/routers/security.py`. Two modes, both disabled
when `ANNA_WEBHOOK_SECRET` is empty:

- **Shared secret** (default): the request carries `X-Webhook-Secret` equal to the configured value. The comparison
  is constant-time (`hmac.compare_digest`). This is what the agent's tools send.
- **HMAC** (opt-in per request): if the request carries `X-Anna-Signature` or `X-Anna-Timestamp`, both must be present
  and must verify against the exact body bytes, with a replay window of 300 seconds. The same algorithm signs the
  outbound integration events.

Behaviour:

- `ANNA_WEBHOOK_SECRET` set: a request that fails the check gets `401`.
- `ANNA_WEBHOOK_SECRET` empty: authentication is **off** (demo and tests). The backend logs a warning at start.
- `ANNA_ENV=prod`: the backend refuses to start without the secret (`mock_backend/main.py`).
- The tunnel start scripts (`mock_backend/tunnel/podman_start.sh`, `start_anna.sh`) refuse to open the public tunnel
  while the secret is empty.

The shared secret must also be configured as the `X-Webhook-Secret` request header on each tool in the ElevenLabs
workspace; otherwise the agent's calls are rejected. A production deployment should still restrict the network path
(fixed domain, IP allow-list or mTLS) and rotate the secret.
