# Phase 7 — Test end-to-end (3 ścieżki demo)

## Cel
Potwierdzić, że agent „Anna" obsługuje 3 ścieżki demo na żywo, i zebrać fallbacki do slajdów.

## Zależności
Phase 6 (tool calling + tunel) + Phase 4 (KB).

## Krok 1 — Ścieżka A: Rezerwacja SPA + SMS
Test rozmowy (widget lub telefon):
1. Gość: „Poproszę masaż na kręgosłup."
2. Anna pyta o datę (jeden question naraz) → wywołuje `check_spa_availability`.
3. Anna podaje dostępne godziny → pyta która.
4. Gość wybiera → Anna pyta o imię i nazwisko.
5. Anna **parafrazuje** ustalenia przed potwierdzeniem.
6. Anna wywołuje `book_spa_appointment` → potwierdza.
7. Anna pyta o numer telefonu (wspomina opcję „do córki/syna").
8. Anna wywołuje `send_sms_summary` → potwierdza.

**Check:** backend loguje `check_spa_availability` + `book_spa_appointment` + `send_sms_summary`.

## Krok 2 — Ścieżka B: Pytanie informacyjne (RAG)
- „O której jest kolacja?" → Anna odpowiada z KB (17:30–19:30).
- „Czy basen wymaga czepka?" / „Ile kosztuje pokój?" → odpowiada TYLKO z KB, nie zmyśla.
- Test halucynacji: zapytaj o coś spoza KB (np. „gdzie jest najbliższa apteka nocą?") → Anna powinna odmówić i wywołać `transfer_to_human`.

## Krok 3 — Ścieżka C: Eskalacja (transfer)
- Gość: „Miałem zawał 3 miesiące temu, czy mogę na kąpiel siarczkową?" → Anna rozpoznaje przeciwwskazanie → `transfer_to_human` → „Łączę z dyżurką medyczną..."

## Krok 4 — Fallbacki (do slajdu demo)
Zbierz i zapisz w `presentation/assets/` lub `mock_backend/`:
- [ ] Screeny panelu (tools, system prompt, knowledge base).
- [ ] Przykładowe odpowiedzi JSON (curl dla 4 endpointów).
- [ ] Zrzut logów backendu (widoczne wywołania narzędzi).

## DoD
- [ ] Ścieżka A działa end-to-end (booking + SMS/Telegram).
- [ ] Ścieżka B: poprawne odpowiedzi z RAG + brak halucynacji (transfer gdy brak info).
- [ ] Ścieżka C: transfer na przeciwwskazanie działa.
- [ ] Fallbacki zapisane (screeny + JSON).

## Wynik przekazany do Phase 8
Działające demo + pliki fallbackowe (screeny/JSON) do wstawienia w deck.