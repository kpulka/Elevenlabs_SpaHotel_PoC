"""Sprawdza spójność docs/INDEX.md z katalogiem docs/ (stdlib, bez zależności).

1. Każdy plik docs/*.md (poza samym INDEX.md i podkatalogami) musi być wymieniony w INDEX.md
   jako `nazwa.md` — inaczej dokument jest "osierocony", a INDEX przestaje być punktem wejścia.
2. Każdy plik `*.md` przywołany w INDEX.md jako `ścieżka.md` musi istnieć (względem docs/
   albo korzenia repo) — inaczej to martwe odniesienie.

Uruchomienie z korzenia repo:  python docs/verify_index.py
Kod wyjścia 0 = OK, 1 = brakujące wpisy lub martwe odniesienia.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent
REPO = DOCS.parent
INDEX = DOCS / "INDEX.md"

# Ścieżki w backtickach zakończone na .md (np. `archive/anna_system_prompt.md`).
ODWOLANIE = re.compile(r"`([^`\s]+\.md)`")


def main() -> int:
    tekst = INDEX.read_text(encoding="utf-8")
    problemy: list[str] = []

    dokumenty = sorted(p.name for p in DOCS.glob("*.md") if p.name != INDEX.name)
    for nazwa in dokumenty:
        if f"`{nazwa}`" not in tekst:
            problemy.append(f"brak wpisu w INDEX.md: {nazwa}")

    for ref in sorted(set(ODWOLANIE.findall(tekst))):
        if not ((DOCS / ref).is_file() or (REPO / ref).is_file()):
            problemy.append(f"martwe odniesienie w INDEX.md: {ref}")

    if problemy:
        print("docs/INDEX.md — niespójności:")
        for linia in problemy:
            print(f"  - {linia}")
        return 1

    print(f"docs/INDEX.md OK: {len(dokumenty)} dokumentów w docs/, wszystkie wpisane; odwołania .md istnieją.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # konsola Windows (cp1252) nie zniesie polskich znaków
    sys.exit(main())
