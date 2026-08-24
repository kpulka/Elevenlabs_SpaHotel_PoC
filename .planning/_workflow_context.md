# Kontekst dla Phase I1+I2 — Mapowanie diagramu workflow na model ElevenLabs

## Cel
Zamienić diagram mermaid (docs/elevenlabs_agent_workflow.md) na projekt grafu workflow JSON zgodny z modelem ElevenLabs.

## Model ElevenLabs (zweryfikowane w OpenAPI — `.planning/_openapi.json`)
### Węzły (nodes):
- `start` — punkt wejścia (WorkflowStartNodeModel: {type:'start', position:{x,y}, edge_order:[]})
- `end` — zakończenie konwersacji (WorkflowEndNodeModel)
- `tool` — wykonuje 1+ narzędzi równolegle (WorkflowToolNodeModel: {type:'tool', tools:[{tool_id}], position, edge_order}). Node "successful" jeśli wszystkie tools OK.
- `phone_number` — transfer do numeru (WorkflowPhoneNumberNodeModel) — dla handoffu
- `override_agent` — subagent z własnym promptem/KB
- `standalone_agent` — transfer do innego agenta

### Krawędzie (edges): {source, target, forward_condition?, backward_condition?}
Warunki (condition):
- `unconditional` — zawsze true
- `llm` — {type:'llm', condition:'opis języka naturalnego', label?} — ewaluacja przez LLM
- `result` — {type:'result', successful:true|false, label?} — na bazie wyniku poprzedniego tool node
- `expression` — {type:'expression', expression: ASTNode, label?} — deterministyczne wyrażenie

Node ma `edge_order` (kolejność ewaluacji wychodzących krawędzi).

### Narzędzia agenta (tool_ids → nazwy):
- tool_4801m0ncs38tf8t93f45jfj992dt = check_spa_availability
- tool_6001m0ncs38vf73v1zbaa9p5vdfv = book_spa_appointment
- tool_6301m0ncs38wewt865sh99v1qkm8 = check_room_availability
- tool_8101m0ncs38xe6tb29923tjt9045 = send_sms_summary
- tool_6001m0ntyt8xefgsx1e8mcqnsw1n = transfer_to_simulated_handoff

## Diagram mermaid (skrót z docs/elevenlabs_agent_workflow.md)
START → GREETING → ROUTER (5 gałęzi: SPA / ROOMS / RAG / HANDOFF / EMERGENCY)
- SPA: IDENTIFY → guard (termalny?) → TAK: TRIAGE (medyczne pytanie) → (przeciwwskazanie → REJECT → lekarz/HANDOFF) | (bezpiecznie → DATE_TIME) → NIE: DATE_TIME → TOOL check_spa_availability → (brak slotów → propozycja → DATE_TIME) | (slotów → PROPOSE 2-3 opcje → COLLECT dane → PARAPHRASE → zgoda? → nie: DATE_TIME | tak: TOOL book_spa_appointment → TOOL send_sms_summary → SUCCESS)
- ROOMS: PARAMS → TOOL check_room_availability → (brak → propozycja → PARAMS) | (dostępny → PRICE_QUOTE → GUEST_DATA → TOOL send_sms_summary → SUCCESS)
- RAG: SEARCH → EVAL (jest? → ANSWER | nie → UNKNOWN → HANDOFF)
- HANDOFF: EMERGENCY → komunikat → TOOL transfer (dyżurka) | prośba → komunikat → TOOL transfer (recepcja)
- WRAP_UP: po SUCCESS/ANSWER → (tak → ROUTER | nie → GOODBYE → END)

## Zadanie podagenta (I1+I2)
1. Dla każdego elementu diagramu określ: node (`tool`/`phone_number`/`end`) czy warunek krawędzi (`llm`/`result`/`unconditional`) czy zostaje w prompcie agenta (mowa, triage — NIE w grafie).
2. Zaprojektuj graf workflow JSON (nodes + edges) odwzorowujący:
   - start → (agent główny mówi, robi router przez LLM — w prompcie) → tool node check_spa_availability / check_room_availability (rozgałęzienie przez warunki `llm` na krawędziach)
   - po toolu: `result` conditions (successful true/false) → next tool (book_spa / send_sms) lub end
   - handoff: `phone_number` node (transfer) z warunkiem `llm` ("gość prosi o człowieka / sytuacja awaryjna")
   - end node na zakończenie
3. Zwróć **kompletny JSON workflow_v1.json** gotowy do PATCH (tylko nodes+edges+prevent_subagent_loops). Użyj prostych, czytelnych ID węzłów (np. n_start, t_check_spa, t_book_spa, t_send_sms, t_check_room, p_handoff, n_end).
4. Odnotuj, które części diagramu NIE dają się odwzorować (mowa/triage/router — zostają w prompcie) i uzasadnij.

Odpowiedz po polsku. Zwróć: (a) tabelę mapowania (element diagramu → model), (b) pełny JSON workflow, (c) listę tego, co zostaje w prompcie.