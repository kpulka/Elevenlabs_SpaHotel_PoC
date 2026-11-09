"""Testy runbooka K2 (`tunnel/run_simulations.py`) — offline, bez sieci i sekretów.

Sprawdzają to, co da się zepsuć po cichu: kształt payloadów wysyłanych do API,
asercje na transkrypt (0% vs 50%), guard kredytów i odczyt transkryptu.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from tunnel import run_simulations as rs


class FakeClient:
    def __init__(self, responses: dict[str, tuple[int, object]] | None = None):
        self.responses = responses or {}
        self.calls: list[tuple[str, str, object]] = []

    def call(self, method: str, path: str, body=None, timeout: int = 120):
        self.calls.append((method, path, body))
        return self.responses[path]


SEEDS = {
    "book": {"id": "SPA-0001", "date": "2026-11-10", "time": "11:00", "service": "masaż leczniczy pleców"},
    "cancel_free": {"id": "SPA-0002", "date": "2026-11-11", "time": "10:00", "service": "masaż leczniczy pleców"},
    "cancel_fee": {"id": "SPA-0003", "date": "2026-11-09", "time": "16:00", "service": "kąpiel siarczkowa"},
}


def test_three_scenarios_with_prefixed_names():
    payloads = rs.scenario_payloads(SEEDS)
    names = [p["body"]["name"] for p in payloads]
    assert len(names) == 3
    assert all(n.startswith(rs.TEST_PREFIX) for n in names)
    assert len(set(names)) == 3
    assert all(p["body"]["type"] == "simulation" for p in payloads)


def test_cancel_scenarios_embed_real_seed_number_and_datetime():
    payloads = {p["slug"]: p for p in rs.scenario_payloads(SEEDS)}

    free = payloads["02-anulowanie-ponad-2h"]["body"]
    assert "SPA-0002" in free["simulation_scenario"]
    assert "2026-11-11T10:00" in " ".join(free["success_conditions"])

    fee = payloads["03-anulowanie-ponizej-2h"]["body"]
    assert "SPA-0003" in fee["simulation_scenario"]
    assert "2026-11-09T16:00" in " ".join(fee["success_conditions"])


def test_fee_assertions_are_not_swapped():
    payloads = {p["slug"]: p for p in rs.scenario_payloads(SEEDS)}
    over_two = payloads["02-anulowanie-ponad-2h"]["expect"]
    under_two = payloads["03-anulowanie-ponizej-2h"]["expect"]
    assert "0%" in over_two["text"] and "50%" in over_two["forbid"]
    assert "50%" in under_two["text"] and "bezpłatn" in under_two["forbid"]


def test_whoami_blocks_when_credits_exhausted():
    client = FakeClient({"/v1/user/subscription": (200, {
        "tier": "payg", "character_count": 10000, "character_limit": 10000,
        "next_character_count_reset_unix": 1795316558,
    })})
    with pytest.raises(SystemExit) as exc:
        rs.whoami(client)
    assert exc.value.code == 3
    ok, text = rs.whoami(client, hard=False)
    assert ok is False and "10000/10000" in text


def test_whoami_passes_with_free_credits():
    client = FakeClient({"/v1/user/subscription": (200, {
        "tier": "payg", "character_count": 10, "character_limit": 10000,
    })})
    ok, text = rs.whoami(client)
    assert ok is True and "10/10000" in text


def test_find_slot_returns_first_free_slot():
    client = FakeClient({"/check_spa_availability": (200, {
        "available": True, "slots": ["10:00", "11:00"],
    })})
    assert rs.find_slot(client, "kąpiel siarczkowa", date(2026, 11, 9)) == "10:00"


def test_find_slot_none_when_unavailable():
    client = FakeClient({"/check_spa_availability": (200, {"available": False, "slots": []})})
    assert rs.find_slot(client, "kąpiel siarczkowa", date(2026, 11, 9)) is None


def test_transcript_text_flattens_agent_responses():
    run = {"agent_responses": [{"role": "agent", "message": "Opłata 50%."}, "SPA-0003"]}
    text = rs.transcript_text(run)
    assert "50%" in text and "SPA-0003" in text
    assert json.loads(text.splitlines()[0])["role"] == "agent"
