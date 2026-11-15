#!/usr/bin/env python3
"""Kontrola zgodności bazy wiedzy: ``agent/knowledge_base/NN_*.md`` <-> ``agent/knowledge_base_txt/NN_*.txt``.

Każdy plik źródłowy ``.md`` (kanon faktów) musi mieć parę ``.txt`` o tej samej nazwie
(bez rozszerzenia), która wgrywana jest do ElevenLabs przez ``scripts/deploy_kb_and_tools.py``.
Porównanie odbywa się po normalizacji, więc różnice formatowania nie są błędem:

- usunięcie BOM i zamiana CRLF na LF,
- usunięcie końcowych spacji,
- usunięcie znaczników markdown (nagłówki ``#``, punktory ``- ``, pogrubienia ``**``, backticki),
- usunięcie pustych linii.

Wynik: exit 0, gdy wszystkie pary są zgodne; exit 1 z podsumowaniem różnic w przeciwnym razie.
README.md nie jest częścią bazy wiedzy i jest pomijany.

Użycie (z katalogu repo)::

    python scripts/check_kb_parity.py
    python scripts/check_kb_parity.py --root /ścieżka/do/repo --max-diff-lines 40
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
MD_DIR = Path("agent") / "knowledge_base"
TXT_DIR = Path("agent") / "knowledge_base_txt"
DOC_PATTERN = re.compile(r"^\d{2}_.+$")

_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
_BULLET = re.compile(r"^\s*[-*]\s+")
_EMPHASIS = re.compile(r"\*\*")
_BACKTICK = re.compile(r"`")


def normalize(text: str) -> List[str]:
    """Zwraca listę znormalizowanych linii (bez znaczników markdown i pustych linii)."""
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines: List[str] = []
    for raw in text.split("\n"):
        line = raw.rstrip()
        line = _HEADING.sub("", line)
        line = _BULLET.sub("", line)
        line = _EMPHASIS.sub("", line)
        line = _BACKTICK.sub("", line)
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def collect_pairs(root: Path) -> Tuple[Dict[str, Path], Dict[str, Path]]:
    """Mapy ``stem -> ścieżka`` dla plików .md i .txt (tylko ``NN_*``)."""
    md = {p.stem: p for p in sorted((root / MD_DIR).glob("*.md")) if DOC_PATTERN.match(p.stem)}
    txt = {p.stem: p for p in sorted((root / TXT_DIR).glob("*.txt")) if DOC_PATTERN.match(p.stem)}
    return md, txt


def compare(root: Path, max_diff_lines: int) -> Tuple[List[str], int]:
    """Zwraca (raport linii, liczba problemów)."""
    report: List[str] = []
    problems = 0
    md, txt = collect_pairs(root)

    if not md:
        report.append(f"BLAD: brak plików NN_*.md w {MD_DIR.as_posix()}")
        return report, 1

    for stem in sorted(set(md) | set(txt)):
        src: Optional[Path] = md.get(stem)
        twin: Optional[Path] = txt.get(stem)
        if src is None:
            problems += 1
            report.append(f"BRAK .md dla {twin.name} (txt bez źródła)")
            continue
        if twin is None:
            problems += 1
            report.append(f"BRAK .txt dla {src.name} (brak pary wdrożeniowej)")
            continue

        a = normalize(src.read_text(encoding="utf-8"))
        b = normalize(twin.read_text(encoding="utf-8"))
        if a == b:
            report.append(f"OK    {src.name} == {twin.name} ({len(a)} linii)")
            continue

        problems += 1
        diff = list(difflib.unified_diff(a, b, fromfile=src.name, tofile=twin.name, lineterm="", n=0))
        changed = sum(1 for d in diff if d[:1] in "+-" and d[:3] not in ("+++", "---"))
        report.append(f"DIFF  {src.name} != {twin.name} (zmienionych linii: {changed})")
        shown = diff[: max_diff_lines]
        report.extend(f"      {d}" for d in shown)
        if len(diff) > max_diff_lines:
            report.append(f"      ... (+{len(diff) - max_diff_lines} linii różnic)")

    return report, problems


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sprawdza zgodność KB .md z wdrożeniowymi .txt.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="katalog repo (domyślnie: nadrzędny do scripts/)")
    parser.add_argument("--max-diff-lines", type=int, default=20, help="ile linii różnic pokazać na parę")
    args = parser.parse_args(argv)

    report, problems = compare(args.root.resolve(), args.max_diff_lines)
    print("\n".join(report))
    if problems:
        print(f"\nFAIL: {problems} problem(y) zgodności KB.")
        return 1
    print("\nOK: wszystkie pary KB są zgodne.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
