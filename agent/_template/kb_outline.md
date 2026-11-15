# Układ bazy wiedzy (KB) dla nowego klienta

Szablon struktury. Wzorzec w repo: `agent/knowledge_base/` (źródło `.md`) i `agent/knowledge_base_txt/` (wdrożeniowe `.txt`), wdrażane przez `scripts/deploy_kb_and_tools.py`.

## Zasady

1. **Jeden fakt, jedno miejsce.** Ceny, godziny, zasady zwrotów: tylko w KB (lub w systemie, do którego podłączone jest narzędzie). Prompt nie powtarza wartości.
2. **Właściciel i data weryfikacji** w nagłówku każdego dokumentu: `> Właściciel: <rola> · Zweryfikowano: RRRR-MM-DD`.
3. **Źródło i wdrożenie zgodne.** `NN_nazwa.md` (kanon, do edycji) i `NN_nazwa.txt` (kopia wdrożeniowa). Kontrola: `scripts/check_kb_parity.py` (adaptacja).
4. **Krótkie sekcje z nagłówkami `##`**, pola w formie `- **Pole:** wartość`. Model lepiej wyszukuje takie fragmenty w RAG.
5. **Żadnych danych osobowych gości** ani przykładowych rezerwacji produkcyjnych.

## Proponowany podział (przykład: hotel / uzdrowisko)

| Nr | Dokument | Zawartość | `usage_mode` | Właściciel |
|---|---|---|---|---|
| 01 | `informacje_ogolne` | adres, godziny pracy, dojazd, dostępność, parking | `auto` (RAG) | recepcja |
| 02 | `katalog_uslug` | usługi: czas trwania, opis, przeciwwskazania, cena (jeśli stała) | `auto` (RAG) | kierownik usług |
| 03 | `pokoje_cennik` | typy zasobów, ceny za dobę, zadatek, zasady zajęcia | `prompt` (pełny kontekst) | sprzedaż |
| 04 | `zywienie_diety` | godziny posiłków, dostępne diety, terminy zgłoszeń | `auto` (RAG) | gastronomia |
| 05 | `procedury_polityki` | anulacje, zmiany terminów, zwierzęta, komunikacja SMS, wyjątki | `prompt` (pełny kontekst) | zarząd / recepcja |

Zasada doboru `usage_mode`:
- `prompt` dla dokumentów, w których pomyłka jest kosztowna (ceny, zwroty, procedury). Są zawsze w kontekście, więc RAG nie może ich pominąć.
- `auto` dla dokumentów opisowych, gdzie wystarczy wyszukiwanie fragmentów.

## Szablon pojedynczego dokumentu

```markdown
# <Tytuł dokumentu> - <Klient>

> Właściciel: <rola> · Zweryfikowano: RRRR-MM-DD

## <Sekcja>
- **Pole:** wartość
- **Pole:** wartość

## Wyjątki i uwagi dla agenta
- Co agent ma powiedzieć, a czego nie ma obiecywać.
- Kiedy przekazać do człowieka (odwołanie do sekcji promptu, nie kopia).
```

## Co NIE trafia do KB

- Dane osobowe, rezerwacje, dane płatnicze.
- Porady medyczne i dawkowanie (KB opisuje usługi, nie leczy). Dla treści medycznej ustal wyraźny zakres i właściciela.
- Wewnętrzne instrukcje dla personelu, które nie są przeznaczone dla gościa.
- Stawki, które zmieniają się częściej niż raz na kwartał: lepiej podłączyć narzędzie niż aktualizować KB.

## Checklista przed wdrożeniem

- [ ] Każdy dokument ma właściciela i datę weryfikacji.
- [ ] Ceny i zasady zwrotów zgadzają się z regulaminem (podpis właściciela).
- [ ] `.md` i `.txt` są zgodne (kontrola parity).
- [ ] Dokumenty krytyczne mają `usage_mode: prompt`.
- [ ] Sprzeczności między dokumentami zostały rozstrzygnięte i opisane w sekcji „Wyjątki" (nie zostawione cicho).
