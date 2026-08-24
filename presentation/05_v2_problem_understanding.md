# V2 — Problem Understanding: Lista Pytań

> **Jak działa ta sesja:**
> Rekruter daje Ci niedookreślony brief — np. „Zaprojektuj asystenta głosowego dla hotelu."
> Twoje zadanie: zadawać pytania i kształtować rozwiązanie WE WSPÓŁPRACY z prowadzącym.
> NIE szukasz informacji w sieci. NIE monologujesz. Dyskutujesz.
>
> **Czego szuka rekruter:**
> - Czy pytasz zanim odpowiesz?
> - Czy Twoje pytania są trafne (nie trywialne)?
> - Czy słuchasz odpowiedzi i budujesz na nich?
> - Czy umiesz ograniczyć zakres zamiast projektować wszystko naraz?

---

## STRUKTURA PYTAŃ — 5 obszarów

Używaj tej kolejności. Każdy obszar = 2-3 pytania, potem sprawdź czy iść dalej.

---

### OBSZAR 1 — Użytkownik końcowy (kim jest, czego potrzebuje)

> *Zasada: nigdy nie projektuj bez persony. Zanim powiesz słowo o architekturze — ustal kto korzysta.*

**Pytania:**
1. „Kto jest głównym użytkownikiem tego asystenta — goście hotelowi, pracownicy recepcji, czy obie grupy?"
2. „Jaki jest typowy wiek i profil gościa? Czy mamy do czynienia z seniorami, biznesmenami, turystami?"
3. „Czy gość ma do asystenta dotrzeć sam z siebie, czy asystent ma *inicjować* kontakt (np. dzwonić przed przyjazdem)?"

**Czego słuchasz w odpowiedzi:**
- Jeśli: *„seniorzy, telefon"* → mówisz: „W takim razie latencja i ton głosu stają się krytyczne — szybki, robotyczny głos odstraszy rozmówcę."
- Jeśli: *„biznesowi, aplikacja"* → mówisz: „To zmienia kanał. Widget WebSocket zamiast SIP Trunk, i możemy być bardziej zwięźli."

---

### OBSZAR 2 — Kanał i infrastruktura (gdzie to działa)

> *Zasada: „voice AI" może znaczyć pięć różnych rzeczy technicznie. Upewnij się, o czym mówisz.*

**Pytania:**
1. „Przez jaki kanał ma działać asystent — telefon tradycyjny, widget na stronie www, aplikacja mobilna, terminal w recepcji?"
2. „Czy hotel ma już centralę telefoniczną (PBX)? Czy możemy się do niej podpiąć przez SIP Trunk?"
3. „Czy mamy do czynienia z jednym obiektem czy siecią hoteli? To zmienia podejście do konfiguracji."

**Czego słuchasz:**
- *„sieć 10 hoteli"* → „Kluczowe pytanie: jeden agent centralny z Dynamic Variables czy osobna instancja per hotel? Rekomendowałbym centralny — łatwiejsze utrzymanie."
- *„widget na stronie"* → „Musimy rozmawiać o Signed URLs — agent nie może eksponować klucza API na froncie."

---

### OBSZAR 3 — Zakres funkcjonalny (co ma umieć)

> *Zasada: zawęź zakres aktywnie. Nie czekaj aż rekruter powie co ciąć — zaproponuj sam.*

**Pytania:**
1. „Jakie są 3 najczęstsze powody dla których gość teraz dzwoni do recepcji? Chcę zacząć od tych."
2. „Czy asystent ma tylko *informować* (FAQ, godziny), czy też *działać* (rezerwować, anulować, przekierowywać)?"
3. „Co się dzieje gdy asystent nie zna odpowiedzi lub sytuacja jest trudna? Czy musi być opcja przekazania do człowieka?"

**Typowe odpowiedzi i Twoja reakcja:**
- *„rezerwacje i info"* → „Dobrze. To oznacza dwie warstwy: RAG dla pytań statycznych i tool calling dla akcji dynamicznych. Zacznijmy od MVP z RAG — tańsze, szybsze w wdrożeniu."
- *„tylko FAQ"* → „W takim razie możemy uprościć architekturę — nie potrzebujemy webhooka do PMS na etapie MVP."

---

### OBSZAR 4 — Dane i systemy zewnętrzne (integracje)

> *Zasada: integracje to zawsze największe ryzyko wdrożeniowe. Zapytaj o nie wcześnie.*

**Pytania:**
1. „Jakie systemy hotelowe są już w użyciu? PMS (np. Opera, KWHotel), CRM, system rezerwacji SPA?"
2. „Czy mamy dostęp do API tych systemów, czy będziemy musieli działać przez pliki lub ręczne eksporty?"
3. „Kto ze strony hotelu będzie właścicielem technicznym tego wdrożenia — czy jest osoba która zarządza integracjami?"

**Czego słuchasz:**
- *„mamy API do Opery"* → „To zmienia harmonogram — możemy przejść od mocku do produkcji w 2-3 tygodnie."
- *„nie mamy API"* → „W takim razie na MVP działamy na statycznej bazie wiedzy i mockach. To wystarczy do walidacji."

---

### OBSZAR 5 — Sukces i ograniczenia (jak mierzymy, co blokuje)

> *Zasada: definicja sukcesu musi być przed architekturą, nie po. Inaczej projektujesz w próżni.*

**Pytania:**
1. „Po czym poznamy za 3 miesiące, że wdrożenie się powiodło? Jakie KPI są dla klienta ważne?"
2. „Czy są ograniczenia regulacyjne, compliance lub RODO które muszę uwzględnić od początku?"
3. „Jaki jest realny budżet i timeline — czy mówimy o pilotażu na jeden hotel w 4 tygodnie, czy o pełnym wdrożeniu?"

**Typowe odpowiedzi:**
- *„KPI: % rozmów obsłużonych bez człowieka"* → „Dobry KPI. Dodałbym też CSAT — asystent który obsługuje 90% rozmów ale denerwuje gości to nie sukces."
- *„dane medyczne, uzdrowisko"* → „To wymaga Zero Retention Mode i Conversation History Redaction — to plan Enterprise ElevenLabs. Musimy to wliczyć w koszty od razu."

---

## JAK TO PRZEPROWADZIĆ W PRAKTYCE

### Tempo i postawa
- Pytaj grupami po 1-2 pytania, nie listy 10 na raz.
- Po każdej odpowiedzi: **sparafrazuj** co usłyszałeś i **powiedz co to zmienia** w projekcie.
- Jeśli rekruter mówi *„sam zdecyduj"* — zdecyduj i powiedz dlaczego: „Zakładam X, bo Y. Jeśli to złe założenie, daj mi znać."

### Sygnał że czas zamknąć pytania i przejść do rysowania
Masz wystarczająco dużo gdy wiesz:
- ✅ Kto jest użytkownikiem (persona)
- ✅ Przez jaki kanał (telefon / widget)
- ✅ Co ma umieć (min. 2-3 funkcje)
- ✅ Co jest poza zakresem MVP
- ✅ Jak wygląda sukces

Wtedy powiedz: *„Okej, myślę że mam wystarczający kontekst żeby zacząć szkicować. Zacznę od architektury wysokopoziomowej."*

---

## PYTANIA KTÓRYCH NIE ZADAWAĆ

❌ „Jaka ma być nazwa asystenta?" — trywialne, nie shows thinking  
❌ „Jakiego LLM używacie?" — za techniczne, za wcześnie  
❌ „Czy mają logo w określonych kolorach?" — UI design, nie twoja rola teraz  
❌ Ciąg 10 pytań bez słuchania odpowiedzi — to przesłuchanie, nie dyskusja
