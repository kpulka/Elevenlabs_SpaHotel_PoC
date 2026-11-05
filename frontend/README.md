# Bukowy Dwór — Demo Website

Demo website for a fictional thermal spa and health resort in Krynica-Zdrój, with the AI voice receptionist **Anna** embedded on every page. It is the front end of the [Elevenlabs SpaHotel PoC](../README.md) and exists to show how a conversational agent can sit inside a real booking website.

The site is bilingual (English by default, Polish via the header switcher). The choice is stored in the browser.

## Stack

- **Next.js 16** (App Router, webpack build)
- **React 19**
- **Tailwind CSS 4** with shadcn/ui primitives
- **TypeScript** (strict)
- **ElevenLabs ConvAI** web component for the voice agent

## Run locally

Requirements: Node.js 20+ and pnpm.

```bash
cd frontend
cp .env.example .env.local   # then fill in ELEVENLABS_API_KEY
pnpm install
pnpm dev                     # http://localhost:3030
```

Other scripts:

| Script | Purpose |
|---|---|
| `pnpm build` | Production build (also type-checks) |
| `pnpm start` | Serve the production build on port 3030 |
| `pnpm typecheck` | `tsc --noEmit` |

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ELEVENLABS_API_KEY` | yes | ElevenLabs API key. Used only on the server to request signed URLs. |
| `ELEVENLABS_AGENT_ID` | no | ConvAI agent ID. Falls back to the demo agent defined in `app/api/anna/signed-url/route.ts`. |

Never prefix these with `NEXT_PUBLIC_`: that would expose them to the browser.

## How the voice widget works

**Signed URL, so the API key never reaches the browser.**
`AnnaEmbedWidget` calls `GET /api/anna/signed-url?lang=<en|pl>`. The route handler calls the ElevenLabs API with the secret key and returns a short-lived `signed_url`. The widget then connects with that URL. The language is passed along so the agent answers in the guest's active language, and it is also sent as a dynamic variable (`user_language`).

**Self-hosted widget script.**
The official ConvAI embed script is served from `public/widget/convai-widget-embed.js` rather than loaded from the ElevenLabs CDN. Many ad blockers and corporate networks block third-party CDN requests, which made the widget silently fail for those visitors. Self-hosting removes that dependency. The file must be refreshed manually when ElevenLabs publishes a new version.

**Microphone access.**
`next.config.mjs` keeps the `microphone` permission enabled (required by `getUserMedia`) and disables camera and geolocation.

## Project layout

```
app/                    Routes: / (home), /rooms, /spa, /restaurant, /directions, /contact
app/api/anna/           Signed-URL route handler (server-side only)
components/             Layout, widget and page components
context/                Language provider (EN/PL, persisted in localStorage)
lib/translations.ts     UI strings for both languages
lib/hotel-data.ts       Rooms, treatments, diets, meal times, contact details
public/widget/          Self-hosted ElevenLabs ConvAI embed script
types/                  Ambient type declarations (ConvAI custom element)
```
