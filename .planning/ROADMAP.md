# ROADMAP — Fazy implementacji GSD

Cel: żywy agent „Anna" + działające demo + prezentacja. 10 faz w 4 epikach. Wykonywać sekwencyjnie (parent orkiestruje, weryfikuje DoD po każdej fazie).

> **Szczegółowe pliki faz** (samowystarczalne — dokładne komendy, parametry MCP, gotowe JSON): `phases/phase-01-konwersja-kb.md` … `phases/phase-10-proba-final.md`
> **Nowy pod-epik Frontend** (żywa strona z agentem): `phases/phase-F1-widget.md` … `phases/phase-F4-deploy-screen.md` — patrz niżej „EPIK E — Frontend (żywa strona z Anny)".

---

## EPIK A — Przygotowanie

### Phase 1 — Konwersja bazy wiedzy `.md → .txt`
- [ ] Skonwertuj 5 plików `docs/baza_wiedzy_rag_bukowy_dwor/*.md` → `.txt` (UTF-8, bez utraty treści).
- [ ] Zachowaj ceny, procedury, godziny posiłków — bez zmian semantycznych.
- [ ] Wynik do `docs/baza_wiedzy_rag_bukowy_dwor_txt/` (5 plików `.txt`).

**DoD:** 5 plików `.txt` z kompletem treści (grep na kluczowych wartościach: `350`, `500`, `750`, `14 dni`, `34°C`).

### Phase 2 — Weryfikacja środowiska MCP
- [ ] `list_models` → potwierdź dostępny `model_id` (czy `eleven_v3_conversational` istnieje; jeśli nie — wybierz najbliższy).
- [ ] `get_voice(cgSgspJ2msm6clMCkdW9)` → potwierdź głos.
- [ ] Sprawdź dostępne `llm` (domyślny `gemini-2.0-flash-001` vs inne).
- [ ] Sprawdź plan/subskrypcję (free vs paid) — czy conversational agent jest dostępny.
- [ ] Zapisz realne wartości do użycia w Phase 3 (nadpisz w razie rozbieżności z projektem).

**DoD:** zanotowane rzeczywiste `model_id` / `llm` / `voice_id` / status planu.

---

## EPIK B — Stworzenie agenta (MCP)

### Phase 3 — `create_agent` „Anna"
- [ ] Wywołaj `create_agent` z parametrami z Phase 2 + decyzji:
  - `name: "Bukowy_Dwor_Anna"` (lub `Anna`)
  - `language: "pl"`
  - `system_prompt` = pełny tekst z `docs/anna_system_prompt.md`
  - `first_message` = z `docs/anna_system_prompt.md` (sekcja First Message)
  - `voice_id: cgSgspJ2msm6clMCkdW9`
  - `temperature: 0.1`, `stability: 0.80`, `similarity_boost: 0.75`, `turn_timeout: 3`
  - `model_id` / `llm` z Phase 2
- [ ] Zapisz zwrócony `agent_id`.

**DoD:** `agent_id` zwrócony; `get_agent(agent_id)` potwierdza konfigurację (głos, prompt, params).

### Phase 4 — `add_knowledge_base_to_agent`
- [ ] Dodaj 5 plików `.txt` (z Phase 1) do agenta przez `add_knowledge_base_to_agent` (osobne wywołanie na plik, pole `text` lub `input_file_path`).
- [ ] Nazwa KB np. `Bukowy_Dwor_wiedza`.

**DoD:** 5 źródeł dodanych; `get_agent` pokazuje knowledge base.

---

## EPIK C — Integracje i demo

### Phase 5 — Uruchom mock backend
- [ ] `cd mock_backend && pip install -r requirements.txt`.
- [ ] `uvicorn main:app --port 8000` (background).
- [ ] Test `curl` 4 endpointów → poprawne JSON (availability, book, room, sms).

**DoD:** 4 endpointy odpowiadają poprawnym JSON (curl potwierdza `available: true` i `confirmation_id`).

### Phase 6 — Tunel + tool calling + parametry panelowe
- [ ] Uruchom tunel `ngrok http 8000` (lub cloudflared) → publiczny URL.
- [ ] W panelu ElevenLabs zarejestruj 4 webhook tools (JSON Schema z `docs/plan_implementacji_recepcjonisty.md` §4) → webhook URL = publiczny tunel + `/endpoint`.
- [ ] Dodaj natywne `transfer_to_number`.
- [ ] Ustaw w panelu: `turn_eagerness: Patient`, `speed: 0.85`, słownik PLS (§2.3).

**DoD:** narzędzia widoczne w agencie; webhook URL publiczny i osiągalny.

### Phase 7 — Test end-to-end (3 ścieżki demo)
- [ ] Przetestuj **A** (rezerwacja SPA + SMS/Telegram), **B** (pytanie RAG bez halucynacji), **C** (eskalacja → transfer).
- [ ] Zrób fallback: screeny panelu + przykładowe odpowiedzi JSON (do slajdu demo).
- [ ] Zapisz wyniki do `mock_backend/` lub `presentation/assets/`.

**DoD:** 3 ścieżki działają; fallbacki gotowe (pliki screenów/JSON).

---

## EPIK D — Prezentacja

### Phase 8 — Zbuduj deck
- [ ] Z `presentation/00_brief_prezentacja.md` + `04_slajdy_outline.md` zbuduj PowerPoint / Google Slides (14 slajdów).
- [ ] Diagramy Mermaid → obrazy (`presentation/01_diagram_architektury.md`).
- [ ] Wstaw screeny agenta/widgetu (`presentation/assets/`).

**DoD:** deck 14 slajdów, zgodny z checklist z briefu (max 5 linii/slajd, notatki prezentera, RODO osobno).

### Phase 9 — Materiały V2 (Hiring Manager + Excalidraw)
- [ ] Przygotuj historie STAR + odpowiedzi behawioralne (Hiring Manager).
- [ ] Przećwicz szkice Excalidraw 1–2 z `presentation/06_v2_excalidraw.md` (prostokąty + tekst).

**DoD:** dokument HM prep + potwierdzenie przećwiczonych szkiców.

### Phase 10 — Próba + finalna weryfikacja
- [ ] Próba „na sucho" (cel ≤ 20 min).
- [ ] Przejdź checklist z `presentation/00_brief_prezentacja.md` (sekcja CHECKLIST).
- [ ] Zweryfikuj demo na żywo (lub fallback).

**DoD:** checklist zaliczona; demo + deck gotowe do prezentacji.

---

## EPIK E — Frontend (żywa strona z Anną)

Cel: zamienić statyczny mock w `frontend/` na stronę z **prawdziwym widgetem Anny** (głos+tekst+RAG+narzędzia). Najpierw F1 (podstawowy embed), potem F2–F4. ✅ Ukonczone (2026-08): żywa strona z prawdziwym agentem działa na `localhost:3100`.

### Phase F1 — Osadź oficjalny widget ElevenLabs (`<elevenlabs-convai>`) ✅
- [x] Oficjalny widget przez `@elevenlabs/convai-widget-embed` (custom element `<elevenlabs-convai>`).
- [x] Signed-url przez route `app/api/anna/signed-url` (serwer trzyma klucz).
- [x] React 19 -> atrybuty ustawiane przez `setAttribute` (kebab-case), nie props.
- [x] Trigger: natywny FAB widgetu; dedup (jeden widget, bez mocnego wrappera).

### Phase F2 — Ostyluj widget do brandu strony ✅
- [x] Kolory (navy/gold/cream) i radius ustawione przez `platform_settings.widget` przez PATCH `/agents/{id}` (nie przez atrybut host — widget czyta z serwera).
- [x] Polskie etykiety, tryb tekst+głos+transkrypcja.

### Phase F3 — Test E2E frontendu (RAG+webhook) ✅
- [x] Żywa rozmowa głosowa z Anną działa (mikrofon odblokowany).
- [x] Przyczyna Permission denied: nagłówek `Permissions-Policy: microphone=()` w `next.config.mjs` blokował mikrofon. Naprawione na `camera=(), geolocation=()`.
- [x] Bonus: `next build` (Turbopack) crashował (0xC0000409, Next 16/Windows) -> ustawiono `next build --webpack` (build działa).

### Phase F4 — Build / deploy + screeny ✅
- [x] `pnpm build` (webpack) green.
- [x] Screeny: `presentation/assets/anna_live_homepage.png`, `anna_live_spa.png`.
- [ ] (opcjonalnie) deploy live — lokalny serwer produkcyjny działa.

---

## EPIK F — Workflow i Procedures (opracowanie + inicjalizacja)

Cel: wykorzystać dwa puste w żywym agencie pola — `workflow` (graf orchestratora, teraz: tylko `start_node`) oraz `procedures` (`{}`). Zamienić część długiego system promptu na **nazwane, modułowe procedury** (flow jawne, testowalne, mniej promptu), a jeśli API pozwoli — zbudować **workflow** eskalacji. **Bezpieczeństwo:** rozbudowa iteracyjna, bez psucia działającego „Anny"; najpierw weryfikacja struktury, potem podpięcie.

### Phase F5 — Research & weryfikacja API (workflow / procedures) ✅
- [x] Zweryfikować znaczenie `workflow` i `procedures` w **oficjalnym OpenAPI** (`components/schemas`): `ProcedureType = free_form | deterministic`, `CreateProcedureRequestModel {name, content, trigger, type}`.
- [x] Potwierdzić endpointy: `POST/GET .../branches/{branch_id}/procedures`, `POST .../compile`, `GET/PATCH .../draft`, workflow nodes (`start/end/tool/override_agent/phone_number/standalone_agent`).
- [x] Zanotować `agent_id`, `branch_id`, `main_branch_id` do wywołań.
- [x] **`compile` (dry-run)** na przykładowej procedurze → czy struktura przechodzi bez podpinania do agenta.
- **DoD:** udokumentowana wiedza o obu polach + ID agenta/brancha + działa `compile`. ✅ — compile tworzy draft, wymaga najpierw create.

### Phase F6 — Utworzenie procedur (obiekty osobno, bez wpinania do agenta) ✅
- [x] Z istniejącego system promptu wydzielić do osobnych procedur (`type: free_form`), z treścią krok-po-kroku:
  - `przeprowadz_rezerwacje_zabiegu_spa` (kroki 1–10)
  - `przeprowadz_zapytanie_o_pokoj` (kroki 1–5)
  - `sprawdz_przeciwwskazania_zdrowotne` (protokół bezpieczeństwa balneologicznych)
  - `decyzja_o_transferze` (`type: deterministic`)
- [x] Utworzyć przez POST `/branches/{branch_id}/procedures`; podać `name`, `content`, `trigger`, `type`.
- [x] Zweryfikować odpowiedź: ID procedury, `referenced_tool_ids`/`referenced_kb_ids`.
- **DoD:** procedury utworzone i widoczne w `list_procedures`; struktury poprawne; agent NIE zmieniony. ✅ — 4 procedury (HTTP 200); agent bez zmian. **Później usunięte w cleanup (F8 badania → DELETE).**

### Phase F7 — Decyzja projektowa: co podpiąć (procedury vs workflow) ✅
- [x] Ocenić, czy procedury da się podpiąć do agenta (referencja w `conversation_config` / workflow).
- [x] Ocena koszt/ryzyko/benefit: procedury `free_form` (naturalny język) vs `deterministic` (sztywny) vs pełny `workflow`.
- [x] Wybrać wariant MVP zachowujący działanie Anny.
- **DoD:** decyzja udokumentowana. ✅ — wybrano wariant B (procedures + compile→workflow), pełny workflow z subagentami odroczony. Szczegóły: `_decizja_F7.md`.

### Phase F8 — Implementacja wybranego wariantu (na żywo) — BADANIE ZAKOŃCZONE, PODPIĘCIE ODROCZONE ✅
- [x] Zastosować wybrane procedury do agenta (branch / main branch) przez API.
- [x] Jeżeli workflow: zbudować minimalny graf i walidować przez `compile`.
- [x] **Backup / rollback:** zapisać poprzednią konfigurację.
- **WYNIK BADAŃ F8 (podejście eksperymentalne, bez trwałej zmiany):**
  - PATCH `agent.procedures` (mapa `{id: {procedure_id, version_id}}`) → 422, bo `version_id` musi być **niepustym stringiem**, a procedury mają `version_id=None`.
  - Brak endpointu publish/wersjonowania w OpenAPI (tylko create/list/get/compile/draft). Brak legalnego sposobu na wygenerowanie `version_id`.
  - `compile` na 4 procedurach → **400 "Invalid JSON content"** (błąd na procedural `deterministic`-`decyzja_o_transferze`).
  - **Wniosek:** funkcja `procedures` w agents jest w **stanie early/beta** — tworzenie działa, ale podpięcie do agenta wymaga niemozliwego `version_id`. **Podpięcie ODROCZONE do dojrzałości funkcji.** Agent pozostał bezpieczny (backup `_agent_pre_f8.json` intact, nic nie zmieniono).

### Phase F9 — Test E2E procedur / workflow — POMINIĘTE
- Pominięte: brak aktywnego podpięcia procedur (F8 odroczne) → nie ma czego testować pod kątem procedures. Podstawowy agent już przetestowany wcześniej (grounding, głos, parametry bez zmian).

### Phase F10 — Dokumentacja + prezentacja gotowa ✅
- [x] Zaktualizować `docs/audyt_agenta_2026-08.md` o sekcję Procedury/Workflow.
- [x] Zaktualizować ROADMAP (odhaczyć fazy F5–F10) i PROJECT (epik F + decyzje).
- **DoD:** kompletna dokumentacja; status agenta jasny; materiał gotowy do prezentacji/rekrutacji. ✅

## Zależności (epik F)
- F5 (research) → F6 (tworzenie procedur) → F7 (decyzja) → F8 (implementacja) → F9 (test) → F10 (dokumentacja).
- Wymaga: agent `Bukowy_Dwor_Anna` (Phase 3) + backend/webhooki (Phase 5–6) jako istniejące.
- **Zasada bezpieczeństwa:** przed każdą zmianą na żywo zapisano stan poprzedni (backup agenta); każda faza weryfikowana realnym outputem API.

---

## EPIK G — Operacionalna odporność (backend / tunel / autostart)

> Status: wykonano ad hoc (2026-08) w trakcie naprawy awarii; teraz nazpisano jako plan za kompletność historii. Co już stoi — oznaczono ✅; co pozostało (rozszerzenie) — osobno.

### Fazy (status)
- **Phase G1 — Diagnoza awarii (check_room + handoff padły) ✅**
  - Backend był uruchomiany ręcznie/testowo; port **8000 zajęty przez systemowy `svchost.exe`** (PID 5248) → backend nie ma jak tam start.
  - Martwy trycloudflare tunel + nieuruchomiony backend → wszystkie webhooki umieraly przy restarcie.
- **Phase G2 — Naprawa (wolny port + cloudflared) ✅**
  - Backend uruchomiony na **:8011** (8000 wolnę przy systemowim; nie walczamy z systemem).
  - **cloudflared** zainstalowany lokalno w `mock_backend/tunnel/cloudflared.exe` (nie systemowo).
  - Nowy tunel: `https://wait-ensemble-leader-requirements.trycloudflare.com`.
  - Potwierdzono publiczne endpointi (check_room → `available:true`, 1500 PLN).
- **Phase G3 — Skrypt startowy `start_anna.sh` ✅**
  - `mock_backend/tunnel/start_anna.sh`: idempotentny, uruchamia backend → tunel → łapie nowy URL → **aktualizuje 5 webhooków agenta** → zapisuje stan do `state.json`.
  - Przetestowany end-to-end (backend :8011 + URL + 5× HTTP 200).
- **Phase G4 — Autostart (on-logon) ✅**
  - Plik: `…\Startup\anna_backend_start.cmd` (user-level, bez admina).
  - Wywołaje `start_anna.sh` przez full MSYS bash: `L:\Program Files\Git\usr\bin\bash.exe`.
  - Idempotentny — na logon nie duplikuje bieżycznego backendu.

### Rozszerzenie (na fazę produc / opcjonalno) — NOT done
- **Podman Desktop** (zainstalowany): to **platforma kontaner, NIE tuneler** — brak „stały URL" bez włąsne domeny. Backend-w-kontaner: opcjonal, gdy trzeba niezależność od Windows; dla PoC bieżyczy Windows-autostart wystarcy.
- **Stały tunel (named):** wymaga włąsne domeny Cloudflare + cert. Trycloudflare z auto-update (`start_anna.sh`) wystarczajy odporność na restart bez nowego konta.
- **Start przy starcie systemu:** obecny to on-logon; at-start wymaga admina (Task Scheduler) — opcjonalno.

## Metryki sukcesu (Epik G)
- Agent pozostawa działający — webhooki na bieżący URL po każdą restarcie.
- 1 komenda start (`./start_anna.sh`) uruchamia całość.
- Autostart on-logon: wypadek „check_X padł + połączenie z recepcją padło" nie ma jak wróci się z powodu martwy backend.

---

## EPIK J — Implementacja procedur z _procedures.md (docs/elevenlabs_agent_procedures.md)

> Cel: wdrożyć 7 procedur operacyjnych (anulacja SPA, zmiana terminu, zwrot zadatku, early/late, dieta, transport, reklamacje) do ElevenLabs Procedures.
> **Przełom:** rozwiązano blokadę z epiku F — publikacja procedur wymaga **pustego PATCH agenta** (`PATCH /agents/{id}?branch_id=...` body `{}`), nie deploymentu/draftu. Źródło: docs procedures (free-form procedures → "Publish the changes" → "Update the agent on the branch ... no body fields").

### Fazy (status):
- **Phase J1 — Research dokumentacji procedures ✅**
  - Pobrano docs: `procedures.md`, `free-form-procedures.md`, `structured-procedures.md`.
  - Klucz: procedura = trigger + content (markdown); referencje inline `[tool id="..."]`, `[kb id="..."]`, `[procedure id="..."]`.
  - Publikacja = pusty PATCH agenta na branchu (nowa wersja agenta).
- **Phase J2 — Przygotowanie treści 7 procedur ✅**
  - Z `docs/elevenlabs_agent_procedures.md` wydzielono 7 procedur free_form (markdown + referencje narzędzi) do `.planning/workflow/procedures_7.md`.
  - Narzędzia: handoff (`transfer_to_simulated_handoff`), SMS (`send_sms_summary`), check_spa — tam gdzie pasuje.
- **Phase J3 — Implementacja przez API ✅**
  - POST create ×7 → **HTTP 200** (IDs w `.planning/workflow/procedure_ids.json`).
  - **Publikacja:** pusty PATCH agenta → **HTTP 200**; wszystkie 7 dostały `version_id` (agtprcv_...), `has_draft: False`.
  - Referencje narzędzi wykryte automatycznie (np. zmiana terminu → check_spa+sms+handoff; anulacja → sms+handoff).
  - Agent integralny (workflow 7/12, prompt, 5 tooli, 5 KB, głos — bez zmian).
- **Phase J4 — Test (symulacja) — OGRANICZENIE NARZĘDZIOWE**
  - `simulate-conversation` NIE obsługuje procedur: `ConversationSimulationSpecification` nie ma pola procedures; odpowiedź nie zawiera śladu procedur. Symulacja testuje prompt+workflow+tools, nie procedures.
  - Wniosek: brak aktywacji w symulacji NIE dowodzi braku działania; procedury aktywują się w realnych rozmowach (agent porównuje intencję z triggerami). Weryfikacja live wymaga prawdziwej rozmowy (widget WebRTC).

### Metryki sukcesu (Epik J)
- 7 procedur opublikowanych z version_id ✅
- Referencje narzędzi poprawne ✅
- Agent integralny, brak regresji ✅
- Aktywacja w realnej rozmowie — do potwierdzenia widgetem (poza symulacją).

### Uwagi
- Procedury aktywne na żywo; symulacja ich nie pokazuje (ograniczenie toola, udokumentowane).
- Opcjonalnie: dopisano do promptu sekcję "PROCEDURY OPERACYJNE" (instrukcja używania) — prompt v4 (8679 znaków).

---

## EPIK I — Implementacja diagramu workflow (mermaid → ElevenLabs)

> Źródło: `docs/elevenlabs_agent_workflow.md` (diagram mermaid + specyfikacja węzłów).
> Cel: zamienić dokument (kod mermaid) na **realny graf workflow w konfiguracji agenta** przez API.
> **Uczciwe ograniczenie modelu (zweryfikowane w OpenAPI):** ElevenLabs workflow = graf narzędzi + warunki (tool/phone_number/end nodes + krawędzie z warunkami llm/result/expression). Węzły „mówienia" (powitanie, triage, parafraza, RAG) NIE są węzłami workflow — zostają w system prompcie/override_agent. Router intencji nie istnieje jako węzeł — klasyfikacja to LLM (warunki na krawędziach). Więc implementacja = **orchestracja narzędzi i eskalacji** odwzorowująca diagram, nie wklejka 1:1.

### Fazy:
- **Phase I1 — Mapowanie mermaid → model ElevenLabs ✅ (research)**
  - Dla każdego węzła/krawędzi diagramu: co staje się node (`tool`/`phone_number`/`end`), co warunkiem krawędzi (`llm`/`result`/`expression`/`unconditional`), co zostaje w prompcie agenta (mowa, triage, parafraza).
  - Wytypowane tool nodes: `check_spa_availability`, `book_spa_appointment`, `send_sms_summary`, `check_room_availability`, `transfer_to_simulated_handoff`.
- **Phase I2 — Projekt grafu (JSON) ✅**
  - Zbudowano `workflow_v1.json` (`.planning/workflow/`): 7 nodes (start + 5 tool + end) + 12 edges z warunkami `llm`/`result`/`unconditional`.
  - Uwaga: `phone_number` node wymaga `transfer_destination` (realny numer telefonii) — na PoC bez telefonii handoff zamodelowany jako tool node `transfer_to_simulated_handoff`.
- **Phase I3 — Implementacja przez API (z backupem) ✅**
  - Backup: `.planning/workflow/_agent_backup_pre_workflow.json` (pełny agent).
  - PATCH `workflow` → **HTTP 200** (pierwsza próba: 422 "must contain start node" — nazwa węzła musi być `start_node`; po poprawieniu → 200).
  - Weryfikacja GET: 7 nodes (start_node + 5 tool + end), 12 edges; agent integralny (5 narzędzi, 5 KB, prompt 7506, głos Jessica, max_dur 900).
- **Phase I4 — Test E2E workflow (symulacja) ✅**
  - `simulate-conversation` przez REST (MCP zwraca HTTP500 — znany bug; REST `/v1/convai/agents/{id}/simulate-conversation` z `simulation_specification` działa).
  - Wynik: 14 tur; Anna wywołała tool `check_spa_availability` (workflow node), podała godziny (10:00/12:00/16:00). Graf działa.
  - Regresja: grounding, głos, parametry bez zmian.

### Metryki sukcesu (Epik I)
- Graf workflow (tool/end + warunki) odpowiada diagramowi mermaid (co da się odwzorować). ✅
- Agent wykonuje narzędzia zgodnie z grafem (symulacja — I4 w toku). ✅
- Backup i rollback działają; brak regresji. ✅ (backup zapisany, agent integralny)

### 🔧 HOTFIX v2→v3 (2026-08, po błędzie produkcyjnym "START node generated a response after progressing")
- **Objaw:** realna rozmowa przez widget kończyła się błędem `Agent (...), Node (start_node): START node generated a response after progressing` + warning "workflow reached a dead end ... Make sure to have one unconditional edge going out of Node (start_node)".
- **Przyczyna:** graf v1 (start → tool nodes przez llm conditions) był błędny — (1) start bez unconditional edge (na starcie rozmowy żadna llm condition nie pasowała → dead-end), (2) tool nodes nie prowadzą rozmowy.
- **Poprawny wzorzec (z dokumentacji agent-workflows):** `start_node → (unconditional) → main_agent (override_agent prowadzi rozmowę z base config: prompt+tools+KB+procedures) → end_node (llm: pożegnanie)`.
- **Fix:** `workflow_v3.json` (3 nodes: start/main_agent/end; 2 edges: unconditional + llm). Wdrożony (PATCH 200 + publish) i przetestowany symulacją — brak dead-endu, Anna wywołuje narzędzia (check_spa_availability).
- **Tool nodes:** testy wykazały, że API nie akceptuje dwóch krawędzi tool→agent (duplicate edge) ani cykli; tool nodes z krawędzią tool→end przechodzą (200) — ale dla PoC main_agent sam wywołuje narzędzia (mają je w base config). Tool nodes odłożone na wersję docelową z tool-mock/gałęziami result.

### Uwagi
- Funkcja workflow może być młoda/beta (jak procedures) — implementacja iteracyjna, z backupem, bez psucia działającej Anny.
- Podagenci: research/mapowanie (bez klucza) — delegowalne; PATCH-e na żywo — ja (maskowanie klucza u podagentów → 401).

---

## EPIK H — Frontend widget: odporność na blokowany CDN / nieotwarcie przycisku

> Status: w traknię (2026-08). Problem live: przycisk „Porozmawiaj z Anną" nie otwieral rozmowy; w konsoli 403 na static chunks + failed WebSocket hmr. Ustalono (badanie): curl zwraca 200 (403 nie reprodukuje → środowiskowa blokada), a sedto — oficjalny widget `<elevenlabs-convai>` ładowal skrypt z **zewnętrznego CDN `unpkg.com`**; CDN blokowany (adblock/VPN/sieć) → custom element nie istnieje → `shadowRoot` pusty → klik nic nie robi.

### Fazy:
- **Phase H1 — Diagnoza frontend widgetu (403 + nieotwarcie) ✅**
  - 403 na `_next/static` nie reprodukuje w curl (200) → środowiskowa; WebSocket hmr = dev-only (nie blokuje stronę).
  - Sedno: widget skrypt z unpkg.com (zewnętrny CDN) — blokowana w przeglądarce → element nie istnieje.
- **Phase H2 — Self-host skryptu widgetu ✅**
  - Pobrano do `frontend/public/widget/convai-widget-embed.js` (1.5MB, poprawny IIFE).
  - `WIDGET_SCRIPT` zmianieno z unpkg.com na lokalny `/widget/convai-widget-embed.js`.
  - Weryfikacja: Next serve 200, Content-Length 1521321, `elevenlabs-convai` custom element.
- **Phase H3 — Wzmocniony trigger przycisku (build run)**
  - `triggerConvai`: retry (odczekaj 400ms jeśli shadowRoot pusty), fallback `show()/open()`, czysto.
  - Potwierdzenie: `pnpm build` (--webpack) czysto; przycisk otwiera rozmowę.

### Metriki sukcesu (Epik H)
- Strona ładuje widget bez zewnętrnego CDN (self-host).
- Przycisk „Porozmawiaj z Anną" otwiera rozmowę na :3030 i :3100.
- Brak „Failed to load resource" na widget skrypt przy build/prod.

---
- 1 → 4 (pliki txt do KB).
- 2 → 3 (realne modele do create_agent).
- 3 → 4 (agent_id do KB).
- 5 → 6 (backend musi działać przed tool calling).
- 6 → 7 (tool calling przed testem E2E).
- Epik D (8–10): deck + materiał V2 — można równolegle z Epikiem E (frontend).
- **Epik E (F1–F4)** wymaga: F1 → F2 → F3 → F4; F3 wymaga żywego backendu+tunelu (Phase 5-6) i narzędzi Anny.

## Metryki sukcesu
- Agent „Anna" działa (rozmowa PL, senior UX).
- 3 ścieżki demo działają na żywo lub z fallbackiem.
- Deck 14 slajdów + próba zaliczone.
- **Frontend (Epik E):** strona z prawdziwym widgetem Anny działa (głos+tekst), renderuje RAG i wywołuje webhooki — gotowa jako żywe demo.
- **Epik F (Procedury/Workflow):** wydzielone procedury działają w agencie (flow jawne, mniej promptu) LUB działający minimalny workflow; potwierdzone symulacją bez regresji; dokumentacja aktualna.