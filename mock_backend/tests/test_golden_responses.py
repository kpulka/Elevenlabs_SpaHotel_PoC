"""Test weryfikujący zgodność odpowiedzi modułu responses z zatwierdzonym wzorcem golden."""

from __future__ import annotations

import json
from pathlib import Path

import responses
from tests.golden_cases import collect_responses

GOLDEN_PATH = Path(__file__).parent / "golden" / "spa_responses.json"


def test_responses_match_golden():
    assert GOLDEN_PATH.exists(), f"Brak pliku wzorca: {GOLDEN_PATH}"
    golden_data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    current_data = collect_responses(responses)
    assert current_data == golden_data, "Odpowiedzi SPA różnią się od zatwierdzonego wzorca golden!"
