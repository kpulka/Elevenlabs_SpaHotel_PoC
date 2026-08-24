# Phase F3 — Test E2E frontendu z żywą Anną (webhook + RAG)

## Cel
Potwierdzić że widget na stronie naprawdę rozmawia z Anną, używa RAG i wywołuje narzędzia w webhook (mock backend).

## Zależności
F1 + F2; mock backend i tunel działają; tool-calling Anny skonfigurowany.

## Kroki
1. Upewnij się, że backend (`mock_backend`) i tunel cloudflared żyją (jak w Phase 5/6). Aktualna URL tunelu → sprawdź że narzędzia Anny wskazują na żywy URL (patrz Phase 6 — quick-tunnel może zmienić URL).
2. `pnpm dev` — uruchom frontend lokalnie.
3. W przeglądarce (lub browser exec) otwórz stronę, kliknij „Porozmawiaj z Anną", przeprowadź **ścieżkę B** (RAG: „O której kolacja?") → Anna odpowiada z bazy (17:30–19:30).
4. Przeprowadź **ścieżkę A** (rezerwacja SPA): Anna ma wywołać `check_spa_availability`/`book_spa_appointment`/`send_sms_summary` przez tunel → logi backendu pokazują wywołania.
5. Sprawdź bez halucynacji: pytanie poza KB → Strict Grounding (`transfer_to_human`).

## DoD
- [ ] W widget na stronie rozmowa na żywo działa (głos lub tekst).
- [ ] Ścieżka RAG (kolacja) odpowiada z bazy.
- [ ] Rezerwacja SPA wykonuje webhooki (logi backend/JSON).
- [ ] Brak halucynacji (grounding).

## Wynik
Frontend + backend + ElevenLabs zintegrowane end-to-end.