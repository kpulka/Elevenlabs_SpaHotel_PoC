# Phase H3 — Wzmocniony trigger przycisku (+ build weryfikacja)

## Cel
Żeby przycisk „Porozmawiaj z Anną" otwieral rozmowę odpornie — nawet jeśli custom element jeszcze się hydratowuje przy kliku.

## Zmienna w `anna-embed-widget.tsx` (`triggerConvai`)
- Odpornie: 
  - ffallback natywnego API (`show()/open()`) przed shadow-root klik;
  - shadow_root button direkt;
  - **retry** — jeśli `host.shadowRoot` pusty (custom element nie gotowy), `setTimeout(attempt, 400ms)` ponowny prób;
  - czysti, bez zależności od `window.customElements` (nie-standard global).
- Solis: if `host` nie gotowy → warn (element nie zarejestrowany — problem w skrypt ładowания, patrz H2).

## Potwierdzenie: build
```bash
cd frontend && pnpm build     # (--webpack w phase; tu pnpm build clean)
# ✓ Compiled successfully in ~20s, 9 routes prerendered
```

## DoD
- `triggerConvai` odporna (retry gdy shadowRoot pusty; fallback show/open; czysto).
- Build czysto; na :3030 przycisk otwiera rozmowu.
- Brak blokowy z CDN (self-host H2).

## Uwaga
- Przycisk wołody normal slate; ewentualno dodać stale jsdelivr fallback w WIDGET_SCRIPT array, jeśli self-host straci se w jakuch environ: późniś. Done.