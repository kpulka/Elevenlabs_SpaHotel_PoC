"""Zapis wyników symulacji K2 (transkrypty JSON + SUMMARY.md) i ocena asercji.

Tylko operacje na plikach i porównanie tekstu, bez żądań HTTP. Wywoływane z ``run_simulations.py``.

Katalog wyjściowy: ``evals/transcripts/`` w repo (albo ``$ANNA_TRANSCRIPTS_DIR``). Transkrypty są
lokalnym materiałem — nie trafiają do publicznego repo, bo zanim trafią na dysk, ``save()`` maskuje dane
osobowe gości:

* numery telefonów (``+48 600 100 200``, dziewięć cyfr w grupach) -> ``+48 *** *** 200``,
* pełne imiona i nazwiska gości (z seedów i scenariuszy) -> ``P*** Z***``, także w argumentach
  narzędzi pod kluczami ``name``, ``guest_name``, ``guest`` (masowane zawsze), i ``phone``,
  ``phone_number`` (maskowane jak telefon).
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:  # uruchomienie jako skrypt: sys.path[0] == katalog tunnel/
    from sequence_check import check_sequence  # type: ignore[import-not-found]  # mypy widzi tylko wariant pakietowy
except ImportError:  # import jako pakiet
    from tunnel.sequence_check import check_sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRANSCRIPTS = PROJECT_ROOT / "evals" / "transcripts"
TRANSCRIPTS_ENV = "ANNA_TRANSCRIPTS_DIR"

NAME_KEYS = frozenset({"name", "guest_name", "guest"})
PHONE_KEYS = frozenset({"phone", "phone_number"})
# Pola, w których siedzą argumenty wywołań narzędzi (także jako tekst JSON).
ARG_CONTAINERS = frozenset({"params", "params_as_json", "arguments", "args", "tool_params"})

_PHONE = re.compile(r"(?<!\d)(?:\+48[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{3}(?!\d)")


def transcripts_dir() -> Path:
    """Katalog transkryptów; ``$ANNA_TRANSCRIPTS_DIR`` nadpisuje domyślny (liczone przy każdym wywołaniu)."""
    override = os.environ.get(TRANSCRIPTS_ENV, "").strip()
    return Path(override).expanduser().resolve() if override else DEFAULT_TRANSCRIPTS


def transcript_text(run: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for item in run.get("agent_responses") or run.get("messages") or []:
        if isinstance(item, dict):
            chunks.append(json.dumps(item, ensure_ascii=False))
        else:
            chunks.append(str(item))
    return "\n".join(chunks)


# ── redakcja ─────────────────────────────────────────────────────────────
def mask_phone(raw: str) -> str:
    """``+48 600 100 200`` -> ``+48 *** *** 200`` (zostają tylko ostatnie 3 cyfry)."""
    digits = re.sub(r"\D", "", raw)
    prefix = "+48 " if raw.lstrip().startswith("+") else ""
    return f"{prefix}*** *** {digits[-3:]}"


def mask_name(full: str) -> str:
    """``Piotr Zieliński`` -> ``P*** Z***``."""
    return " ".join(f"{word[0]}***" for word in full.split() if word)


def _redact_names(text: str, names: Iterable[str]) -> str:
    for name in sorted({n for n in names if n and n.strip()}, key=len, reverse=True):
        text = re.sub(re.escape(name), mask_name(name), text, flags=re.IGNORECASE)
    return text


def redact_text(text: str, names: Iterable[str] = ()) -> str:
    """Maskuje telefony i pełne imiona w dowolnym tekście."""
    return _redact_names(_PHONE.sub(lambda m: mask_phone(m.group(0)), text), names)


def _redact(obj: Any, names: List[str], in_args: bool = False) -> Any:
    """Rekurencyjnie: w argumentach narzędzi maskuje pola name/guest_name/phone, wszędzie maskuje tekst."""
    if isinstance(obj, dict):
        result: Dict[str, Any] = {}
        for key, value in obj.items():
            if key in ARG_CONTAINERS and isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = redact_text(value, names)
                    continue
                result[key] = json.dumps(_redact(parsed, names, True), ensure_ascii=False)
            elif in_args and isinstance(value, str) and key in NAME_KEYS:
                result[key] = mask_name(value)
            elif in_args and isinstance(value, str) and key in PHONE_KEYS:
                result[key] = mask_phone(value)
            else:
                result[key] = _redact(value, names, in_args or key in ARG_CONTAINERS)
        return result
    if isinstance(obj, list):
        return [_redact(item, names, in_args) for item in obj]
    if isinstance(obj, str):
        return redact_text(obj, names)
    return obj


def redact_run(run: Dict[str, Any], names: Iterable[str]) -> Dict[str, Any]:
    """Kopia transkryptu bez danych osobowych gości (oryginał nie jest zmieniany)."""
    return _redact(run, list(names))


# ── zapis i ocena ────────────────────────────────────────────────────────
def _evaluate(run: Dict[str, Any], checks: Dict[str, Any]) -> List[str]:
    """Naruszenia asercji dla jednego transkryptu (pusta lista = OK)."""
    text = transcript_text(run)
    problems: List[str] = []
    for pattern in checks.get("text", []):
        if not re.search(pattern, text, re.IGNORECASE):
            problems.append(f"brak w transkrypcie: /{pattern}/")
    for pattern in checks.get("forbid", []):
        if re.search(pattern, text, re.IGNORECASE):
            problems.append(f"zakazana fraza: /{pattern}/")
    if checks.get("tools") or checks.get("forbid_tools"):
        problems.extend(check_sequence(run, checks.get("tools", []), checks.get("forbid_tools", [])))
    return problems


def save(resp: Dict[str, Any], payloads: List[Dict[str, Any]], seeds: Dict[str, Dict[str, Any]]) -> int:
    out_dir = transcripts_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    expect = {p["body"]["name"]: p["expect"] for p in payloads}
    names: List[str] = [n for p in payloads for n in p.get("names", [])]
    names += [str(s.get("guest", "")) for s in seeds.values()]
    rows = []
    failures = 0
    for run in resp.get("test_runs") or []:
        name = run.get("test_name", "unknown")
        slug = next((p["slug"] for p in payloads if p["body"]["name"] == name), name)
        path = out_dir / f"k2-{slug}.json"
        redacted = redact_run(run, names)
        path.write_text(json.dumps(redacted, ensure_ascii=False, indent=2), encoding="utf-8")

        problems = _evaluate(run, expect.get(name, {}))
        verdict = run.get("status")
        if verdict != "passed" or problems:
            failures += 1
        rows.append({
            "name": name, "status": verdict, "file": _display(path), "problems": problems,
            "conditions": sum(1 for c in (run.get("success_conditions") or [])
                              if (c.get("result") or c.get("passed")) is True),
        })

    seeds_safe = redact_run({"seeds": seeds}, names)["seeds"]
    summary = [f"# K2 — dowód symulacji ({date.today().isoformat()})", "",
               f"Inwokacja: `{resp.get('id')}` · seed: `{json.dumps(seeds_safe, ensure_ascii=False)}`", "",
               "| test | status | warunki OK | naruszenia asercji | plik |",
               "|---|---|---|---|---|"]
    for r in rows:
        summary.append(f"| {r['name']} | {r['status']} | {r['conditions']} | "
                       f"{'; '.join(r['problems']) or '—'} | `{r['file']}` |")
    (out_dir / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"zapisano {len(rows)} transkryptów + SUMMARY.md w {out_dir}")
    return failures


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:  # katalog z ANNA_TRANSCRIPTS_DIR poza repo
        return str(path)
