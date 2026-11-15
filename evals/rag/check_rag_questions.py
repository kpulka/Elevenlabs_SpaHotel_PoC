"""Offline ground-truth check for the RAG question set (stdlib only).

    python evals/rag/check_rag_questions.py          # verify the question set against the KB files
    python evals/rag/check_rag_questions.py --live   # STUB: prints "not implemented" and exits 3

What the default mode proves: every question points to a KB file that exists, and the
expected snippet is an exact substring of that file. It does NOT prove that the agent answers
correctly or that retrieval finds the right chunk. See README.md.

Exit codes: 0 all checks pass, 1 check failures, 3 live mode requested (not implemented).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
KB_DIR = REPO / "agent" / "knowledge_base_txt"
QUESTIONS = HERE / "questions.json"
MIN_QUESTIONS = 40
LIVE_NOT_IMPLEMENTED = "not implemented: requires ElevenLabs agent simulation"


def load_questions(path: Path = QUESTIONS) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["questions"]


def load_kb(kb_dir: Path = KB_DIR) -> dict[str, str]:
    # utf-8-sig: some KB files start with a byte-order mark that must not leak into snippets.
    return {path.name: path.read_text(encoding="utf-8-sig") for path in sorted(kb_dir.glob("*.txt"))}


def check(questions: list[dict], kb: dict[str, str]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors make the run fail; warnings are informational."""
    errors: list[str] = []
    warnings: list[str] = []
    if len(questions) < MIN_QUESTIONS:
        errors.append(f"expected at least {MIN_QUESTIONS} questions, found {len(questions)}")

    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    for item in questions:
        qid = item.get("id", "<no id>")
        if qid in seen_ids:
            errors.append(f"{qid}: duplicate id")
        seen_ids.add(qid)

        text = (item.get("question") or "").strip()
        if not text:
            errors.append(f"{qid}: empty question")
        elif text in seen_questions:
            errors.append(f"{qid}: duplicate question text")
        seen_questions.add(text)

        doc = item.get("expected_doc")
        if doc not in kb:
            errors.append(f"{qid}: expected_doc {doc!r} is not a file in agent/knowledge_base_txt/")
            continue

        snippet = item.get("expected_snippet") or ""
        if not snippet.strip():
            errors.append(f"{qid}: empty expected_snippet")
        elif "\n" in snippet:
            errors.append(f"{qid}: expected_snippet must be a single line")
        elif snippet not in kb[doc]:
            errors.append(f"{qid}: expected_snippet not found in {doc}: {snippet!r}")
        elif kb[doc].count(snippet) > 1:
            warnings.append(f"{qid}: expected_snippet occurs {kb[doc].count(snippet)} times in {doc} (ambiguous)")
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Offline ground-truth check for the RAG question set.")
    parser.add_argument("--live", action="store_true", help="run against the live agent (not implemented)")
    args = parser.parse_args(argv)

    if args.live:
        print(LIVE_NOT_IMPLEMENTED)
        return 3

    questions = load_questions()
    errors, warnings = check(questions, load_kb())
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")
    kb_count = len(load_kb())
    print(
        f"checked {len(questions)} questions against {kb_count} KB files: "
        f"{len(errors)} errors, {len(warnings)} warnings"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
