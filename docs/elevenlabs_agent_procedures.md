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

---

## 2. Katalog 7 Głównych Procedur Bukowego Dworu

---

### PROCEDURA 1: `procedura_anulowania_rezerwacji_spa`
*Anulowanie zabiegu balneologicznego lub masażu w strefie Medical SPA*

- **Trigger / Kiedy aktywować:** Gość mówi, że nie może przyjść na zabieg, chce zrezygnować z masażu/kąpieli lub prosi o odwołanie rezerwacji.
- **Reguła biznesowa:**
  - Odwołanie **powyżej 2 godzin** przed terminem zabiegu: bezpłatna anulacja, zwolnienie slotu w kalendarzu.
  - Odwołanie **poniżej 2 godzin**: standardowo 50% opłaty, **CHYBA ŻE** powodem jest nagłe pogorszenie stanu zdrowia, ból lub zalecenie lekarza (wtedy anulacja jest w 100% bezpłatna).
- **Instrukcja krok po kroku (SOP):**
  1. Zapytaj uprzejmie o **numer rezerwacji** (`SPA-XXXX`) lub **imię, nazwisko i numer telefonu** gościa.
  2. Sprawdź rezerwację w PMS.
  3. Jeśli do zabiegu zostało mniej niż 2 godziny, zapytaj z troską: *„Czy powodem odwołania jest gorsze samopoczucie lub kwestie zdrowotne?”*. Jeśli tak — oznacz jako zwolnienie medyczne (bez opłat).
  4. Wywołaj narzędzie `cancel_spa_appointment(confirmation_id, reason)`.
  5. Poinformuj gościa o pomyślnym anulowaniu i wyślij SMS z potwierdzeniem.
  6. Zapytaj, czy zapisać na inny termin w trakcie pobytu.

---

### PROCEDURA 2: `procedura_zmiany_terminu_zabiegu`
*Przełożenie godziny lub dnia zabiegu SPA (Rescheduling)*

- **Trigger / Kiedy aktywować:** Gość chce zmienić godzinę, przełożyć masaż na popołudnie lub zamienić dzień zabiegu.
- **Reguła biznesowa:** Bezpłatna zmiana terminu w miarę dostępności grafiku fizjoterapeutów i balneologów.
- **Instrukcja krok po kroku (SOP):**
  1. Pobierz numer rezerwacji (`SPA-XXXX`) i zidentyfikuj aktualny termin.
  2. Zapytaj o preferowany nowy dzień i porę (rano / popołudnie).
  3. Wywołaj `check_spa_availability(service_name, new_date)`.
  4. Zaproponuj 2–3 konkretne godziny.
  5. Po wyborze przez gościa sparafrazuj zmianę: *„Zmieniłam termin kąpieli siarczkowej z czwartku 10:00 na piątek o 15:00. Zgadza się?”*.
  6. Wywołaj narzędzie aktualizacji w PMS i wyślij zaktualizowany SMS.

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
  6. W przypadku sporu lub sytuacji losowej — zaoferuj natychmiastowe połączenie z Kierownikiem Recepcji (`transfer_to_number`).

---

### PROCEDURA 4: `procedura_wczesnego_przyjazdu_i_poznego_wyjazdu`
*Obsługa Early Check-in (przed 14:00) i Late Check-out (po 11:00)*

- **Trigger / Kiedy aktywować:** Gość pyta, czy może przyjechać rano (np. pociąg o 8:30) lub zostać w pokoju dłużej w dniu wyjazdu.
- **Reguła biznesowa:**
  - Doba hotelowa trwa od **14:00 do 11:00**.
  - **Wczesny przyjazd:** Bezpłatna przechowalnia bagażu + bezpłatny dostęp do strefy basenów termalnych i restauracji od godziny 9:00 rano. Pokój udostępniany wcześniej bez opłat, jeśli był posprzątany.
  - **Późny wyjazd:** Przedłużenie do 14:00 (50 PLN) / do 18:00 (100 PLN) w miarę dostępności pokoju.
- **Instrukcja krok po kroku (SOP):**
  1. Sprawdź termin rezerwacji gościa.
  2. Uspokój gościa: *„Nawet jeśli pokój nie będzie jeszcze gotowy o 9:00, bezpłatnie przechowamy bagaże i może Pani/Pan od razu korzystać z basenów termalnych i kawiarni.”*
  3. Zapisz w uwagach do rezerwacji w PMS szacowaną godzinę przyjazdu (priorytet dla serwisu sprzątającego).

---

### PROCEDURA 5: `procedura_zgloszenia_diety_leczniczej`
*Rejestracja zaleceń żywieniowych i alergii w restauracji hotelowej*

- **Trigger / Kiedy aktywować:** Gość informuje o cukrzycy, celiakii, diecie lekkostrawnej, bezmlecznej lub ograniczeniu soli.
- **Reguła biznesowa:** Diety lecznicze (cukrzycowa, lekkostrawna, bezglutenowa, niskosodowa) są w cenie pobytu bez dopłat, ale wymagają zgłoszenia min. 24h przed przyjazdem.
- **Instrukcja krok po kroku (SOP):**
  1. Zapytaj o dokładny rodzaj diety i ewentualne alergie pokarmowe.
  2. Poinformuj, że posiłki są przygotowywane pod bezpośrednim nadzorem dietetyka klinicznego.
  3. Zapisz adnotację żywieniową w profilu gościa w PMS.
  4. Przekaż godziny posiłków (Śniadanie: 7:30–9:30, Obiad: 13:00–15:00, Kolacja: 18:00–19:30).

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
  4. W przypadku poważnego niezadowolenia: zaoferuj voucher na herbatę ziołową / grotę solną i natychmiast połącz z Managerem Dyżurnym przez `transfer_to_number`.

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
       └─ <2h: Wywiad zdrowotny ├─ 7-14 dni: Zwrot 50%   └─ Na terenie: Meleks 24h
                                └─ <7 dni: Voucher/Brak
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
      "instructions": "1. Poproś o numer rezerwacji SPA-XXXX lub imię i nazwisko.\n2. Jeśli zabieg jest za mniej niż 2h, zapytaj o samopoczucie/kwestie zdrowotne (brak opłat w razie choroby).\n3. Wywołaj tool cancel_spa_appointment.\n4. Potwierdź anulację i wyślij SMS.",
      "tools": ["cancel_spa_appointment", "send_sms_summary"]
    },
    {
      "name": "procedura_odwolania_pobytu_i_zwrotu_zadatku",
      "description": "Uruchom, gdy gość pyta o rezygnację z pokoju hotelowego i zwrot wpłaconego zadatku.",
      "instructions": "1. Pobierz numer rezerwacji i sprawdź termin zameldowania.\n2. Zastosuj politykę: >14 dni (100% zwrotu lub voucher 110%), 7-14 dni (50% zwrotu lub voucher 100%), <7 dni (bezzwrotny).\n3. Zaproponuj voucher na inny termin.\n4. W razie kwestii spornych połącz z recepcją.",
      "tools": ["transfer_to_number", "send_sms_summary"]
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
