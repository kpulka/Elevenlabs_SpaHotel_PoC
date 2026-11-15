"""Testy renderera wertykali (agent/verticals/render_vertical.py) i spójności wertykali dentystycznej.

Sprawdzają: walidację client.json, renderowanie szkieletów, zgodność promptu i scenariuszy
z konfiguracją (nazwy narzędzi, działy przekazania, numer alarmowy) — ten sam błąd, co
„prompt obiecuje narzędzie, którego nie ma" z audytu agenta.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
VERTICALS = REPO / "agent" / "verticals"
DENTAL = VERTICALS / "dental_clinic"


def _load_renderer():
    spec = importlib.util.spec_from_file_location("render_vertical", VERTICALS / "render_vertical.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


rv = _load_renderer()


@pytest.fixture(scope="module")
def client() -> dict:
    return rv.load_client(DENTAL / "client.json")


@pytest.fixture(scope="module")
def tool_names(client) -> set[str]:
    return {tool["name"] for tool in client["tools"]}


# ── walidacja client.json ────────────────────────────────────────────────────

def test_dental_client_is_valid_and_marked_fictional(client):
    assert rv.validate(client) == []
    assert client["fictional"] is True


def test_missing_required_key_is_reported(client):
    broken = copy.deepcopy(client)
    del broken["emergency"]
    assert any("emergency" in error for error in rv.validate(broken))


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (lambda c: c["tools"].append({**c["tools"][0]}), "duplicate tool names"),
        (lambda c: c["tools"][0].update(name="CheckAvailability"), "not snake_case"),
        (lambda c: c["services"][0].update(price_pln=150), "price fields"),
        (lambda c: c["never_automate"][0].update(fallback="nieistniejacy_dzial"), "is not a department"),
        (lambda c: c["kb_documents"][0].update(usage_mode="rag"), "usage_mode"),
        (lambda c: c.update(default_language="de"), "default_language"),
        (lambda c: c["handoff"].update(tool="transfer_to_number"), "exactly one tool"),
    ],
    ids=[
        "duplicate-tool",
        "bad-name",
        "price-in-config",
        "bad-fallback",
        "bad-usage-mode",
        "bad-language",
        "bad-handoff",
    ],
)
def test_invalid_client_is_rejected(client, mutate, expected):
    broken = copy.deepcopy(client)
    mutate(broken)
    errors = rv.validate(broken)
    assert errors, "expected validation errors"
    assert any(expected in error for error in errors), errors


def test_cli_exits_2_on_invalid_file(tmp_path, capsys):
    bad = tmp_path / "client.json"
    bad.write_text(json.dumps({"client_id": "x"}), encoding="utf-8")
    assert rv.main([str(bad)]) == 2
    assert "missing required keys" in capsys.readouterr().err


# ── renderowanie szkieletów ──────────────────────────────────────────────────

def test_prompt_skeleton_lists_every_tool_and_the_emergency_number(client):
    text = rv.render_prompt_skeleton(client)
    for tool in client["tools"]:
        assert f"`{tool['name']}`" in text
    assert "112" in text
    assert "TODO" in text, "skeleton must leave wording slots for a human"


def test_scenario_skeleton_covers_services_never_automate_and_guardrails(client):
    stubs = rv.render_scenario_skeleton(client)
    slugs = [stub["slug"] for stub in stubs]
    assert len(slugs) == len(set(slugs)), "slugs must be unique"
    assert len(stubs) >= len(client["services"]) + len(client["never_automate"]) + 2
    assert any(slug.startswith("emergency-") for slug in slugs)
    assert "guardrail-prompt-injection" in slugs
    for stub in stubs:
        assert {"slug", "seed", "prompt", "max_turns", "success_criteria", "expect"} <= stub.keys()
        assert set(stub["expect"]) == {"tool", "text", "forbid"}


def test_write_outputs_creates_both_files(client, tmp_path):
    message = rv.write_outputs(client, tmp_path / "out")
    assert "prompt_skeleton.md" in message
    assert (tmp_path / "out" / "prompt_skeleton.md").read_text(encoding="utf-8").startswith("# System prompt skeleton")
    json.loads((tmp_path / "out" / "scenarios_skeleton.json").read_text(encoding="utf-8"))


# ── spójność hand-written artefaktów wertykali dentystycznej ─────────────────

TOOL_LIKE = re.compile(r"\b(?:check|book|cancel|reschedule|send|transfer)_[a-z_]*[a-z]\b")


def test_hand_written_prompt_mentions_only_configured_tools(tool_names):
    prompt = (DENTAL / "system_prompt.md").read_text(encoding="utf-8")
    mentioned = set(TOOL_LIKE.findall(prompt))
    assert mentioned, "prompt should reference its tools"
    assert mentioned <= tool_names, f"prompt names tools that are not configured: {sorted(mentioned - tool_names)}"


def test_hand_written_prompt_uses_only_configured_departments(client):
    prompt = (DENTAL / "system_prompt.md").read_text(encoding="utf-8")
    departments = {dept["id"] for dept in client["handoff"]["departments"]}
    used = set(re.findall(r"department = ([a-z_]+)", prompt))
    assert used, "prompt should name handoff departments"
    assert used <= departments, sorted(used - departments)


def test_hand_written_prompt_puts_112_in_the_emergency_section():
    prompt = (DENTAL / "system_prompt.md").read_text(encoding="utf-8")
    emergency = prompt.split("## Zagrożenie życia", 1)[1].split("## Zdrowie pacjenta", 1)[0]
    assert "112" in emergency
    assert emergency.index("112") < emergency.index("transfer_to_simulated_handoff")


def test_tool_schema_matches_client_tools(client, tool_names):
    schema = json.loads((DENTAL / "tool_schema.example.json").read_text(encoding="utf-8"))
    assert {tool["name"] for tool in schema["tools"]} == tool_names


def test_scenarios_reference_only_configured_tools_and_cover_key_risks(tool_names):
    scenarios = json.loads((DENTAL / "scenarios.json").read_text(encoding="utf-8"))
    assert len(scenarios) >= 10
    slugs = [s["slug"] for s in scenarios]
    assert len(slugs) == len(set(slugs))
    for scenario in scenarios:
        assert {"slug", "seed", "prompt", "max_turns", "success_criteria", "expect"} <= scenario.keys()
        assert isinstance(scenario["success_criteria"], list) and scenario["success_criteria"]
        tool = scenario["expect"]["tool"]
        assert tool == "" or tool in tool_names, f"{scenario['slug']} expects unknown tool {tool!r}"

    def has(keyword: str) -> bool:
        return any(keyword in s["slug"] for s in scenarios)

    assert any("112" in s["expect"]["text"] for s in scenarios), "needs an emergency scenario that names 112"
    assert has("injection")
    assert has("dane-innej")
    assert has("alergia") or has("sms-do-osoby")
    assert has("nagrywanie")
