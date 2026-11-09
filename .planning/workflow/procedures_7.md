# 7 procedur do wdrożenia (z docs/elevenlabs_agent_procedures.md)
# Format: free_form, content = markdown z inline reference [tool id="..."]

# Tool IDs (istniejące w agencie):
# tool_4801m0ncs38tf8t93f45jfj992dt = check_spa_availability
# tool_6001m0ncs38vf73v1zbaa9p5vdfv = book_spa_appointment
# tool_6301m0ncs38wewt865sh99v1qkm8 = check_room_availability
# tool_8101m0ncs38xe6tb29923tjt9045 = send_sms_summary
# tool_6001m0ntyt8xefgsx1e8mcqnsw1n = transfer_to_simulated_handoff
# UWAGA: cancel_spa_appointment i reschedule_spa_appointment są zarejestrowane w agencie,
# ale ich tool_id nie jest jeszcze znane (.planning/workflow/new_tools.json: null).
# Do czasu uzupełnienia ID odwołujemy się do nich po nazwie: [tool name="..."].
# Każde wywołanie przekazuje language (pl/en) z dynamicznej zmiennej user_language.

## 1. procedura_anulowania_rezerwacji_spa
trigger: "Gdy gość mówi, że nie może przyjść na zabieg, chce zrezygnować z masażu lub kąpieli, lub prosi o odwołanie rezerwacji zabiegu SPA."
type: free_form
content: |
  1. Uprzejmie poproś o numer rezerwacji (SPA-XXXX). Bez numeru nie anuluj.
  2. Ustal termin zabiegu — datę i godzinę (są w rezerwacji). Przekaż go jako appointment_datetime w ISO 8601 z godziną, np. 2026-11-09T18:30. Bez godziny backend zawsze nalicza 50%.
  3. Jeśli do zabiegu zostało mniej niż 2 godziny, zapytaj z troską: „Czy powodem odwołania jest gorsze samopoczucie lub kwestie zdrowotne?" Jeśli tak — przekaż medical_release=true (anulacja 0%).
  4. Odwołanie powyżej 2 godzin przed terminem: bezpłatna anulacja (fee: 0) i zwolnienie slotu.
  5. Odwołanie poniżej 2 godzin bez powodu medycznego: 50% opłaty (fee: 0.5).
  6. Wywołaj [tool name="cancel_spa_appointment"] z confirmation_id, reason, medical_release, appointment_datetime i language.
  7. Odczytaj z odpowiedzi fee, free_of_charge i fee_rule — podaj gościowi dokładnie tę kwotę i uzasadnienie. Nigdy nie licz opłaty samodzielnie.
  8. Jeśli odpowiedź ma success:false (nieznany numer) — NIE potwierdzaj anulowania, poproś o ponowne sprawdzenie numeru i ponów wywołanie.
  9. Poinformuj gościa o pomyślnym anulowaniu i zaproponuj wysłanie potwierdzenia przez [tool id="tool_8101m0ncs38xe6tb29923tjt9045"].
  10. Zapytaj, czy zapisać gościa na inny termin w trakcie pobytu.

## 2. procedura_zmiany_terminu_zabiegu
trigger: "Gdy gość chce zmienić godzinę, przełożyć masaż na popołudnie lub zamienić dzień zabiegu SPA."
type: free_form
content: |
  1. Pobierz numer rezerwacji (SPA-XXXX), nazwę zabiegu i imię gościa.
  2. Zapytaj o preferowany nowy dzień i porę (rano / popołudnie).
  3. Najpierw sprawdź nowy termin: wywołaj [tool id="tool_4801m0ncs38tf8t93f45jfj992dt"] z service_name, nową datą i language. Przy odpowiedzi ambiguous przeczytaj kandydatów i dopytaj, który zabieg gość wybiera.
  4. Zaproponuj gościowi 2–3 konkretne godziny z listy slots; podaj price_pln i duration_min z odpowiedzi.
  5. Po wyborze sparafrazuj zmianę: „Zmieniłam termin kąpieli siarczkowej z czwartku 10:00 na piątek o 15:00. Zgadza się?"
  6. Po potwierdzeniu wywołaj [tool name="reschedule_spa_appointment"] z confirmation_id, service_name, new_date, new_time, guest_name i language.
  7. Podaj gościowi nowy numer z pola confirmation_id odpowiedzi i wyślij zaktualizowany SMS przez [tool id="tool_8101m0ncs38xe6tb29923tjt9045"].
  8. Jeśli odpowiedź ma success:false: przy zajętym slocie zaproponuj inną godzinę z listy slots; przy „nie znaleziono rezerwacji" poproś o sprawdzenie numeru i nie twórz nowej rezerwacji bez zgody gościa.

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
  2. Doba hotelowa trwa od 15:00 do 11:00 (zameldowanie od 15:00, wymeldowanie do 11:00).
  3. Wczesny przyjazd: bezpłatna przechowalnia bagażu + bezpłatny dostęp do strefy basenów termalnych i restauracji od 9:00. Pokój udostępniany wcześniej bez opłat, jeśli posprzątany.
  4. Uspokój gościa: „Nawet jeśli pokój nie będzie jeszcze gotowy o 9:00, bezpłatnie przechowamy bagaże i może Pani/Pan od razu korzystać z basenów termalnych i kawiarni."
  5. Późny wyjazd: przedłużenie do 14:00 (50 PLN) / do 18:00 (100 PLN) w miarę dostępności pokoju.
  6. Zapisz w uwagach do rezerwacji szacowaną godzinę przyjazdu (priorytet dla serwisu sprzątającego).

## 5. procedura_zgloszenia_diety_leczniczej
trigger: "Gdy gość informuje o cukrzycy, diecie lekkostrawnej albo diecie bezglutenowej i bezmlecznej."
type: free_form
content: |
  1. Zapytaj o dokładny rodzaj diety i ewentualne alergie pokarmowe.
  2. Poinformuj, że dostępne są dokładnie trzy diety — cukrzycowa, lekkostrawna oraz bezglutenowa i bezmleczna — wszystkie w cenie pobytu bez dopłat. Dieta bezglutenowa i bezmleczna wymaga zgłoszenia min. 3 dni przed przyjazdem.
  3. Poinformuj, że posiłki w restauracji „Bukowy Smak" są przygotowywane pod bezpośrednim nadzorem dietetyka klinicznego.
  4. Zapisz adnotację żywieniową w profilu gościa.
  5. Przekaż godziny posiłków: Śniadanie 7:30–10:00, Obiad 13:00–15:00, Kolacja 17:30–19:30.

## 6. procedura_zamowienia_transportu_i_meleksa
trigger: "Gdy gość pyta o dojazd z dworca PKP/PKS, prosi o odebranie ze stacji lub podwiezienie meleksem z parkingu/SPA."
type: free_form
content: |
  1. Ustal godzinę przyjazdu pociągu/autobusu na stację Krynica-Zdrój oraz numer połączenia/przewoźnika.
  2. Zapytaj o liczbę osób, bagaży oraz ewentualne wózki inwalidzkie lub balkoniki rehabilitacyjne.
  3. Poinformuj, że transfer hotelowym busem/meleksem jest bezpłatny dla wszystkich gości uzdrowiska.
  4. Przekaż zgłoszenie do recepcji, żeby recepcja zamówiła meleks (wywołaj [tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"] z department="recepcja"; to alert, nie połączenie telefoniczne).
  5. Wyślij SMS z potwierdzeniem i numerem kontaktowym do dyżurnego kierowcy przez [tool id="tool_8101m0ncs38xe6tb29923tjt9045"].

## 7. procedura_reklamacji_i_trudnego_goscia
trigger: "Gdy gość jest zdenerwowany, narzeka na jakość usługi, temperaturę wody, zachowanie personelu lub usterkę w pokoju."
type: free_form
content: |
  1. Nigdy nie polemizuj ani nie przerywaj — pozwól gościowi opowiedzieć o problemie.
  2. Użyj zwrotu empatii: „Bardzo przepraszam za tę niedogodność. W pełni rozumiem Pani/Pana zdenerwowanie. Już zajmuję się tą sprawą."
  3. W przypadku drobnych usterek w pokoju (brak ręcznika, problem z pilotem TV): wyślij natychmiastowe zgłoszenie do służby pięter / konserwatora.
  4. W przypadku poważnego niezadowolenia: zaoferuj voucher na herbatę ziołową / grotę solną i połącz z Managerem Dyżurnym przez [tool id="tool_6001m0ntyt8xefgsx1e8mcqnsw1n"] z department="recepcja".
