# Phase H1 — Diagnoza frontend widgetu (403 + nieotwarcie przycisku)

## Cel
Ustalić, dlaczego przycisk „Porozmawiaj z Anną" nie otwiera rozmowy i skąd 403/failed WebSocket w konsoli przeglądarki.

## Krok 1 — Sprawdzenie odpowiedzi serwera (curl vs browser)
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3030/                    # root
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:3030/_next/static/chunks/_1de7n1s._.js"
curl -s -o /dev/null -w "%{http_code}\n" "http://192.168.0.102:3030/_next/static/chunks/_1de7n1s._.js"
```
- Obserwedzia: root i static zwracają **200** (także z Host: IP). **403 nie reprodukuje w curl** → to środowiskowa blokada (proxy/VPN/extension/stary cache), nie serwer.

## Krok 2 — WebSocket hmr
`ws://<ip>:3030/_next/hmr` to **Next dev Hot Module Reload** — development-only (obecne preseleszenie, nie blokujь stron). Do produkcjnej rozmowy bez wpływa.

## Krok 3 — Sedno: widget skrypt z CDN
Oficjalny komponent `<elevenlabs-convai>` ładowal skrypt z `https://unpkg.com/@elevenlabs/convai-widget-embed@0.16.4/dist/index.js`.
- Ce wymaga: custom element `<elevenlabs-convai>` jest definied TYLKO po załadowowaniu tego zinęgo skrypt.
- Jeśli CDN zablokowany (adblock/VPN/sieć) → element nie istuje w DOM → `shadowRoot` pusty → `triggerConvai()` nie ma czego kliknąć → „przycisk nie otwiera".
- Konsol 403/„Failed to load resource" powiązane — nie tylko `_next/static`, ale i zablokowany zawier.

## DoD
- Ustalono: 403 static środowiskowa; WebSocket = dev-only; **sedno = zewnętrzny CDN skrypt не загрузка → element nie istuje.**
- Ścieżka rozwiązania: self-host skrypt (H2) + odporny trigger (H3).