# Phase 1 — Konwersja bazy wiedzy `.md → .txt`

## Cel
Przygotować 5 plików bazy wiedzy do załadowania w ElevenLabs (MCP `add_knowledge_base_to_agent` przyjmuje tylko `epub/pdf/docx/txt/html`).

## Zależności
Brak (pierwsza faza).

## Wejście
`docs/baza_wiedzy_rag_bukowy_dwor/` — 5 plików `.md`:
- `01_informacje_ogolne_i_dojazd.md`
- `02_katalog_zabiegow_spa_i_zdrowie.md`
- `03_pokoje_i_cennik.md`
- `04_restauracja_i_diety.md`
- `05_procedury_i_polityki.md`

## Kroki

1. Utwórz katalog docelowy i skopiuj pliki (bezzębna, bezstratna konwersja — KB czyta plain text; markdown jest nieszkodliwy, ale lepiej go lekko oczyścić):

```bash
mkdir -p docs/baza_wiedzy_rag_bukowy_dwor_txt
for f in docs/baza_wiedzy_rag_bukowy_dwor/*.md; do
  base=$(basename "$f" .md)
  # usun znaczniki markdown (nagłówki #, pogrubienie **, listy nie są usuwane — bezpieczne)
  sed -e 's/^#\{1,\} *//' -e 's/\*\*//g' "$f" > "docs/baza_wiedzy_rag_bukowy_dwor_txt/${base}.txt"
done
```

2. Zweryfikuj kompletność — kluczowe wartości muszą przetrwać:

```bash
grep -l "350" docs/baza_wiedzy_rag_bukowy_dwor_txt/*.txt
grep -l "34°C" docs/baza_wiedzy_rag_bukowy_dwor_txt/*.txt
grep -l "14 dni" docs/baza_wiedzy_rag_bukowy_dwor_txt/*.txt
wc -l docs/baza_wiedzy_rag_bukowy_dwor_txt/*.txt
```

## DoD
- [ ] 5 plików `.txt` w `docs/baza_wiedzy_rag_bukowy_dwor_txt/`.
- [ ] Kodowanie UTF-8.
- [ ] Kluczowe wartości obecne: ceny (350/500/750), temperatura 34°C, polityka anulacji „14 dni", procedury SMS, godziny posiłków.
- [ ] Linie nie zgubione (porównaj `wc -l` z oryginałami).

## Wynik przekazany do Phase 4
Ścieżka katalogu `docs/baza_wiedzy_rag_bukowy_dwor_txt/` z 5 plikami `.txt`.