# Phase 4 — `add_knowledge_base_to_agent` (baza wiedzy)

## Cel
Załadować 5 plików `.txt` (z Phase 1) jako knowledge base agenta „Anna".

## Zależności
Phase 1 (pliki txt) + Phase 3 (`agent_id`).

## ⚠️ BLOKER MCP (odkryty podczas wykonania)

Narzędzie MCP `add_knowledge_base_to_agent` jest **zepsute po stronie serwera** — zwraca błąd `'AgentConfig' object has no attribute 'get'` niezależnie od argumentów (testowane z `text`). To błąd implementacji MCP, nie naszych danych.

**Workaround:** dodać bazę wiedzy **ręcznie w panelu ElevenLabs** (ElevenLabs → Agents → `Bukowy_Dwor_Anna` → Knowledge Base → upload 5 plików `.txt` z `docs/baza_wiedzy_rag_bukowy_dwor_txt/`). Treść KB jest gotowa, agent istnieje (`agent_8401m0n03cggfgebhfh0cj96t7aj`).

## Możliwe ścieżki (wybór: panel)
- **A. Panel (rekomendacja):** upload 5 `.txt` w UI — 2 min, zero kodu.
- **B. REST API (curl):** Conversational AI API + klucz API, jeśli wolimy automatyzować.

---

## Kroki — 5 wywołań MCP

Dla każdego pliku wywołaj `add_knowledge_base_to_agent`:
```
tool_call: mcp__elevenlabs__add_knowledge_base_to_agent, args:
{
  "agent_id": "<agent_id z Phase 3>",
  "knowledge_base_name": "Bukowy_Dwor_wiedza",
  "text": "<TREŚĆ PLIKU .txt>"
}
```

Lista plików (czytaj treść i wstaw w `text`):
1. `docs/baza_wiedzy_rag_bukowy_dwor_txt/01_informacje_ogolne_i_dojazd.txt`
2. `.../02_katalog_zabiegow_spa_i_zdrowie.txt`
3. `.../03_pokoje_i_cennik.txt`
4. `.../04_restauracja_i_diety.txt`
5. `.../05_procedury_i_polityki.txt`

## Uwagi
- Pole `text` jest najpewniejsze (treść inline); `input_file_path` może nie działać, jeśli serwer MCP nie widzi lokalnego dysku Windows. Użyj `text`.
- Nazwa KB taka sama dla wszystkich (spójna grupa), treść się sumuje.
- MCP NIE wystawia trybów `usage_mode` (`prompt`/`auto`) — Jeśli zależy nam na podziale (cennik+procedury w `prompt`, reszta w `auto`), zrób to później w panelu (Phase 6). Dla PoC domyślny tryb jest wystarczający.

## DoD
- [ ] 5 wywołań zakończonych sukcesem.
- [ ] `get_agent(agent_id)` pokazuje załadowaną knowledge base.
- [ ] Kluczowe wartości w KB (ceny 350/500/750, „14 dni", 34°C) obecne.

## Wynik przekazany do Phase 7
Potwierdzenie załadowanej bazy wiedzy (agent potrafi odpowiadać z RAG).