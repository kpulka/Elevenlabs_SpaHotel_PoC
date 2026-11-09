# Phase K5 — Żywe demo online (decyzja + wdrożenie)

## Cel
Dać recruterowi jedno kliknięcie zamiast „sklonuj i ustaw klucz”: publiczny link do strony z widgetem
Anny i działającym mock backendem, albo — jeśli hosting nie wchodzi w grę — nagranie demo jako
świadomy fallback.

**Stan wyjściowy:** demo działa lokalnie (frontend :3000, backend :8011, tunel trycloudflare z URL-em
zmienianym przy każdym starcie). W repo README jest sekcja Quick start, ale brak linku do czegokolwiek
publicznego poza GitHubem. Obowiązuje zasada: **żadnych trwałych usług projektowych na tym hoście**.

## Warianty (wybrać jeden i zapisać decyzję niżej)
- **A. Pełne demo (rekomendowane):** frontend na Vercel (`ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID`,
  `NEXT_PUBLIC_ELEVENLABS_AGENT_ID` w env) + backend z `mock_backend/tunnel/Dockerfile` na Fly.io/Render
  (port 8011) + **stały** publiczny URL backendu (własna domena/named tunnel), wpisany w 7 narzędzi
  agenta przez `sync_agent_tools.py --base-url`.
- **B. Demo częściowe:** tylko frontend na Vercel; widget działa (signed-url przez API route), ale
  narzędzia lecą do lokalnego backendu → rezerwacje nie działają. Uczciwie opisane w README.
- **C. Nagranie:** 60–90 s wideo/GIF z prawdziwej rozmowy + zrzut potwierdzenia; zero hostingu.

## Kroki (dla A)
1. Backend: wdrożyć obraz na Fly.io (`fly launch --dockerfile mock_backend/tunnel/Dockerfile`), ustawić
   `CORS_ORIGINS=https://<vercel-domain>`, `ANNA_DEMO_LOGS=0`, opcjonalnie Telegram.
2. Sprawdzić `GET /health` publicznie; sprawdzić `POST /check_spa_availability` z datą w przyszłości.
3. Frontend: projekt na Vercel (root `frontend/`), env z kluczem (sk_… **tylko w panelu**, nigdy w repo),
   `NEXT_PUBLIC_SITE_URL=https://<vercel-domain>` (sitemap/robots/OG przestaną wskazywać placeholder).
4. Przepiąć 7 narzędzi agenta na stały URL backendu: `python mock_backend/tunnel/sync_agent_tools.py --base-url https://<backend>`.
5. Test end-to-end z publicznego linku (3 scenariusze z fazy K2); transkrypty w `.planning/`.
6. README: link „Live demo” pod tytułem + sekcja „What the demo covers” (backend w pamięci → rezerwacje
   resetują się przy restarcie, to świadome).
7. Zaktualizować `.planning/AGENT_ID.txt`: adresy narzędzi i hosty.

## Weryfikacja (DoD)
- [ ] Link publiczny otwiera stronę; widget łączy się z Anną (signed-url 200).
- [ ] Rezerwacja z publicznego demo tworzy `SPA-XXXX` w backendzie (dowód: log/transkrypt).
- [ ] `sitemap.xml` i OG zawierają prawdziwą domenę (nie `bukowydwor.example`).
- [ ] README: link + uczciwe ograniczenia (memory state, brak telefonii, brak płatności).
- [ ] Koszt: 0 zł/mies. w darmowych limitach (Vercel Hobby + Fly free/Render free).

## Kluczowe / ryzyka
- **Darmowe hosty usypiają** (Fly/Render cold start 10–60 s) — pierwsza rozmowa po przerwie może się
  nie zawiązać; alternatywa: mały keep-alive ping albo wariant C jako plan B na rozmowę.
- Klucz API na hostingu = **publicznie dostępny agent**; ustawić limity w ElevenLabs (max duration,
  budżet) i monitorować zużycie kredytów.
- Nie przenosić na hosting `mock_backend/.env` z Telegramem — bot nie może być publiczny.
- Zgodnie ze standing rule: nic nie zostaje uruchomione na tym laptopie na stałe; autostart
  (`start_anna.sh` w on-logon) wyłączyć, gdy demo żyje w chmurze.

## Scenariusz nagrania (wariant C — wybrany 2026-11-09)

Cel: **60–90 s**, jedno ujęcie ciągłe tam, gdzie to możliwe, plus cięcie na log backendu. Nagranie ma
dowieść, że liczby w rozmowie pochodzą z narzędzi, nie z modelu.

**Przygotowanie (5 minut przed nagraniem)**
1. `bash mock_backend/tunnel/start_anna.sh` — backend `:8011`, tunel i przepięcie 7 narzędzi; sprawdź
   `GET /health` publicznie i w panelu, że narzędzia wskazują nowy URL.
2. `cd frontend && pnpm dev` → `http://localhost:3000`.
3. Osobne okno terminala z logiem backendu (`demo_log`) — będzie potrzebne na cięcie dowodowe.
4. Przeglądarka 1440×900, zoom 100%, język PL, powiadomienia wyłączone, kursor widoczny.
5. Kartka z numerem rezerwacji do scenariusza anulowania (jeśli nagrywasz też anulowanie) i z godziną
   w oknie <2 h — inaczej scenariusz nie pokaże reguły 50%.

**Ujęcia**
| czas | obraz | mówisz / robisz |
|---|---|---|
| 0:00–0:08 | strona główna, hero + przycisk widgetu | „To strona hotelu z agentem osadzonym jak w normalnym wdrożeniu." |
| 0:08–0:25 | widget otwarty, rozmowa | „Dzień dobry, chciałbym zarezerwować masaż." — agent **musi** dopytać o rodzaj; Ty: „leczniczy pleców". |
| 0:25–0:50 | ta sama rozmowa | podajesz termin; agent sprawdza dostępność, mówi **120 zł / 30 min**, pyta o dane → „Piotr Zieliński, +48 600 100 200" → potwierdzenie **SPA-XXXX**. |
| 0:50–1:05 | cięcie: terminal z logiem | `POST /check_spa_availability 200`, `POST /book_spa_appointment 200`, numer rezerwacji — dowód, że cena i termin przyszły z backendu. |
| 1:05–1:20 | z powrotem widget albo karta potwierdzenia | „Cena, godzina i numer rezerwacji pochodzą z mockowego PMS-u — agent ich nie wymyśla." |

**Zasady**
- Bez przyspieszania i bez wycinania momentu wywołania narzędzia — to jest cały dowód.
- Nie pokazuj klucza API, panelu ElevenLabs z ID agenta ani `.env`.
- Jeśli mikrofon zawiedzie: tryb „Napisz" jest akceptowalny, ale wtedy zaznacz w podpisie, że to czat.
- Zapisz plik jako `presentation/assets/demo_anna_60s.mp4` (albo link, jeśli plik jest za duży na repo)
  i dodaj jedno zdanie w `README.md` pod sekcją o decku.

**Blokada:** nagranie wymaga żywej rozmowy → kredyty ElevenLabs. Do resetu (2026-11-22 04:02 UTC)
scenariusz jest gotowy, ale nie ma czego nagrywać.
