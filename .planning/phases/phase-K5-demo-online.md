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
