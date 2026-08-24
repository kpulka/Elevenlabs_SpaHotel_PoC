# Phase H2 — Self-host skryptu widgetu (eliminacja zewnętrnego CDN)

## Cel
Zamieniezyć zależność od `unpkg.com` (CDN blokowany w przeglądarce → widget nie ładowal) na **lokalny self-host** — skrypt w `public/widget/`, stron serve przez Next bez zewnętrnego load.

## Krok 1 — Pobieram skrypt
```bash
cd frontend
mkdir -p public/widget
curl -s -L -o public/widget/convai-widget-embed.js \
  "https://cdn.jsdelivr.net/npm/@elevenlabs/convai-widget-embed@0.16.4/dist/index.js"
# -> HTTP 200, ~1.5MB, poprawny JS IIFE: (function(){function e(e){...
```

## Krok 2 — Podpięcie w komponentzie
`components/anna-embed-widget.tsx`:
```ts
// z: const WIDGET_SCRIPT = 'https://unpkg.com/@elevenlabs/convai-widget-embed@0.16.4/dist/index.js'
const WIDGET_SCRIPT = '/widget/convai-widget-embed.js'   // self-host
```
`useEffect` wstrzykiwania: `el.src = WIDGET_SCRIPT` → skrypt z localhost.

## Krok 3 — Weryfikacja served
```bash
curl -s -I "http://localhost:3030/widget/convai-widget-embed.js"
# HTTP 200, Content-Length: 1521321, Content-Type: application/javascript
```

## DoD
- Skrypt w `public/widget/`, servy przez Next (200, 1.5MB).
- Komponent ładowała `/widget/convai-widget-embed.js` (no unpkg).
- Custom element `<elevenlabs-convai>` rejestruje się (ni zależny od CDN).

## Uwaga
Skrypt wersja 0.16.4 — przy aktualizacji ElevenLabs widgetu nastarzić pobrał nowu wersju.