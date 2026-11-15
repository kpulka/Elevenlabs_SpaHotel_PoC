"""Offline ground-truth check of the RAG question set (evals/rag/questions.json).

Proves that every expected snippet exists in its KB file. It does not measure retrieval or
answer quality (see evals/rag/README.md). The live mode is a stub and must stay that way here.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
RAG = REPO / "evals" / "rag"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_rag_questions", RAG / "check_rag_questions.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


checker = _load_checker()


@pytest.fixture(scope="module")
def questions() -> list[dict]:
    return checker.load_questions()


@pytest.fixture(scope="module")
def kb() -> dict[str, str]:
    return checker.load_kb()


def test_question_set_has_at_least_40_questions(questions):
    assert len(questions) >= 40


def test_every_expected_snippet_exists_in_its_kb_file(questions, kb):
    errors, _ = checker.check(questions, kb)
    assert errors == []


def test_every_question_points_to_a_kb_txt_file(questions, kb):
    for item in questions:
        assert item["expected_doc"] in kb, item["id"]
        assert item["expected_doc"].endswith(".txt"), item["id"]


def test_snippets_are_single_line_and_not_blank(questions):
    for item in questions:
        snippet = item["expected_snippet"]
        assert snippet.strip() == snippet and snippet, item["id"]
        assert "\n" not in snippet, item["id"]


def test_questions_are_polish_guest_questions(questions):
    for item in questions:
        assert item["question"].endswith("?"), item["id"]


def test_check_detects_a_snippet_that_is_not_in_the_kb(questions, kb):
    broken = json.loads(json.dumps(questions))
    broken[0]["expected_snippet"] = "ten tekst nie istnieje w bazie wiedzy"
    errors, _ = checker.check(broken, kb)
    assert any("not found" in error and broken[0]["id"] in error for error in errors)


def test_check_detects_a_missing_kb_file(questions, kb):
    broken = json.loads(json.dumps(questions))
    broken[1]["expected_doc"] = "99_nie_istnieje.txt"
    errors, _ = checker.check(broken, kb)
    assert any(broken[1]["id"] in error and "expected_doc" in error for error in errors)


def test_check_detects_duplicate_ids(questions, kb):
    broken = json.loads(json.dumps(questions))
    broken[1]["id"] = broken[0]["id"]
    errors, _ = checker.check(broken, kb)
    assert any("duplicate id" in error for error in errors)


def test_live_mode_is_a_stub_and_says_so(capsys):
    assert checker.main(["--live"]) == 3
    assert capsys.readouterr().out.strip() == "not implemented: requires ElevenLabs agent simulation"


def test_offline_mode_exits_zero_on_the_committed_set():
    assert checker.main([]) == 0
