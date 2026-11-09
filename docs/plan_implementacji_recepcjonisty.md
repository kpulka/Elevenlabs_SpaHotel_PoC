> **Status:** aktualny (2026-11) — źródło prawdy dla konfiguracji technicznej (JAK jest zbudowany).

# Plan Implementacji Wirtualnego Recepcjonisty AI dla Uzdrowiska „Bukowy Dwór”

Dokument ten stanowi kompletny, kanoniczny plan implementacji wdrożenia wirtualnego asystenta głosowego **Anna** w Uzdrowisku Termalnym „Bukowy Dwór” w Krynicy-Zdroju. Specyfikacja łączy wymagania biznesowe i specyfikę grupy docelowej (seniorzy 60+) z technicznymi możliwościami platformy **ElevenLabs Agents** (Conversational AI) [cite: 12, 13].

Niniejszy plan został zaprojektowany pod kątem natychmiastowego wdrożenia przez **Agenta MCP ElevenLabs** (Model Context Protocol), który potrafi przetłumaczyć instrukcje i schematy JSON bezpośrednio na gotową konfigurację w Twoim panelu ElevenLabs [cite: 31, 118].

---

## 1. Architektura Systemowa i Przepływ Konwersacyjny

### 1.1. Wybór modelowania: Natywny Conversational Agent
W celu wyeliminowania skumulowanego opóźnienia tradycyjnych systemów kaskadowych (STT → LLM → TTS), które przekracza 2 sekundy i uniemożliwia naturalny dialog, wdrażamy zintegrowany silnik **ElevenLabs Agents** [cite: 138]. 

Dla Fazy PoC oraz wdrożenia docelowego rezygnujemy z zewnętrznych potoków LLM na rzecz natywnego modelu konwersacyjnego ElevenLabs, co pozwala zamknąć proces detekcji głosu, wnioskowania i syntezy w jednej, zunifikowanej pętli konwersacyjnej [cite: 138].

### 1.2. Dobór Modeli i Latencja
*   **Speech-to-Text (STT):** **Scribe v2 Realtime** [cite: 81, 99]. Model o opóźnieniu transkrypcji mowy wynoszącym zaledwie ok. **150 ms** [cite: 81, 140], ze wsparciem dla języka polskiego i automatyczną detekcją aktywności głosowej (VAD) [cite: 283].
*   **Language Model (LLM):** Zintegrowany model językowy w panelu ElevenLabs (np. GPT-4o Mini lub Gemini 2.5 Flash dla obniżenia kosztów operacyjnych) [cite: 166, 233, 234].
*   **Text-to-Speech (TTS):** **Eleven v3 Conversational** [cite: 47, 280]. Zastosowanie tego modelu zwiększa latencję syntezy mowy do ok. **280 ms** (w porównaniu do 75 ms modelu Flash) [cite: 140], jednak zapewnia **nieporównywalnie wyższą ekspresję emocjonalną, naturalną intonację i głębię tonu** [cite: 140, 280]. Jest to kluczowe dla budowania zaufania, ciepła i poczucia bezpieczeństwa u seniorów (60+) [cite: 12].

---

## 2. Parametry UX i Akustyczne dostosowane do Seniorów (60+)

Seniorzy jako odbiorcy końcowi wymagają wolniejszego tempa mowy, dłuższego oczekiwania na sformułowanie myśli oraz stabilnej, pozbawionej agresywnych modulacji barwy głosu [cite: 12]. Konfiguracja agenta wprowadza rygorystyczne wytyczne akustyczne:

### 2.1. Dynamika rozmowy (Turn-taking) [cite: 139]
*   **turn_timeout (Take turn after silence):** Ustawiony na **3.0 sekundy** (wartość domyślna to zazwyczaj 1.0 - 1.5 sekundy) [cite: 141]. Zapobiega to wchodzeniu seniorom w słowo, dając im czas na oddech lub przypomnienie sobie szczegółów (np. daty urodzenia czy nazwy zabiegu) [cite: 141].
*   **turn_eagerness (Czułość przejmowania tury):** Skonfigurowana w trybie **`Patient`** (Cierpliwy) [cite: 141]. Idealna do pozyskiwania danych ustrukturyzowanych (imię, nazwisko, data), chroniąca przed przerywaniem wypowiedzi w trakcie naturalnych pauz konwersacyjnych [cite: 141].

### 2.2. Charakterystyka barwy głosu i TTS (Głos „Anna”) [cite: 13]
Kanonizujemy personę pod imieniem **Anna** i przypisujemy jej ciepły, kojący głos kobiecy [cite: 5, 12]. Na etapie PoC zaleca się wykorzystanie profesjonalnego głosu lektorskiego o wysokiej empatii, np. **Jessica — Playful, Bright, Warm** (głos premade, ID: `cgSgspJ2msm6clMCkdW9`) [cite: 77], lub stworzenie dedykowanego głosu w generatorze **Voice Design** na podstawie opisu tekstowego [cite: 12, 33].

*   **Stabilność (Stability):** **0.80** (zakres zalecany: 0.60 - 0.85) [cite: 142]. Wysoka wartość chroni przed nienaturalnymi piskami, szeptem czy zniekształceniami emocjonalnymi, gwarantując stałą, spokojną barwę [cite: 142].
*   **Wskaźnik podobieństwa (Similarity Boost):** **0.75** [cite: 142]. Optymalne ustawienie zapewniające najwyższą klarowność i wierność głosu referencyjnego [cite: 142].
*   **Kontrola tempa (Speed Control):** **0.85x** [cite: 142]. Tempo spowolnione o 15% względem standardowej prędkości mowy [cite: 142]. Pozwala starszym kuracjuszom bez problemu zrozumieć podawane przez agenta instrukcje i ceny.

### 2.3. Słownik Wymowy (Pronunciation Dictionary .pls) [cite: 143]
Aby zapobiec błędnej i nienaturalnej wymowie nazw własnych i pojęć medycznych, do agenta podłączamy słownik PLS (XML) [cite: 143]:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0" 
         xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.w3.org/2005/01/pronunciation-lexicon 
                             http://www.w3.org/TR/PRONUNCIATION-LEXICON/pls.xsd"
         alphabet="ipa" xml:lang="pl-PL">
         
  <lexeme>
    <grapheme>Bukowy Dwór</grapheme>
    <phoneme>buˈkɔvɨ dvuːr</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>Krynica-Zdrój</grapheme>
    <phoneme>krɨˈɲit͡sa zdruj</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>borowinowe</grapheme>
    <phoneme>bɔrɔvʲiˈnɔvɛ</phoneme>
  </lexeme>
</lexicon>
```

---

## 3. Baza Wiedzy (RAG) i Eliminacja Halucynacji

Agent będzie zasilany wiedzą z pięciu przygotowanych plików Markdown (Dojazd, SPA, Pokoje, Restauracja, Procedury) [cite: 7, 8]. Ich integracja w panelu ElevenLabs odbywa się w oparciu o ich objętość i przeznaczenie [cite: 92, 94]:

### 3.1. Przypisanie Trybów Użycia (`usage_mode`) [cite: 94]
*   **Tryb `prompt` (Pełny kontekst):** Przeznaczony dla małych plików o krytycznym znaczeniu, które muszą być bezwzględnie dostępne w każdej turze rozmowy słowo w słowo [cite: 94]:
    *   `05_procedury_i_polityki.md` (anulacje, polityka zwrotów, SMS-y) [cite: 7].
    *   `03_pokoje_i_cennik.md` (ceny pokoi, zasady zadatków) [cite: 7].
    *   *Uzasadnienie:* Unikamy ryzyka, że silnik RAG pominie kluczową procedurę lub cenę w trakcie wyszukiwania [cite: 94]. Łączna objętość tych plików nie może przekroczyć 300 000 znaków [cite: 96].
*   **Tryb `auto` (Semantic Search / RAG):** Przeznaczony dla obszernych dokumentów opisowych [cite: 94, 95]:
    *   `01_informacje_ogolne_i_dojazd.md` [cite: 7].
    *   `02_katalog_zabiegow_spa_i_zdrowie.md` [cite: 7].
    *   `04_restauracja_i_diety.md` [cite: 7].
    *   *Uzasadnienie:* System dynamicznie wstrzykuje tylko najbardziej dopasowane fragmenty (chunks) do promptu systemowego, oszczędzając okno kontekstowe LLM [cite: 94, 147].

### 3.2. Reguły Strict Grounding w System Prompcie
W celu całkowitej eliminacji halucynacji (np. wymyślania cen SPA czy wolnych terminów rezerwacji pokoi), w sekcji instrukcji agenta pod kluczem `system_prompt` definiujemy twarde ramy bezpieczeństwa [cite: 120]:

```text
ZASADY BEZWZGLĘDNE (STRICT GROUNDING):
1. Twoje odpowiedzi muszą być w 100% oparte na dostarczonej Bazie Wiedzy oraz wynikach wywołań narzędzi.
2. Jeśli gość pyta o ceny, pakiety, dostępność lub dojazd, a nie ma tych informacji w bazie wiedzy, odpowiedz dokładnie: „Przepraszam, ale nie mam w tej chwili dostępu do tych informacji. Połączę Państwa z Recepcją, gdzie otrzymają Państwo dokładną odpowiedź.” i natychmiast wywołaj narzędzie transfer_to_human.
3. Nigdy nie wymyślaj cen, terminów zabiegów, diet ani procedur. Uzdrowisko dba o zdrowie seniorów, więc informacje muszą być absolutnie precyzyjne.
```

---

## 4. Narzędzia i Integracje API (Zestaw Kanoniczny)

Wszystkie narzędzia są zdefiniowane bezpośrednio w konfiguracji agenta za pomocą standardowego formatu **JSON Schema** [cite: 9, 32].

### 4.1. Webhook Tools (Symulacja Integracji z PMS) [cite: 2, 24]
Podczas prezentacji dane będą zamockowane, ale proces wywołań w tle będzie w pełni autentyczny. Integracja z systemem PMS (np. *KWHotel, Opera*) zostaje zaprogramowana jako zestaw żądań HTTP POST Webhook, które wysyłają parametry i oczekują na odpowiedź ze statycznej makiety JSON [cite: 8, 9]:

#### Narzędzie 1: `check_spa_availability`
*   **Rola:** Sprawdzenie wolnych godzin dla wybranego zabiegu SPA.
*   **JSON Schema:**
```json
{
  "name": "check_spa_availability",
  "description": "Sprawdza dostępność zabiegu SPA lub rehabilitacyjnego w wybranym dniu.",
  "parameters": {
    "type": "object",
    "properties": {
      "service_name": {
        "type": "string",
        "description": "Nazwa zabiegu (np. kąpiel borowinowa, masaż klasyczny)."
      },
      "date": {
        "type": "string",
        "description": "Data w formacie YYYY-MM-DD."
      }
    },
    "required": ["service_name", "date"]
  }
}
```

#### Narzędzie 2: `book_spa_appointment`
*   **Rola:** Zarezerwowanie zabiegu w systemie hotelowym dla konkretnego gościa.
*   **JSON Schema:**
```json
{
  "name": "book_spa_appointment",
  "description": "Dokonuje rezerwacji zabiegu SPA dla gościa na konkretny termin.",
  "parameters": {
    "type": "object",
    "properties": {
      "service_name": { "type": "string" },
      "date": { "type": "string", "description": "YYYY-MM-DD" },
      "time": { "type": "string", "description": "Format HH:MM" },
      "guest_name": { "type": "string", "description": "Imię i nazwisko gościa." }
    },
    "required": ["service_name", "date", "time", "guest_name"]
  }
}
```

#### Narzędzie 3: `check_room_availability`
*   **Rola:** Odpytanie bazy PMS o wolne pokoje w wybranym okresie.
*   **JSON Schema:**
```json
{
  "name": "check_room_availability",
  "description": "Sprawdza dostępność pokoi w wybranym przedziale czasowym.",
  "parameters": {
    "type": "object",
    "properties": {
      "room_type": { "type": "string", "enum": ["jednoosobowy", "dwuosobowy", "apartament"] },
      "check_in": { "type": "string", "description": "YYYY-MM-DD" },
      "check_out": { "type": "string", "description": "YYYY-MM-DD" }
    },
    "required": ["room_type", "check_in", "check_out"]
  }
}
```

---

### 4.2. Bramka Informacyjna/SMS (PoC: Telegram/WhatsApp Bot Webhook)
Aby wywrzeć spektakularne wrażenie podczas prezentacji („Wow effect”), narzędzie `send_sms_summary` zostanie skonfigurowane tak, aby w tle wysyłało zapytanie HTTP do bota **Telegram** lub **WhatsApp** [cite: 13, 15]. 

Podczas rozmowy na żywo z agentem, w momencie gdy Anna powie „*Właśnie wysłałam Panu podsumowanie na telefon*” [cite: 13], na kanale Telegramu (np. wyświetlonym na drugim monitorze lub rzutniku) natychmiast pojawi się estetyczna wiadomość z rezerwacją!

#### Narzędzie 4: `send_sms_summary` (implemented via Messenger Webhook)
*   **JSON Schema:**
```json
{
  "name": "send_sms_summary",
  "description": "Wysyła podsumowanie rezerwacji pokoju lub SPA bezpośrednio na telefon gościa.",
  "parameters": {
    "type": "object",
    "properties": {
      "phone_number": { "type": "string", "description": "Numer telefonu gościa (np. +48123456789)." },
      "summary_text": { "type": "string", "description": "Treść podsumowania (np. 'Rezerwacja kąpieli borowinowej: 25.08 o godz. 14:00. Zapraszamy!')" }
    },
    "required": ["phone_number", "summary_text"]
  }
}
```
*   **Docelowa Faza II:** Połączenie z produkcyjnym API **Twilio SMS** [cite: 15, 29].

---

### 4.3. Human Handoff (Przekierowanie Połączenia Telefonicznego)
Platforma ElevenLabs wspiera natywne przekazywanie aktywnego połączenia telefonicznego za pomocą systemowego narzędzia **`transfer_to_number`** [cite: 25, 28, 149].

*   **Implementacja PoC/Prezentacja:** Narzędzie zostanie skonfigurowane z Twoim prywatnym numerem komórkowym. W momencie eskalacji rozmowy (np. trudne pytania medyczne lub zgłoszenie złego samopoczucia) agent wypowie słowa: „*Łączę z dyżurnym fizjoterapeutą...*” i Twój telefon natychmiast zadzwoni, przejmując rozmowę na żywo!
*   **JSON Schema narzędzia systemowego:**
```json
{
  "name": "transfer_to_human",
  "description": "Natywne przekierowanie połączenia na zdefiniowany numer recepcji lub dyżurki medycznej.",
  "parameters": {
    "type": "object",
    "properties": {
      "department": { "type": "string", "enum": ["recepcja", "dyzurka_medyczna"] },
      "reason": { "type": "string", "description": "Powód przekazania rozmowy." }
    },
    "required": ["department", "reason"]
  }
}
```
*   **Logika routingu (Faza II):** 
    *   Jeśli `department == "recepcja"` -> przekierowanie na numer główny PBX hotelu [cite: 8].
    *   Jeśli `department == "dyzurka_medyczna"` -> przekierowanie na dedykowaną linię medyczną / dyżurkę pielęgniarską [cite: 7].

---

## 5. Skalowanie na Sieć Hoteli (Multi-obiektowość)

W celu łatwego skalowania rozwiązania na całą sieć hoteli SPA bez konieczności powielania i utrzymywania dziesiątek niezależnych agentów, wdrażamy architekturę opartą na **Dynamic Variables** oraz **Overrides** [cite: 25, 28].

### 5.1. Model Jednego Nadrzędnego Agenta z Dynamicznym Nadpisywaniem
Tworzymy jednego, centralnego agenta „Anna”. W momencie nawiązywania połączenia telefonicznego (przez SIP Trunk centrali PBX) lub otwierania widżetu WebSocket, system przesyła pakiet inicjalizacyjny `conversation_initiation_client_data` zawierający zmienne kontekstowe specyficzne dla danego obiektu [cite: 28, 155]:

```json
{
  "type": "conversation_initiation_client_data",
  "conversation_config_override": {
    "agent": {
      "prompt": {
        "system_prompt": "Jesteś recepcjonistką w hotelu {{hotel_name}} w miejscowości {{location}}. Kontakt do nas to {{reception_phone}}."
      }
    }
  },
  "dynamic_variables": {
    "hotel_name": "Bukowy Dwór - Skrzydło Termalne",
    "location": "Krynica-Zdrój",
    "reception_phone": "+48 18 123 45 67",
    "pms_hotel_id": "HOTEL_001_A"
  }
}
```

### 5.2. Przekazywanie Metadanych w Sygnalizacji SIP (RFC 7433)
Dla połączeń telefonicznych, centrala PBX hotelu przekazuje identyfikator dzwoniącego i ID hotelu bezpośrednio w sygnalizacji SIP za pomocą nagłówków **UUI (User-to-User Information, RFC 7433)** [cite: 5, 160]. Serwer ElevenLabs odczytuje te dane (do 256 bajtów) i automatycznie aplikuje odpowiednie nadpisania konfiguracji, dopasowując bazę wiedzy i zachowanie asystenta w czasie rzeczywistym [cite: 5, 160].

---

## 6. Enterprise Compliance, RODO i Bezpieczeństwo

Głównym wyzwaniem w branży uzdrowiskowej jest przetwarzanie danych osobowych (RODO) oraz wrażliwych danych medycznych (stan zdrowia, przeciwwskazania do zabiegów rehabilitacyjnych) [cite: 7, 12].

### 6.1. Ochrona Kluczy API: Signed URLs [cite: 19, 20]
W celu osadzenia interaktywnego widgetu na stronie internetowej uzdrowiska, aplikacja kliencka nie może komunikować się bezpośrednio przy użyciu głównego klucza API dewelopera (ryzyko kradzieży klucza i nielimitowanych kosztów) [cite: 156]. 
*   **Proces autoryzacji:** Serwer hotelu (bezpieczne środowisko) wysyła żądanie do API ElevenLabs `/get_signed_url` [cite: 19, 157]. W odpowiedzi otrzymuje podpisany token ważny przez **15 minut** [cite: 19, 157]. Połączenie WebSocket jest nawiązywane przy użyciu tego tymczasowego adresu URL, zapewniając 100% bezpieczeństwo infrastruktury [cite: 19, 157].

### 6.2. Strategia RODO dla Prezentacji (Enterprise Plan) [cite: 11]
Podczas prezentacji dla Hiring Managera należy wytłumaczyć, w jaki sposób ElevenLabs zapewnia pełne bezpieczeństwo danych gości [cite: 13]:
1.  **Zero Retention Mode (ZRM):** Po aktywacji tego trybu w planie Enterprise, pliki audio oraz generowane transkrypcje są przetwarzane wyłącznie w pamięci RAM i **nigdy** nie są zapisywane na dyskach twardych ElevenLabs [cite: 26, 132].
2.  **Conversation History Redaction:** Jeśli chcemy zachować statystyki rozmów i badać trendy, aktywujemy tryb redukcji historii [cite: 26, 131]. System automatycznie wykrywa i zamienia na gwiazdki (maskuje) wrażliwe dane osobowe: nazwiska, numery telefonów, numery rezerwacji oraz pojęcia o charakterze medycznym [cite: 26, 131].
3.  **Data Residency:** Gwarancja przetwarzania danych na terenie Unii Europejskiej (serwery w regionie EU) w celu pełnej zgodności z DPA i regulacjami RODO.

---

## 7. Analiza Kosztów i Limitów Operacyjnych

| Parametr | Środowisko PoC (Testy & Demo) | Skala Produkcyjna (Wdrożenie Enterprise) |
| :--- | :--- | :--- |
| **Rekomendowany Plan** | **Creator** ($22/miesiąc) [cite: 11, 53] | **Enterprise / Scale** ($299/miesiąc) [cite: 11, 53] |
| **Pakiet minut w cenie** | **275 minut** [cite: 53] | **3 738 minut** [cite: 53] |
| **Koszt minuty nadmiarowej**| $0.080 [cite: 53] | $0.080 (negocjowany niżej przy skali) [cite: 53, 164] |
| **Limit jednoczesnych połączeń**| **10 concurrent calls** [cite: 53] | **30 concurrent calls** [cite: 53] |
| **Obsługa piku ruchu** | Standardowy limit [cite: 101] | **Burst Pricing** (Zwiększenie jednoczesności 3x do 90 concurrent calls, dodatkowe połączenia płatne $0.160/min) [cite: 11, 13, 165] |
| **Dostęp dla zespołu** | 1 konto [cite: 53] | 3 Workspace Seats (Scale) / Dedykowany podział uprawnień [cite: 53] |

---

## 8. Wytyczne Wykonawcze dla Agenta MCP

*Instrukcja dla Twojego Agenta MCP, który automatycznie skonfiguruje Recepcjonistę w ElevenLabs.*

> **⚠️ KOREKTA (zweryfikowano z realnym MCP ElevenLabs).** Narzędzie MCP `create_agent` NIE obsługuje: webhook tool-calling, `turn_eagerness`, `speed` ani trybów `usage_mode` bazy wiedzy. Poniżej podział na to, co da się zrobić przez MCP, a co wymaga panelu ElevenLabs / pełnego API.

### 8.1. Co wykonuje MCP `create_agent`
1. **Stwórz agenta** o nazwie `Bukowy_Dwor_Anna` (lub `Anna`), parametrami:
   * `language: "pl"`
   * `temperature: 0.1` (rygorystyczność, minimalizacja kreatywności)
   * `stability: 0.80`, `similarity_boost: 0.75`
   * `turn_timeout: 3` (w sekundach; parametr MCP jest liczbą całkowitą)
   * `model_id: eleven_v3_conversational` (zweryfikuj dostępność przez `list_models`)
   * `voice_id: cgSgspJ2msm6clMCkdW9` (Jessica — Playful, Bright, Warm)
   * `first_message` + `system_prompt` = treść z `docs/anna_system_prompt_v3.md`

### 8.2. Baza wiedzy — konwersja i ograniczenie
* MCP `add_knowledge_base_to_agent` przyjmuje wyłącznie **epub / pdf / docx / txt / html** — NIE `.md`.
* **Krok 1:** skonwertuj 5 plików `docs/baza_wiedzy_rag_bukowy_dwor/*.md` do `.txt` (kodowanie UTF-8).
* **Krok 2:** dodaj je do agenta przez MCP (osobne wywołanie na plik; użyj pola `text` lub `input_file_path`).
* **Ograniczenie:** podział na tryby `prompt` vs `auto` (`usage_mode`) NIE jest dostępny w MCP — ustaw w panelu ElevenLabs (Knowledge Base → tryb per plik), jeśli jest wymagany.

### 8.3. Co wymaga panelu ElevenLabs / pełnego API (poza MCP)
* **Tool calling (4 webhooki + `transfer_to_number`):** zarejestruj narzędzia z JSON Schema (§4) ręcznie w panelu agenta → sekcja Tools. Webhook URL: `http://localhost:8000/{endpoint}` (PoC lokalny) lub publiczny adres z ngrok — patrz `mock_backend/README.md`.
* **`turn_eagerness: Patient`:** ustaw w panelu (Conversation → Turn-taking); brak tego parametru w MCP.
* **`speed: 0.85`:** ustaw w sekcji głosu agenta w panelu (brak w MCP).
* **Słownik wymowy (PLS, §2.3):** podłącz w panelu (nie w MCP).

### 8.4. Kolejność realizacji
1. Skonwertuj 5 plików `.md → .txt`.
2. MCP `create_agent` (głos, system prompt, parametry akustyczne).
3. MCP `add_knowledge_base_to_agent` (5 plików txt).
4. Panel / API: tool calling + `turn_eagerness` + `speed` + PLS.
5. Uruchom mock backend (`uvicorn main:app --port 8000`) + ngrok dla webhooków.
