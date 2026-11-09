> **Status:** aktualny (2026-11) — źródło prawdy dla procedur operacyjnych (Procedures/SOP).

# Procedury Operacyjne Agenta ElevenLabs (Procedures SOP) — Anna (Bukowy Dwór)

> Dokumentacja procedur zadaniowych (**ElevenLabs Agent Procedures**) dla Wirtualnej Recepcjonistki Anny w Uzdrowisku Termalnym „Bukowy Dwór”.
> Zgodna z oficjalną specyfikacją ElevenAgents: dynamicznie ładowane instrukcje operacyjne (SOP), warunki aktywacji (Trigger Conditions), reguły biznesowe, walidacje i integracje z systemem hotelowym PMS.

---

## 1. Czym są Procedury w ElevenLabs i dlaczego ich używamy?

W architekturze ElevenLabs **Procedures** to wyspecjalizowane, modularne instrukcje krok po kroku ładowane do kontekstu agenta **wyłącznie wtedy, gdy wystąpi konkretna intencja gościa**.

### Korzyści biznesowe i techniczne:
1. **Odchudzenie Promptu Głównego:** Zamiast utrzymywać 5000 słów z opisem każdego wyjątku, agent ma lekki prompt bazowy (~400 słów), a szczegółowe procedury (np. zwrot zadatku, reklamacja) ładuje na żądanie.
2. **Determinizm i Zgodność z Prawem:** Zapewniają ścisłe przestrzeganie regulaminu uzdrowiska, polityki zadatków i wytycznych medycznych bez ryzyka improwizacji LLM.
3. **Standaryzacja Obsługi Seniora:** Każda procedura zawiera wymóg parafrazowania, cierpliwego tonu i wysyłki SMS z podsumowaniem.

### Wspólny kontrakt narzędzi (obowiązuje w każdej procedurze)
W agencie istnieje **7 narzędzi** + `end_call`: `check_spa_availability`, `book_spa_appointment`, `cancel_spa_appointment`, `reschedule_spa_appointment`, `check_room_availability`, `send_sms_summary`, `transfer_to_simulated_handoff`. Zasady wspólne:

- **`language` w każdym wywołaniu** (`pl`/`en`, z dynamicznej zmiennej `user_language`) — dzięki temu `message`, `fee_rule` i błędy wracają w języku gościa.
- **`success: false` / `available: false` to odpowiedź biznesowa, nie awaria.** Czytaj `message`, `slots`, `ambiguous`, `available_services` / `available_room_types` i pytaj dalej.
- **`ambiguous`** (lista nazw) — przeczytaj kandydatów i dopytaj, nigdy nie zgaduj.
- **`price_pln` i `duration_min`** — jedyne źródło ceny i czasu zabiegu; nie zgaduj kwot.
- **HTTP 422 = błąd formatu** (data, godzina, pusty numer). Nie powtarzaj identycznego wywołania — poproś o datę `RRRR-MM-DD` i godzinę `GG:MM`, potem wywołaj ponownie z poprawnymi danymi.
- **`appointment_datetime`** przy anulowaniu to ISO 8601 **z godziną** (`2026-11-09T18:30`); bez godziny backend zawsze naliczy 50 %.

---

## 2. Katalog 7 Głównych Procedur Bukowego Dworu

### 2.1 Rejestr procedur w agencie (nazwa → `procedure_id`)

| Procedura | `procedure_id` |
|---|---|
| `procedura_anulowania_rezerwacji_spa` | `agtprc_5301m0r0e03mfy5b2se1afbye78z` |
| `procedura_zmiany_terminu_zabiegu` | `agtprc_9001m0r0e0a5f4fv2j88e8ewz9t1` |
| `procedura_odwolania_pobytu_i_zwrotu_zadatku` | `agtprc_0701m0r0e0gre1ra8jhh51xm1pan` |
| `procedura_wczesnego_przyjazdu_i_poznego_wyjazdu` | `agtprc_3701m0r0e0qnfpf9ysz2g5a62trs` |
| `procedura_zgloszenia_diety_leczniczej` | `agtprc_8001m0r0e0yff679gj7sxvdgd1sk` |
| `procedura_zamowienia_transportu_i_meleksa` | `agtprc_7001m0r0e15kfv28bnc9x9x3p11t` |
| `procedura_reklamacji_i_trudnego_goscia` | `agtprc_1801m0r0e1c1enmvsrcttyh36jq7` |

*Źródło: `.planning/workflow/procedure_ids.json`.*

---

### PROCEDURA 1: `procedura_anulowania_rezerwacji_spa`
*Anulowanie zabiegu balneologicznego lub masażu w strefie Medical SPA*

- **Trigger / Kiedy aktywować:** Gość mówi, że nie może przyjść na zabieg, chce zrezygnować z masażu/kąpieli lub prosi o odwołanie rezerwacji.
- **Reguła biznesowa:**
  - Odwołanie **powyżej 2 godzin** przed terminem zabiegu: bezpłatna anulacja (`fee: 0`), zwolnienie slotu w kalendarzu.
  - Odwołanie **poniżej 2 godzin**: standardowo **50 %** opłaty (`fee: 0.5`), **CHYBA ŻE** powodem jest nagłe pogorszenie stanu zdrowia, ból lub zalecenie lekarza (`medical_release: true` — wtedy 0 %).
  - Kwota i uzasadnienie pochodzą **wyłącznie z odpowiedzi narzędzia** — pola `fee`, `free_of_charge`, `fee_rule`. Anna czyta je gościowi; nie liczy opłaty sama.
- **Instrukcja krok po kroku (SOP):**
  1. Zapytaj uprzejmie o **numer rezerwacji** (`SPA-XXXX`). Bez numeru nie anuluj.
  2. Ustal **termin zabiegu** — datę **i godzinę** (są w rezerwacji). Termin przekazujesz w polu `appointment_datetime` jako ISO 8601 z godziną, np. `2026-11-09T18:30`. Bez godziny backend przyjmuje opłatę 50 % („brak godziny”).
  3. Jeśli do zabiegu zostało mniej niż 2 godziny, zapytaj z troską: *„Czy powodem odwołania jest gorsze samopoczucie lub kwestie zdrowotne?”*. Jeśli tak — ustaw `medical_release: true`.
  4. Wywołaj `cancel_spa_appointment(confirmation_id, reason, medical_release, appointment_datetime, language)` — `language` zawsze (`user_language`: `pl`/`en`).
  5. Odczytaj z odpowiedzi `fee`, `free_of_charge` i `fee_rule`; powiedz gościowi dokładnie tę kwotę i uzasadnienie („ponad 2 h przed zabiegiem — bezpłatnie” / „poniżej 2 h — opłata 50 %” / „zwolnienie medyczne — bezpłatnie”).
  6. Jeśli odpowiedź ma **`success: false`** (nieznany numer rezerwacji) — NIE potwierdzaj anulowania. Poproś gościa o ponowne sprawdzenie numeru (`SPA-XXXX`) i ponów wywołanie z poprawnym numerem.
  7. Poinformuj gościa o pomyślnym anulowaniu i wyślij SMS z potwierdzeniem.
  8. Zapytaj, czy zapisać na inny termin w trakcie pobytu.

---

### PROCEDURA 2: `procedura_zmiany_terminu_zabiegu`
*Przełożenie godziny lub dnia zabiegu SPA (Rescheduling)*

- **Trigger / Kiedy aktywować:** Gość chce zmienić godzinę, przełożyć masaż na popołudnie lub zamienić dzień zabiegu.
- **Reguła biznesowa:** Bezpłatna zmiana terminu w miarę dostępności grafiku fizjoterapeutów i balneologów. Nowy numer potwierdzenia `SPA-XXXX` nadaje narzędzie — stary numer przestaje obowiązywać.
- **Instrukcja krok po kroku (SOP):**
  1. Pobierz numer rezerwacji (`SPA-XXXX`), nazwę zabiegu i imię gościa.
  2. Zapytaj o preferowany nowy dzień i porę (rano / popołudnie).
  3. **Najpierw sprawdź nowy termin:** `check_spa_availability(service_name, new_date, language)`. Przy odpowiedzi `ambiguous` przeczytaj kandydatów i dopytaj o zabieg. Przy zajętym dniu podaj godziny z listy `slots`.
  4. Zaproponuj 2–3 konkretne godziny i podaj cenę (`price_pln`) oraz czas trwania (`duration_min`) z odpowiedzi.
  5. Po wyborze przez gościa sparafrazuj zmianę: *„Zmieniłam termin kąpieli siarczkowej z czwartku 10:00 na piątek o 15:00. Zgadza się?”*.
  6. Wywołaj `reschedule_spa_appointment(confirmation_id, service_name, new_date, new_time, guest_name, language)`.
  7. Podaj gościowi **nowy numer z pola `confirmation_id`** odpowiedzi i wyślij zaktualizowany SMS.
  8. Jeśli odpowiedź ma **`success: false`**: przy zajętym slocie zaproponuj inną godzinę z `slots`; przy komunikacie „nie znaleziono rezerwacji” poproś o sprawdzenie numeru i nie twórz nowej rezerwacji bez zgody gościa.

---

### PROCEDURA 3: `procedura_odwolania_pobytu_i_zwrotu_zadatku`
*Anulacja rezerwacji pokoju hotelowego / turnusu sanatoryjnego i polityka zwrotów*

- **Trigger / Kiedy aktywować:** Gość prosi o odwołanie rezerwacji pokoju i pyta o zwrot wpłaconego zadatku (30%).
- **Reguły biznesowe polityki anulacji:**
  - **Powyżej 14 dni przed przyjazdem:** Zwrot 100% wpłaconego zadatku na konto LUB bezterminowy voucher na pobyt o wartości 110% zadatku.
  - **7–14 dni przed przyjazdem:** Zwrot 50% zadatku LUB voucher na 100% wartości do wykorzystania w ciągu 12 miesięcy.
  - **Poniżej 7 dni przed przyjazdem:** Zadatek bezzwrotny.
  - *Wyjątek medyczny:* W przypadku hospitalizacji lub nagłego zwolnienia lekarskiego — pełen zwrot po przesłaniu zaświadczenia na `recepcja@bukowydwor.pl`.
- **Instrukcja krok po kroku (SOP):**
  1. Pobierz numer rezerwacji pokoju oraz nazwisko gościa.
  2. Oblicz liczbę dni pozostałych do planowanego zameldowania.
  3. Wytłumacz spokojnie obowiązujący wariant regulaminu.
  4. W pierwszej kolejności zarekomenduj **voucher 100% na inny termin** (ochrona przychodu hotelu).
  5. Jeśli gość wybiera zwrot na konto — zarejestruj dyspozycję w systemie PMS.
  6. W przypadku sporu lub sytuacji losowej — zaoferuj natychmiastowe połączenie z Kierownikiem Recepcji (`transfer_to_simulated_handoff`, `department: "recepcja"`).

---

### PROCEDURA 4: `procedura_wczesnego_przyjazdu_i_poznego_wyjazdu`
*Obsługa Early Check-in (przed 15:00) i Late Check-out (po 11:00)*

- **Trigger / Kiedy aktywować:** Gość pyta, czy może przyjechać rano (np. pociąg o 8:30) lub zostać w pokoju dłużej w dniu wyjazdu.
- **Reguła biznesowa:**
  - Doba hotelowa trwa od **15:00 do 11:00** (zameldowanie od 15:00, wymeldowanie do 11:00).
  - **Wczesny przyjazd:** Bezpłatna przechowalnia bagażu + bezpłatny dostęp do strefy basenów termalnych i restauracji od godziny 9:00 rano. Pokój udostępniany wcześniej bez opłat, jeśli był posprzątany.
  - **Późny wyjazd:** Przedłużenie do 14:00 (50 PLN) / do 18:00 (100 PLN) w miarę dostępności pokoju.
- **Instrukcja krok po kroku (SOP):**
  1. Sprawdź termin rezerwacji gościa.
  2. Uspokój gościa: *„Nawet jeśli pokój nie będzie jeszcze gotowy o 9:00, bezpłatnie przechowamy bagaże i może Pani/Pan od razu korzystać z basenów termalnych i kawiarni.”*
  3. Zapisz w uwagach do rezerwacji w PMS szacowaną godzinę przyjazdu (priorytet dla serwisu sprzątającego).

---

### PROCEDURA 5: `procedura_zgloszenia_diety_leczniczej`
*Rejestracja zaleceń żywieniowych i alergii w restauracji hotelowej*

- **Trigger / Kiedy aktywować:** Gość informuje o cukrzycy, celiakii, diecie lekkostrawnej lub diecie bezmlecznej.
- **Reguła biznesowa:** Dostępne są dokładnie **trzy diety** — **cukrzycowa**, **lekkostrawna** oraz **bezglutenowa i bezmleczna** — wszystkie w cenie pobytu, **bez dodatkowych dopłat**. Dieta **bezglutenowa i bezmleczna** wymaga zgłoszenia **minimum 3 dni** przed przyjazdem (pozostałe wystarczy zgłosić przy rezerwacji).
- **Instrukcja krok po kroku (SOP):**
  1. Zapytaj o dokładny rodzaj diety i ewentualne alergie pokarmowe.
  2. Poinformuj, że posiłki w restauracji **„Bukowy Smak”** są przygotowywane pod bezpośrednim nadzorem dietetyka klinicznego.
  3. Zapisz adnotację żywieniową w profilu gościa w PMS.
  4. Przekaż godziny posiłków (Śniadanie: 7:30–10:00, Obiad: 13:00–15:00, Kolacja: 17:30–19:30).

---

### PROCEDURA 6: `procedura_zamowienia_transportu_i_meleksa`
*Transfer ze stacji PKP/PKS Krynica-Zdrój oraz transport wewnętrzny*

- **Trigger / Kiedy aktywować:** Gość pyta o dojazd z dworca, prosi o odebranie ze stacji lub o podwiezienie meleksem z parkingu/SPA.
- **Reguła biznesowa:** Bezpłatny transfer hotelowym busem/meleksem dla wszystkich gości uzdrowiska.
- **Instrukcja krok po kroku (SOP):**
  1. Ustal godzinę przyjazdu pociągu/autobusu na stację Krynica-Zdrój oraz numer połączenia/przewoźnika.
  2. Zapytaj o liczbę osób, bagaży oraz ewentualne wózki inwalidzkie lub balkoniki rehabilitacyjne.
  3. Wygeneruj zlecenie transferu dla kierowcy w hotelu.
  4. Wyślij SMS do gościa z potwierdzeniem i numerem kontaktowym do dyżurnego kierowcy busa.

---

### PROCEDURA 7: `procedura_reklamacji_i_trudnego_goscia`
*Obsługa zażaleń, hałasu, problemów technicznych lub niezadowolenia*

- **Trigger / Kiedy aktywować:** Gość jest zdenerwowany, narzeka na jakość usługi, temperaturę wody, zachowanie personelu lub usterkę w pokoju.
- **Zasady empatii dla seniora:**
  1. **Nigdy nie polemizuj ani nie przerywaj.** Pozwól gościowi opowiedzieć o problemie.
  2. Użyj zwrotu empatii: *„Bardzo przepraszam za tę niedogodność. W pełni rozumiem Pani/Pana zdenerwowanie. Już zajmuję się tą sprawą.”*
  3. W przypadku drobnych usterek w pokoju (np. brak ręcznika, problem z pilotem TV): wyślij natychmiastowe zgłoszenie do służby pięter / konserwatora.
  4. W przypadku poważnego niezadowolenia: zaoferuj voucher na herbatę ziołową / grotę solną i natychmiast połącz z Managerem Dyżurnym przez `transfer_to_simulated_handoff` (`department: "recepcja"`).

---

## 3. Matryca Decyzyjna Procedur (Decision Matrix)

```
                       [Wypowiedź Gościa]
                                │
       ┌────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
[Odwołanie/Zmiana SPA]   [Anulacja Pokoju]        [Transport/Dojazd]
       │                        │                        │
       ├─ >2h: Bez opłat        ├─ >14 dni: Zwrot 100%   ├─ Z Dworca: Bus bezpłatny
       └─ <2h: 50% (med. 0%)    ├─ 7-14 dni: Zwrot 50%   └─ Na terenie: Meleks 24h
                                └─ <7 dni: Zadatek przepada
```

---

## 4. Format JSON do Wdrożenia w ElevenLabs Studio / API

Poniższy fragment przedstawia przykładową definicję procedury w strukturze API ElevenLabs:

```json
{
  "procedures": [
    {
      "name": "procedura_anulowania_rezerwacji_spa",
      "description": "Uruchom, gdy gość chce odwołać, zrezygnować lub anulować zabieg SPA lub masaż.",
      "instructions": "1. Poproś o numer rezerwacji SPA-XXXX i ustal termin zabiegu (data + godzina).\n2. Wywołaj cancel_spa_appointment z confirmation_id, appointment_datetime (ISO 8601 z godziną, np. 2026-11-09T18:30), medical_release i language.\n3. Odczytaj fee / free_of_charge / fee_rule i podaj gościowi dokładną kwotę.\n4. Przy success:false poproś o ponowne sprawdzenie numeru — nie potwierdzaj anulowania.\n5. Po anulowaniu wyślij SMS.",
      "tools": ["cancel_spa_appointment", "send_sms_summary"]
    },
    {
      "name": "procedura_odwolania_pobytu_i_zwrotu_zadatku",
      "description": "Uruchom, gdy gość pyta o rezygnację z pokoju hotelowego i zwrot wpłaconego zadatku.",
      "instructions": "1. Pobierz numer rezerwacji i sprawdź termin zameldowania.\n2. Zastosuj politykę: >14 dni (100% zwrotu lub voucher 110%), 7-14 dni (50% zwrotu lub voucher 100%), <7 dni (bezzwrotny).\n3. Zaproponuj voucher na inny termin.\n4. W razie kwestii spornych połącz z recepcją.",
      "tools": ["transfer_to_simulated_handoff", "send_sms_summary"]
    },
    {
      "name": "procedura_zamowienia_transportu_i_meleksa",
      "description": "Uruchom, gdy gość prosi o odbiór z dworca PKP/PKS lub transport meleksem.",
      "instructions": "1. Ustal godzinę przyjazdu pociągu i obecność wózka/bagaży.\n2. Poinformuj o bezpłatnym transferze.\n3. Wyślij SMS z kontaktem do kierowcy.",
      "tools": ["send_sms_summary"]
    }
  ]
}
```
