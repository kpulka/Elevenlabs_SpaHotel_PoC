# Phase F1 — Osadź oficjalny pływający widget ElevenLabs (custom element `<elevenlabs-convai>`)

## Cel
Wstawić **prawdziwy, oficjalny widget** żywego agenta Anna (głos + tekst + RAG + narzędzia) na stronie, zamiast mocka w `frontend/components/anna-widget.tsx`. Zachowujemy złoty guzik „Porozmawiaj z Anną" jako trigger.

## Kontekst techniczny (zweryfikowany)
- Oficjalny widget to **custom element** `<elevenlabs-convai>` ładowany przez **snippet `<script>` z CDN** (`cdn.elevenlabs.io`). NIE jest to `@11labs/react` (ten pakiet: hooki `useConversation` — do własnego UI, bez gotowego widgetu).
- Embed snippet pozyskuje się z: **Agent → Deploy/Embed** w panelu, lub z publicznego/udostępnionego widget-agenta przez endpoint **signed URL**.
- Widget potrzebuje **publicznego lub zalogowanego dostępu** do agenta (w "Wczycie" używaliśmy w koncie zalogowanym) — do osadzenia na stronie (bez zalogowania) ElevenLabs generuje **signed URL** z konfiguracją.

## Zależności
- Agent działa: `agent_8401m0n03cggfgebhfh0cj96t7aj` (KB, RAG, tools, głos).
- Widget config (kolory/teksty/first_message) dostępny: `.planning/_agent_widget.json`.

## Kroki
1. **Pozyskaj oficjalny embed snippet** dla agenta:
   - W panelu ElevenLabs → `Bukowy_Dwor_Anna` → **Deploy / Interaction → Embed / Shareable** → skopiuj fragment (script + `<elevenlabs-convai>` z `agent-id` i ewentualnie `signed-url`).
   - *Fallback:* endpoint podpisany na sessję — pobierz przez API, jeśli UI nie poda snippet automatic.
   - Zachowaj snippet w `frontend` (np. `components/anna-embed-snippet.tsx` lub plik config).

2. **Utwórz `frontend/components/anna-embed-widget.tsx`** (`'use client'`):
   - Warunkowo renderuje **oficjalny widget** (nie nasz mock): wstrzykuje `<script>` CDN + `<elevenlabs-convai>` z `agent-id`, otwiera się na żądanie (event `open-anna-widget`).
   - Przekaż atrybuty jeśli w snippecie: identyfikator, signed-url/config.

3. **Podmień trigger** w `anna-widget.tsx`:
   - Na otwarcie (klik FAB lub `open-anna-widget`) renderuj **prawdziwy widget** zamiast mocku kroków (Język → Temat → Szczegóły). Usuń komunikat „Podgląd — bez realnego AI".
   - Można zostawić własną obudowę FAB/banera (anna-inline-banner.tsx), która otwiera embedowany widget.

4. **Auth/signed-url:** jeśli wersja nieudostępniona (public) wymaga signed — skonfiguruj backend do zwracania signed URL do widgeta (endpoint ElevenLabs), i przekazuj do `<elevenlabs-convai signed-url=...>`.

## DoD
- [ ] Oficjalny snippet widgetu poprawnie wstawiony (bez obcięcia).
- [ ] Klik Klik nie uruchamia mock, lecz prawdziwy widget rozmowy.
- [ ] Build przechodzi (pnpm build) — TS/Next nie błądzi.
- [ ] Dev: FAB otwiera i rozmawia z żywą Anną (głos lub tekst).

## Uwaga do F4 (deploy)
W staging/production widget może wymagać signed URL / publicznie aktywnego agenta; przygotuj w fazie F4 numer.

## Wynik
Żywy widget Anny zintegrowany na stronie.