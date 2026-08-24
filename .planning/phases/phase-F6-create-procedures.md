# Phase F6 — Utworzenie procedur (obiekty osobno, bez wpinania do agenta)

## Cel
Wydzielić z istniejącego system promptu Anny logiczne, nazwane procedury i utworzyć je przez API jako **osobne obiekty**. ANIEN agent nie jest jeszcze modyfikowany — tworzymy procedury niezależnie, by zweryfikować, że da się je zapisać i skompilować.

## Zależności
- Phase F5 (endpointy + branch_id).
- Treść kroków: `docs/anna_system_prompt_v3.md` (sekcja `PROTOKÓŁ ZBIERANIA DANYCH DO REZERWACJI`, `OBSŁUGA ZABIEGÓW SPA`, `KIEDY PRZEKAZAĆ DO CZŁOWIEKA`).

## Krok 1 — Definiuj procedury (typ: `free_form` dla płynnych, `deterministic` dla decyzji)

### 1. `przeprowadz_rezerwacje_zabiegu_spa` (free_form)
Treść: kroki 1–10 z promptu — zapytaj o zabieg → datę → `check_spa_availability` → godziny → dane gościa → **parafraza + potwierdzenie** → `book_spa_appointment` → numer telefonu (opcjonalnie opiekun) → `send_sms_summary` → pożegnaj ciepło.
`trigger`: "Gdy gość chce zarezerwować zabieg SPA."

### 2. `przeprowadz_zapytanie_o_pokoj` (free_form)
Treść: typ pokoju → daty → `check_room_availability` → wynik (dostępność, cena/noc, łączna kwota) → finalizacja u recepcji.
`trigger`: "Gdy gość pyta o dostępność lub rezerwację pokoju."

### 3. `sprawdz_przeciwwskazania_zdrowotne` (free_form)
Treść: przed zabiegiem balneologicznym (kąpiel siarczkowa/borowinowa, jonoforeza) zapytaj o zawał/krążenie; przy przeciwwskazaniu → lekarz uzdrowiskowy + `transfer_to_simulated_handoff`; masaże nie wymagają.
`trigger`: "Przed rezerwacją zabiegu balneologicznego."

### 4. `decyzja_o_transferze` (deterministic)
Treść: reguły kiedy przekazać do człowieka (stan nagły, skarga, negocjacja, brak danych, prośba) vs. nie przekazywać przy braku wolnego terminu (zaproponuj alternatywę).
`trigger`: "Gdy gość zgłasza sytuację wymagającą interwencji człowieka."

## Krok 2 — Utwórz procedury przez POST
```
POST /v1/convai/agents/{agent_id}/branches/{branch_id}/procedures
Body: {"name": "<nazwa>", "content": "<treść>", "trigger": "<trigger>", "type": "free_form"|"deterministic"}
```
- Utwórz osobno każdą z 4 procedur.
- Zachowaj odpowiedzi (`procedure_id`, `version_id`).

## Krok 3 — Weryfikacja
- `GET /v1/convai/agents/{agent_id}/branches/{branch_id}/procedures` → wszystkie 4 widoczne.
- Sprawdź `referenced_tool_ids` / `referenced_kb_ids` w `ProcedureRefResponseModel` — czy procedury wykryły odwołania do narzędzi.
- Opcjonalnie: `POST .../compile` → czy wszystkie przechodzą walidację.

## DoD
- 4 procedury utworzone i widoczne w `list_procedures`.
- Struktury poprawne (compile green / konkretny wynik).
- Agent `Bukowy_Dwor_Anna` NIE został zmodyfikowany (procedury są osobnymi obiektami).