"""Test weryfikujący zgodność odpowiedzi modułu responses z zatwierdzonym wzorcem golden."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

import responses
from store import SpaStore
from tests.golden_cases import collect_responses

GOLDEN_PATH = Path(__file__).parent / "golden" / "spa_responses.json"


# Wzorzec zawiera okno rezerwacji liczone od „dzisiaj" — bez zamrożenia daty test czerwieniał
# po północy (2026-11-13). Zmiana tej daty = świadome przegenerowanie wzorca.
GOLDEN_TODAY = date(2026, 11, 12)


@pytest.fixture(autouse=True)
def _frozen_today(monkeypatch):
    monkeypatch.setattr(SpaStore, "dzisiaj", property(lambda self: GOLDEN_TODAY))


def test_responses_match_golden():
    assert GOLDEN_PATH.exists(), f"Brak pliku wzorca: {GOLDEN_PATH}"
    golden_data = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    current_data = collect_responses(responses)
    assert current_data == golden_data, "Odpowiedzi SPA różnią się od zatwierdzonego wzorca golden!"
