# Brief / Wytyczne dla agenta (ElevenLabs Docs)

Poniższy dokument to **kompletny pakiet do przekazania zewnętrznemu agentowi/asystentowi**, który ma pełną dokumentację ElevenLabs. Przekaż mu ten plik + pliki źródłowe wymienione w sekcji „Dane wejściowe".

---

## 1. Kontekst (kim jesteśmy, co robimy)
- Przygotowujemy **case study** na stanowisko **Deployment Strategist w ElevenLabs** (proces rekrutacyjny, etapy V1 i V2).
- Budujemy **Wirtualnego Recepcjonistę AI** dla sieci hoteli & SPA (Uzdrowisko Termalne „Bukowy Dwór", Krynica-Zdrój).
- **Odbiorca końcowy:** goście seniorzy 60+ (wolne tempo, uprzejmość, minimum żargonu).
- Produkt końcowy = **prezentacja** (PowerPoint lub Google Slides), nie działający system produkcyjny.

## 2. Podjęte decyzje (już zablokowane — nie zmieniaj)
1. **Persona:** „Anna" (ciepły, empatyczny żeński głos).
2. **Zakres narracji:** „PoC (demo na mockupach) → wizja docelowa (pełne wdrożenie)". Pokazujemy myślenie architektoniczne.
3. **Format prezentacji:** PowerPoint lub Google Slides.

## 3. Dane wejściowe (pliki, które agent MUSI przeczytać)
Ścieżki względem `D:\Projects\Elevenlabs\SpaHotels\`:
- `ElevenLabs_Etap_V1.md` — wytyczne etapu 1 (czego oczekuje rekruter).
- `ElevenLabs_Etap_V2.md` — wytyczne etapu 2 (product design, wireframing, system design, HM).
- `docs/specyfikacja_poc_recepcjonista_ai.md` — spec PoC (mockupy, 3 ścieżki demo).
- `docs/specyfikacja_recepcjonista_ai.md` — pełna spec funkcjonalna (architektura, tool calling, RODO, roadmapa).
- `docs/baza_wiedzy_rag_bukowy_dwor/*.md` (5 plików) — wiedza hotelowa dla RAG.

## 4. Czego potrzebujemy od agenta (zakres pracy — TYLKO analiza/rekomendacje, NIE kod)

Agent ma odpowiedzieć, w oparciu o aktualną dokumentację ElevenLabs, na poniższe. Każda odpowiedź musi wskazywać **co konkretnie w ElevenLabs pasuje do naszej spec**.

### A. Architektura konwersacyjna
1. **Conversational AI Agent vs Custom LLM (Webhook)**: którą ścieżkę wybrać dla PoC i dla wersji docelowej? Jak skonfigurować przepływ STT → LLM → TTS.
2. **Konfiguracja agenta**: system prompt, first message, interruption, endpointing (VAD) — jakie parametry dla rozmówcy mówiącego wolno (seniorzy).

### B. Wiedza (RAG / Knowledge Base)
3. Jak dodać nasze 5 plików Markdown jako bazę wiedzy? Chunking, limity, jak agent z niej korzysta.
4. Jak zapewnić, by agent odpowiadał wyłącznie z tej wiedzy (nie zmyślał cen/terminów).

### C. Tool calling / integracje
5. Jak zdefiniować narzędzia (check availability, book, sms, transfer) — natywnie w panelu czy przez webhook? JSON Schema.
6. **Bramka SMS**: rekomendowana ścieżka do demo (Discord/Slack webhook zamiast płatnej bramki) vs realny SMS.
7. **Human handoff / transfer**: jak przekazać połączenie do recepcji/dyżurki.
8. **Telefonia**: WebRTC (demo) vs SIP/PBX/mikser — rekomendowana ścieżka dla pełnego wdrożenia.

### D. Głos i TTS
9. Rekomendowany model TTS i głos do polskiego, dla seniorów (wyraźny, spokojny, niska latencja). Nasza preferencja: „Anna".

### E. Enterprise / „dobre wdrożenie"
10. Skalowanie na sieć hoteli (multi-obiekt): tenant model, voice/agent per obiekt czy jeden wspólny.
11. RODO / compliance: co ElevenLabs oferuje (retencja, anonimizacja, DPA, regiony).
12. Analiza kosztów/limitów: jaki plan jest potrzebny dla PoC vs produkcyjnego wdrożenia.

### F. Metodyka prezentacji
13. Jak najlepiej zademonstrować „to, co pod maską" (custom LLM, webhook, mockupy) na slajdach — co pokazać jako diagram, co jako screeny.

## 5. Zasady (constraints)
- **NIE pisz kodu ani implementacji.** Tylko architektura, konfiguracja, rekomendacje, diagramy.
- Odpowiadaj po polsku, zwięźle, w punktach.
- Każdą rekomendację wiąż z konkretną funkcją/parametrem ElevenLabs (nazwa, gdzie się znajduje).
- Oznaczaj, co jest wersją **PoC**, a co **docelową** (Faza II).

## 6. Oczekiwany wynik (output)
Zwrotnie: uzupełniony ten sam plik (sekcja 4 wypełniona) LUB osobny plik `plan/03_rekomendacje_integracyjne.md` z odpowiedziami A–F, gotowy do wbudowania w prezentację.