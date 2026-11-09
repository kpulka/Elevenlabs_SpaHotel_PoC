# Narracja Demo — 3 Ścieżki na Prezentację

> Skrypt dla Ciebie jako prowadzącego demo.
> Każda ścieżka ma: setup, przebieg rozmowy, co pokazuje rekruterowi.

---

## SETUP PRZED DEMO

1. Uruchom mock backend: `cd mock_backend && uvicorn main:app --reload --port 8011`
2. Otwórz panel ElevenLabs z agentem Anna (lub otwórz widżet webowy)
3. Jeśli Telegram: ustaw drugi monitor z kanałem Telegram widocznym
4. Otwórz Swagger UI (`localhost:8011/docs`) na trzecim oknie — pokaż „co pod maską"

---

## ŚCIEŻKA A — Rezerwacja Zabiegu SPA ⭐ (główna, efekt WOW)

**Co pokazuje:** tool calling, krok-po-kroku zbieranie danych, potwierdzenie SMS, latencja

**Zanim zaczniesz powiedz rekruterowi:**
> „Zaraz zadzwonię do Anny. Zwróć uwagę na trzy rzeczy: tempo mowy, sposób zbierania danych krok po kroku, i moment gdy na tym ekranie pojawi się wiadomość na Telegramie."

**Przebieg rozmowy (Ty jako gość):**
```
Ty:    "Dzień dobry, chciałbym zarezerwować jakiś masaż."
Anna:  "Dzień dobry, chętnie pomogę. Mamy masaż leczniczy pleców oraz masaż klasyczny relaksacyjny.
        Który z tych zabiegów Pana interesuje?"
Ty:    "Ten masaż pleców poproszę."
Anna:  "Oczywiście. Na który dzień chciałby Pan zarezerwować?"
Ty:    "Eee... na środę."
Anna:  [wywołuje check_spa_availability w tle]
        "Sprawdzam... Na środę 27 sierpnia mam dostępne godziny: 10:00, 14:00 i 14:30.
        Która godzina Panu odpowiada?"
Ty:    "14:30."
Anna:  "Dobrze. Jak się Pan nazywa?"
Ty:    "Kowalski, Jan Kowalski."
Anna:  "Dobrze rozumiem — rezerwuję masaż leczniczy pleców na środę 27 sierpnia
        o godzinie 14:30 dla Pana Jana Kowalskiego. Czy zgadza się?"
Ty:    "Tak, zgadza."
Anna:  [wywołuje book_spa_appointment]
        "Rezerwacja potwierdzona, numer SPA-4821. Na jaki numer telefonu
        wysłać potwierdzenie? Możemy też wysłać do córki lub syna, jeśli Pan woli."
Ty:    "Na mój: 48 123 456 789."
Anna:  [wywołuje send_sms_summary]
        "Właśnie wysłałam potwierdzenie na telefon. Czy mogę jeszcze w czymś pomóc?"
Ty:    "Nie, dziękuję bardzo."
Anna:  "Dziękuję za kontakt. Życzę miłego dnia i do usłyszenia!"
```

**Co powiedz po demo:**
> „Zwróć uwagę na kilka rzeczy. Anna zadawała jedno pytanie naraz — to nie jest przypadek, to świadoma decyzja architektoniczna dla seniorów. Parafrazowała przed potwierdzeniem — to eliminuje błędy rezerwacji. W tle zadziałały dwa webhooki: booking i SMS. I wiadomość pojawiła się tutaj [wskaż Telegram] zanim skończyłem mówić 'dziękuję'. Całkowita latencja to około 430 milisekund."

---

## ŚCIEŻKA B — Informacja z Bazy Wiedzy / RAG 📚

**Co pokazuje:** strict grounding, RAG bez halucynacji, naturalność rozmowy

**Zanim zaczniesz powiedz rekruterowi:**
> „Teraz pokażę, jak Anna odpowiada na pytania informacyjne. Agent nie może zmyślać — każda odpowiedź musi pochodzić z bazy wiedzy."

**Przebieg rozmowy (Ty jako gość):**
```
Ty:    "O której są śniadania?"
Anna:  "Śniadania serwujemy w formie bufetu szwedzkiego od 7:30 do 10:00. Czy mogę pomóc w czymś jeszcze?"

Ty:    "Czy basen wymaga czepka?"
Anna:  "Nasze baseny termalne są dostępne z łagodnymi schodkami i mocnymi poręczami.
        Jeśli chodzi o zasady dotyczące czepka, połączę Pana z recepcją,
        gdzie uzyska Pan dokładną odpowiedź."
        [wywołuje transfer_to_simulated_handoff]
```

**Co powiedz po demo:**
> „Widzisz różnicę? Na pierwsze pytanie Anna odpowiedziała bezpośrednio — ta informacja jest w bazie wiedzy. Na drugie — o czepku — bazy nie ma tej informacji, więc zamiast zmyślić, natychmiast eskaluje. To jest strict grounding. W kontekście uzdrowiska, gdzie gość może mieć chorobę serca, zmyślona odpowiedź to ryzyko prawne dla hotelu."

**Wariant — pytanie na granicy:**
```
Ty:    "Czy mogę zabrać psa?"
Anna:  "Oczywiście — akceptujemy małe psy i koty do 10 kilogramów,
        koszt to 50 złotych za dobę. Psy przewodnicy są bezpłatne
        i mogą wejść wszędzie, również do restauracji."
```
> „Tu widać, że RAG zadziałał poprawnie — ta informacja jest w bazie procedur. Anna nie musiała eskalować."

---

## ŚCIEŻKA C — Eskalacja / Human Handoff 🚨

**Co pokazuje:** bezpieczeństwo, obsługa edge cases, transfer do człowieka LIVE

**Zanim zaczniesz powiedz rekruterowi:**
> „Pokażę teraz najważniejszy safety feature. Mój telefon jest skonfigurowany jako numer dyżurki medycznej. Zaraz — dosłownie — zadzwoni."

**Przebieg rozmowy (Ty jako gość):**
```
Ty:    "Dzień dobry, chciałbym zarezerwować kąpiel borowinową,
        ale mam rozrusznik serca."
Anna:  "Rozumiem. Zanim zarezerwuję ten zabieg, chciałam zapytać
        o kwestię zdrowotną. Kąpiel borowinowa przy rozruszniku serca
        wymaga wcześniejszej konsultacji z naszym lekarzem uzdrowiskowym.
        Łączę Pana teraz z dyżurką medyczną. Chwileczkę proszę."
        [wywołuje transfer_to_simulated_handoff → log + alert na Telegramie]
```

**Co powiedz po demo:**
> „To jest ten moment. Gość powiedział 'rozrusznik serca' — agent rozpoznał to jako przeciwwskazanie do konkretnego zabiegu i nie podjął ryzyku. Połączenie trafiło natychmiast na mój telefon — w produkcji byłoby to do dyżurki pielęgniarskiej. Ważne: Anna nie powiedziała 'nie wiem' — powiedziała dokładnie dlaczego eskaluje i co się teraz stanie. Dla seniora to różnica między poczuciem bezpieczeństwa a frustracją."

---

## CO POKAZAĆ „POD MASKĄ" (dla rekrutera technicznego)

Po demo otwórz 2-3 rzeczy:

**1. Panel ElevenLabs — agent config:**
> Pokaż system prompt, listę narzędzi z JSON Schema, parametry głosu (stability, speed), konfigurację bazy wiedzy (tryby prompt/auto).

**2. Swagger UI (localhost:8011/docs):**
> Pokaż endpointy, wykonaj live request `POST /check_spa_availability` z okna Swagger — pokaż odpowiedź JSON.

**3. Logi konsoli mock backendu:**
> Pokaż czytelne logi z separatorami z każdego wywołania — „tu widać każde narzędzie które Anna wywołała i co dostała w odpowiedzi."

---

## FALLBACK — jeśli coś nie zadziała

**Mock backend nie odpowiada:**
> „Normalnie tutaj zadziałałby webhook do backendu. Pokażę Wam zamiast tego screen z odpowiedzią JSON którą agent dostaje — [pokaż plik data/spa_schedule.json]. To jest właśnie to co Anna widzi gdy sprawdza terminy."

**ElevenLabs agent nie odpowiada:**
> „Pokażę zamiast tego diagram sekwencyjny i przejdziemy przez architekturę krok po kroku — co moim zdaniem i tak jest wartościowsze z perspektywy system design."

**Zła transkrypcja:**
> „To dobry przykład rzeczywistego wyzwania — Scribe v2 świetnie radzi sobie z polskim, ale akcenty regionalne to area do poprawy. W produkcji dodalibyśmy przykłady do fine-tuningu i słownik wymowy dla specyficznych nazw."
