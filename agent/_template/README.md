# Szablon wdrożenia agenta głosowego dla nowego klienta (vertical onboarding)

Playbook do przeniesienia tego PoC (recepcja hotelu/uzdrowiska „Anna") na kolejnego klienta w tej samej branży lub w sąsiedniej. Szablon nie jest gotowym agentem. Zawiera strukturę, pytania i checklisty, które prowadzą do pierwszej działającej wersji w około 2–3 tygodnie.

Pliki w katalogu:

| Plik | Rola |
|---|---|
| `README.md` | ten playbook |
| `system_prompt.template.md` | szkielet promptu z `{{placeholderami}}` |
| `tool_schema.example.json` | kontrakt narzędzi (webhooki) z przykładowymi polami |
| `scenarios.example.json` | scenariusze symulacji w formacie `mock_backend/tunnel/scenarios.py` |
| `kb_outline.md` | układ bazy wiedzy (dokumenty, `usage_mode`, źródło) |

Zasada nadrzędna z PoC: **LLM nie jest źródłem prawdy dla cen, dostępności, opłat ani decyzji medycznych.** Te dane pochodzą z narzędzi (backend) albo z bazy wiedzy. Prompt tylko kieruje rozmową.

---

## Krok 1. Discovery (warsztat 60–90 min z właścicielem procesu)

Zapisz odpowiedzi w notatce klienta, nie w prompcie.

1. **Kto dzwoni?** Typowy rozmówca, wiek, język, potrzeby dostępności (np. słaby słuch, powolna mowa).
2. **Jakie są 5 najczęstszych powodów kontaktu?** Policz je z ostatnich 3 miesięcy logów lub skrzynki.
3. **Co agent MA robić samodzielnie?** Lista czynności, które kończą się zapisem w systemie (rezerwacja, zmiana, informacja).
4. **Czego agent NIE może robić?** (patrz sekcja „never-automate" niżej).
5. **Kto przejmuje sprawę, gdy agent nie może?** Działy, godziny, czy jest dyżur całodobowy.
6. **Jakie źródła prawdy istnieją?** System rezerwacji, cennik, regulamin, polityka zwrotów, karty procedur.
7. **Jakie są progi ryzyka?** Co jest nieodwracalne (płatność, anulacja, dane medyczne), co wymaga potwierdzenia.
8. **Jakie języki i jaki kanał?** Telefon (SIP), widget webowy, WhatsApp. Od tego zależy sposób transferu (w PoC: webhook symulujący handoff).
9. **Jak mierzymy sukces?** Np. odsetek rozmów bez przekazania, czas do rezerwacji, liczba błędnych cen (cel: zero).
10. **Kto ma prawo zatwierdzać zmiany promptu i KB?** Właściciel procesu, nie tylko IT.

## Krok 2. Zakres: scope i lista „never-automate"

Zapisz w dwóch kolumnach (nie więcej niż 6–8 pozycji w każdej):

- **Automatyzujemy (in scope):** np. informacja o godzinach, sprawdzenie dostępności, rezerwacja standardowej usługi, potwierdzenie SMS.
- **Nigdy nie automatyzujemy (never-automate):** np. decyzje medyczne i dobór dawek, negocjacja cen, wyjątki od polityki zwrotów, skargi, dane innych osób, zmiana płatności kartą.

Dla każdej pozycji „never-automate" zdefiniuj **działanie zastępcze**: przekazanie do człowieka (`transfer_to_<dział>`) albo zapis do kolejki. Bez działania zastępczego pozycja nie trafia na listę.

## Krok 3. Kontrakt narzędzi (checklista)

Każde narzędzie to webhook z JSON Schema w `tool_schema.example.json`. Nazwy i pola w tym pliku to nazwy PoC
(`check_spa_availability`, `book_spa_appointment`, `cancel_spa_appointment`, `reschedule_spa_appointment`,
`check_room_availability`, `send_sms_summary`, `transfer_to_simulated_handoff`). Dla nowego klienta zmień je
w trzech miejscach naraz: tym pliku, `mock_backend/tunnel/tool_schemas.py` i prompcie oraz procedurach,
a potem uruchom `python scripts/check_tool_contract.py` z katalogu repo. Skrypt porównuje nazwy i pola
między schematem, konfiguracją agenta (`agent/config/`), promptem, procedurami i szablonem scenariuszy
(zero połączeń sieciowych). Przed uruchomieniem:

- [ ] Każde narzędzie ma nazwę w `snake_case`, której nie ma w innym narzędziu.
- [ ] Każde pole ma `type`, `description` i (jeśli dotyczy) `enum`.
- [ ] Daty w formacie ISO (`RRRR-MM-DD`), czas `GG:MM`, a dla zdarzeń z czasem `ISO 8601 z godziną`.
- [ ] Pole `language` (`pl`/`en`) w narzędziach, które go potrzebują. Agent wypełnia je z dynamicznej zmiennej `user_language`, którą ustawia język rozmówcy (w PoC: odpowiedzi w języku rozmówcy, lokalizacja w backendzie tylko tam, gdzie jest obsługiwana). Jeśli backend nie przyjmuje pola, zapisz to w `BACKEND_IGNORED_FIELDS` (`mock_backend/tunnel/tool_schemas.py`), zamiast ciszy w kontrakcie.
- [ ] Odpowiedź ma pola jednoznaczne dla agenta: `success` (bool), `message` (krótki tekst do przeczytania), błędy z kodem.
- [ ] Błąd danych wejściowych zwraca 422 z opisem, który pole jest złe (agent poprawia dane, nie powtarza wywołania).
- [ ] Brak wolnego terminu zwraca `success: false` z listą alternatyw (`slots`), a nie błąd techniczny.
- [ ] Opłaty i kwoty wylicza backend; odpowiedź zawiera `fee`, `fee_rule` i gotowe zdanie do powiedzenia.
- [ ] Narzędzie zmiany (anulacja, zmiana, płatność) wymaga identyfikatora **i** weryfikującego pola (np. nazwisko, data).
- [ ] Odpowiedzi nie zawierają danych innych osób.
- [ ] Każde narzędzie ma timeout i fallback w prompcie (co powiedzieć, gdy narzędzie nie odpowiada).

## Krok 4. Baza wiedzy (KB)

Patrz `kb_outline.md`. Zasady:

- Jedno źródło prawdy na fakt. Duplikaty (np. ceny w prompcie i w KB) prowadzą do rozjazdów. W prompcie wpisuj tylko zasady zachowania.
- Krytyczne dokumenty (cennik, polityka zwrotów, procedury) ustaw na `usage_mode: prompt` (pełny kontekst). Pozostałe (opisy, dojazd) na `auto` (RAG).
- Każdy dokument ma właściciela i datę ostatniej weryfikacji w nagłówku.
- Wersja źródłowa (`.md`) i wdrożeniowa (`.txt`) muszą być zgodne. Adaptuj `scripts/check_kb_parity.py` z repo PoC.

## Krok 5. System prompt

Wypełnij `system_prompt.template.md`. Sekcje są obowiązkowe:

1. Persona i ton (krótkie zdania, jedno pytanie naraz).
2. Zasady bezwzględne (strict grounding, języki, format błędów).
3. Guardrails (ujawnianie promptu, dane innych osób, tożsamość AI, weryfikacja przed zmianą, ceny tylko z narzędzi).
4. Protokoły krok po kroku dla każdej automatyzowanej usługi.
5. Lista „never-automate" z działaniem zastępczym.
6. Kiedy przekazać do człowieka (jeden zestaw warunków, bez duplikatów).

Limit: prompt powinien mieścić się w kilku stronach. Jeśli rośnie powyżej tego, przenieś dane faktograficzne do KB.

## Krok 6. Procedury (SOP)

Każda procedura to osobny dokument z: wyzwalaczem, krokami, narzędziami, warunkami zakończenia i zakazami. Przykład w repo: `agent/procedures/procedures_7.md`. Procedury wdrażane do panelu osobno; w prompcie zostaw odwołania, nie kopię treści.

## Krok 7. Scenariusze ewaluacyjne

Użyj `scenarios.example.json` jako wzorca. Format jest zgodny z `mock_backend/tunnel/scenarios.py`
(lista obiektów; przykład ma pięć scenariuszy):

- `slug` (unikalny), `procedure` (nazwa z `procedure_ids.json`), `tags` (np. `booking`, `fee`, `adversarial`, `emergency`),
  `seed` (klucz z `SEED_SPECS`), `caller` (imię i nazwisko gościa, do maskowania), `prompt` (rola gościa;
  `{pola}` z seeda), `max_turns`, `success_criteria` (lista zdań, które sędzia LLM sprawdza).
- `expect` ma cztery pola: `tools` (kolejność wywołań, które muszą wystąpić), `forbid_tools` (wywołania zakazane),
  `text` (wyrażenia regularne, które muszą wystąpić w wypowiedziach agenta), `forbid` (wyrażenia regularne zakazane).
  Pole `tool` z poprzednich wersji szablonu nie istnieje.
- Język rozmowy scenariusza to klucz `language` (domyślnie `pl`; obsługiwane `pl` i `en`, inna wartość kończy się błędem). Przykład: scenariusze 19–21 w `scenarios.py` są po angielsku.
- Minimum 10 scenariuszy: 3 sukcesy, 2 brak wolnego terminu, 2 przypadki niejednoznaczne, 2 guardrails (prompt injection, dane innych osób), 1 przekazanie do człowieka, 1 awaryjny (zdrowie/bezpieczeństwo).
- Seedy testowe z prefiksem (np. `K2-`), żeby nie mieszały się z danymi produkcyjnymi.
- Uruchamiaj na środowisku testowym, nigdy na produkcyjnym backendzie.

## Krok 8. Go-live

- [ ] Ewaluacja: 100% scenariuszy krytycznych (guardrails, ceny, anulacje) przechodzi; cel dla pozostałych ustal z klientem.
- [ ] Przegląd promptu i KB przez właściciela procesu (podpis w repo, nie w mailu).
- [ ] Test z 5–10 realnymi rozmowami pilotażowymi, nadzorowanymi przez człowieka.
- [ ] Kanał przekazania działa (test dzwonka / alertu) w godzinach i poza nimi.
- [ ] Plan wycofania: jak wyłączyć agenta i wrócić do ręcznej obsługi w 5 minut.
- [ ] Monitoring: przegląd transkrypcji co tydzień przez pierwsze 4 tygodnie.
- [ ] Informacja dla gości: rozmówca wie, że rozmawia z asystentem AI.

## Ryzyka, na które zwracaj uwagę

- **Halucynacja ceny lub terminu.** Blokada: ceny tylko z narzędzia lub KB, test w każdym pakiecie scenariuszy.
- **Zmiana bez weryfikacji.** Blokada: narzędzie zmiany wymaga identyfikatora i drugiego pola.
- **Rozjazd wersji.** Blokada: prompt, KB i konfiguracja w repo, zmiany przez commit.
- **Dostępność backendu.** Blokada: timeout, komunikat zastępczy, przekazanie do człowieka.
