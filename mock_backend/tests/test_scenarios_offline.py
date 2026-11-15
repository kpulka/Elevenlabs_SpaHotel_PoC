"""Walidacja scenariuszy symulacji K2 i sprawdzacza sekwencji narzędzi — offline.

Nic tu nie dzwoni do ElevenLabs ani do backendu i nie czyta sekretów. Pilnuje struktury
scenariuszy, zakresu dat, pokrycia 7 procedur oraz działania ``tunnel/sequence_check.py``
na syntetycznych transkryptach (także na takim, który ma nie przejść).
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pytest

from tunnel import scenarios as sc, sequence_check as seq
from tunnel.tool_schemas import TOOL_PATHS

TODAY = date(2026, 11, 13)
PROCEDURE_IDS = Path(__file__).resolve().parents[2] / "agent" / "procedures" / "procedure_ids.json"
REQUIRED_KEYS = {"slug", "procedure", "tags", "seed", "prompt", "max_turns", "success_criteria", "expect"}
EXPECT_KEYS = {"tools", "forbid_tools", "text", "forbid"}
LABELS = {"rezerwacja_zabiegu", "dostepnosc_pokoi", "bezpieczenstwo", "zagrozenie_zycia"}


def _procedure_names() -> set[str]:
    return {item["name"] for item in json.loads(PROCEDURE_IDS.read_text(encoding="utf-8"))}


def _payloads(today: date = TODAY):
    return sc.scenario_payloads(sc.dry_run_seeds(today), today=today)


# ── struktura ────────────────────────────────────────────────────────────
def test_every_scenario_has_required_keys():
    for scenario in sc.SCENARIOS:
        missing = REQUIRED_KEYS - scenario.keys()
        assert not missing, (scenario.get("slug"), missing)
        assert set(scenario["expect"]) >= EXPECT_KEYS, scenario["slug"]
        assert isinstance(scenario["tags"], list)
        assert scenario["success_criteria"], scenario["slug"]
        assert 1 <= scenario["max_turns"] <= 30, scenario["slug"]


def test_slugs_and_names_are_unique_and_well_formed():
    slugs = [s["slug"] for s in sc.SCENARIOS]
    assert len(slugs) == len(set(slugs))
    assert all(re.fullmatch(r"\d{2}-[a-z0-9-]+", slug) for slug in slugs)
    names = [p["body"]["name"] for p in _payloads()]
    assert len(names) == len(set(names))


def test_seeds_reference_known_specs():
    for scenario in sc.SCENARIOS:
        seed = scenario["seed"]
        assert seed is None or seed in sc.SEED_SPECS, scenario["slug"]


def test_every_pattern_compiles():
    for scenario in sc.SCENARIOS:
        for key in ("text", "forbid"):
            for pattern in scenario["expect"][key]:
                try:
                    re.compile(sc.fill(pattern, {"id": "SPA-0000", "datetime": "x", "date_pl": "x",
                                                 "time": "x", "service": "x", "date": "x"}))
                except re.error as err:  # pragma: no cover - the failure message is the point
                    pytest.fail(f"{scenario['slug']}: wzorzec /{pattern}/ nie kompiluje się: {err}")


def test_tool_names_in_expectations_exist_on_backend_contract():
    for scenario in sc.SCENARIOS:
        names = scenario["expect"]["tools"] + scenario["expect"]["forbid_tools"]
        unknown = [n for n in names if n not in TOOL_PATHS]
        assert not unknown, (scenario["slug"], unknown)


def test_payloads_have_no_leftover_placeholders():
    for payload in _payloads():
        texts = [payload["body"]["simulation_scenario"], *payload["body"]["success_conditions"],
                 *payload["expect"]["text"], *payload["expect"]["forbid"]]
        leftovers = [t for t in texts if sc.leftover_placeholders(t)]
        assert not leftovers, (payload["slug"], leftovers)


def test_payload_body_matches_api_contract():
    for payload in _payloads():
        body = payload["body"]
        assert body["name"].startswith(sc.TEST_PREFIX)
        assert body["type"] == "simulation"
        assert body["simulation_scenario"] and body["success_conditions"]
        assert body["tool_mock_config"] == {"mocking_strategy": "none"}


# ── daty ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("today", [TODAY, date(2026, 12, 31)])
def test_scenario_dates_are_in_the_future_unless_marked_past(today):
    for payload in _payloads(today):
        day = date.fromisoformat(payload["day"])
        if "past-date" in payload["tags"]:
            assert day < today, payload["slug"]
        else:
            assert day >= today, payload["slug"]


def test_exactly_one_scenario_uses_a_past_date():
    past = [s["slug"] for s in sc.SCENARIOS if "past-date" in s["tags"]]
    assert len(past) == 1


def test_dry_run_seed_dates_are_not_in_the_past():
    for name, seed in sc.dry_run_seeds(TODAY).items():
        assert date.fromisoformat(seed["date"]) >= TODAY, name


def test_seeded_scenarios_use_the_seed_date_and_reserved_id():
    seeds = sc.dry_run_seeds(TODAY)
    for payload in _payloads():
        scenario = next(s for s in sc.SCENARIOS if s["slug"] == payload["slug"])
        if not scenario["seed"]:
            continue
        seed = seeds[scenario["seed"]]
        assert payload["day"] == seed["date"], payload["slug"]
        if sc.SEED_SPECS[scenario["seed"]]["reserve"]:
            assert seed["id"] in payload["body"]["simulation_scenario"], payload["slug"]
        else:
            assert seed["id"] == ""


def test_seed_specs_are_not_shared_between_cancellation_scenarios():
    seeds_used = [s["seed"] for s in sc.SCENARIOS if s["seed"] and s["seed"].startswith("cancel")]
    assert len(seeds_used) == len(set(seeds_used))


# ── pokrycie procedur ────────────────────────────────────────────────────
def test_every_one_of_the_seven_procedures_is_covered():
    covered = {s["procedure"] for s in sc.SCENARIOS}
    missing = _procedure_names() - covered
    assert not missing, f"bez scenariusza: {sorted(missing)}"


def test_procedure_field_is_a_known_procedure_or_label():
    known = _procedure_names() | LABELS
    for scenario in sc.SCENARIOS:
        assert scenario["procedure"] in known, scenario["slug"]


def test_procedure_is_carried_into_payloads():
    by_slug = {p["slug"]: p["procedure"] for p in _payloads()}
    assert by_slug["02-anulowanie-ponad-2h"] == "procedura_anulowania_rezerwacji_spa"
    assert by_slug["15-injection-prompt"] == "bezpieczenstwo"


def test_adversarial_scenarios_exist_and_forbid_state_changes():
    adversarial = [s for s in sc.SCENARIOS if "adversarial" in s["tags"]]
    assert len(adversarial) >= 2
    injection = next(s for s in adversarial if "prompt-injection" in s["tags"])
    assert "procedura_" in injection["expect"]["forbid"][0]
    assert "cancel_spa_appointment" in next(s for s in adversarial if "identity" in s["tags"])["expect"]["forbid_tools"]


# ── sprawdzacz sekwencji ─────────────────────────────────────────────────
def _good_booking_transcript():
    return [
        {"role": "user", "message": "Chcę masaż."},
        {"role": "agent", "message": "Który masaż ma Pan na myśli?"},
        {"role": "user", "message": "Leczniczy pleców."},
        {"role": "agent", "message": "Masaż leczniczy pleców kosztuje 120 zł, trwa 30 minut.",
         "tool_calls": [{"tool_name": "check_spa_availability",
                         "params_as_json": "{\"service_name\": \"masaż leczniczy pleców\"}"}]},
        {"role": "agent", "message": "Zarezerwowane, numer SPA-0001.",
         "tool_calls": [{"tool_name": "book_spa_appointment", "params": {"guest_name": "Piotr"}}]},
    ]


def test_sequence_passes_on_good_transcript():
    assert seq.check_sequence(_good_booking_transcript(),
                              expected_order=["check_spa_availability", "book_spa_appointment"],
                              forbidden_tools=["cancel_spa_appointment"],
                              forbidden_claims=[r"anulowa[łl]\w*"]) == []


def test_sequence_fails_when_order_is_wrong():
    transcript = _good_booking_transcript()
    violations = seq.check_sequence(transcript, expected_order=["book_spa_appointment", "check_spa_availability"])
    assert len(violations) == 1 and "kolejności" in violations[0]


def test_sequence_fails_when_expected_tool_is_missing():
    violations = seq.check_sequence(_good_booking_transcript(),
                                    expected_order=["reschedule_spa_appointment"])
    assert violations and "reschedule_spa_appointment" in violations[0]


def test_failing_transcript_reports_forbidden_tool_and_claim():
    transcript = [
        {"role": "user", "message": "Odwołaj mój zabieg SPA-0002."},
        {"role": "agent", "message": "Anulowałam rezerwację, opłaty nie ma.",
         "tool_calls": [{"tool_name": "cancel_spa_appointment",
                         "params_as_json": "{\"confirmation_id\": \"SPA-0002\", \"medical_release\": false}"}]},
    ]
    violations = seq.check_sequence(transcript,
                                    forbidden_tools=["cancel_spa_appointment"],
                                    forbidden_claims=[r"anulowa[łl]\w*"])
    assert any("zakazane wywołanie narzędzia 'cancel_spa_appointment'" in v for v in violations)
    assert any("zakazane twierdzenie" in v for v in violations)


def test_user_messages_are_not_scanned_for_claims():
    transcript = [{"role": "user", "message": "Anulowałam już wszystko."},
                  {"role": "agent", "message": "Rozumiem."}]
    assert seq.check_sequence(transcript, forbidden_claims=[r"anulowa[łl]\w*"]) == []


def test_wrapped_transcript_and_bad_json_arguments_are_tolerated():
    wrapped = {"transcript": [{"role": "agent", "message": "ok",
                               "tool_calls": [{"tool_name": "send_sms_summary", "params_as_json": "{broken"}]}]}
    calls = seq.extract_tool_calls(wrapped)
    assert [c.name for c in calls] == ["send_sms_summary"]
    assert calls[0].args == {"_raw": "{broken"}


# ── język i nowe scenariusze (2.1, 2.2, 2.5) ─────────────────────────────
def _by_slug(slug: str) -> dict:
    return next(s for s in sc.SCENARIOS if s["slug"] == slug)


def test_user_language_comes_from_each_scenario_not_a_constant():
    by_slug = {p["slug"]: p for p in _payloads()}
    for scenario in sc.SCENARIOS:
        expected = scenario.get("language", "pl")
        payload = by_slug[scenario["slug"]]
        assert payload["language"] == expected, scenario["slug"]
        assert payload["body"]["dynamic_variables"] == {"user_language": expected}, scenario["slug"]


def test_at_least_three_english_scenarios_cover_booking_cancel_and_injection():
    english = [s for s in sc.SCENARIOS if s.get("language") == "en"]
    assert len(english) >= 3
    tags = set().union(*(set(s["tags"]) for s in english))
    assert {"booking", "fee", "prompt-injection"} <= tags


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError):
        sc.scenario_language({"slug": "x", "language": "de"})


def test_emergency_scenario_demands_112_and_forbids_connection_promises():
    scenario = _by_slug("17-zagrozenie-zycia-klatka-piersiowa")
    assert scenario["procedure"] == "zagrozenie_zycia"
    assert "112" in scenario["expect"]["text"][0]
    assert "book_spa_appointment" in scenario["expect"]["forbid_tools"]
    forbid = scenario["expect"]["forbid"]
    assert any(re.search(p, "Łączę Pana z dyżurką", re.IGNORECASE) for p in forbid)
    assert not any(re.search(p, "Nie mogę w tej chwili połączyć Pana bezpośrednio.", re.IGNORECASE)
                   for p in forbid)


def test_balneology_screening_scenario_blocks_booking_on_contraindication():
    scenario = _by_slug("18-przesiew-balneo-rozrusznik")
    assert "book_spa_appointment" in scenario["expect"]["forbid_tools"]
    assert "transfer_to_simulated_handoff" in scenario["expect"]["tools"]


def test_english_cancel_scenario_uses_fee_seed_for_english_guest():
    payload = next(p for p in _payloads() if p["slug"] == "20-en-cancel-fee-under-2h")
    assert payload["body"]["dynamic_variables"]["user_language"] == "en"
    assert "Lena Schmidt" in payload["names"]
    assert "50" in payload["expect"]["text"][0]


def test_synthetic_transcript_passes_scenario_expectations_for_cancel_fee():
    expect = next(p["expect"] for p in _payloads() if p["slug"] == "03-anulowanie-ponizej-2h")
    transcript = [
        {"role": "agent", "message": "Zabieg jest dzisiaj. Opłata wynosi 50% zgodnie z regulaminem.",
         "tool_calls": [{"tool_name": "cancel_spa_appointment",
                         "params_as_json": json.dumps({"confirmation_id": "SPA-0003",
                                                       "medical_release": False})}]},
        {"role": "agent", "message": "Anulowanie zapisane, numer SPA-0003."},
    ]
    assert seq.check_sequence(transcript, expected_order=expect["tools"], forbidden_tools=expect["forbid_tools"]) == []
    for pattern in expect["text"]:
        assert re.search(pattern, json.dumps(transcript, ensure_ascii=False), re.IGNORECASE), pattern
    for pattern in expect["forbid"]:
        assert not re.search(pattern, json.dumps(transcript, ensure_ascii=False), re.IGNORECASE), pattern
