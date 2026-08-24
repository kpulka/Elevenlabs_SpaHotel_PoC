# Phase F4 — Deploy / podgląd i finalna weryfikacja frontendu

## Cel
Ostateczna weryfikacja całości (strona + agent) i przygotowanie do podglądu/prezentacji.

## Zależności
F3 (test e2e ok).

## Kroki
1. `pnpm build` + `pnpm start` w `frontend/` (tryb production) — potwierdź że działa maksymalnie (bez dev-only whitespace).
2. Publikacja (opcjonalnie, jeśli chcesz pokazać link): np. `vercel`/`netlify` albo local host; embed potrzebuje który URL.
   - Uwaga: webhook backend musi być publiczny (tunel) — jeśli odwiedziny z innego urządzenia.
3. Głęboka weryfikacja: złap screeny (hero, spa, pokoje, widget otwarty rozmowy), zapisz w `presentation/assets/` dla decku.
4. Przećwicz demo 3 ścieżek na żywo na gotowej stronie.

## DoD
- [ ] `pnpm build` green.
- [ ] Strona + agent prezentuje/la (lokalnie lub zdalnie).
- [ ] Screeny (hero + widget rozmowa) zapisane w `presentation/assets/`.
- [ ] 3 ścieżki przećwiczone na żywo na stronie.

## Wynik
Frontend gotowy jako żywe demo dla V1/V2. (To odpowiada „żywej strony" zamiast statycznego decku.)