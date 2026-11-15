#!/usr/bin/env python3
"""Grounding lint: fakty z promptu i procedur muszą istnieć w bazie wiedzy (KB).

Sprawdza pliki agenta (``agent/system_prompt_v3.md``, ``agent/procedures/procedures_7.md``)
względem ``agent/knowledge_base/NN_*.md`` (kanon faktów):

* kwoty w walucie (``50 zł``, ``100 PLN``) — ta sama liczba musi wystąpić w KB przy walucie,
* godziny ``GG:MM`` — ta sama godzina musi wystąpić w KB (daty ISO z godziną, np.
  ``2026-11-09T18:30``, są formatem, nie faktem, i są pomijane),
* nazwy zabiegów i usług (rodzina słów: kąpiel, masaż, jonoforeza, grota, herbata, przechowalnia…)
  — pierwsze dwa słowa frazy muszą wystąpić w KB,
* nazwy własne w cudzysłowie (``„Bukowy Smak"``: same wielkie litery, bez interpunkcji) — muszą
  wystąpić w KB.

Porównanie słów jest odporne na odmianę: każde słowo sprowadzane jest do pierwszych 5 liter
(``siarczkową`` ≈ ``siarczkowa``). Wyjątki dla przykładów w prompcie są w
``scripts/lint_prompt_kb_allowlist.json`` (z uzasadnieniem przy każdym wpisie).

Wynik: exit 0, gdy nie ma naruszeń; exit 1 z listą miejsc (plik:linia) w przeciwnym razie.
Stdlib only, bez sieci.

Użycie (z katalogu repo)::

    python scripts/lint_prompt_kb.py
    python scripts/lint_prompt_kb.py --root /ścieżka/do/repo
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWLIST = Path(__file__).resolve().parent / "lint_prompt_kb_allowlist.json"
# (plik, czy sprawdzać tylko tekst w blokach ``` — prompt jest w bloku, reszta to dokumentacja)
CHECKED_FILES: Tuple[Tuple[Path, bool], ...] = (
    (Path("agent") / "system_prompt_v3.md", True),
    (Path("agent") / "procedures" / "procedures_7.md", False),
)
KB_DIR = Path("agent") / "knowledge_base"
KB_PATTERN = re.compile(r"^\d{2}_.+\.md$")
STEM_LEN = 5  # porównanie po pierwszych 5 literach: odmiana nie robi fałszywych alarmów

AMOUNT = re.compile(r"(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(?:PLN|zł|zl)(?!\w)", re.IGNORECASE)
ISO_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}")
CLOCK = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?!\d)")
QUOTED = re.compile(r"„([^„”\"\n]{1,80})[”\"]")
SERVICE_HEAD = re.compile(
    r"\b(kąpie\w*|masaż\w*|masaz\w*|jonofore\w*|ionofore\w*|gimnastyk\w*|grot\w*|herbat\w*|"
    r"sauna\w*|sauny|saunie|peeling\w*|przechowal\w*|dietetyk\w*|fizjoterap\w*)\b",
    re.IGNORECASE,
)
WORD = re.compile(r"[^\W\d_]+")
STOPWORDS = frozenset({
    "a", "albo", "ale", "bez", "czy", "dla", "do", "i", "jak", "lub", "na", "nad", "od", "oraz",
    "po", "pod", "przy", "się", "to", "u", "w", "we", "z", "za", "ze", "że",
})
NAME_BLOCKERS = re.compile(r"[,.;:!?()/—–]")
# Drugie słowo nazwy usługi to zwykle przymiotnik (leczniczy, siarczkowa, lecznicza, ziołową):
# te końcówki odsiewają czasowniki i przysłówki stojące tuż po rzeczowniku (kosztuje, zawsze).
ADJECTIVE_ENDINGS = ("y", "a", "ą", "ej", "ego", "ych", "ym", "i")
# Przysłówki i czasowniki stojące tuż po rzeczowniku usługi — nie są częścią nazwy usługi.
MODIFIER_STOPWORDS = frozenset({
    "bardzo", "dobrze", "jako", "jest", "jeszcze", "już", "mam", "ma", "można", "może", "mogę",
    "najpierw", "nigdy", "potem", "przed", "razem", "są", "teraz", "także", "tylko", "też",
    "wcześniej", "później", "zawsze", "zwykle", "będzie",
})


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    value: str

    def render(self) -> str:
        return f"{self.file}:{self.line}: {self.kind} '{self.value}' nie występuje w bazie wiedzy"


@dataclass
class Allowlist:
    amounts: Dict[str, str]
    hours: Dict[str, str]
    phrases: Dict[str, str]

    @classmethod
    def load(cls, path: Optional[Path]) -> "Allowlist":
        if path is None or not path.exists():
            return cls({}, {}, {})
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            amounts={str(k): str(v) for k, v in raw.get("amounts", {}).items()},
            hours={str(k): str(v) for k, v in raw.get("hours", {}).items()},
            phrases={str(k).lower(): str(v) for k, v in raw.get("phrases", {}).items()},
        )


def stems(text: str) -> List[str]:
    """Słowa (bez cyfr) sprowadzone do pierwszych ``STEM_LEN`` liter, małymi literami."""
    return [word.lower()[:STEM_LEN] for word in WORD.findall(text)]


def normalize_amount(raw: str) -> str:
    return f"{float(raw.replace(',', '.')):g}"


def normalize_clock(hours: str, minutes: str) -> str:
    return f"{int(hours)}:{minutes}"


@dataclass
class KnowledgeBase:
    amounts: Set[str]
    clocks: Set[str]
    stream: str  # " stem stem ... " — dopasowanie fraz jako ciągów słów

    @classmethod
    def from_texts(cls, texts: List[str]) -> "KnowledgeBase":
        amounts: Set[str] = set()
        clocks: Set[str] = set()
        words: List[str] = []
        for text in texts:
            amounts.update(normalize_amount(m.group(1)) for m in AMOUNT.finditer(text))
            clocks.update(normalize_clock(m.group(1), m.group(2)) for m in CLOCK.finditer(text))
            words.extend(stems(text))
        return cls(amounts=amounts, clocks=clocks, stream=" " + " ".join(words) + " ")

    def has_phrase(self, phrase: str) -> bool:
        needle = " " + " ".join(stems(phrase)) + " "
        return needle in self.stream


def service_phrases(line: str, start: int) -> List[str]:
    """Rdzeń usługi (np. „grota") i, jeśli jest, dwuwyrazowa nazwa („grota solna").

    Drugie słowo dołączane jest tylko wtedy, gdy stoi tuż za rdzeniem i nie jest spójnikiem
    ani przysłówkiem (``jonoforezie zawsze`` -> sam rdzeń).
    """
    head = SERVICE_HEAD.match(line, start)
    if head is None:  # pragma: no cover - wywoływane tylko z dopasowaniem SERVICE_HEAD
        return []
    phrases = [head.group(1)]
    rest = line[head.end():]
    following = WORD.match(rest.lstrip())
    if following and rest[:1].isspace():
        word = following.group(0).lower()
        if word.endswith(ADJECTIVE_ENDINGS) and word not in STOPWORDS and word not in MODIFIER_STOPWORDS:
            phrases.append(f"{head.group(1)} {following.group(0)}")
    return phrases


def quoted_name(content: str) -> bool:
    """Czy treść cudzysłowu wygląda na nazwę własną (wielkie litery, bez zdania)."""
    words = content.split()
    if not 1 <= len(words) <= 4 or NAME_BLOCKERS.search(content):
        return False
    return all(word[0].isupper() for word in words)


def lint_text(
    file_label: str,
    text: str,
    kb: KnowledgeBase,
    allow: Allowlist,
) -> Tuple[List[Finding], int]:
    """Zwraca (naruszenia, liczba sprawdzeń) dla jednego pliku."""
    findings: List[Finding] = []
    checks = 0
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = ISO_DATETIME.sub("", raw_line)

        for match in AMOUNT.finditer(line):
            value = normalize_amount(match.group(1))
            checks += 1
            if value not in kb.amounts and value not in allow.amounts:
                findings.append(Finding(file_label, number, "kwota", match.group(0)))

        for match in CLOCK.finditer(line):
            value = normalize_clock(match.group(1), match.group(2))
            checks += 1
            if value not in kb.clocks and value not in allow.hours:
                findings.append(Finding(file_label, number, "godzina", match.group(0)))

        for match in SERVICE_HEAD.finditer(line):
            checks += 1
            head, *bigram = service_phrases(line, match.start())
            if not kb.has_phrase(head) and head.lower() not in allow.phrases:
                findings.append(Finding(file_label, number, "usługa", head))
                continue
            for phrase in bigram:
                checks += 1
                if not kb.has_phrase(phrase) and phrase.lower() not in allow.phrases:
                    findings.append(Finding(file_label, number, "usługa", phrase))

        for match in QUOTED.finditer(line):
            content = match.group(1).strip()
            if not quoted_name(content):
                continue
            checks += 1
            if not kb.has_phrase(content) and content.lower() not in allow.phrases:
                findings.append(Finding(file_label, number, "nazwa", content))
    return findings, checks


def load_kb_texts(root: Path) -> List[str]:
    kb_dir = root / KB_DIR
    paths = sorted(p for p in kb_dir.glob("*.md") if KB_PATTERN.match(p.name))
    if not paths:
        raise FileNotFoundError(f"{KB_DIR.as_posix()}/NN_*.md")
    return [p.read_text(encoding="utf-8") for p in paths]


def fenced_only(text: str) -> str:
    """Zostawia tylko linie w blokach ``` (numeracja linii bez zmian, reszta pusta)."""
    kept: List[str] = []
    inside = False
    for raw in text.splitlines():
        if raw.strip().startswith("```"):
            inside = not inside
            kept.append("")
            continue
        kept.append(raw if inside else "")
    return "\n".join(kept)


def run(root: Path, allow: Allowlist) -> Tuple[List[Finding], int]:
    """Lintuje wszystkie ``CHECKED_FILES`` względem KB. Zwraca (naruszenia, sprawdzenia)."""
    kb = KnowledgeBase.from_texts(load_kb_texts(root))
    findings: List[Finding] = []
    total = 0
    for relative, only_fenced in CHECKED_FILES:
        path = root / relative
        text = path.read_text(encoding="utf-8")
        if only_fenced:
            text = fenced_only(text)
        found, checks = lint_text(relative.as_posix(), text, kb, allow)
        findings.extend(found)
        total += checks
    return findings, total


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sprawdza, czy fakty w prompcie i procedurach są w bazie wiedzy.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="katalog repo (domyślnie: nadrzędny do scripts/)")
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST, help="plik z wyjątkami (JSON)")
    args = parser.parse_args(argv)

    try:
        allow = Allowlist.load(args.allowlist)
        findings, checks = run(args.root.resolve(), allow)
    except (FileNotFoundError, json.JSONDecodeError) as err:
        print(f"BŁĄD: nie mogę odczytać danych wejściowych: {err}")
        return 1

    for finding in findings:
        print(finding.render())
    if findings:
        print(f"\nFAIL: {len(findings)} naruszeń (fakt w prompcie/procedurach bez pokrycia w KB). "
              f"Dodaj fakt do KB albo usuń go z promptu; wyjątek tylko z uzasadnieniem w allowlist.")
        return 1
    print(f"OK: {checks} sprawdzeń, brak faktów bez pokrycia w KB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
