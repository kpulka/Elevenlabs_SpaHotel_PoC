# INDEX dokumentacji — Wirtualny Recepcjonista AI „Anna" (Bukowy Dwór)

To repozytorium to działający proof-of-concept głosowego recepcjonisty AI „Anna" zbudowanego na ElevenLabs Agents dla uzdrowiska „Bukowy Dwór" w Krynicy-Zdroju: z bazą wiedzy RAG, mock backendem PMS/SPA, stroną demo z osadzonym widgetem i deckiem rekrutacyjnym.

Ten plik jest **jedynym punktem wejścia**. Każdy temat ma dokładnie jeden dokument kanoniczny — pozostałe wersje są tłumaczeniami, materiałem referencyjnym albo archiwum. Jeśli dwa pliki mówią to samo, wiążący jest ten oznaczony jako **KANONICZNY**.

## Dokumenty kanoniczne

| dokument | temat | status |
|---|---|---|
| `specyfikacja_recepcjonista_ai.md` | zakres funkcjonalny — CO robi produkt (persona, ścieżki, narzędzia, RAG, RODO, koszty) | **KANONICZNY** |
| `plan_implementacji_recepcjonisty.md` | konfiguracja techniczna — JAK jest zbudowany (modele, parametry, schematy JSON, koszty, wdrożenie) | **KANONICZNY** |
| `anna_system_prompt_v3.md` | system prompt agenta (wersja obowiązująca, symulowany handoff) | **KANONICZNY** |
| `architektura_stack_technologiczny.md` | architektura systemu i stack technologiczny (wersja źródłowa, PL) | **KANONICZNY** |
| `architecture_and_tech_stack_en.md` | to samo co wyżej po angielsku | **TŁUMACZENIE** (EN wersji PL) |
| `elevenlabs_agent_procedures.md` | procedury operacyjne / SOP (trigger conditions, walidacje, PMS) | **KANONICZNY** |
| `elevenlabs_agent_workflow.md` | graf workflow konwersacji (stany, przejścia, guardrails) | **KANONICZNY** |
| `agent_workflows_and_procedures_en.md` | workflow + procedury po angielsku | **TŁUMACZENIE** (EN powyższych dwóch) |
| `audyt_agenta_2026-08.md` | audyt realnej konfiguracji live (co działa, co poprawiono, rekomendacje) | **REFERENCYJNY** (stan z audytu 2026-08) |
| `baza_wiedzy_rag_bukowy_dwor/` | 5 plików Markdown — human-readable baza wiedzy hotelu (źródło) | **KANONICZNY** |
| `baza_wiedzy_rag_bukowy_dwor_txt/` | te same 5 plików jako `.txt` — artefakt wgrywany do ElevenLabs przez `deploy_kb_and_tools.py` | **ARTEFAKT WDROŻENIOWY** (nie edytować ręcznie) |
| `archive/` | wersje historyczne — patrz sekcja niżej | **ARCHIWUM** |

Żaden plik w `docs/` nie jest otwartym szkicem — otwarte punkty wdrożenia (deploy frontendu, brak zapisów testów E2E) są śledzone w `.planning/README.md`, nie w dokumentacji.

Zasady, które wynikają z tabeli:

- **System prompt:** obowiązuje `anna_system_prompt_v3.md`. v1 i v2 są w `archive/` — v3 różni się sposobem eskalacji (`transfer_to_simulated_handoff` przez mock backend, bo PoC nie ma telefonii).
- **Specyfikacja:** `specyfikacja_recepcjonista_ai.md` (kanoniczna) zastąpiła `specyfikacja_poc_recepcjonista_ai.md` (archiwum). Podział ról: specyfikacja mówi CO, plan implementacji mówi JAK.
- **Architektura:** źródłem jest wersja polska (`architektura_stack_technologiczny.md`); plik `_en` to tłumaczenie. Zmiana merytoryczna idzie najpierw do PL.
- **Baza wiedzy:** edytujesz `.md` w `baza_wiedzy_rag_bukowy_dwor/`, kopiujesz 1:1 do `.txt` i wdrażasz `deploy_kb_and_tools.py`. Nie ruszaj plików `.txt` bezpośrednio — są wgrywane na żywo. Uwaga: API **nie aktualizuje treści** dokumentu przez `PATCH` (przyjmie 200 i zignoruje plik) — zmianę treści robi się przez utworzenie nowego dokumentu, ponowne podpięcie listy do agenta i usunięcie starego.
- **Wdrożony stan agenta** (procedure ID, grafy workflow, narzędzia) leży w `.planning/workflow/` — to nie dokumentacja, tylko artefakty wdrożenia.

## Jak czytać to repo w 10 minut

1. **`docs/INDEX.md`** (ten plik) — 1 min: co to jest i który dokument jest wiążący.
2. **`docs/architektura_stack_technologiczny.md`** — 3 min: jak system wygląda end-to-end (albo `_en`, jeśli czytasz po angielsku).
3. **`docs/elevenlabs_agent_procedures.md`** — 2 min: jakie zadania agent wykonuje i na jakich warunkach.
4. **`docs/elevenlabs_agent_workflow.md`** — 2 min: jak rozmowa przechodzi między stanami i gdzie są guardrails.
5. **`docs/audyt_agenta_2026-08.md`** — 2 min: co realnie działa na żywym agencie i co trzeba poprawić.

Dopiero potem warto wejść w `specyfikacja_recepcjonista_ai.md` (zakres produktu) i `plan_implementacji_recepcjonisty.md` (szczegóły konfiguracji) — to dokumenty robocze, nie lektura na wejście. Ścieżka wdrożenia i prezentacja są opisane w `.planning/README.md` i `presentation/README.md`.

## Co jest w archiwum i dlaczego

Katalog `docs/archive/` zawiera wyłącznie wersje nieaktualne, zachowane dla historii decyzji. Każdy plik ma na górze nagłówek statusu wskazujący następcę.

| plik archiwalny | dlaczego jest archiwalny |
|---|---|
| `archive/anna_system_prompt.md` | v1 promptu — ma błędną nazwę narzędzia eskalacji (`transfer_to_human`); następcą jest v3 |
| `archive/anna_system_prompt_v2.md` | v2 promptu — zakłada realny `transfer_to_number`, niedostępny bez telefonii; następcą jest v3 |
| `archive/specyfikacja_poc_recepcjonista_ai.md` | wczesna specyfikacja PoC z mockupami; scalona do `specyfikacja_recepcjonista_ai.md` |
| `archive/ElevenLabs_Etap_V1.md` | wymagania etapu rekrutacyjnego V1 — kontekst powstania projektu, nie dokumentacja systemu |
| `archive/ElevenLabs_Etap_V2.md` | wymagania etapu rekrutacyjnego V2 — jw. |
| `archive/pre-gsd/00_roadmapa.md` | roadmapa sprzed wdrożenia GSD; zastąpiona przez `.planning/ROADMAP.md` |
| `archive/pre-gsd/01_inwentaryzacja.md` | inwentaryzacja dokumentów sprzed porządków; bieżący stan opisuje ten INDEX |
| `archive/pre-gsd/02_brief_dla_agenta.md` | jednorazowy brief dla zewnętrznego agenta ElevenLabs — zadanie wykonane |

Nie czytaj archiwum, żeby zrozumieć system. Czytaj je tylko wtedy, gdy interesuje Cię, jak projekt dochodził do obecnego kształtu.
