# V2 — Przygotowanie na Hiring Manager (historie STAR + zachowanie)

> Cel: mieć gotowe, spójne odpowiedzi behawioralne na pytania Hiring Managera.
> Metoda STAR: **S**ituation, **T**ask, **A**ction, **R**esult — konkretne, z liczbami, ≤ 90 sek.

---

## TEMATY, KTÓRE PEWNIE PADNĄ

1. **Niejednoznaczny problem → dekompozycja** (V2 wymaga tego wprost)
2. **Debugging pod presją** (ostatnio mieliśmy realny przypadek!)
3. **Integracja z systemem którego nie kontroluję** (ElevenLabs API / webhook)
4. **Współpraca z zespołem / stakeholderem**
5. **Wdrożenie — przełożenie techniki na wartość biznesową**

---

## HISTORIA 1 — Dekomponuję niejednoznaczny problem  [idealna na V2 problem-understanding]

**S:** Dostałem niedookreślony brief podczas case study: „Zaprojektuj asystenta głosowego dla hotelu."
**T:** Nawet nie zacznę rysować. Musiałem ustalić: kto rozmawia, ile hoteli, co ma umieć.
**A:**
- Zadałem pytania w 5 obszarach (persona → kanał → zakres → integracje → sukces), NIE w sieci.
- Kluczowe spostrzeżenie: dla persony seniora 60+ **latencja i ton są ważniejsze niż funkcje**.
- Zawęzłem MVP do 3 ścieżek zamiast pełnego wdrożenia.
**R:** Powstał spójny deck + działający prototyp Ann (żywa strona z widgetem). Rekruter zobaczył tok myślenia, nie szablon.

---

## HISTORIA 2 — Debugging 'Permission denied' w mikrofonie  [realna, świeża]

**S:** Widget ElevenLabs na stronie nie uruchamiał rozmowy — błąd `Permission denied`, konsola `microphone is not allowed`.
**T:** Wiedziałem że agent działa (zweryfikowany), więc to integracja frontendu.
**A:**
- Zdiagnozowałem: **nagłówek `Permissions-Policy: microphone=()` w `next.config.mjs`** blokował dostęp do mikrofonu na całej stronie.
- Sprawdziłem CORS (OK), React 19 custom-element atrybuty (naprawione przez `setAttribute`), potem nagłówki HTTP.
- Znajazłem sedno: Next konfiguracja wyłączała mikrofon. Zmieniłem na `camera=(), geolocation=()` → permission state `prompt`.
**R:** Rozmowa głosowa z Anną zaskoczyła. Naprawiłem root cause, nie objaw. Bonus: `next build` Turbopack crash → przeszedłem na webpack.

---

## HISTORIA 3 — Integracja z API którego nie kontrolujesz  [webhook / tool calling]

**S:** Agent Anna miał Calling tool (check_spa_availability, book…) wywoływać webhook do mock PMS.
**T:** Narzędzie MCP `add_knowledge_base_to_agent` zwracało błąd (`AgentConfig has no attribute get`).
**A:**
- Nie czekałem na fix dostawcy — napisałem **autonomiczny skrypt REST** omijający zepsuty MCP.
- Zweryfikowałem prawdziwą strukturę API (przez OpenAPI) zamiast zgadywać endpointy.
- Podpiąłem KB + RAG + narzędzia przez PATCH `/agents/{id}`, oraz dynamic var / tunel dla webhooków.
**R:** Pełny agent z RAG + tool callingiem działa. Efektem ubocznym jest arkanal — uczyłem się ich API „na boju".

---

## HISTORIA 4 — Współpraca z human handoff / projektowanie bezpieczne  [RODO]

**S:** Goście uzdrowiskowi, dane medyczne (przeciwwskazania, diety).
**T:** Projektowałem asystenta który nie wymyśla (medical risk) i szanu je RODO.
**A:** Strict grounding (brak info = transfer do człowieka), Zero Retention Mode, Conversation History Redaction, pytania o przeciwwskazania przed zabiegiem.
**T:** Agent nigdy nie potwierdza rezerwacji bez tool call, eskalacja deterministyczna.

---

## HISTORIA 5 — Przekształcanie techniki na biznes (skalowanie / ROI)

**S:** Sieć hoteli — >1 obiekt.
**T:** Jak skogoować Annę bez 10-krotnienia kosztów utrzymania.
**A:** jeden centralny agent + dynamic variables per hotel (SIP UUI RFC 7433), zamiast instancji per obiekt.
**T:** Dodanie hotelu = zmiana danych, nie konfiguracja. PoC za $22, skala za $299 — ROI prawie liniowy na 10 obiektów.

---

## PRZYGOTOWANIE POSTAWY (client-facing / HM)

| Pytanie | Odpowiedź |
|---|---|
| „Co ekscytuje Cię w ElevenLabs?" | Konwergencja STT/LLM/TTS w jednym nie — natywna pętla zamiast kaskady to przełom w latencji i naturalności. |
| „Jak handle niejasny brief?" | Zadaję 3-5 pytań, parafrazuję odpowiedź i wracam z decyzją — pokazuję tok myślenia, nie zgaduję sam. |
| „Gdy coś nie działa dostawcy?" | Diagnozuję root cause (headers, CORS, SDK), robię workaround i przekazuję feedback. |
| "Jakie wodorzenie kubat?" | Przechodzę od mocku do prototypu do produkcji; KPI przed architekturą. |

---

## EXCALIDRAW — NAJWAŻNIEJSZE ZAPAMIĘTANIE

- Zarządzaj rysowaniem: Szkic 1 (architektura) → Szkic 2 (przepływ rozmowy) → Szkic 3 opcjonalny (panel).
- Mów cały czas. Każdy prostok laa: co to, dlaczego tu.
- Tylko prostokąty + strzałki + tekst; zaokrąglone = start/koniec, ostre = krok.
- Zakończ każdy szkic pytaniem; nie przepraszaj za estetykę.

*(Szczegółowe scenariusze rysowania w `06_v2_excalidraw.md` — ten plik jest streszczeniem.)*