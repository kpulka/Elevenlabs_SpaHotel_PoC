# .planning/ — ślad pracy GSD (Get Shit Done)

Ten katalog **nie jest dokumentacją produktu** (ta żyje w `docs/`, punkt wejścia: `docs/INDEX.md`). To warsztat: plan, fazy, artefakty wdrożenia i dowody, że coś zostało zrobione.

- **`HANDOFF.md`** — punkt startowy dla nowego agenta/osoby: stan faktyczny z liczbami, otwarte decyzje, zasady pracy, pułapki i gotowy prompt do realizacji EPIK-u K.
- `PROJECT.md` — kontekst i zasady projektu: co budujemy, jakie decyzje zapadły, czego nie robimy.
- `ROADMAP.md` — fazy i epiki (A–K) z kryteriami DoD. Nadrzędny plan wykonania.
- `phases/` — po jednym pliku na fazę: samowystarczalny brief z komendami, parametrami MCP i gotowymi JSON-ami. To zapis historyczny — nie aktualizujemy treści, tylko odwołania do plików.
- `workflow/` — faktyczny stan wysłany do ElevenLabs: `workflow_v1/v2/v3.json` (kolejne iteracje grafu), `procedure_ids.json` (7 procedur z ID z API), `procedures_7.md` (treść procedur w formacie API), `new_tools.json`.
- `AGENT_ID.txt` — realne parametry żywego agenta (`agent_8401m0n03cggfgebhfh0cj96t7aj`): głos, LLM, TTS.
- `_workflow_context.md`, `workflow_v1.json` — kontekst i pierwszy graf workflow.

Status faz oceniam po tym, czy **artefakt istnieje w repo** — nie po checkboxach w `ROADMAP.md` (te zostały odhaczone nierówno). `?` = brak dowodu w repo, nie znaczy „nie zrobione".

| Faza | Epik | Status | Dowód |
|---|---|---|---|
| phase-01 konwersja KB | A Przygotowanie | done | `docs/baza_wiedzy_rag_bukowy_dwor_txt/` — 5 plików |
| phase-02 weryfikacja MCP | A Przygotowanie | done | `AGENT_ID.txt` z realnym voice/LLM/TTS |
| phase-03 create agent | B Agent | done | `AGENT_ID.txt` (agent istnieje w API) |
| phase-04 add KB | B Agent | done | `deploy_kb_and_tools.py` + pliki `.txt` |
| phase-05 mock backend | C Backend | done | `mock_backend/` (FastAPI, testy, `main.py`) |
| phase-06 tool calling | C Backend | done | ID narzędzi w `workflow/procedures_7.md` |
| phase-07 test E2E | C Backend | done | `docs/audyt_agenta_2026-08.md` — wyniki realnych rozmów |
| phase-08 deck | D Prezentacja | done | `presentation/Bukowy_Dwor_Case_Study.pptx` + `.html` |
| phase-09 materiały V2 | D Prezentacja | done | `presentation/05_*`, `06_*`, `09_*` |
| phase-10 próba finalna | D Prezentacja | ? | brak zapisu przebiegu |
| phase-F1 widget | E/F Frontend | done | `frontend/components/anna-embed-widget.tsx` |
| phase-F2 styling | E/F Frontend | done | styling w `anna-embed-widget.tsx` |
| phase-F3 test E2E frontendu | E/F Frontend | ? | brak logu testu na żywo |
| phase-F4 deploy screen | E/F Frontend | ? | brak artefaktu deploya w repo |
| phase-F5 research workflow/procedures | F Procedury | done | `workflow/workflow_v1.json`, `workflow_v2.json` |
| phase-F6 create procedures | F Procedury | done | `workflow/procedure_ids.json` — 7 procedur z ID |
| phase-F7 decyzja procedury vs workflow | F Procedury | done | oba wdrożone: `procedure_ids.json` + `workflow_v3.json` |
| phase-F8 implementacja | F Procedury | done | `workflow/workflow_v3.json` |
| phase-F9 test E2E procedur | F Procedury | ? | brak logu symulacji/live |
| phase-F10 dokumentacja | F Procedury | done | porządki dokumentacji 2026-11 (`docs/INDEX.md`) |
| phase-G1 diagnoza awarii | G Stabilizacja | done | opis w pliku fazy (webhooki nieaktywne) |
| phase-G2 naprawa port/tunel | G Stabilizacja | done | `mock_backend/tunnel/podman_start.sh` (port 8011; `state.json` jest lokalny, poza repo) |
| phase-G3 skrypt startowy | G Stabilizacja | done | `mock_backend/tunnel/start_anna.sh` |
| phase-G4 autostart | G Stabilizacja | done | `mock_backend/tunnel/start_anna.sh` (log autostartu jest lokalny, poza repo) |
| phase-H1/H2/H3 widget frontend | H Naprawa widgetu | done | `frontend/public/widget/convai-widget-embed.js` (self-host) |
| phase-I/J workflow + procedures | I/J Wdrożenie | done | `workflow/workflow_v3.json` + `procedure_ids.json` |
| phase-K1 historia gita | K Portfolio | done (2026-11-09) | `.git` 64 MB → **31 MB**, `size-pack` **30,57 MiB**; blob `cloudflared.exe` (52,35 MiB) i stara wersja decku (8,94 MiB) usunięte z historii; HEAD tree identyczny (`2f184d8`); świeży klon 31 MB / 0 trafień `cloudflared` / 68 testów; backup `D:/Backups/spahotels-pre-filter-2026-11-09.bundle`; tag `archive/english-wip-2026-11-04`, gałąź `claude/*` usunięta. **DoD „<6 MB” odrzucone jako nieosiągalne** (bieżące drzewo = 34,18 MiB) |
| phase-K2 prompt live | K Portfolio | todo | cel: hosted prompt = `docs/anna_system_prompt_v3.md` + procedury z `appointment_datetime` |
| phase-K3 deck | K Portfolio | todo | cel: oba PPTX po korekcie faktów (7 narzędzi, 8011) |
| phase-K4 higiena repo | K Portfolio | todo | cel: jedna gałąź, tag `v1.0.0`, homepage, martwe klucze i18n |
| phase-K5 demo online | K Portfolio | todo | cel: publiczny link (Vercel + Fly/Render) albo jawny fallback |
