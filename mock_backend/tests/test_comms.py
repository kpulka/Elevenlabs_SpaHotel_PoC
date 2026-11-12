"""Komunikacja: SMS z podsumowaniem i symulowany handoff do działu."""

from __future__ import annotations

from helpers import (
    HANDOFF,
    SMS,
)

# ── SMS, handoff, health, kontrakt ──────────────────────────────────────────

def test_send_sms_summary_en(client):
    odpowiedz = client.post(
        SMS,
        json={
            "phone_number": "+48600100200",
            "summary_text": "Booking confirmed.",
            "confirmation_id": "SPA-1234",
            "language": "en",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is True
    assert body["delivered_to"] == "+48600100200"
    assert body["language"] == "en"
    assert body["message"] == "Message sent."


def test_send_sms_rejects_bad_phone(client):
    odpowiedz = client.post(SMS, json={"phone_number": "12", "summary_text": "x"})
    assert odpowiedz.status_code == 422


def test_transfer_to_simulated_handoff(client):
    body = client.post(
        HANDOFF,
        json={"department": "dyzurka_medyczna", "reason": "ból", "guest_name": "Anna", "language": "pl"},
    ).json()
    assert body["success"] is True
    assert body["simulated"] is True
    assert body["department"] == "Dyżurka medyczna (gabinet 101)"
    assert body["language"] == "pl"
