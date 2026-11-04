# 7 operating procedures deployed to the agent (see docs/operating-procedures.md)
# Format: free_form, content = markdown with inline reference [tool id="..."]

# Tool IDs (istniejące w agencie):
# tool_4801m0ncs38tf8t93f45jfj992dt = check_spa_availability
# tool_6001m0ncs38vf73v1zbaa9p5vdfv = book_spa_appointment
# tool_6301m0ncs38wewt865sh99v1qkm8 = check_room_availability
# tool_8101m0ncs38xe6tb29923tjt9045 = send_sms_summary
# tool_6001m0ntyt8xefgsx1e8mcqnsw1n = transfer_to_simulated_handoff

## 1. procedura_anulowania_rezerwacji_spa
trigger: "Gdy gość mówi, że nie może przyjść na zabieg, chce zrezygnować z masażu lub kąpieli, lub prosi o odwołanie rezerwacji zabiegu SPA."
type: free_form
content: |
  1. Uprzejmie poproś o numer rezerwacji (SPA-XXXX) lub imię, nazwisko i numer telefonu gościa.
  2. Jeśli do zabiegu zostało mniej niż 2 godziny, zapytaj z troską: „Czy powodem odwołania jest gorsze samopoczucie lub kwestie zdrowotne?" Jeśli tak — anulacja w 100% bezpłatna (zwolnienie medyczne).
  3. Odwołanie powyżej 2 godzin przed terminem: bezpłatna anulacja i zwolnienie slotu.
  4. Odwołanie poniżej 2 godzin bez powodu medycznego: standardowo 50% opłaty.
  5. Wywołaj [tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"] z department="recepcja" i reason opisującym anulację, aby poinformować zespół (na produkcji: cancel_spa_appointment).
  6. Poinformuj gościa o pomyślnym anulowaniu i zaproponuj wysłanie potwierdzenia przez [tool id="tool_8101m0ncs38xe6tb29923tjt9045"].
  7. Zapytaj, czy zapisać gościa na inny termin w trakcie pobytu.

## 2. procedura_zmiany_terminu_zabiegu
trigger: "Gdy gość chce zmienić godzinę, przełożyć masaż na popołudnie lub zamienić dzień zabiegu SPA."
type: free_form
content: |
  1. Pobierz numer rezerwacji (SPA-XXXX) i zidentyfikuj aktualny termin zabiegu.
  2. Zapytaj o preferowany nowy dzień i porę (rano / popołudnie).
  3. Wywołaj [tool id="tool_4801m0ncs38tf8t93f45jfj992dt"] z service_name i nową datą.
  4. Zaproponuj gościowi 2–3 konkretne godziny.
  5. Po wyborze sparafrazuj zmianę: „Zmieniłam termin kąpieli siarczkowej z czwartku 10:00 na piątek o 15:00. Zgadza się?"
  6. Po potwierdzeniu wywołaj [tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"] z department="recepcja" (na produkcji: aktualizacja PMS) i wyślij zaktualizowany SMS przez [tool id="tool_8101m0ncs38xe6tb29923tjt9045"].

## 3. procedura_odwolania_pobytu_i_zwrotu_zadatku
trigger: "Gdy gość prosi o odwołanie rezerwacji pokoju hotelowego i pyta o zwrot wpłaconego zadatku (30%)."
type: free_form
content: |
  1. Pobierz numer rezerwacji pokoju oraz nazwisko gościa.
  2. Oblicz liczbę dni pozostałych do planowanego zameldowania.
  3. Zastosuj politykę anulacji:
     - Powyżej 14 dni przed przyjazdem: zwrot 100% zadatku na konto LUB bezterminowy voucher na 110% wartości.
     - 7–14 dni przed przyjazdem: zwrot 50% zadatku LUB voucher na 100% wartości ważny 12 miesięcy.
     - Poniżej 7 dni: zadatek bezzwrotny.
     - Wyjątek medyczny: hospitalizacja lub nagłe zwolnienie lekarskie → pełen zwrot po przesłaniu zaświadczenia na recepcja@bukowydwor.pl.
  4. W pierwszej kolejności zarekomenduj voucher na inny termin (ochrona przychodu hotelu).
  5. Jeśli gość wybiera zwrot na konto — zarejestruj dyspozycję (wywołaj [tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"] z department="recepcja").
  6. W przypadku sporu lub sytuacji losowej — zaoferuj natychmiastowe połączenie z Kierownikiem Recepcji ([tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"]).

## 4. procedura_wczesnego_przyjazdu_i_poznego_wyjazdu
trigger: "Gdy gość pyta, czy może przyjechać rano (early check-in) lub zostać w pokoju dłużej w dniu wyjazdu (late check-out)."
type: free_form
content: |
  1. Sprawdź termin rezerwacji gościa.
  2. Doba hotelowa trwa od 14:00 do 11:00.
  3. Wczesny przyjazd: bezpłatna przechowalnia bagażu + bezpłatny dostęp do strefy basenów termalnych i restauracji od 9:00. Pokój udostępniany wcześniej bez opłat, jeśli posprzątany.
  4. Uspokój gościa: „Nawet jeśli pokój nie będzie jeszcze gotowy o 9:00, bezpłatnie przechowamy bagaże i może Pani/Pan od razu korzystać z basenów termalnych i kawiarni."
  5. Późny wyjazd: przedłużenie do 14:00 (50 PLN) / do 18:00 (100 PLN) w miarę dostępności pokoju.
  6. Zapisz w uwagach do rezerwacji szacowaną godzinę przyjazdu (priorytet dla serwisu sprzątającego).

## 5. procedura_zgloszenia_diety_leczniczej
trigger: "Gdy gość informuje o cukrzycy, celiakii, diecie lekkostrawnej, bezmlecznej lub ograniczeniu soli."
type: free_form
content: |
  1. Zapytaj o dokładny rodzaj diety i ewentualne alergie pokarmowe.
  2. Poinformuj, że diety lecznicze (cukrzycowa, lekkostrawna, bezglutenowa, niskosodowa) są w cenie pobytu bez dopłat, ale wymagają zgłoszenia min. 24h przed przyjazdem.
  3. Poinformuj, że posiłki są przygotowywane pod bezpośrednim nadzorem dietetyka klinicznego.
  4. Zapisz adnotację żywieniową w profilu gościa.
  5. Przekaż godziny posiłków: Śniadanie 7:30–9:30, Obiad 13:00–15:00, Kolacja 18:00–19:30.

## 6. procedura_zamowienia_transportu_i_meleksa
trigger: "Gdy gość pyta o dojazd z dworca PKP/PKS, prosi o odebranie ze stacji lub podwiezienie meleksem z parkingu/SPA."
type: free_form
content: |
  1. Ustal godzinę przyjazdu pociągu/autobusu na stację Krynica-Zdrój oraz numer połączenia/przewoźnika.
  2. Zapytaj o liczbę osób, bagaży oraz ewentualne wózki inwalidzkie lub balkoniki rehabilitacyjne.
  3. Poinformuj, że transfer hotelowym busem/meleksem jest bezpłatny dla wszystkich gości uzdrowiska.
  4. Wygeneruj zlecenie transferu dla kierowcy (wywołaj [tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"] z department="recepcja").
  5. Wyślij SMS z potwierdzeniem i numerem kontaktowym do dyżurnego kierowcy przez [tool id="tool_8101m0ncs38xe6tb29923tjt9045"].

## 7. procedura_reklamacji_i_trudnego_goscia
trigger: "Gdy gość jest zdenerwowany, narzeka na jakość usługi, temperaturę wody, zachowanie personelu lub usterkę w pokoju."
type: free_form
content: |
  1. Nigdy nie polemizuj ani nie przerywaj — pozwól gościowi opowiedzieć o problemie.
  2. Użyj zwrotu empatii: „Bardzo przepraszam za tę niedogodność. W pełni rozumiem Pani/Pana zdenerwowanie. Już zajmuję się tą sprawą."
  3. W przypadku drobnych usterek w pokoju (brak ręcznika, problem z pilotem TV): wyślij natychmiastowe zgłoszenie do służby pięter / konserwatora.
  4. W przypadku poważnego niezadowolenia: zaoferuj voucher na herbatę ziołową / grotę solną i połącz z Managerem Dyżurnym przez [tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"] z department="recepcja".
