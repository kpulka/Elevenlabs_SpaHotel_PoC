# INDEX dokumentacji — Wirtualny Recepcjonista AI „Anna" (Bukowy Dwór)

> **English summary.** This repository is a working proof of concept of Anna, a Polish/English voice receptionist
> for a fictional thermal spa resort, built on ElevenLabs Conversational AI with a FastAPI mock PMS, a Next.js
> demo site and a case-study deck. Each topic has exactly one canonical document; the Polish originals live in
> `docs/pl/`, and the English documents here are written for an external reader. Start with the list below.
>
> **Documentation language.** English is canonical for every document in `docs/` (the top level). The Polish
> originals of the architecture and the agent procedures live in `docs/pl/`, and the English versions in `docs/`
> are translations of them. Identifiers, prompts and Polish domain terms are not translated. If the two languages
> disagree, the Polish original of the architecture and procedures wins until the English text is corrected.

To repozytorium to działający proof-of-concept głosowego recepcjonisty AI „Anna" zbudowanego na ElevenLabs Agents dla uzdrowiska „Bukowy Dwór" w Krynicy-Zdroju: z bazą wiedzy RAG, mock backendem PMS/SPA, stroną demo z osadzonym widgetem i deckiem case study.

Ten plik jest **jedynym punktem wejścia**. Każdy temat ma dokładnie jeden dokument kanoniczny — pozostałe wersje są tłumaczeniami, materiałem referencyjnym albo archiwum. Jeśli dwa pliki mówią to samo, wiążący jest ten oznaczony jako **KANONICZNY**.

## Start here (reviewers)

1. [`business-case.md`](business-case.md) — problem, zakres „co automatyzujemy / czego nigdy", KPI, ekonomia z jawnymi założeniami.
2. [`lessons-learned.md`](lessons-learned.md) — osiem incydentów z tego projektu, każdy z dowodem w repozytorium.
3. [`deployment-playbook.md`](deployment-playbook.md) — droga od PoC do produkcji: fazy z bramkami, go-live, bezpieczeństwo i RODO, runbook, wdrożenie na PaaS (konfiguracja, bez wdrożenia).
3a. [`repo-guide.md`](repo-guide.md) — mapa repozytorium, bramki jakości, znane ograniczenia.
3b. [`fde-fit.md`](fde-fit.md) — obowiązki wdrożeniowe zmapowane na artefakty w repo, każdy ze statusem (zrealizowane / częściowo / projekt / brak).
3c. [`flows/README.md`](flows/README.md) — diagramy stanów procesów (anulowanie, przełożenie) wyprowadzone z kodu; każde przejście jest sprawdzane offline w `mock_backend/tests/test_flow_transitions.py`.
3d. [`discovery/dental_clinic_brief.md`](discovery/dental_clinic_brief.md) — wypełniony brief klienta (fikcyjna klinika stomatologiczna, ćwiczenie na szablonie `agent/_template`); drugi klient w `agent/verticals/dental_clinic/`, bez plików bazy wiedzy i bez uruchomienia.
3e. [`telephony.md`](telephony.md) — status telefonii: działa widget w przeglądarce, linia PSTN nie jest zaimplementowana; opcje A/B/C i diagram wyłącznie jako projekt.
3f. [`PRODUCT_FEEDBACK.md`](PRODUCT_FEEDBACK.md) — priorytetyzowany feedback produktowy PF-01..PF-12, oparty wyłącznie na faktach udokumentowanych w repozytorium.
3g. [`gdpr/README.md`](gdpr/README.md) — RODO: rejestr czynności (`gdpr/ropa.md`), DPIA-lite (`gdpr/dpia-lite.md`), macierz retencji (`gdpr/retention.md`); szkice, nie porada prawna.
3h. [`postmortems/TEMPLATE.md`](postmortems/TEMPLATE.md) — szablon postmortem i jeden przykład: [`postmortems/2026-kb-update-200-ok-changed-nothing.md`](postmortems/2026-kb-update-200-ok-changed-nothing.md).
4. [`architecture.md`](architecture.md) — architektura end-to-end i stack technologiczny (EN).
5. [`agent-workflows-and-procedures.md`](agent-workflows-and-procedures.md) — procedury i workflow agenta: co jest zaprojektowane, a co realnie wdrożone (EN).
6. [`pl/audyt_agenta_2026-08.md`](pl/audyt_agenta_2026-08.md) — audyt realnej konfiguracji agenta na żywo (PL, wersja oryginalna).
7. [`presentation/README.md`](../presentation/README.md) — deck case study (PL/EN) i sposób weryfikacji liczb.

## Dokumenty kanoniczne (PL)

| dokument | temat | status |
|---|---|---|
| `pl/specyfikacja_recepcjonista_ai.md` | zakres funkcjonalny — CO robi produkt (persona, ścieżki, narzędzia, RAG, RODO, koszty) | **KANONICZNY** |
| `pl/plan_implementacji_recepcjonisty.md` | konfiguracja techniczna — JAK jest zbudowany (modele, parametry, schematy JSON, koszty, wdrożenie) | **KANONICZNY** |
| `agent/system_prompt_v3.md` | system prompt agenta (wersja obowiązująca, symulowany handoff) | **KANONICZNY** |
| `pl/architektura_stack_technologiczny.md` | architektura systemu i stack technologiczny (wersja źródłowa, PL) | **KANONICZNY** |
| `pl/elevenlabs_agent_procedures.md` | procedury operacyjne / SOP (trigger conditions, walidacje, PMS) | **KANONICZNY** |
| `pl/elevenlabs_agent_workflow.md` | graf workflow konwersacji (stany, przejścia, guardrails) | **KANONICZNY** |
| `agent/knowledge_base/` | 5 plików Markdown — human-readable baza wiedzy hotelu (źródło; opis w `agent/knowledge_base/README.md`) | **KANONICZNY** |
| `agent/knowledge_base_txt/` | te same 5 plików jako `.txt` — artefakt wgrywany do ElevenLabs przez `scripts/deploy_kb_and_tools.py` | **ARTEFAKT WDROŻENIOWY** (nie edytować ręcznie) |
| `pl/audyt_agenta_2026-08.md` | audyt realnej konfiguracji live (co działa, co poprawiono, rekomendacje) | **REFERENCYJNY** (stan z audytu 2026-08) |
| `adr-language-routing.md` | routing językowy frontendu (PL/EN): status quo vs cookie vs segment `[lang]`, SEO, `pages.yml`, sitemap, widget Anny; decyzja „zostajemy", warunki ponownego otwarcia | **REFERENCYJNY** (decyzja z 2026-11) |

Zasady, które wynikają z tabeli:

- **System prompt:** obowiązuje `agent/system_prompt_v3.md`. Wersje v1 i v2 są w `agent/archive/`. v3 różni się sposobem eskalacji (`transfer_to_simulated_handoff` przez mock backend, bo PoC nie ma telefonii).
- **Specyfikacja:** `pl/specyfikacja_recepcjonista_ai.md` (kanoniczna) zastąpiła `pl/archive/specyfikacja_poc_recepcjonista_ai.md` (archiwum). Podział ról: specyfikacja mówi CO, plan implementacji mówi JAK.
- **Architektura:** źródłem jest wersja polska (`pl/architektura_stack_technologiczny.md`); plik `architecture.md` to tłumaczenie. Zmiana merytoryczna idzie najpierw do PL.
- **Baza wiedzy:** edytujesz `.md` w `agent/knowledge_base/`, kopiujesz 1:1 do `agent/knowledge_base_txt/` i wdrażasz `scripts/deploy_kb_and_tools.py`. Nie ruszaj plików `.txt` bezpośrednio — są wgrywane na żywo. Uwaga: API **nie aktualizuje treści** dokumentu przez `PATCH` (przyjmie 200 i zignoruje plik) — zmianę treści robi się przez utworzenie nowego dokumentu, ponowne podpięcie listy do agenta i usunięcie starego.
- **Wdrożony stan agenta** (procedure ID, graf workflow) leży w `agent/procedures/` i `agent/workflow/`. To artefakty wdrożenia, które dokumentacja opisuje, nie dokumentacja.
- **Otwarte punkty wdrożenia** (deploy frontendu, testy E2E zapisów) są śledzone w prywatnych notatkach projektu, nie w publicznym repozytorium.

## Dokumenty w języku angielskim (EN, dla zewnętrznego czytelnika)

Dokumenty pisane po angielsku, bo trafiają do zewnętrznego czytelnika. Są **kanoniczne** dla swoich tematów
(po polsku odpowiednika nie ma i nie planujemy — reszta repo zostaje dwujęzyczna tylko tam, gdzie już była).

| dokument | temat | status |
|---|---|---|
| `business-case.md` | uzasadnienie biznesowe: problem, zakres „co automatyzujemy / czego nigdy", KPI, ilustracyjna ekonomia (założenia jawnie oznaczone), ryzyka, rekomendacja | **KANONICZNY** (EN) |
| `deployment-playbook.md` | droga od PoC do produkcji: fazy z bramkami, checklista go-live, architektura docelowa, bezpieczeństwo i RODO, runbook awarii, model kosztów, governance | **KANONICZNY** (EN) |
| `lessons-learned.md` | 8 realnych incydentów z tego projektu: diagnoza, poprawka, wniosek — każdy wskazuje plik w repo | **KANONICZNY** (EN) |
| `architecture.md` | tłumaczenie EN `pl/architektura_stack_technologiczny.md` | **TŁUMACZENIE** (EN wersji PL) |
| `agent-workflows-and-procedures.md` | tłumaczenie EN workflow i procedur (`pl/elevenlabs_agent_workflow.md`, `pl/elevenlabs_agent_procedures.md`) | **TŁUMACZENIE** (EN powyższych dwóch) |

Zasada, która wyszła z `lessons-learned.md` §8: **liczby muszą być spójne między artefaktami**. Kanon to
`presentation/generate_deck.py` + `business-case.md` §6 (kurs 4,0 PLN/USD, $0,08/min, 3 × 500 PLN ≈ $375
pokrywa plan $299). Zmieniasz cennik — zmieniasz w generatorze, w obu HTML-ach, w `deck_spec*.json`
i w business case, potem regenerujesz PPTX. Bramka: `python presentation/verify_deck.py`.

## Jak czytać to repo w 10 minut

1. **`docs/INDEX.md`** (ten plik) — 1 min: co to jest i który dokument jest wiążący.
2. **`pl/architektura_stack_technologiczny.md`** — 3 min: jak system wygląda end-to-end (albo `architecture.md`, jeśli czytasz po angielsku).
3. **`pl/elevenlabs_agent_procedures.md`** — 2 min: jakie zadania agent wykonuje i na jakich warunkach.
4. **`pl/elevenlabs_agent_workflow.md`** — 2 min: jak rozmowa przechodzi między stanami i gdzie są guardrails.
5. **`pl/audyt_agenta_2026-08.md`** — 2 min: co realnie działa na żywym agencie i co trzeba poprawić.

Dopiero potem warto wejść w `pl/specyfikacja_recepcjonista_ai.md` (zakres produktu) i `pl/plan_implementacji_recepcjonisty.md` (szczegóły konfiguracji) — to dokumenty robocze, nie lektura na wejście. Ścieżka wdrożenia i prezentacja są opisane w `presentation/README.md`.

## Archiwum — co jest i dlaczego

Archiwum zawiera wyłącznie wersje nieaktualne, zachowane dla historii decyzji. Każdy plik ma na górze nagłówek statusu wskazujący następcę.

| plik archiwalny | dlaczego jest archiwalny |
|---|---|
| `agent/archive/system_prompt_v1.md` | v1 promptu — ma błędną nazwę narzędzia eskalacji (`transfer_to_human`); następcą jest v3 |
| `agent/archive/system_prompt_v2.md` | v2 promptu — zakłada realny `transfer_to_number`, niedostępny bez telefonii; następcą jest v3 |
| `pl/archive/specyfikacja_poc_recepcjonista_ai.md` | wczesna specyfikacja PoC z mockupami; scalona do `pl/specyfikacja_recepcjonista_ai.md` |

Nie czytaj archiwum, żeby zrozumieć system. Czytaj je tylko wtedy, gdy interesuje Cię, jak projekt dochodził do obecnego kształtu.
