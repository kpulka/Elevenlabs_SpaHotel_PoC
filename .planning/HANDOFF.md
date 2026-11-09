# HANDOFF — co dalej z tym repo (dla następnego agenta)

> Napisane 2026-11-09, po zakończeniu dużego refaktoru portfolio. Ten plik jest **jedynym** miejscem,
> od którego nowy agent ma zacząć. Nie powtarzaj pracy opisanej w sekcji 2 — ona jest zrobiona,
> zweryfikowana i wypchnięta.

---

## 1. Co to jest

`github.com/kpulka/Elevenlabs_SpaHotel_PoC` — publiczne portfolio / case study na rekrutację
(ElevenLabs Deployment Strategist). Fikcyjne uzdrowisko „Bukowy Dwór”: agent głosowy **Anna**
(ElevenLabs Conversational AI, PL/EN), mock backend PMS (**FastAPI**, port **8011**), strona
marketingowa (**Next.js 16**, PL/EN) z osadzonym widgetem, deck rekrutacyjny.
Wszystko fikcyjne (hotel, ceny, zdjęcia AI) — patrz `NOTICE.md` i `LICENSE` (MIT).

Dokumentacja produktu: **`docs/INDEX.md`** (jeden kanon na temat). Parametry żywego agenta:
**`.planning/AGENT_ID.txt`**. Plan faz: **`.planning/ROADMAP.md`** + `.planning/phases/`.
Wizytówka: **`README.md`**.

## 2. Stan faktyczny (zmierzony, nie z raportów)

- Gałąź `main`, drzewo czyste, `main` == `origin/main`. Ostatni commit historii: `fc22c74` (K1);
  dokumentacja K1 w kolejnym commicie. `.git` = **31 MB** po K1 (było 64 MB; usunięte z historii:
  `cloudflared.exe` 52,35 MiB i stara wersja decku 8,94 MiB).
- CI (`.github/workflows/ci.yml`) zielone: job `backend (pytest)` + job `frontend (typecheck + build)`
  z dodatkowymi bramkami `pnpm i18n:check` i `pnpm data:check`.
- Bramki lokalne: `cd mock_backend && python -m pytest -q` → **68 passed**;
  `cd frontend && ./node_modules/.bin/tsc --noEmit` → 0; `node scripts/check-i18n.mjs` → **182 klucze**;
  `node scripts/sync-data.mjs --check` → **3 pokoje, 6 zabiegów**; `next build` → 11 stron statycznych.
- Backend: 7 tras POST + `/health` + `/`. Walidacja typów, reguła opłat >2 h/<2 h/medyczna, slot
  sprzedawany raz (klucz data+godzina), ceny z `data/*.json`, blokada 28–29.12.2026 generowana z JSON.
- Frontend: jedno źródło copy (`lib/translations.ts`, `pl` definiuje typ, `en` musi pasować — jest też
  skrypt bramki), dane dwujęzyczne + ceny generowane z backendu (`lib/generated/hotel-facts.ts`,
  generator `scripts/sync-data.mjs`), per-route metadata + sitemap/robots/OG, obrazy AVIF/WebP.
- Dokumentacja: `docs/INDEX.md` + `docs/archive/`, `.planning/README.md` (tabela 24 faz + K1–K5),
  `presentation/README.md`. Porty, liczba narzędzi, modele i ID wyrównane do kodu.
- **Żywa warstwa agenta (przez API, zweryfikowane):** 7 narzędzi webhook podpiętych; schematy body
  uzupełnione o `appointment_datetime` (cancel) i `language` (send_sms, handoff); 5 dokumentów bazy
  wiedzy odtworzonych z poprawionych `.txt` i ponownie podpiętych (nowe ID w `AGENT_ID.txt`).
  **Hosted prompt jest starszy niż `docs/anna_system_prompt_v3.md`** — to jedyna świadoma różnica.

## 3. Co dalej — EPIK K (zapisany w `.planning`)

Pełne briefy: `.planning/phases/phase-K1…K5-*.md`. Skrót z zależnościami:

| Faza | Cel | Zależność | Wymaga decyzji |
|---|---|---|---|
| **K1** historia gita | ✅ 2026-11-09 — `.git` 64 MB → **31 MB**; usunięte `cloudflared.exe` (52,35 MiB) i stara wersja decku (8,94 MiB); tree HEAD bez zmian (`2f184d8`); świeży klon 31 MB, 0 trafień `cloudflared`, 68 testów; backup bundle + tag `archive/english-wip-2026-11-04`, gałąź `claude/*` usunięta | pierwsza | zamknięte |
| **K2** prompt live | ✅/⚠️ 2026-11-09 — prompt live = `docs/anna_system_prompt_v3.md` (10 520 znaków, sha256 `ce1e5166…`), 8 narzędzi / 7 tool_id, 5 plików KB; naprawiony martwy `tool_id` w procedurze zmiany terminu (nowa wersja agenta `agtvrsn_4901m713bqdkedeb9f8vck1chb96`). **Otwarte:** 3 testy symulacyjne startują i kończą się „Insufficient credits” → brak transkryptów w `.planning/transcripts/` | może równolegle z K3 | zamknięte (czekamy na reset kredytów) |
| **K3** deck | ✅ 2026-11-09 — oba PPTX z `generate_deck.py --lang all`: 14 slajdów, 7/7 narzędzi, `:8011`, 0× `transfer_to_number`/`8000`/`4 webhook`/`$15`; README opisuje realny generator | niezależna | zamknięte (wybór: `--lang`, nie HTML→PDF) |
| **K4** higiena GitHuba | ✅ 2026-11-09 — tag `v1.0.0` + release z oboma PPTX, Pages z deckiem (homepage), topics, Wiki off, 0 issues; 44 martwe klucze i18n usunięte (182 → 138, `tsc`/`build` zielone) | po K1 i K3 | zamknięte (`gh auth login` zrobiony) |
| **K5** demo online | Vercel + backend na Fly/Render (Docker z `mock_backend/tunnel/Dockerfile`) albo nagranie jako fallback | po K2 | **TAK — wariant A/B/C i budżet kredytów** |

Decyzje właściciela — **wszystkie podjęte 2026-11-09** (nie pytaj ponownie):
1. **K1:** zgoda na przepisanie historii i force-push po backupie bundle; zakres = `cloudflared.exe` +
   stara wersja decku; backup `D:/Backups/spahotels-pre-filter-2026-11-09.bundle`.
2. **K4/gałąź:** `origin/claude/trusting-fermi-dy8rdu` → tag `archive/english-wip-2026-11-04` + usunięcie
   gałęzi (wykonane razem z K1, bo inaczej klon nadal ciągnął 52 MB).
3. **K2/prompt:** wgrać teraz, z backupem live promptu i markerem potwierdzającym wejście treści.
4. **K5/demo:** wariant **C** — nagranie 60–90 s jako fallback; bez hostingu i bez publicznego klucza API.
5. **K3/deck EN:** rozszerzyć `generate_deck.py` o `--lang en` i generować oba PPTX.
6. **K4/GitHub:** właściciel zaloguje `gh` sam; do tego czasu release/metadane czekają.
7. **Kredyty ElevenLabs (2026-11-09):** konto `payg`, `character_count = character_limit = 10000`
   (limit wyczerpany, reset **2026-11-22 04:02 UTC**). Decyzja właściciela: **czekamy do resetu**, nie
   doładowujemy — K2 (transkrypty) i K5 (nagranie) zostają otwarte do kolejnej sesji po tej dacie.
   Do tego czasu nie odpalaj symulacji ani rozmów z agentem (każda kończy się błędem i zaśmieca stan).

## 4. Zasady pracy w tym repo

- **Bramki przed każdym commitem:** `pytest` (68+), `tsc --noEmit`, `check-i18n.mjs`, `sync-data.mjs
  --check`, `next build`. Czerwona bramka = nie ma commita „na potem”.
- **Commit per logiczny obszar, jawne ścieżki**, nigdy `git add -A`. `git status --short` przed każdym
  commitem — użytkownik prowadzi równoległe sesje na tym samym drzewie.
- **Nie pushuj zmian w żywym systemie** (prompt, KB, deck) bez backupu i sprawdzenia markerem, że nowa
  treść faktycznie weszła — API potrafi zwrócić 200 i zignorować payload (patrz pułapki).
- Zakończone fazy oznaczaj w `.planning/README.md` (tabela) i dopisuj dowód — nie tylko w czacie.
- Kod/comments po angielsku, komunikacja i dokumentacja produktu po polsku (README: EN + krótkie PL).

## 5. Pułapki zmierzone w tej sesji

1. **ElevenLabs KB:** `PATCH /v1/convai/knowledge-base/{id}` z plikiem zwraca **200 i nie zmienia
   treści**. Zmiana treści = utworzyć nowy dokument → PATCH listy `knowledge_base` agenta (zachowując
   `usage_mode`) → usunąć stary. Sprawdzać markerem w `extracted_inner_html`.
2. **Hosted prompt** na agencie to inna wersja niż plik w repo — nie zakładać równości; porównuj długość
   i markery.
3. **`sync_agent_tools.py`** rozwiązuje narzędzia po nazwie (7), a nie po ID — ID w repo służą tylko do
   diagnostyki (`--list`). Skrypty startowe wołają go po restarcie tunelu.
4. **Bramka `data:check` w CI** wymaga, by wygenerowany plik był aktualny — po zmianie
   `mock_backend/data/*.json` uruchom `pnpm data:sync` **przed** commitem, inaczej badge robi się czerwony.
5. **`.gitattributes` = LF.** Pliki w worktree bywają CRLF; pierwszy commit po edycji przepisuje cały
   plik. To jednorazowa normalizacja, nie regresja — ale nie mieszaj jej z edycją treści w jednym diffie,
   jeśli da się uniknąć.
6. **`write_file` odmawia nadpisania** istniejącego pliku, jeśli nie widział jego pełnej treści;
   `read_file` z domyślnym limitem liczy się jako „częściowy”. Do podmiany całego pliku użyj `patch`,
   a w ostateczności `cat > plik <<'EOF'`.
7. **GitHub Actions miało 2026-11-09 major outage** — runy padały z 0 jobów. Przed diagnozą kodu
   sprawdź `githubstatus.com/api/v2/components.json`. Workflow waliduj `actionlint -no-color`.
8. **Historia gita to część deliverable** — `.git` miało 64 MB przez binarkę usuniętą z drzewa, ale nie
   z historii. K1 (2026-11-09) usunęło `cloudflared.exe` i starą wersję decku: `.git` = 31 MB.
9. **Martwe klucze i18n** nie kłują w oczy, ale `i18n:check` sprawdza tylko parytet, nie użycie —
   usuwanie rób partiami z `tsc`+`build` po każdej.

## 6. Gotowy prompt dla następnego agenta

```
Pracujesz w D:\Projects\Elevenlabs\SpaHotels (Windows, git-bash). To publiczne portfolio:
agent głosowy ElevenLabs + mock backend FastAPI (:8011) + strona Next.js 16 (PL/EN).

ZACZNIJ OD PRZECZYTANIA (w tej kolejności):
1. .planning/HANDOFF.md — stan, zasady, pułapki, otwarte decyzje
2. .planning/ROADMAP.md — sekcja EPIK K
3. .planning/phases/phase-K1..K5-*.md — pełne briefy faz
4. docs/INDEX.md — który dokument jest kanonem
5. README.md — co repo obiecuje

STAN: main == origin/main, drzewo czyste, CI zielone, 68 testów, 182 klucze i18n, 6 zabiegów.
K1 (historia gita) UKOŃCZONE 2026-11-09 — `.git` 31 MB, szczegóły w `.planning/README.md`.
Nie powtarzaj pracy z sekcji 2 HANDOFF — jest zrobiona i zweryfikowana.

ZADANIE: realizuj EPIK K fazami, w kolejności zależności (K1 → [K2 ∥ K3] → K4 → K5),
trybem GSD: jedna faza = dispatch/implementacja → pełna bramka → commit jawnymi ścieżkami
→ push → wpis w .planning/README.md (status + dowód) → następna faza.

BRAMKI po każdej fazie (wszystkie muszą być zielone, wklej wyniki):
  cd mock_backend && python -m pytest -q
  cd frontend && ./node_modules/.bin/tsc --noEmit && node scripts/check-i18n.mjs \
    && node scripts/sync-data.mjs --check && ./node_modules/.bin/next build

ZASADY:
- Przed każdą fazą sprawdź `git status --short` i `git fetch --all --prune` — inne sesje mogą pisać
  w tym samym drzewie. Nigdy `git add -A`.
- ZATRZYMAJ SIĘ i zapytaj właściciela przed: (a) kolejnym przepisaniem historii / force-push,
  (b) usunięciem czegokolwiek na remote, (c) zmianą promptu lub bazy wiedzy na żywym agencie (K2)
  — te rzeczy są nieodwracalne albo zmieniają zachowanie demo.
- Nic nie twierdź bez dowodu: każdą liczbę i każdy fakt weryfikuj komendą albo zapytaniem do API.
  Nie ufaj raportom poprzednich agentów — w tej sesji dwa raporty były nieprawdziwe (liczba podpiętych
  narzędzi, istnienie .dockerignore).
- Zmiany w żywym systemie (prompt, baza wiedzy, deck) tylko z backupem i markerem potwierdzającym,
  że nowa treść weszła. API ElevenLabs potrafi zwrócić 200 i zignorować payload.
- Nie dodawaj bramki CI na artefakt generowany, zanim go nie wygenerujesz.
- Raportuj krótko: faza, commit, liczby bramek, co odłożone i dlaczego.

ZACZNIJ od fazy K2 (prompt live) równolegle z K3 (deck) — K1 jest zrobione i zweryfikowane.
Po nich K4 (czeka na `gh auth login` właściciela), na końcu K5 wariant C (nagranie 60–90 s).
Zatrzymaj się i zapytaj właściciela przed każdą zmianą na żywym agencie (K2), usunięciem czegokolwiek
na remote i wgraniem czegokolwiek publicznego.
```
