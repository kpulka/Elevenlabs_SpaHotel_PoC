# Phase F9 — Test E2E procedur / workflow (symulacja + live)

## Cel
Zweryfikować, że podpięte procedury (oraz ewentualny workflow) działają zgodnie z zamysłem i NIE wprowadziły regresji w podstawowym zachowaniu Anny. Używamy symulacji konwersacji i realnej interakcji.

## Zależności
- F8 (procedury/workflow aktywne na żywo).
- Backend + tunel (webhooki) uruchomione — jak w Phase 6.

## Krok 1 — Symulacje (`simulate_conversation` / ręczne)
- Kształt A: gość chce masaż → agent powinien przejść przez procedure `przeprowadz_rezerwacje_zabiegu_spa` (check → book → SMS).
- Kształt B: gość pyta o pokój → procedure `przeprowadz_zapytanie_o_pokoj`.
- Kształt C: gość negocjuje / zgłasza skargę → `decyzja_o_transferze` → `transfer_to_simulated_handoff`.

## Krok 2 — Weryfikacja wywołań
- Sprawdź w logach/odpowiedziach, że agent naprawdę wywołuje powiązane narzędzia (`check_spa_availability`, `book_spa_appointment`, `transfer_to_simulated_handoff`), a nie tylko "mówi".
- Zweryfikuj numery `confirmation_id`, odpowiedzi `available:true/false`.

## Krok 3 — Regresja
- Potwierdź BRAK regresji: grounding (nie wymyśla cen/terminów), głos Jessica, parametry akustyczne (turn 3.0/patient/speed 0.85), KB (5 plików) nadal działają.
- Test scenariusza RAG (poza procedurami): np. "Czy basen wymaga czepka?" — powinien odpowiedzieć z KB bez halucynacji.

## Krok 4 — (live) Test widget/frontend
- Jeśli dostępny: otworzyć widget (frontend na `localhost:3100`), sprowokować eskalację → potwierdzić log `🛎️ [HANDOFF]` w backendzie / alert Telegram.

## DoD
- Ścieżki A/B/C przechodzą z faktycznym wywoływaniem narzędzi.
- Brak regresji w grounding/głosie/parametrach/KB.
- (jeśli dotyczy) eskalacja → handoff potwierdzony realnym logiem.