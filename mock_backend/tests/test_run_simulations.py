"""Testy runbooka K2 (`tunnel/run_simulations.py`) — offline, bez sieci i sekretów.

Sprawdzają to, co da się zepsuć po cichu: kształt payloadów wysyłanych do API,
asercje na transkrypt (0% vs 50%), guard kredytów, wybór agenta z env i odczyt transkryptu.
"""

from __future__ import annotations

import json
import re
from datetime import date

import pytest

from tunnel import run_simulations as rs, scenarios as sc

TODAY = date(2026, 11, 13)


class FakeClient:
    def __init__(self, responses: dict[str, tuple[int, object]] | None = None):
        self.responses = responses or {}
        self.calls: list[tuple[str, str, object]] = []

    def request_json(self, method: str, path: str, body=None, timeout: int = 120):
        self.calls.append((method, path, body))
        return self.responses[path]


def _payloads(slugs_prefix: str | None = None):
    seeds = sc.dry_run_seeds(TODAY)
    scenarios = sc.selected(only=[slugs_prefix] if slugs_prefix else None)
    return {p["slug"]: p for p in sc.scenario_payloads(seeds, today=TODAY, scenarios=scenarios)}


def test_all_scenarios_have_prefixed_unique_names():
    payloads = sc.scenario_payloads(sc.dry_run_seeds(TODAY), today=TODAY)
    names = [p["body"]["name"] for p in payloads]
    assert len(names) == len(sc.SCENARIOS) >= 16
    assert all(n.startswith(rs.TEST_PREFIX) for n in names)
    assert len(set(names)) == len(names)
    assert all(p["body"]["type"] == "simulation" for p in payloads)


def test_cancel_scenarios_embed_real_seed_number_and_datetime():
    seeds = sc.dry_run_seeds(TODAY)
    payloads = _payloads()

    free = payloads["02-anulowanie-ponad-2h"]["body"]
    assert seeds["cancel_free"]["id"] in free["simulation_scenario"]
    assert f"{seeds['cancel_free']['date']}T{seeds['cancel_free']['time']}" in " ".join(free["success_conditions"])

    fee = payloads["03-anulowanie-ponizej-2h"]["body"]
    assert seeds["cancel_fee"]["id"] in fee["simulation_scenario"]
    assert f"{seeds['cancel_fee']['date']}T{seeds['cancel_fee']['time']}" in " ".join(fee["success_conditions"])


def test_fee_assertions_are_not_swapped():
    payloads = _payloads()
    over_two = payloads["02-anulowanie-ponad-2h"]["expect"]
    under_two = payloads["03-anulowanie-ponizej-2h"]["expect"]
    assert any(re.search(p, "zwolnienie: 0%") for p in over_two["text"])
    assert not any(re.search(p, "opłata 50%") for p in over_two["text"])
    assert any(re.search(p, "opłata 50%") for p in under_two["text"])
    assert any(re.search(p, "bezpłatnie") for p in under_two["forbid"])


def test_zero_percent_pattern_does_not_match_fifty_percent():
    payloads = _payloads("02")
    pattern = payloads["02-anulowanie-ponad-2h"]["expect"]["text"][0]
    assert re.search(pattern, "opłata 50%") is None
    assert re.search(pattern, "bezpłatnie, 0%") is not None


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


def test_scenario_placeholders_are_all_filled():
    for payload in sc.scenario_payloads(sc.dry_run_seeds(TODAY), today=TODAY):
        texts = [payload["body"]["simulation_scenario"], *payload["body"]["success_conditions"],
                 *payload["expect"]["text"], *payload["expect"]["forbid"]]
        assert not [t for t in texts if sc.leftover_placeholders(t)], payload["slug"]


def test_agent_id_comes_from_env_and_fails_closed(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    assert rs.default_agent() == ""
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_test_123")
    assert rs.default_agent() == "agent_test_123"
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "   ")
    assert rs.default_agent() == ""


def test_dispatch_without_agent_id_exits_2(monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    args = rs.parse_args([])
    assert rs.dispatch(args) == 2
    assert "ELEVENLABS_AGENT_ID" in capsys.readouterr().out


def test_only_filter_selects_by_slug_prefix():
    args = rs.parse_args(["--dry-run", "--only", "02,16"])
    assert rs.only_prefixes(args) == ["02", "16"]
    chosen = sc.selected(only=rs.only_prefixes(args))
    assert [s["slug"][:2] for s in chosen] == ["02", "16"]


def test_skip_scenario3_drops_the_fee_scenario_only():
    chosen = sc.selected(skip_scenario3=True)
    assert all(not s["slug"].startswith("03") for s in chosen)
    assert len(chosen) == len(sc.SCENARIOS) - 1


def test_build_seed_without_reservation_only_reads_slot(monkeypatch):
    client = FakeClient({"/check_spa_availability": (200, {"available": True, "slots": ["09:00"]})})
    seed = rs.build_seed(client, "book", sc.SEED_SPECS["book"])
    assert seed is not None and seed["id"] == "" and seed["time"] == "09:00"
    assert all(path != "/book_spa_appointment" for _, path, _ in client.calls)
