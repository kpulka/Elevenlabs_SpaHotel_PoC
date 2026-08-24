# GSD Project — Wirtualny Recepcjonista AI „Anna" (ElevenLabs Case Study)

> Framework GSD (Get Shit Done). Ten plik = kontekst i reguły. Plan faz w `ROADMAP.md`.

## Cel
Dokonać wdrożenia żywego agenta „Anna" w ElevenLabs (PoC → wizja docelowa) oraz zbudować prezentację na rekrutację (Deployment Strategist, etapy V1 + V2).

## Punkt startowy (co już jest)
- ✅ Dokumentacja ujednolicona: `docs/specyfikacja_recepcjonista_ai.md` (CO), `docs/plan_implementacji_recepcjonisty.md` (JAK), `docs/anna_system_prompt.md` (prompt).
- ✅ Baza wiedzy RAG: 5 plików `.md` (`docs/baza_wiedzy_rag_bukowy_dwor/`).
- ✅ Mock backend: `mock_backend/` (FastAPI, 4 endpointy webhook + dane).
- ✅ Materiały prezentacyjne: `presentation/` (brief, outline 14 slajdów, diagramy, narracja, V2).
- ❌ Brak: żywy agent w ElevenLabs, tool calling, działające demo, gotowy deck.

## Decyzje (ZABLOKOWANE)
1. **Persona:** Anna.
2. **Zakres narracji:** PoC (mockupy) → wizja docelowa.
3. **Głos:** `cgSgspJ2msm6clMCkdW9` (Jessica — Playful, Bright, Warm).
4. **Model TTS:** `eleven_v3_conversational` (zweryfikować dostępność w Phase 1).
5. **Format prezentacji:** PowerPoint lub Google Slides.
6. **Human handoff:** PoC → symulowany webhook `transfer_to_simulated_handoff` (brak telefonii/SIP na widgetcie; realny `transfer_to_number` wymaga planu z telefonii). Na produkcję: `transfer_to_number` (SIP) / PBX.

## Epiki (przegląd)
| Epik | Zakres | Fazy |
|---|---|---|
| **A. Przygotowanie** | konwersja KB, weryfikacja MCP | 1–2 |
| **B. Stworzenie agenta (MCP)** | create_agent + knowledge base | 3–4 |
| **C. Integracje i demo** | mock backend, tunel, tool calling, test E2E | 5–7 |
| **D. Prezentacja** | deck, materiały V2, próba | 8–10 |
| **E. Frontend (widget)** | żywa strona z Anną | F1–F4 |
| **F. Workflow i Procedures** | badania API, procedury, decyzja, implementacja, test, doc | F5–F10 |
| **G. Operacyjna odporność** | diagnoza awarii, wolny port, skrypt startowy, autostart | G1–G4 |
| **H. Frontend widget odporność** | self-host CDN skrypt, trigger przycisku, build | H1–H3 |
| **I. Workflow diagram → ElevenLabs** | mapowanie mermaid, projekt grafu, PATCH workflow, test | I1–I4 |
| **J. Procedures z _procedures.md** | research docs, 7 procedur, publikacja (pusty PATCH), test | J1–J4 |

## Środowisko i narzędzia
- **MCP ElevenLabs** (Hersys toolset): `create_agent`, `add_knowledge_base_to_agent`, `get_agent`, `list_agents`, `list_models`, `search_voices`, `get_voice`.
  - ⚠️ MCP NIE obsługuje: tool-calling (webhooki), `turn_eagerness`, `speed`, trybów `usage_mode` KB → te elementy wymagają panelu ElevenLabs / pełnego API (patrz `docs/plan_implementacji_recepcjonisty.md` §8).
  - ⚠️ KB przyjmuje tylko `epub/pdf/docx/txt/html` → konwersja `.md → .txt`.
- **Mock backend:** FastAPI na `localhost:8000`; tunel `ngrok` dla webhooków.
- **Środowisko wykonawcze:** Windows (Hermes CLI), ścieżki Windows.

## Konwencja wykonania (GSD)
- **Tryb domyślny: MVP** — wykonujemy pracę i weryfikujemy, NIE commit/push automatycznie. (To nie jest repo kodu wymagające commitów per faza; commity tylko gdy użytkownik zażąda.)
- **Orkiestracja: parent** — parent Hermes wykonuje kolejne fazy sekwencyjnie (bezpośrednie wywołania MCP / terminal) i weryfikuje wynik przed przejściem dalej.
- **Subagenty (`delegate_task`)** — tylko dla cięższych zadań (np. budowa decku w Faza 8), z pełnym kontekstem (ścieżki, decyzje, DoD).
- **Zależności:** faza N+1 dostaje w kontekście rezultat fazy N.
- **Weryfikacja po każdej fazie:** potwierdź realnym outputem (agent_id, `get_agent`, odpowiedź curl, liczba plików) — nie wierz deklaracjom.

## Powiązane pliki (kontekst)
- Prezentacyjny roadmap (wysokopoziomowy): `../plan/00_roadmapa.md`
- Źródło prawdy technicznej: `../docs/plan_implementacji_recepcjonisty.md` (§8 = kolejność MCP)
- System prompt: `../docs/anna_system_prompt.md`