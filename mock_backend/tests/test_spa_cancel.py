"""Anulowanie rezerwacji zabiegu SPA: reguła opłat, zwolnienie slotu, odmowa dla nieznanego numeru."""

from __future__ import annotations

from helpers import (
    CANCEL,
    SPA,
    dzien,
    godzina_od_teraz,
    rezerwuj,
)

from data import SPA_STORE


def test_malformed_appointment_datetime_is_schema_error(client):
    odpowiedz = client.post(
        CANCEL,
        json={"confirmation_id": "SPA-1234", "appointment_datetime": "9 listopada 2026"},
    )
    assert odpowiedz.status_code == 422


def test_cancel_restores_slot(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    assert client.post(CANCEL, json={"confirmation_id": identyfikator}).status_code == 200

    po = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" in po["slots"]

    # slot jest znowu wolny — można go zarezerwować ponownie
    assert rezerwuj(client).json()["success"] is True


# ── reguła opłat przy anulacji ───────────────────────────────────────────────

def test_cancel_more_than_2h_before_is_free_of_charge(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    odpowiedz = client.post(
        CANCEL,
        json={
            "confirmation_id": identyfikator,
            "reason": "zmiana planów",
            "appointment_datetime": godzina_od_teraz(300),  # 5h przed zabiegiem
            "language": "pl",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is True
    assert body["cancelled"] is True
    assert body["fee"] == 0.0
    assert body["free_of_charge"] is True
    assert body["found"] is True
    assert "ponad 2h" in body["fee_rule"]


def test_cancel_less_than_2h_before_charges_50_percent(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    odpowiedz = client.post(
        CANCEL,
        json={"confirmation_id": identyfikator, "appointment_datetime": godzina_od_teraz(90)},
    )
    body = odpowiedz.json()
    assert body["fee"] == 0.5
    assert body["free_of_charge"] is False
    assert "poniżej 2h" in body["fee_rule"]


def test_cancel_with_medical_release_is_always_free(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    odpowiedz = client.post(
        CANCEL,
        json={
            "confirmation_id": identyfikator,
            "medical_release": True,
            "appointment_datetime": godzina_od_teraz(30),
            "language": "pl",
        },
    )
    body = odpowiedz.json()
    assert body["fee"] == 0.0
    assert body["free_of_charge"] is True
    assert body["medical_release"] is True
    assert "medyczne" in body["fee_rule"].lower()


def test_cancel_without_appointment_datetime_reports_unknown_timing(client):
    """Bez appointment_datetime backend nie zna terminu → 50% + jawny fee_rule."""
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    body = client.post(CANCEL, json={"confirmation_id": identyfikator}).json()
    assert body["fee"] == 0.5
    assert body["free_of_charge"] is False
    assert body["found"] is True
    assert "Brak godziny zabiegu" in body["fee_rule"]


def test_cancel_english_language_uses_english_rule(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    body = client.post(
        CANCEL,
        json={
            "confirmation_id": identyfikator,
            "appointment_datetime": godzina_od_teraz(300),
            "language": "en",
        },
    ).json()
    assert body["message"] == "Reservation cancelled."
    assert body["fee_rule"].startswith("Cancelled more than 2h")
    assert body["found"] is True


# ── druga tura hardeningu: nieistniejące rezerwacje, wspólny kalendarz, cennik ──


def test_cancel_unknown_reservation_is_refused(client):
    """Anulowanie numeru, którego nie ma, nie może raportować sukcesu (defekt #1)."""
    body = client.post(CANCEL, json={"confirmation_id": "SPA-0000"}).json()
    assert body["success"] is False
    assert body["cancelled"] is False
    assert body["found"] is False
    assert body["fee"] == 0.0, "za nieistniejącą rezerwację nie naliczamy opłaty"
    assert "SPA-0000" in body["message"]
    assert "sprawdzenie numeru potwierdzenia" in body["message"]


def test_cancel_unknown_reservation_message_in_english(client):
    body = client.post(
        CANCEL, json={"confirmation_id": "SPA-0000", "language": "en"}
    ).json()
    assert body["success"] is False
    assert body["cancelled"] is False
    assert body["found"] is False
    assert "No reservation found" in body["message"]


def test_cancel_unknown_reservation_does_not_touch_existing_booking(client):
    """Odmowa dla obcego numeru nie może zwolnić slotu prawdziwej rezerwacji."""
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    client.post(CANCEL, json={"confirmation_id": "SPA-0000"})

    wolne = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" not in wolne["slots"], "slot prawdziwej rezerwacji musi zostać zajęty"
    assert SPA_STORE.rezerwacja(identyfikator) is not None
