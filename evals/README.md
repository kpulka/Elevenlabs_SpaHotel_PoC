# Evals — symulacje agenta Anny (K2)

Katalog na dowód działania agenta: żywe symulacje ElevenLabs uruchamiane przez
`mock_backend/tunnel/run_simulations.py`, ich transkrypty i podsumowanie `SUMMARY.md`.
Same scenariusze (treść rozmowy, oczekiwana kolejność narzędzi, zakazane frazy) są danymi w
`mock_backend/tunnel/scenarios.py`; tu jest instrukcja uruchamiania i opis tego, co wychodzi na dysk.

## Co jest sprawdzane

21 scenariuszy (`scenarios.py`, `selected()`) obejmuje procedury z `agent/procedures/procedure_ids.json`,
rezerwację niejednoznacznego zabiegu, dostępność pokoi z datą przeszłą, ataki (prompt injection po polsku
i po angielsku, anulowanie ze złym nazwiskiem), zagrożenie życia (scenariusz 17: oczekiwany numer 112 i
przekazanie zgłoszenia, bez obietnicy połączenia) oraz przesiew balneologiczny (scenariusz 18: rozrusznik
blokuje rezerwację zabiegu). Scenariusze 19–21 są po angielsku (rezerwacja, opłata poniżej 2 h, injection).
Każdy ma `procedure` i `tags`. Asercje: kolejność wywołań narzędzi (z przeplotem), zakazane wywołania,
wyrażenia regularne, które muszą lub nie mogą wystąpić w wypowiedziach agenta.

Testy samych scenariuszy i kontroli działają offline (bez kluczy i sieci):

```bash
cd mock_backend
python -m pytest tests/test_scenarios_offline.py tests/test_transcripts.py tests/test_lint_prompt_kb.py \
  tests/test_tool_schemas.py tests/test_deploy_kb.py tests/test_diff_agent_config.py tests/test_run_simulations.py -q
```

## Uruchomienie

Wszystkie polecenia z katalogu głównego repo.

```bash
python mock_backend/tunnel/run_simulations.py --check                 # kredyty, /health backendu, gałąź
python mock_backend/tunnel/run_simulations.py --dry-run               # payloady, zero kosztów, zero zapisów
python mock_backend/tunnel/run_simulations.py --only 02,16            # wybrane scenariusze (prefiksy slugów)
python mock_backend/tunnel/run_simulations.py --skip-scenario3        # bez scenariusza <2 h
python mock_backend/tunnel/run_simulations.py                         # pełny przebieg
```

Wymagania: uruchomiony `mock_backend` (port 8011), aktualny tunel z przepiętymi webhookami
(`sync_agent_tools.py`), klucz w `$ELEVENLABS_API_KEY` albo `frontend/.env.local`. ID agenta:
`$ELEVENLABS_AGENT_ID` albo `--agent-id`. Brak ID poza `--dry-run` kończy się kodem 2 (w repo nie ma
domyślnego agenta). Scenariusz `03` wymaga wolnego slotu kąpieli siarczkowej w ciągu 2 godzin —
uruchamiaj między 08:00 a 16:00 albo z `--skip-scenario3`.

### Koszt i guard kredytów

Każda symulacja zużywa kredyty ElevenLabs (liczone za tokeny rozmowy, nie za minutę). Skrypt:

* przed startem czyta saldo (`/v1/user/subscription`); gdy kredyty są wyczerpane, kończy się kodem 3
  i niczego nie uruchamia,
* `--dry-run` i `--check` nie tworzą testów i nie uruchamiają symulacji (ale wykonują odczyty:
  saldo, `/health`, listę narzędzi),
* `--only` pozwala puścić jeden scenariusz zamiast wszystkich, np. po zmianie promptu.

Pełny przebieg to 21 symulacji naraz — sprawdź `--check` i saldo przed uruchomieniem.

## Kody wyjścia

| kod | znaczenie |
|---|---|
| 0 | wszystkie symulacje przeszły, wszystkie asercje spełnione |
| 1 | co najmniej jedna symulacja nie przeszła albo naruszyła asercję (patrz `SUMMARY.md`) |
| 2 | konfiguracja lub backend: brak klucza, brak ID agenta, martwy host webhooka, brak slotu, błąd seeda |
| 3 | wyczerpane kredyty ElevenLabs |
| 4 | przekroczony czas oczekiwania na wynik (15 min) |

## Skrypty kontroli i wdrożenia

Poza symulacjami repo ma kilka skryptów, które sprawdzają spójność agenta z dokumentacją.
Wszystkie kontrole poniżej działają offline; tylko wdrożenie i `diff_agent_config.py` bez `--from-file` łączą się z API.

| skrypt | co robi | sieć |
|---|---|---|
| `scripts/check_kb_parity.py` | zgodność `agent/knowledge_base/*.md` z `agent/knowledge_base_txt/*.txt` (exit 1 przy różnicy) | nie |
| `scripts/lint_prompt_kb.py` | każda kwota, godzina i nazwa usługi w prompcie (blok ```) i procedurach ma pokrycie w KB; wyjątki w `scripts/lint_prompt_kb_allowlist.json` | nie |
| `scripts/check_tool_contract.py` | spójność nazw i pól narzędzi: `tool_schemas.py`, config, prompt, procedury, szablon | nie |
| `scripts/diff_agent_config.py` | porównuje agenta z repo: prompt, first_message, język, LLM, TTS, turn, RAG, lista KB (exit 1 przy dryfie, 2 przy błędnym wejściu) | tylko `--from-file` nie; bez argumentu robi `GET` agenta |
| `scripts/deploy_kb_and_tools.py` | wdraża 5 dokumentów KB, RAG, strefę czasową, `turn_eagerness` i prędkość TTS | tak (zapisy), `--dry-run` nie |

```bash
python scripts/check_kb_parity.py
python scripts/lint_prompt_kb.py
python scripts/check_tool_contract.py
python scripts/diff_agent_config.py --from-file zapis_get_agenta.json   # offline, bez sieci
python scripts/deploy_kb_and_tools.py --dry-run                                 # plan, zero połączeń
```

`diff_agent_config.py` bez `--from-file` wykonuje wyłącznie `GET /v1/convai/agents/{id}` i wymaga
`ELEVENLABS_API_KEY` oraz `ELEVENLABS_AGENT_ID`. Ścieżki pól odpowiedzi są opisane w nagłówku skryptu;
część z nich nie została zweryfikowana na żywym agencie, więc brak pola w odpowiedzi jest raportowany jako dryf.

`scripts/deploy_kb_and_tools.py` nie wdraża narzędzi ani promptu (narzędzia: `mock_backend/tunnel/sync_agent_tools.py`).
Kolejność przy wdrożeniu: POST nowych dokumentów KB, potem PATCH agenta, dopiero po sukcesie PATCH kasowanie
starych dokumentów. Błąd PATCH-a nie kasuje niczego. Manifest `.kb_deploy_manifest.json` jest zapisywany po
każdym kroku. Wymaga obu zmiennych środowiskowych; brak `ELEVENLABS_AGENT_ID` kończy się błędem.

## Co trafia na dysk i redakcja

Do `evals/transcripts/` (albo do katalogu z `ANNA_TRANSCRIPTS_DIR`) zapisywane są:

* `k2-<slug>.json` — pełny transkrypt jednego scenariusza,
* `SUMMARY.md` — tabela wyników z naruszeniami asercji.

Przed zapisem dane osobowe gości są maskowane:

* numery telefonów (`+48 600 100 200`, także bez prefiksu i z myślnikami) -> `+48 *** *** 200`,
* pełne imiona i nazwiska gości (z seedów i scenariuszy) -> inicjały z gwiazdkami, np. `P*** Z***`,
  także w argumentach narzędzi pod kluczami `name`, `guest_name`, `guest` (i `phone`, `phone_number`).

Maskowanie nie obejmuje samych imion ani nazwisk pojedynczo (np. „Pani Maria”) — to świadome ograniczenie.
Asercje działają na tekście przed redakcją, więc redakcja nie zmienia wyniku testu.

Numery rezerwacji (`SPA-XXXX`), daty i ceny nie są danymi osobowymi i zostają w pliku.

## Git

Transkrypty są lokalnym materiałem dowodowym i nie powinny trafiać do publicznego repo.
Wpisy `evals/transcripts/*` i `!evals/transcripts/.gitkeep` są w roboczej kopii `.gitignore`, ale nie są
jeszcze w zatwierdzonym HEAD; trafią do repo razem z commitem `.gitignore` (decyzja właściciela).
