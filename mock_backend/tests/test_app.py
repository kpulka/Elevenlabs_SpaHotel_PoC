"""Aplikacja jako całość: health-check, CORS i kontrakt pól odpowiedzi dla agenta."""

from __future__ import annotations

import pytest
from helpers import (
    BOOK,
    CANCEL,
    HANDOFF,
    RESCHEDULE,
    ROOM,
    SMS,
    SPA,
    dzien,
)

import main


def test_health_endpoint(client):
    odpowiedz = client.get("/health")
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["status"] == "ok"
    assert body["version"] == main.APP_VERSION
    assert body["uptime_seconds"] >= 0


def test_cors_wildcard_disables_credentials():
    """CORS "*" + allow_credentials=True jest niezgodne ze spec — ustawiamy False."""
    opcje = {m.cls: m.kwargs for m in main.app.user_middleware}
    cors = opcje[__import__("fastapi.middleware.cors", fromlist=["CORSMiddleware"]).CORSMiddleware]
    assert cors["allow_origins"] == ["*"]
    assert cors["allow_credentials"] is False


@pytest.mark.parametrize(
    "sciezka,payload,wymagane_pola",
    [
        (SPA, {"service_name": "jonoforeza", "date": dzien(3)}, {"available", "slots", "service_name", "date", "message", "available_services", "price_pln", "duration_min"}),
        (BOOK, {"service_name": "jonoforeza", "date": dzien(3), "time": "10:00", "guest_name": "Anna"}, {"success", "confirmation_id", "service_name", "date", "time", "guest_name", "message"}),
        (CANCEL, {"confirmation_id": "SPA-1111"}, {"success", "confirmation_id", "cancelled", "fee", "medical_release", "message", "note", "free_of_charge", "fee_rule"}),
        (RESCHEDULE, {"confirmation_id": "SPA-2222", "service_name": "jonoforeza", "new_date": dzien(4), "new_time": "11:00", "guest_name": "Anna"}, {"success", "confirmation_id", "service_name", "new_date", "new_time", "guest_name", "message", "note", "found"}),
        (ROOM, {"room_type": "dwuosobowy", "check_in": dzien(8), "check_out": dzien(10)}, {"available", "room_type", "price_per_night", "check_in", "check_out", "total_nights", "total_price", "message"}),
        (SMS, {"phone_number": "+48600100200", "summary_text": "ok", "confirmation_id": "SPA-1111", "language": "pl"}, {"success", "message", "delivered_to", "language"}),
        (HANDOFF, {"department": "recepcja", "reason": "pomoc", "guest_name": "Anna", "language": "pl"}, {"success", "simulated", "message", "department", "reason", "guest_name", "language", "note"}),
    ],
)
def test_contract_fields_are_preserved(client, sciezka, payload, wymagane_pola):
    """Kontrakt z agentem ElevenLabs: te pola muszą istnieć w każdej odpowiedzi 200."""
    odpowiedz = client.post(sciezka, json=payload)
    assert odpowiedz.status_code == 200
    brakujace = wymagane_pola - set(odpowiedz.json())
    assert not brakujace, f"{sciezka} nie zwraca pól: {brakujace}"
