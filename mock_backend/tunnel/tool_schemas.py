"""Dane narzędzi agenta spa: nazwy, ścieżki webhooków i pola body (bez logiki sieciowej).

Kontrakt agent <-> backend: tabela „Kontrakt pól” w ``mock_backend/README.md`` oraz modele
Pydantic w ``mock_backend/schemas.py``. ``tests/test_tool_schemas.py`` pilnuje, że oba są zgodne.

Moduł jest czysty: nie wykonuje żądań HTTP i nie zna klucza API. Importują go
``sync_agent_tools.py`` (przepinanie webhooków) i ``run_simulations.py`` (sprawdzenie hostów).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Canonical tool name -> path on the mock backend (see mock_backend/main.py).
# This map is the single source of truth for the demo: add a tool here once and
# both tunnel scripts pick it up.
TOOL_PATHS: Dict[str, str] = {
    "check_spa_availability": "/check_spa_availability",
    "book_spa_appointment": "/book_spa_appointment",
    "check_room_availability": "/check_room_availability",
    "send_sms_summary": "/send_sms_summary",
    "transfer_to_simulated_handoff": "/transfer_to_simulated_handoff",
    "cancel_spa_appointment": "/cancel_spa_appointment",
    "reschedule_spa_appointment": "/reschedule_spa_appointment",
}

# Pola request body, które AGENT wysyła (zgodnie z agent/system_prompt_v3.md i procedures_7.md).
# Porównanie z modelami Pydantic w mock_backend/schemas.py robi tests/test_tool_schemas.py,
# z dwoma wyjątkami opisanymi niżej.
TOOL_BODY_FIELDS: Dict[str, Tuple[str, ...]] = {
    "check_spa_availability": ("service_name", "date", "language"),
    "book_spa_appointment": ("service_name", "date", "time", "guest_name", "language"),
    "check_room_availability": ("room_type", "check_in", "check_out", "language"),
    "send_sms_summary": ("phone_number", "summary_text", "confirmation_id", "language"),
    "transfer_to_simulated_handoff": ("department", "reason", "guest_name", "language"),
    "cancel_spa_appointment": (
        "confirmation_id", "reason", "medical_release", "language", "appointment_datetime",
    ),
    "reschedule_spa_appointment": (
        "confirmation_id", "service_name", "new_date", "new_time", "guest_name", "language",
    ),
}


# Pola, które agent wysyła, a które backend (Pydantic) ignoruje: modele ZapytanieSPA,
# RezerwacjaSPA i SprawdzeniePokoj nie definiują ``language``, więc odpowiedzi tych tras
# są po polsku. Gdy backend doda pole, usuń wpis stąd (test to wymusi).
BACKEND_IGNORED_FIELDS: Dict[str, Tuple[str, ...]] = {
    "check_spa_availability": ("language",),
    "book_spa_appointment": ("language",),
    "check_room_availability": ("language",),
}

# Pola przyjmowane przez backend, których agent NIE wysyła. ``idempotency_key`` jest opcjonalny
# w RezerwacjaSPA; prompt go nie używa, bo nie ma w panelu generowanego klucza (decyzja: brak).
BACKEND_OPTIONAL_UNSENT_FIELDS: Dict[str, Tuple[str, ...]] = {
    "book_spa_appointment": ("idempotency_key",),
}


def _string_property(description: str, enum: Optional[List[str]] = None) -> Dict[str, Any]:
    """Build a request-body property in the exact shape the API returns."""
    return {
        "type": "string",
        "description": description,
        "enum": enum,
        "is_system_provided": False,
        "dynamic_variable": "",
        "allowed_values": None,
        "allowed_values_dynamic_variable": "",
        "constant_value": "",
        "is_omitted": False,
    }


# Optional body properties the agent should send but currently does not.
# Strictly additive: --ensure-schema only ever *adds* these keys and never
# touches ``required``, never renames and never removes an existing property.
SCHEMA_ADDITIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "cancel_spa_appointment": {
        "appointment_datetime": _string_property(
            "Scheduled treatment date and time, ISO 8601 with time "
            "(e.g. 2026-11-09T18:30). Needed to apply the cancellation fee "
            "rule: more than 2 hours before the appointment is free.",
        ),
    },
    "send_sms_summary": {
        "language": _string_property(
            "Guest's language code (pl/en) so the SMS/Telegram summary uses the right language.",
            enum=["pl", "en"],
        ),
    },
    "transfer_to_simulated_handoff": {
        "language": _string_property(
            "Guest's language code (pl/en) so the handoff message uses the right language.",
            enum=["pl", "en"],
        ),
    },
}


# ── pure accessors for the API's tool dicts (no I/O) ───────────────────────
def tool_name(tool: dict) -> str:
    return str((tool.get("tool_config") or {}).get("name") or "")


def tool_config_of(tool: dict) -> dict:
    return tool.get("tool_config") or {}


def api_schema_of(tool_config: dict) -> dict:
    schema = tool_config.get("api_schema")
    return schema if isinstance(schema, dict) else {}


def body_schema_of(tool_config: dict) -> Optional[dict]:
    body = api_schema_of(tool_config).get("request_body_schema")
    return body if isinstance(body, dict) else None


def body_fields(tool_config: dict) -> List[str]:
    body = body_schema_of(tool_config) or {}
    return list((body.get("properties") or {}).keys())


def additions_gaps(index: Dict[str, dict]) -> List[str]:
    """``"narzędzie: pole, ..."`` dla opcjonalnych pól z SCHEMA_ADDITIONS, których brakuje w body."""
    gaps: List[str] = []
    for name, additions in SCHEMA_ADDITIONS.items():
        tool = index.get(name)
        if tool is None:
            continue
        fields = set(body_fields(tool_config_of(tool)))
        missing = [prop for prop in additions if prop not in fields]
        if missing:
            gaps.append(f"{name}: {', '.join(missing)}")
    return gaps


def index_by_name(tools: List[dict]) -> Dict[str, dict]:
    """name -> tool (first occurrence wins)."""
    index: Dict[str, dict] = {}
    for tool in tools:
        name = tool_name(tool)
        if name and name not in index:
            index[name] = tool
    return index
