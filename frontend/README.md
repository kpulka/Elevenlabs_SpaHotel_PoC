# Bukowy Dwór — frontend

Next.js 16 (App Router) site for the Bukowy Dwór hotel, with the Anna voice assistant
(ElevenLabs ConvAI widget). This is a demonstration build of a fictional hotel. Package manager: pnpm.

## Requirements

- Node.js 20 or newer
- pnpm (`corepack enable` or `npm i -g pnpm`)

## Environment variables

Copy `.env.example` to `.env.local` and fill in the values. Never commit `.env.local`.

| Variable | Scope | Required | Purpose |
| --- | --- | --- | --- |
| `ELEVENLABS_API_KEY` | server only (secret) | yes, for voice | API key used by `GET /api/anna/signed-url`. Never exposed to the browser. |
| `ELEVENLABS_AGENT_ID` | server only | yes, for voice | Anna agent id (`agent_...`). Falls back to `NEXT_PUBLIC_ELEVENLABS_AGENT_ID` when empty. No hardcoded fallback. |
| `NEXT_PUBLIC_ELEVENLABS_AGENT_ID` | public (browser bundle) | yes, for voice | Same agent id, set on the `<elevenlabs-convai>` element. Not a secret. |
| `ALLOWED_ORIGINS` | server only | no | Comma-separated extra origins allowed to call the API routes. Localhost, 127.0.0.1 and the site's own origin are always allowed. |
| `TRUST_PROXY` | server only | no | Default: trusted (any value except `false`). `false` ignores `X-Forwarded-For` and `X-Real-IP` for rate limiting. See *Rate limit and trust model*. |
| `NEXT_PUBLIC_SITE_URL` | public | recommended in production | Absolute base URL for sitemap, robots and metadata. Fallback: `https://bukowydwor.example`. |

Validation lives in `lib/env.ts`. A missing or malformed agent id produces a clear error that names
the variable (never its value). The signed-url endpoint answers `500 Voice assistant is not configured`,
and the voice widget is disabled on the client.

## Scripts

```bash
pnpm install --frozen-lockfile   # install exactly the locked versions
pnpm dev                         # dev server on http://localhost:3000
pnpm build                       # production build (webpack)
pnpm start                       # serve the production build
pnpm typecheck                   # tsc --noEmit
pnpm lint                        # ESLint with --quiet: reports errors only (warnings are not shown or gated)
pnpm test                        # Vitest unit and route tests (jsdom and node environments), e2e/ excluded
pnpm test:e2e                    # Playwright smoke tests in Chromium, against the production build
pnpm i18n:check                  # PL and EN dictionaries have the same keys
pnpm data:check                  # hotel data in lib/generated is in sync with its source
pnpm images:optimize -- --source=<dir>   # PNG -> WebP tool (see below)
```

Tests live next to the code as `*.test.ts(x)`. End-to-end tests live in `e2e/` and run with Playwright.

### End-to-end smoke tests

`e2e/smoke.spec.ts` covers: the home page loads in Polish, the Anna button is present, clicking it
requests `/api/anna/signed-url` (mocked with `page.route`, nothing reaches ElevenLabs), no
Content-Security-Policy violations on the home and privacy pages, and the privacy page is reachable
from the footer.

```bash
pnpm build                                  # optional: skips the build step inside the Playwright web server
pnpm exec playwright install --with-deps chromium   # once per machine (CI: see the workflow)
pnpm test:e2e                               # starts `next start` on E2E_PORT (default 3100)
```

If `.next/BUILD_ID` is missing, the Playwright web server runs `pnpm build` first (several minutes).

## Project layout (short)

- `app/` routes (App Router). API routes: `app/api/anna/signed-url` (voice session) and
  `app/api/contact` (contact form). Special pages: `app/error.tsx`, `app/global-error.tsx`,
  `app/not-found.tsx`. Privacy policy: `app/polityka`.
- `components/` UI; `hooks/use-anna-widget.ts` controls the ElevenLabs widget
- `lib/env.ts` environment validation, `lib/logger.ts` structured logs,
  `lib/rate-limit.ts` and `lib/request-guard.ts` protect the API routes, `lib/contact/validation.ts`
  validates the contact form
- `public/widget/` vendored ElevenLabs widget script (not our code, excluded from lint)
- `scripts/` build-time tools: `check-i18n.mjs`, `sync-data.mjs`, `optimize-images.mjs`

## Voice widget loading

Nothing voice-related happens on page load. The first interaction with the Anna button (hover, focus or
click) starts the signed-url request and loads the widget script (about 1.5 MB). The signed URL is cached
per language in the browser tab for 10 minutes. The conversation itself starts only on a click, and the
consent notice next to the button says so. The microphone is requested by the browser only after that click.

## Images

Photos in `public/images` are WebP, each at most 300 KB (total about 2.3 MB, down from 15.3 MB of PNG).
Social cards in `public/og` stay JPEG (Open Graph needs JPEG or PNG). Favicons stay PNG.

To regenerate or add a photo, keep the original PNG outside the repo and run:

```bash
pnpm images:optimize -- --source=/path/to/original-pngs             # writes .webp into public/images
pnpm images:optimize -- --source=/path/to/original-pngs --check      # verifies every source has a WebP
```

Then point the references (`lib/hotel/*.ts`, pages, `components/`) at the new `.webp` names.

## Security notes

**Signed URL.** The browser never sees `ELEVENLABS_API_KEY`. The client asks
`/api/anna/signed-url?lang=pl|en`, the server calls ElevenLabs with the key and returns a short-lived
signed URL that the widget uses to start a conversation. Upstream errors are logged server-side
(status only) and returned to the client as a generic message.

**Rate limit and trust model.** `lib/rate-limit.ts` is a sliding-window limiter. The signed-url route allows
10 requests per minute per client IP; the contact route allows 5 submissions per 10 minutes per IP.
Exceeding a limit returns `429` with `Retry-After`.

- The client IP comes from `X-Forwarded-For` (first entry), then `X-Real-IP`. These headers are **trusted by
  default**, because the app is meant to run behind a reverse proxy or platform that sets them.
- If the app is exposed directly, anyone can send any `X-Forwarded-For` value and get a fresh budget. Two
  options: set `TRUST_PROXY=false` (headers ignored, every request shares one budget: spoof-proof but coarse),
  or enforce the limit at the proxy.
- State is **in memory and per process**: it is lost on restart and each instance keeps its own counters.
  With several instances, enforce the limit at the proxy or move the counters to a shared store (for example
  Redis with an atomic increment and expiry). The limiter's interface (`check(key)`) is the place to swap it.

**Origin check.** Requests with an `Origin` (or, without it, a `Referer`) that is neither the site, localhost,
127.0.0.1 nor listed in `ALLOWED_ORIGINS` get `403`. Requests with neither header are allowed for
non-browser clients and are logged with `signed_url.no_origin`. Browsers always send `Origin` on
cross-origin requests, so this check is about browser callers; the rate limit still covers the rest.

**Contact form.** `POST /api/contact` validates the message (length limits, e-mail shape, optional phone
format), has a honeypot field (`website`), and answers `{ "ok": true, "delivered": false }`. **Messages are not
delivered and not stored anywhere in this demo.** The response and the on-page notice say so. Logs carry event
names, the failing field name and counts; they never carry the name, e-mail, phone or message text.

**Logging.** `lib/logger.ts` writes one JSON line per event and drops fields whose names look like
credentials. Callers must not pass request headers, keys, upstream bodies or user-entered text.
Error boundaries log the Next.js digest and error name, not the message.

**Content-Security-Policy and headers.** Set in `next.config.mjs` for all routes:

- `default-src 'self'`; `frame-ancestors 'none'` and `X-Frame-Options: DENY` (no framing)
- `connect-src`, `media-src`, `frame-src` and `worker-src` allow the ElevenLabs endpoints and `blob:` that the
  widget needs for the microphone session and audio
- `script-src` and `style-src` allow `'unsafe-inline'`. Next.js inline bootstrap scripts and widget styles
  need it; a per-request nonce would require middleware and would make pages dynamic. `'unsafe-eval'` is
  added only in development.
- Microphone access is governed by `Permissions-Policy` (microphone not blocked, camera and geolocation blocked).
- `X-Powered-By` is disabled (`poweredByHeader: false`).

If the widget stops working after a CSP change, check the browser console for `Refused to connect` or
`Refused to create a worker` messages and extend the matching directive.

**Privacy.** `/polityka` (linked from the footer and the consent notice) describes the processing: the
ElevenLabs voice session, the microphone, recordings, analytics (Vercel Analytics in production and the
widget's telemetry), and the rights of data subjects. It is a demonstration text: retention periods and the
legal basis for health data are marked "to be defined by the controller" rather than invented.
