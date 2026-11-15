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
    assert body["delivered_to"] == "********200"  # PII: masked in responses too (see logs.mask_phone)
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


def test_handoff_telegram_alert_masks_guest_and_phone(client, monkeypatch):
    import telegram

    wyslane: list[str] = []

    async def falszywy_telegram(tekst: str, etykieta: str = "") -> bool:
        wyslane.append(tekst)
        return True

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(telegram, "wyslij_wiadomosc", falszywy_telegram)

    client.post(
        HANDOFF,
        json={
            "department": "recepcja",
            "reason": "Oddzwońcie na 600 100 299",
            "guest_name": "Jan Kowalski",
            "language": "pl",
        },
    )
    assert len(wyslane) == 1
    alert = wyslane[0]
    assert "Jan K." in alert
    assert "Jan Kowalski" not in alert
    assert "600 100 299" not in alert and "600100299" not in alert
    assert "******299" in alert  # nine digits: six stars and the last three
