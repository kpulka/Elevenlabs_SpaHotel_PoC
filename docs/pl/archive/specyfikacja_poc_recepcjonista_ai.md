> **Status:** historyczne — zastąpione przez `docs/specyfikacja_recepcjonista_ai.md` (archiwum, nieaktualne). Zarchiwizowano 2026-11: zakres PoC scalono do specyfikacji kanonicznej, szczegóły techniczne do `docs/plan_implementacji_recepcjonisty.md`.

# Specyfikacja PoC: Wirtualny Recepcjonista AI (Hotel & SPA) — ZDEPRECJONOWANY

> **⚠️ Dokument zdeprecjonowany (archiwalny).** Treść została scalona do kanonicznej specyfikacji **`specyfikacja_recepcjonista_ai.md`**, a szczegóły techniczne przeniesione do **`plan_implementacji_recepcjonisty.md`**.
> Niniejszy plik zachowano wyłącznie jako historię. Nie edytuj — aktualizuj specyfikację kanoniczną.

## 1. Cel Projektu (Proof of Concept)
Stworzenie działającego prototypu agenta głosowego opartego na platformie ElevenLabs Conversational AI. Celem PoC jest zaprezentowanie inwestorom lub zarządowi sieci hoteli sposobu interakcji, płynności działania oraz zdolności agenta do realizacji procesów biznesowych. Wersja ta opiera się na wyimaginowanych danych (mockups) i symuluje integracje z prawdziwymi systemami.

## 2. Kluczowe Założenia UX (Grupa Docelowa: Seniorzy)
Architektura konwersacji musi uwzględniać ograniczenia technologiczne i specyfikę grupy docelowej (goście sanatoriów i hoteli SPA):
* **Wydłużone okno detekcji ciszy (VAD):** Skonfigurowane na dłuższą pauzę (np. 2-3 sekundy), aby system nie przerywał w pół zdania osobom mówiącym wolniej.
* **Krokowa komunikacja (One-step-at-a-time):** Zbieranie informacji powoli. Agent nie zadaje złożonych pytań (np. "Kiedy i na jaki zabieg mam panią zapisać?"), lecz dzieli je na etapy.
* **Zasada Potwierdzenia:** Agent zawsze parafrazuje ustalenia przed zasymulowaniem zapisu ("Rozumiem, że rezerwujemy masaż na wtorek o 15:00. Czy zgadza się?").
* **Wsparcie asynchroniczne (SMS):** Głos służy do załatwienia sprawy, ale potwierdzenia, przypomnienia i linki przychodzą SMS-em, by odciążyć pamięć rozmówcy.

## 3. Zakres Funkcjonalny PoC (Ścieżki do zaprezentowania)
W ramach demonstracji agent płynnie obsłuży następujące scenariusze:

### A. Ścieżka Rezerwacji SPA
1. Gość dzwoni z pytaniem o masaż kręgosłupa.
2. Agent sprawdza (w zasymulowanej bazie) dostępne terminy.
3. Agent proponuje godziny, a następnie zbiera imię, nazwisko i fikcyjny numer telefonu.
4. Agent potwierdza rezerwację głosowo i uruchamia symulację wysyłki SMS.

### B. Ścieżka Informacyjna (Baza Wiedzy / RAG)
1. Gość pyta o godziny wydawania posiłków (śniadania/kolacje) lub o to, czy basen wymaga czepka.
2. Agent czerpie wiedzę z wstrzykniętego kontekstu hotelu i udziela uprzejmej, zwięzłej odpowiedzi.

### C. Ścieżka Eskalacji (Human Handoff)
1. Gość zgłasza nietypową prośbę (np. negocjacja ceny, skarga, skomplikowane wymogi medyczne).
2. Agent rozpoznaje brak kompetencji, przeprasza i symuluje przełączenie połączenia do "prawdziwej recepcji".

## 4. Architektura Systemu dla PoC

Dla zachowania pełnej kontroli nad przepływem i umożliwienia łatwej prezentacji "pod maską", PoC zostanie zrealizowany w modelu **Custom LLM (Webhook Workflow)** połączonym z ElevenLabs.

* **Frontend / Głos:** ElevenLabs Conversational AI (zarządza STT, TTS, WebRTC).
* **Backend (Orkiestrator):** Prosta aplikacja (np. Python/FastAPI lub Node.js), która odbiera transkrypcje z ElevenLabs, zarządza promptami dla wybranego LLM (np. GPT-4o) i zwraca odpowiedzi.
* **Symulowane Bazy Danych (Mock-upy):**
  * Pliki `rooms.json` i `spa_schedule.json` pełniące rolę systemu PMS i kalendarza SPA.
  * Z góry zdefiniowane, "sztywne" terminy dostępności na potrzeby dema (np. zawsze wolny wtorek o 15:00).
* **Symulacja SMS:** Zamiast płatnej bramki (Twilio/SMSAPI), funkcja wysyłająca SMS po prostu zrzuci log do konsoli backendu lub wyśle powiadomienie na darmowy webhook (np. kanał Slack/Discord), aby podczas dema pokazać "fizyczny" efekt działania agenta na innym ekranie.

## 5. Zestaw Narzędzi (Tool Calling) do wdrożenia w PoC
W panelu ElevenLabs (lub na backendzie) zdefiniowane zostaną następujące funkcje, które LLM może wywołać w trakcie rozmowy:

1. `check_spa_availability(service_name, target_date)`
   * *Opis:* Sprawdza wolne godziny dla wybranego zabiegu w danym dniu.
   * *Odpowiedź z mocka:* Zwraca tablicę godzin (np. `["10:00", "14:30", "15:00"]`).
2. `book_spa_appointment(guest_name, service_name, datetime, phone_number)`
   * *Opis:* Zapisuje wizytę. Uruchamia asynchronicznie procesowanie potwierdzenia.
   * *Odpowiedź z mocka:* `{"status": "success", "confirmation_id": "ABC-123"}`.
3. `trigger_sms(phone_number, message_type, details)`
   * *Opis:* "Wysyła" SMS. W rzeczywistości odpala webhook na Discord/Slack dla wizualizacji sukcesu podczas prezentacji.
4. `transfer_to_human(reason)`
   * *Opis:* Zakańcza przetwarzanie AI i symuluje przełączenie do konsultanta.

## 6. Propozycja Persony (Ton Głosu)
* **Imię:** Pani Anna (lub bezosobowy, ale ciepły, żeński głos).
* **Styl:** Empatyczny, niespieszny, bardzo uprzejmy. Brak żargonu ("aplikacja", "system", "autoryzacja").
* **Głos z bazy ElevenLabs:** Zalecane użycie starszego, cieplejszego głosu z biblioteki (np. Rachel, Nicole lub wygenerowany Voice Clone lektorki o radiowym, spokojnym brzmieniu) z wykorzystaniem modelu Turbo v2.5.
