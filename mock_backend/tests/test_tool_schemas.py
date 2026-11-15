"""Kontrakt backend <-> agent w jednym miejscu (offline, bez API ElevenLabs).

Pola body, które agent wysyła (``tunnel/tool_schemas.py``), muszą pokrywać się z polami modeli
Pydantic z ``schemas.py`` (to je przyjmuje backend) z dwoma jawnie opisanymi wyjątkami:
``BACKEND_IGNORED_FIELDS`` (agent wysyła, backend ignoruje) i ``BACKEND_OPTIONAL_UNSENT_FIELDS``
(backend przyjmuje, agent nie wysyła). Ścieżki webhooków muszą być trasami POST aplikacji FastAPI.
Zmiana nazwy pola po jednej stronie bez drugiej czerwieni ten test.
"""

from __future__ import annotations

import pytest

import schemas
from main import app
from tunnel import tool_schemas as ts

MODEL_FOR_TOOL = {
    "check_spa_availability": schemas.ZapytanieSPA,
    "book_spa_appointment": schemas.RezerwacjaSPA,
    "check_room_availability": schemas.SprawdzeniePokoj,
    "send_sms_summary": schemas.WysylkaSMS,
    "transfer_to_simulated_handoff": schemas.Handoff,
    "cancel_spa_appointment": schemas.AnulowanieSPA,
    "reschedule_spa_appointment": schemas.PrzelozenieSPA,
}


def test_seven_tools_have_path_fields_and_model():
    assert len(ts.TOOL_PATHS) == 7
    assert set(ts.TOOL_BODY_FIELDS) == set(ts.TOOL_PATHS) == set(MODEL_FOR_TOOL)


@pytest.mark.parametrize("tool", sorted(MODEL_FOR_TOOL))
def test_body_fields_equal_pydantic_model_fields(tool):
    sent_and_used = set(ts.TOOL_BODY_FIELDS[tool]) - set(ts.BACKEND_IGNORED_FIELDS.get(tool, ()))
    accepted_unsent = set(ts.BACKEND_OPTIONAL_UNSENT_FIELDS.get(tool, ()))
    assert sent_and_used | accepted_unsent == set(MODEL_FOR_TOOL[tool].model_fields)


@pytest.mark.parametrize("tool", sorted(ts.BACKEND_IGNORED_FIELDS))
def test_ignored_fields_are_really_absent_from_backend_model(tool):
    # Gdy backend zacznie przyjmować pole, ten test wymusi usunięcie wpisu z BACKEND_IGNORED_FIELDS.
    fields = set(MODEL_FOR_TOOL[tool].model_fields)
    assert not (set(ts.BACKEND_IGNORED_FIELDS[tool]) & fields), tool


def test_idempotency_key_is_optional_and_not_sent_by_agent():
    assert "idempotency_key" not in ts.TOOL_BODY_FIELDS["book_spa_appointment"]
    assert ts.BACKEND_OPTIONAL_UNSENT_FIELDS["book_spa_appointment"] == ("idempotency_key",)
    assert schemas.RezerwacjaSPA.model_fields["idempotency_key"].is_required() is False


@pytest.mark.parametrize("tool", sorted(MODEL_FOR_TOOL))
def test_body_fields_are_unique(tool):
    fields = ts.TOOL_BODY_FIELDS[tool]
    assert len(fields) == len(set(fields))


def test_optional_additions_are_contract_fields():
    for tool, additions in ts.SCHEMA_ADDITIONS.items():
        assert set(additions) <= set(ts.TOOL_BODY_FIELDS[tool]), tool


def test_tool_paths_are_post_routes_of_the_backend():
    post_paths = {route.path for route in app.routes if "POST" in getattr(route, "methods", set())}
    for tool, path in ts.TOOL_PATHS.items():
        assert path == f"/{tool}"
        assert path in post_paths, tool
