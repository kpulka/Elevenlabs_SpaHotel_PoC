# Tok Myślenia „na głos" — Rozmowa V1 (Case Study)

> **Cel:** Pokazać rekruterowi sposób myślenia, nie gotowe rozwiązanie.
> ElevenLabs szuka kogoś kto *pushuje pracę do przodu* i *łączy technikę z biznesem*.
> Ten dokument to Twój wewnętrzny skrypt — nie czytaj go wprost, internalizuj go.

---

## JAK ZACZĄĆ — pierwsze 60 sekund

Zamiast od razu „rozwiązywać", zacznij od **pytań doprecyzowujących**. To pokazuje dojrzałość.

**Przykładowe otwarcie:**
> „Zanim zaproponuję architekturę, chciałbym upewnić się, że dobrze rozumiem kontekst biznesowy.
> Kilka pytań: Czy sieć hoteli ma już jakiś system PMS? Czy połączenia przychodzą przez centralę SIP, czy mówimy o widgecie webowym? Jaka jest tolerancja na opóźnienie — czy goście dzwonią z pilnymi sprawami medycznymi, czy głównie z rezerwacjami?"

Czego to dowodzi:
- Rozumiesz, że architektura zależy od kontekstu
- Nie zakładasz — pytasz
- Myślisz w kategoriach wdrożenia, nie POC-u

---

## DEKOMPOZYCJA PROBLEMU — jak myśleć na głos

Użyj tej struktury gdy dostaniesz otwarte pytanie:

```
1. KTO jest użytkownikiem? → persona, ograniczenia
2. CO chce osiągnąć? → job-to-be-done
3. GDZIE system musi działać? → kanał, infrastruktura
4. KIEDY może się posypać? → edge cases, błędy
5. JAK zmierzymy sukces? → KPI, metryki
```

**Przykład zastosowania dla tego case study:**

**1. KTO?** Seniorzy 60+ — wolne tempo mowy, brak tolerancji na błędy AI, nieufność wobec technologii.
→ *Decyzja architektoniczna:* `turn_timeout 3.0s`, `turn_eagerness: Patient`, `speed: 0.85x`

**2. CO?** Rezerwacja zabiegu / pokoju przez telefon, bez konieczności czekania na recepcjonistę.
→ *Decyzja:* Tool calling (availability + booking) + RAG dla informacji ogólnych

**3. GDZIE?** Telefon (SIP Trunk centrali PBX) lub widget na stronie hotelu.
→ *Decyzja:* ElevenLabs natywny agent (WebRTC dla widgetu, SIP Trunk dla telefonu)

**4. KIEDY się posypie?**
- Gość pyta o coś, czego nie ma w bazie → strict grounding + transfer
- Zabieg z przeciwwskazaniami → protokół bezpieczeństwa przed potwierdzeniem
- Webhook PMS nie odpowiada → fallback + „połączę z recepcją"
- Zbyt dużo jednoczesnych połączeń → Burst Pricing (3x concurrent calls)

**5. JAK mierzę sukces?**
- % rozmów zakończonych rezerwacją bez udziału człowieka
- Czas oczekiwania na pierwszą odpowiedź (target: <500ms)
- NPS / satysfakcja gości (ankieta SMS po pobycie)
- Koszt rozmowy vs koszt recepcjonisty (ElevenLabs: ~$0.08/min vs ~$25/h pracownik)

---

## NARRACJA TECHNICZNA — jak wytłumaczyć architekturę nie-technikowi

**Złe (za technicznie):**
> „Używamy Scribe v2 Realtime z VAD i WebRTC transport layer, który feed-uje do Gemini 3.5 Flash Lite z RAG..."

**Dobre (technika przez pryzmat wartości):**
> „System działa tak: gość mówi, Anna słyszy go w czasie rzeczywistym — w ciągu 150 milisekund zamienia mowę na tekst. Potem myśli — sprawdza naszą bazę wiedzy o hotelu i wykonuje akcje jak sprawdzenie wolnych terminów. Na koniec mówi — w sposób naturalny, ciepły, specjalnie zwolniony dla starszych gości. Cały cykl trwa mniej niż pół sekundy. Dla gościa to brzmi jak normalna rozmowa z człowiekiem."

---

## KLUCZOWE DECYZJE ARCHITEKTONICZNE — miej gotowe uzasadnienie

### Dlaczego natywny ElevenLabs Agent, nie Custom LLM?

**Pytanie rekrutera:** „Czemu nie zbudowałeś własnego pipeline'u STT→LLM→TTS?"

**Odpowiedź:**
> „Tradycyjny kaskadowy pipeline (STT → zewnętrzny LLM → TTS) generuje skumulowane opóźnienie powyżej 2 sekund — to zabija naturalność dialogu. ElevenLabs Agents łączy te trzy warstwy w jedną zunifikowaną pętlę konwersacyjną, co redukuje latencję do ~430ms. Dla seniorów, którzy już mają obawy przed technologią, każda sekunda ciszy to utrata zaufania."

### Dlaczego Eleven v3 Conversational zamiast Flash?

**Pytanie rekrutera:** „Flash jest 4x szybszy. Czemu nie użyłeś?"

**Odpowiedź:**
> „Flash generuje mowę w ~75ms zamiast ~280ms, ale kosztem ekspresji emocjonalnej. Dla młodego gościa to idealne. Dla seniora 70+ ciepło tonu i naturalna intonacja to nie luksus — to warunek zaufania. Jeśli głos brzmi robotycznie, gość się rozłącza. ROI z wyboru lepszego modelu głosowego jest wyższy niż zaoszczędzone 200ms."

### Dlaczego RAG a nie 'wsadź wszystko do prompta'?

**Pytanie rekrutera:** „Macie tylko 5 plików. Czemu nie wrzucić wszystkiego do system promptu?"

**Odpowiedź:**
> „Dwa pliki krytyczne (procedury i cennik) wrzucamy na stałe do promptu — muszą być dostępne w każdej turze bez wyjątku. Ale katalog SPA i opis dojazdu to opisy narracyjne — wstrzykiwanie ich za każdym razem to marnotrawstwo okna kontekstowego i podnosi koszty tokenów. RAG w trybie auto wstrzykuje tylko dopasowane fragmenty. To architektura, która skaluje się do setek dokumentów bez zmiany kodu."

### Dlaczego strict grounding jest kluczowy w branży medyczno-uzdrowiskowej?

**Pytanie rekrutera:** „Co jeśli gość zapyta o coś czego nie ma w bazie?"

**Odpowiedź:**
> „To jest właśnie najważniejsza zasada tego wdrożenia. Agent który zmyśla cenę zabiegu to tylko kłopot sprzedażowy. Agent który zmyśla przeciwwskazania do zabiegu borowinowego może komuś zaszkodzić. Dlatego zaimplementowałem hard rule: brak informacji w bazie = natychmiastowe przekazanie do człowieka. Bez wyjątków. To nie jest ograniczenie — to feature, który chroni hotel przed odpowiedzialnością prawną."

---

## WARTOŚĆ BIZNESOWA — liczby, które warto znać

| Metryka | Wartość |
|---|---|
| Koszt minuty rozmowy (ElevenLabs) | ~$0.08 |
| Koszt recepcjonisty / godzina | ~25–35 PLN brutto ≈ $6–9 (Polska; narzuty pracodawcy podnoszą to o ok. 20–40%) |
| Break-even przy 275 min/mies. (Creator plan) | $22 ≈ 88 PLN ≈ 3,5 h pracy recepcjonisty — parytet kosztu, nie oszczędność |
| Czas pracy recepcjonisty AI | 24/7, 0 zwolnień lekarskich |
| Czas wdrożenia MVP | 2-4 tygodnie (PoC w 1 dzień) |
| Skalowanie na 10 hoteli | +0 agentów (Dynamic Variables) |

**Zdanie do zapamiętania:**
> „Na Creatorze za $22/miesiąc mam 275 minut obsługi — to mniej niż godzina pracy recepcjonisty. Ale ta godzina obsługi działa o 3 w nocy, mówi po polsku i nigdy nie jest nieuprzejma."

---

## EDGE CASES — pokaż, że myślisz o tym co może pójść źle

Recruiter doceni, jeśli sam z siebie poruszysz ryzyka:

1. **„Co jeśli gość mówi gwarą lub z silnym akcentem?"**
   → Scribe v2 ma nierównomierne wsparcie dialektów. Mitygacja: `turn_timeout` 3s daje więcej czasu na doprecyzowanie, a przy braku zrozumienia Anna prosi o powtórzenie.

2. **„Co jeśli serwer mock padnie podczas prezentacji?"**
   → Na demo mam statyczne odpowiedzi jako fallback. W produkcji: retry logic + circuit breaker po stronie webhooka.

3. **„Co jeśli gość mówi jednocześnie z Anną?"**
   → `turn_eagerness: Patient` + interruption handling. Anna daje się przerwać — to naturalniejsze niż robot który dokańcza zdanie.

4. **„Co z RODO i danymi medycznymi?"**
   → Zero Retention Mode (dane tylko w RAM), Conversation History Redaction (maskowanie PII), Data Residency EU. Dla prawdziwego wdrożenia: DPA z ElevenLabs + zgoda ustna gościa na początku rozmowy.

---

## PYTANIA DO REKRUTERA (obowiązkowe — V1 wymaga tego wprost)

Przygotuj 3-5 pytań. Cel: pokazać zainteresowanie kulturą pracy, nie tylko produktem.

1. **O codzienną pracę:** „Jak wygląda typowy tydzień Deployment Strategist — ile czasu na klientów vs budowanie wewnętrznych narzędzi/procesów?"

2. **O wyzwania techniczne:** „Jakie są najczęstsze pułapki przy wdrożeniach enterprise — co klienci zazwyczaj niedoszacowują?"

3. **O skalę i decyzje:** „Czy Deployment Strategist ma realny wpływ na decyzje produktowe, kiedy widzi powtarzający się ból klienta?"

4. **O kulturę:** „Jak zespół radzi sobie z sytuacją, gdy klient ma oczekiwania, których platforma jeszcze nie obsługuje — co się wtedy dzieje?"

5. **O sukces:** „Po czym poznasz, że ktoś na tym stanowisku świetnie sobie radzi — co odróżnia dobrego Deployment Strategist od bardzo dobrego?"
