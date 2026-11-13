# ADR: routing językowy frontendu (PL/EN) — zostajemy czy migrujemy?

**Status:** przyjęty (spike, faza M6). **Zakres:** tylko decyzja i analiza. Zero zmian w kodzie aplikacji.
**Data:** 2026-11-13.

## 1. Kontekst

Frontend (`frontend/`, Next 16.3.0, App Router) ma sześć stron publicznych: `/`, `/pokoje`, `/spa`,
`/restauracja`, `/dojazd`, `/kontakt`. Wszystkie są komponentami klienckimi (`'use client'`), bo język
żyje w `LanguageContext` (`frontend/context/language-context.tsx`):

- stan startowy to `'pl'`; wybór `'en'` jest czytany z `localStorage` (`bukowy_dwor_lang`) dopiero
  w `useEffect`, a `setLanguage` ustawia `document.documentElement.lang` po stronie klienta;
- `frontend/app/layout.tsx` ma na sztywno `<html lang="pl">`;
- metadata (tytuł, opis, OpenGraph, `alternates.canonical`) są statyczne i **po polsku**, w osobnych
  `layout.tsx` każdej trasy (`app/spa/layout.tsx` itd.);
- `app/sitemap.ts` generuje wpisy z `PUBLIC_ROUTES` (`lib/site.ts`), jeden URL na trasę, bez `hreflang`.

Ważne: `'use client'` **nie wyłącza renderowania po stronie serwera** w App Routerze. Komponent kliencki
jest i tak wyrenderowany do HTML na serwerze, ale ze stanem startowym `'pl'`. Skutek: crawler i użytkownik
EN dostają polski HTML, a treść angielska pojawia się po hydratacji. Nie ma osobnego URL dla wersji EN,
więc wyszukiwarka nie ma czego zindeksować jako angielskiej strony.

Dodatkowe ograniczenia wynikające z repo:

- **Hosting i eksport statyczny.** `frontend/next.config.mjs` nie ma `output: 'export'`.
  `.github/workflows/pages.yml` publikuje wyłącznie katalog `presentation/` (deck), nie frontend.
  Frontend ma route handler `app/api/anna/signed-url` (podpisany URL do ElevenLabs, klucz tylko po stronie
  serwera). Route handlery z logiką serwerową nie są częścią eksportu statycznego, więc eksport
  `output: 'export'` nie wchodzi w grę bez przeniesienia tej funkcji gdzie indziej.
  Hosting frontu nie jest opisany w repo; `@vercel/analytics` sugeruje Vercel, ale to do potwierdzenia.
- **Widget Anny.** `components/anna-embed-widget.tsx` renderuje `<elevenlabs-convai agent-id>`.
  `hooks/use-anna-widget.ts` przyjmuje `language` i używa go dwa razy: pobiera podpisany URL z
  `/api/anna/signed-url?lang=…` oraz wysyła zmienną dynamiczną `user_language` (i `guest_language`).
  Ta wartość musi więc być dostępna w hooku niezależnie od wybranej opcji routingu.
- **Zdarzenie `language-changed`** jest emitowane przez `setLanguage`, ale w kodzie frontendu nikt go
  nie nasłuchuje (poza tym, że zostało tam zostawione dla „widgetów spoza Reacta").

## 2. Opcje

### A. Status quo: `'use client'` + `LanguageContext`

- **Koszt:** zero. Działa dziś.
- **SEO:** słabe. Jeden URL na stronę, treść i metadata po polsku, brak wersji EN do indeksowania,
  brak `hreflang`. Przełączenie języka nie zmienia URL, więc udostępniony link zawsze otwiera PL.
- **pages.yml:** bez zmian (frontend nie jest tam publikowany).
- **sitemap.ts:** bez zmian.
- **Widget Anny:** bez zmian; hook dostaje `language` z kontekstu.
- **hreflang:** niemożliwe (brak dwóch URL-i).
- **Wada dodatkowa:** flash polskiej treści dla użytkownika, który wybrał EN.

### B. Cookie + `generateMetadata`

Język w cookie (`lang=en`), odczyt przez `cookies()` w `layout.tsx`, metadata przez `generateMetadata`.

- **Koszt:** średni. Potrzebny middleware lub odczyt cookie w każdej trasie. `cookies()` wymusza
  renderowanie dynamiczne dla każdej strony, więc znika prerender statyczny (na Vercel nadal działa,
  ale każdy request idzie przez serwer).
- **SEO:** słabe, a czasem gorsze niż A. Ten sam URL zwraca różną treść zależnie od cookie. Googlebot
  zwykle nie ma cookie, więc indeksuje PL. Trzeba dodać `Vary: Cookie`, inaczej cache CDN miesza języki.
- **pages.yml:** bez zmian.
- **sitemap.ts:** bez zmian, ale i tak brak wpisów EN.
- **Widget Anny:** hook dostaje język z cookie przez serwer. Działa.
- **hreflang:** niemożliwe (nadal jeden URL).
- **Ocena:** najgorszy stosunek kosztu do korzyści. Zmienia zachowanie cache i renderowania, nie
  dając dwóch indeksowalnych wersji.

### C. Segment `app/[lang]/…` (`/pl/spa`, `/en/spa`)

Przeniesienie tras do `app/[lang]/`, `generateStaticParams` dla `pl` i `en`, słownik ładowany w layoutcie
`[lang]`, `alternates.languages` w metadata, `hreflang` i wpisy EN w sitemap, przekierowanie `/` i starych
URL-i (`/spa` → `/pl/spa`) przez `next.config` (redirects) lub middleware.

- **Koszt:** największy. Przenosimy sześć stron i sześć layoutów; `LanguageContext` zamienia się w
  provider inicjalizowany z parametru (lub zostaje, ale zasilany z `params`); przełącznik języka staje się
  linkiem; trzeba przepisać `lib/site.ts` (ścieżki) i testy Vitest, które dziś zakładają jeden URL.
  Ryzyko: linki w treści i w widgetach, `canonical` i OG `url` (dziś `'/spa'` — ścieżki względne).
  Szacunek rzędu kilku dni pracy plus testy; to nie jest precyzyjna wycena.
- **SEO:** najlepsze. Dwa indeksowalne URL-e, metadata EN, `hreflang` (pl, en, x-default), przekierowania
  ze starych adresów zachowują sygnał.
- **pages.yml:** bez zmian dziś. Gdyby frontend trafił na statyczny hosting, `generateStaticParams` daje
  prerender obu języków, ale route handler `signed-url` nadal blokuje `output: 'export'`.
- **sitemap.ts:** trzeba generować 12 wpisów (6 tras × 2 języki) z `alternates.languages`. Prosta zmiana.
- **Widget Anny:** `language` przychodzi z `params.lang` w layoutcie; hook i `user_language` bez zmian
  w logice. Wymaga przekazania języka z serwera do klienta (props/provider).
- **hreflang:** tak, to główna korzyść tej opcji.

## 3. Decyzja

**Zostajemy przy statusie quo (A) na teraz. Migracja do `[lang]` (C) jest odłożona do momentu spełnienia
jednego z warunków poniżej.** Opcja B odrzucona.

Uzasadnienie:

1. To jest PoC i demo widgetu. Repo mówi wprost, że deploy frontendu jest otwartym punktem
   (`docs/INDEX.md`: „otwarte punkty wdrożenia"). SEO dla strony, której jeszcze nie ma publicznie,
   nie uzasadnia kosztu przeniesienia sześciu tras i testów.
2. Opcja C to jednorazowy koszt, który i tak wymaga decyzji o hostingu (czy trasy dynamiczne, czy
   statyczne). Nie ma sensu robić jej przed tą decyzją.
3. Opcja B pogarsza SEO i cache bez korzyści. Odrzucona.

**Warunki ponownego otwarcia decyzji (migrujemy do C):**

- strona frontu ma być publicznie indeksowana i wersja EN ma pozyskiwać ruch organiczny;
- hosting jest wybrany i potwierdzono, że Next działa w trybie serwerowym (to i tak potrzebne dla
  `signed-url`), co eliminuje ryzyko eksportu statycznego;
- pojawi się wymóg `hreflang` od klienta lub kampanii.

**Mała poprawka niezależna od decyzji (poza zakresem tej fazy, osobny commit):** `<html lang>` zawsze
ustawiać z serwera, nie tylko po hydratacji. To usunie część problemu z polskim HTML dla EN bez migracji.

## 4. Konsekwencje

- `pages.yml` zostaje bez zmian: publikuje deck, nie frontend. Decyzja nie zmienia jego zakresu.
- `sitemap.ts` zostaje bez zmian dziś; w opcji C przepisanie na 12 wpisów z `alternates`.
- Widget Anny: w każdej opcji język musi trafić do `useAnnaWidget`; w opcji A to kontekst, w C `params`.
- Wpis w `docs/INDEX.md` jest jedynym miejscem, gdzie ta decyzja jest widoczna z punktu wejścia.

## 5. Czego nie sprawdzono w tym spike

- Dokumentacja ElevenLabs dotycząca tego, jak `elevenlabs-convai` obsługuje język poza zmienną
  `user_language`. Opieramy się na tym, co robi kod repo.
- Rzeczywisty hosting frontu i jego konfiguracja cache (Vary, ISR). Nie ma tego w repo.
- Pomiar: nie porównywano HTML zwracanego crawlerowi dla obu opcji; wnioski o SEO wynikają z mechaniki
  Next i HTML-a, nie z pomiaru indeksacji.
