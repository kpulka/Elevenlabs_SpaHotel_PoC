"""Zapis wyników symulacji K2 (transkrypty JSON + SUMMARY.md) i ocena asercji.

Tylko operacje na plikach i porównanie tekstu, bez żądań HTTP. Wywoływane z ``run_simulations.py``.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS = PROJECT_ROOT / ".planning" / "transcripts"


def transcript_text(run: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for item in run.get("agent_responses") or run.get("messages") or []:
        if isinstance(item, dict):
            chunks.append(json.dumps(item, ensure_ascii=False))
        else:
            chunks.append(str(item))
    return "\n".join(chunks)


def save(resp: Dict[str, Any], payloads: List[Dict[str, Any]], seeds: Dict[str, Dict[str, Any]]) -> int:
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    expect = {p["body"]["name"]: p["expect"] for p in payloads}
    rows = []
    failures = 0
    for run in resp.get("test_runs") or []:
        name = run.get("test_name", "unknown")
        slug = next((p["slug"] for p in payloads if p["body"]["name"] == name), name)
        path = TRANSCRIPTS / f"k2-{slug}.json"
        path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")

        text = transcript_text(run)
        checks = expect.get(name, {})
        missing = [m for m in checks.get("text", []) if m not in text]
        forbidden = [f for f in checks.get("forbid", []) if f in text]
        verdict = run.get("status")
        if verdict != "passed" or missing or forbidden:
            failures += 1
        rows.append({
            "name": name, "status": verdict, "file": str(path.relative_to(PROJECT_ROOT)),
            "missing": missing, "forbidden_hits": forbidden,
            "conditions": sum(1 for c in (run.get("success_conditions") or [])
                              if (c.get("result") or c.get("passed")) is True),
        })

    summary = [f"# K2 — dowód symulacji ({date.today().isoformat()})", "",
               f"Inwokacja: `{resp.get('id')}` · seed: `{json.dumps(seeds, ensure_ascii=False)}`", "",
               "| test | status | warunki OK | brak w transkrypcie | zakazane frazy | plik |",
               "|---|---|---|---|---|---|"]
    for r in rows:
        summary.append(f"| {r['name']} | {r['status']} | {r['conditions']} | "
                       f"{', '.join(r['missing']) or '—'} | {', '.join(r['forbidden_hits']) or '—'} | "
                       f"`{r['file']}` |")
    (TRANSCRIPTS / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"zapisano {len(rows)} transkryptów + SUMMARY.md w {TRANSCRIPTS}")
    return failures
