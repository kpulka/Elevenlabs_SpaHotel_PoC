> **Status:** historyczne — zastąpione przez `.planning/ROADMAP.md` (archiwum, nieaktualne). Zarchiwizowano 2026-11: plan sprzed wdrożenia frameworka GSD.

# Roadmapa do Prezentacji „Wirtualny Recepcjonista AI"

Cel: prezentacja case study zgodna z Etapem V1 (rozmowa + wspólna sesja) i Etapem V2 (product design, wireframing, system design, hiring manager).

---

## FAZA 0 — Uporządkowanie repozytorium ✅ ZROBIONE
- [x] Inwentaryzacja wszystkich dokumentów.
- [x] Ujednolicenie nazewnictwa plików i folderów.
- [x] README z mapą i konwencją nazewnictwa (zaktualizowany).

## FAZA 1 — Ujednolicenie specyfikacji ✅ ZROBIONE
- [x] Jedna kanoniczna spec: `docs/specyfikacja_recepcjonista_ai.md`
- [x] Źródło prawdy technicznej: `docs/plan_implementacji_recepcjonisty.md`
- [x] Persona → Anna, głos → Jessica — Playful, Bright, Warm (`cgSgspJ2msm6clMCkdW9`), narzędzia → kanoniczny zestaw 5
- [x] RAG → 5 plików z trybami prompt/auto + uzupełnione (apartament, 3 zabiegi)
- [x] PoC spec → oznaczona ZDEPRECJONOWANY

## FAZA 2 — Hands-on z produktem ElevenLabs ⚠️ CZĘŚCIOWO
- [x] Diagram architektury (5 wariantów Mermaid) → `presentation/01_diagram_architektury.md`
- [x] „Dobre wdrożenie" zdefiniowane: skalowanie, RODO, koszty
- [x] Mock backend uruchamialny lokalnie → `mock_backend/` (FastAPI, 4 endpointy)
- [x] ngrok — instrukcja w README mock_backend (`ngrok http 8000`)
- [ ] **BRAKUJE: fizyczne stworzenie agenta w panelu ElevenLabs** (demo niemożliwe bez tego)

## FAZA 3 — Materiał na V1 (Case Study) ✅ ZROBIONE
- [x] Scenariusz klienta: `docs/specyfikacja_recepcjonista_ai.md`
- [x] 3 ścieżki demo ze skryptem: `presentation/03_narracja_demo.md`
- [x] Tok myślenia „na głos" + odpowiedzi na trudne pytania: `presentation/02_tok_myslenia_v1.md`
- [x] Pytania do rekrutera (5 sztuk): `presentation/02_tok_myslenia_v1.md` (ostatnia sekcja)

## FAZA 4 — Product & System Design (V2) ✅ ZROBIONE
- [x] System design — 5 diagramów Mermaid: `presentation/01_diagram_architektury.md`
- [x] Problem understanding — 5 obszarów pytań: `presentation/05_v2_problem_understanding.md`
- [x] Wireframing — guide Excalidraw (3 szkice krok po kroku): `presentation/06_v2_excalidraw.md`
- [x] UX — journey map + widget spec + stany błędów: `presentation/07_ux_design.md`
- [x] UI mockupy & diagramy (7 grafik): `presentation/assets/`
- [x] Przygotowanie na Hiring Manager (historie STAR): `presentation/09_v2_hiring_manager_prep.md`

## FAZA 5 — Slajdy i materiały prezentacyjne ✅ ZROBIONE
- [x] Brief dla budowniczego slajdów: `presentation/00_brief_prezentacja.md`
- [x] Outline slajdów (14 slajdów): `presentation/04_slajdy_outline.md`
- [x] **Prezentacja PowerPoint (.pptx):** `presentation/Bukowy_Dwor_Case_Study.pptx`
- [x] **Interaktywna prezentacja Web/HTML:** `presentation/prezentacja.html` (ze sterowaniem, notatkami N i pełnym ekranem F)
- [ ] **Próba „na sucho"** — przejście przez całość głośno, zmierz czas (cel: ≤20 min)

---

## Decyzje (ZABLOKOWANE)
1. **Persona:** Anna.
2. **Zakres:** „PoC (demo) → wizja docelowa".
3. **Human handoff:** natywne `transfer_to_number` (nie custom webhook).
4. **Format prezentacji:** PowerPoint lub Google Slides.

---

## Mapa plików — szybki dostęp

### Dokumenty źródłowe
| Plik | Rola |
|---|---|
| `docs/plan_implementacji_recepcjonisty.md` | Źródło prawdy technicznej |
| `docs/specyfikacja_recepcjonista_ai.md` | Spec funkcjonalna (kanoniczna) |
| `docs/architektura_stack_technologiczny.md` | **Architektura & Stack Technologiczny (Mermaid)** |
| `docs/elevenlabs_agent_workflow.md` | Workflow Agenta (Graf stanów & Mermaid) |
| `docs/elevenlabs_agent_procedures.md` | Procedury Operacyjne Agenta (SOP & Reguły biznesowe) |
| `docs/anna_system_prompt.md` | System prompt gotowy do wklejenia w ElevenLabs |
| `docs/baza_wiedzy_rag_bukowy_dwor/` | 5 plików RAG (wiedza hotelowa) |

### Materiały prezentacyjne
| Plik | Rola |
|---|---|
| `presentation/00_brief_prezentacja.md` | Brief dla AI/człowieka do zbudowania slajdów |
| `presentation/01_diagram_architektury.md` | 5 diagramów Mermaid |
| `presentation/02_tok_myslenia_v1.md` | V1: tok myślenia, trudne pytania, liczby, pytania do rekrutera |
| `presentation/03_narracja_demo.md` | Skrypt 3 ścieżek demo + fallbacki |
| `presentation/04_slajdy_outline.md` | Outline 14 slajdów |
| `presentation/05_v2_problem_understanding.md` | V2: pytania do problem understanding (5 obszarów) |
| `presentation/06_v2_excalidraw.md` | V2: co rysować w Excalidraw (3 szkice, krok po kroku) |
| `presentation/07_ux_design.md` | UX: journey map + widget UI spec + stany błędów + chips |

### Backend PoC
| Plik | Rola |
|---|---|
| `mock_backend/main.py` | FastAPI, 4 endpointy webhook |
| `mock_backend/README.md` | Instrukcja uruchomienia + curl + ngrok |
