# Phase K2 — Wgranie promptu i procedur na żywo (domknięcie warstwy agenta)

## Cel
Zlikwidować ostatnią różnicę między repozytorium a żywym agentem: wgrać na agenta prompt
z `docs/anna_system_prompt_v3.md` (stan 2026-11) i sprawić, żeby opublikowane procedury przekazywały
`appointment_datetime` — bez tego reguła „>2 h = bezpłatna anulacja” nigdy się nie uruchomi, mimo że
backend i schemat narzędzia już to obsługują.

**Stan wyjściowy (zmierzony 2026-11-09):** schematy narzędzi uzupełnione przez
`sync_agent_tools.py --ensure-schema` (cancel ma `appointment_datetime`, send_sms i handoff mają
`language`); baza wiedzy odświeżona (5 dokumentów, nowe ID w `.planning/AGENT_ID.txt`); hosted prompt
jest starszy niż plik w repo (repo: blok ~10,5 tys. znaków z sekcją anulowania/przełożenia).

## Zakres
- Żywy agent ElevenLabs: `conversation_config.agent.prompt.prompt` oraz 7 opublikowanych procedur.
- W repo: `.planning/AGENT_ID.txt` (stan warstwy live), ewentualnie `docs/anna_system_prompt_v3.md`
  jeśli test wykryje potrzebę skrócenia.

## Kroki
1. **Backup stanu live** (poza repo): `GET /v1/convai/agents/{id}` → zapisz `prompt.prompt` do pliku
   z datą; to jest rollback jednym PATCH-em.
2. **Wyciągnij blok promptu** z `docs/anna_system_prompt_v3.md` (treść między ogrodzeniem kodu, bez
   nagłówków dokumentu) i porównaj długość z wersją live (dziś: 9 558 vs ~10 521 znaków).
3. **PATCH promptu**: `{"conversation_config": {"agent": {"prompt": {"prompt": "<blok>"}}}}`.
4. **Procedury:** sprawdzić endpoint procedur (`GET /v1/convai/agents/{id}/procedures` albo panel),
   zaktualizować kroki anulowania i przełożenia tak, aby zbierały `appointment_datetime` (ISO z godziną)
   i przekazywały `language`; treść źródłowa w `.planning/workflow/procedures_7.md` i
   `docs/elevenlabs_agent_procedures.md`.
5. **Test na żywo — 3 scenariusze, transkrypty zapisać w `.planning/` (dowód):**
   - rezerwacja zabiegu (kontrola: „masaż” → Anna dopytuje, bo `ambiguous`),
   - anulowanie >2 h przed terminem → Anna mówi **0 %** i cytuje `fee_rule`,
   - anulowanie <2 h → 50 %; oraz eskalacja do recepcji (`transfer_to_simulated_handoff`).
6. Jeśli prompt po wgraniu daje rozwlekłe odpowiedzi: przenieść kroki rezerwacji SPA (Krok 1–10)
   do procedury i zostawić w promptcie jednozdaniowe odesłanie.

## Weryfikacja (DoD)
- [ ] `GET` promptu zwraca treść zgodną z plikiem w repo (porównanie długości i 3 markerów: „>2 h”,
      „appointment_datetime”, „ambiguous”).
- [ ] 3 transkrypty w `.planning/` (plik na scenariusz), każdy z dowodem: poprawna kwota, poprawny
      język komunikatu (`language: en` → angielska odpowiedź narzędzia).
- [ ] Backup promptu leży obok (rollback opisany jedną komendą w `.planning/AGENT_ID.txt`).
- [ ] `.planning/AGENT_ID.txt` nie zawiera już zdania „hosted prompt starszy niż repo”.

## Kluczowe / ryzyka
- To jedyna faza w epiku K, która **zmienia zachowanie produktu** — robić poza oknem prezentacji i
  zawsze z backupem promptu.
- Bez telefonii nadal nie ma `transfer_to_number`; handoff pozostaje symulowany (spójne z README).
- Procedury na żywo mogą nie mieć publicznego endpointu PATCH — wtedy zmiana idzie przez panel, a faza
  kończy się zapisem „wykonane ręcznie + dowód w transkrypcie”.

## Stan (2026-11-09)

Zrobione: prompt wgrany (10 520 znaków, sha256 `ce1e5166…` — zgodny z repo), 8 narzędzi / 7 `tool_id`,
5 plików KB, workflow bez zmian; backupy w `D:/Backups/`. Naprawiony realny defekt: procedura
`procedura_zmiany_terminu_zabiegu` wskazywała nieistniejący `tool_1601m0smvbqfaxaqppzcghdcpg8`
(brak `v`) — po PATCH+publish nowa wersja agenta `agtvrsn_4901m713bqdkedeb9f8vck1chb96`, 0 martwych
referencji w 7 procedurach (szczegóły w `.planning/AGENT_ID.txt`).

Otwarte: 3 testy symulacyjne (`POST /v1/convai/agents/{id}/run-tests`) tworzą się i startują, ale każdy
przebieg kończy się „Insufficient credits to run this simulation” — konto ma
`character_count = character_limit = 10000`, reset **2026-11-22 04:02 UTC**. Decyzja właściciela:
czekamy do resetu, więc DoD „3 transkrypty” pozostaje niezaznaczony do tego czasu.
