"""Przejścia stanów rezerwacji SPA (book -> cancel / book -> reschedule) przez prawdziwe trasy HTTP.

Diagramy stanów: docs/flows/cancellation.md i docs/flows/reschedule.md.
Testy są deterministyczne: „dziś" magazynu i zegar reguły opłat są przypięte do stałych wartości.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from helpers import BOOK, CANCEL, RESCHEDULE, SPA

import services.spa as spa_service
from data import SPA_STORE
from store import SpaStore

FIXED_TODAY = date(2026, 11, 12)
DAY = "2026-11-15"  # 3 dni po „dziś" — w 14-dniowym oknie
SERVICE = "masaż klasyczny"  # slot 14:00 istnieje w katalogu
GUEST = "Jan Kowalski"


@pytest.fixture(autouse=True)
def _przypiety_kalendarz(monkeypatch):
    monkeypatch.setattr(SpaStore, "dzisiaj", property(lambda self: FIXED_TODAY))


def _zegar(monkeypatch, godzina: datetime) -> None:
    monkeypatch.setattr(spa_service, "teraz_warszawa", lambda: godzina)


def _book(client, godzina: str = "14:00", gosc: str = GUEST) -> dict:
    response = client.post(
        BOOK,
        json={"service_name": SERVICE, "date": DAY, "time": godzina, "guest_name": gosc, "language": "pl"},
    )
    assert response.status_code == 200
    return response.json()


def _free_slots(client, day: str = DAY) -> list[str]:
    return client.post(SPA, json={"service_name": SERVICE, "date": day, "language": "pl"}).json()["slots"]


# ── stan: zarezerwowany -> anulowany (z opłatą lub bez) ──────────────────────

def test_cancel_more_than_2h_before_is_free_and_frees_the_slot(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 10, 0))  # 4 h przed 14:00
    booking = _book(client)
    assert "14:00" not in _free_slots(client)

    response = client.post(
        CANCEL,
        json={
            "confirmation_id": booking["confirmation_id"],
            "reason": "zmiana planów",
            "appointment_datetime": f"{DAY}T14:00",
            "language": "pl",
        },
    )
    body = response.json()
    assert body["success"] is True
    assert body["cancelled"] is True
    assert body["fee"] == 0.0
    assert body["free_of_charge"] is True
    assert "14:00" in _free_slots(client)


def test_cancel_less_than_2h_before_charges_50_percent(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 13, 30))  # 30 min przed
    booking = _book(client)

    body = client.post(
        CANCEL,
        json={
            "confirmation_id": booking["confirmation_id"],
            "reason": "zmiana planów",
            "appointment_datetime": f"{DAY}T14:00",
            "language": "pl",
        },
    ).json()
    assert body["success"] is True
    assert body["fee"] == 0.5
    assert body["free_of_charge"] is False
    assert "14:00" in _free_slots(client), "anulowana rezerwacja zwalnia slot także przy opłacie"


def test_cancel_with_medical_release_is_free_even_inside_2h(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 13, 30))
    booking = _book(client)

    body = client.post(
        CANCEL,
        json={
            "confirmation_id": booking["confirmation_id"],
            "medical_release": True,
            "appointment_datetime": f"{DAY}T14:00",
            "language": "pl",
        },
    ).json()
    assert body["fee"] == 0.0
    assert body["free_of_charge"] is True


def test_cancel_without_appointment_time_is_charged_50_percent(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 10, 0))
    booking = _book(client)

    body = client.post(CANCEL, json={"confirmation_id": booking["confirmation_id"], "language": "pl"}).json()
    assert body["success"] is True
    assert body["fee"] == 0.5  # procedura: bez godziny backend nalicza 50 %


# ── odmowa biznesowa: nieznany numer ─────────────────────────────────────────

def test_cancel_nonexistent_booking_is_business_rejection_not_error(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 10, 0))
    response = client.post(
        CANCEL,
        json={"confirmation_id": "SPA-9999", "appointment_datetime": f"{DAY}T14:00", "language": "pl"},
    )
    assert response.status_code == 200  # odmowa biznesowa, nie błąd transportu
    body = response.json()
    assert body["success"] is False
    assert body["cancelled"] is False
    assert body["found"] is False
    assert body["fee"] == 0.0
    assert body["free_of_charge"] is True


def test_cancel_nonexistent_does_not_touch_an_existing_booking(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 10, 0))
    booking = _book(client)

    client.post(CANCEL, json={"confirmation_id": "SPA-9999", "language": "pl"})
    assert "14:00" not in _free_slots(client), "obca odmowa nie może zwolnić cudzego slotu"
    assert SPA_STORE.rezerwacja(booking["confirmation_id"]) is not None


def test_second_cancel_of_the_same_booking_is_rejected(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 10, 0))
    numer = _book(client)["confirmation_id"]

    first = client.post(CANCEL, json={"confirmation_id": numer, "language": "pl"}).json()
    second = client.post(CANCEL, json={"confirmation_id": numer, "language": "pl"}).json()
    assert first["success"] is True
    assert second["success"] is False
    assert second["found"] is False


# ── stan: zarezerwowany -> przełożony (nowy numer, stary slot wraca) ─────────

def test_reschedule_issues_new_number_and_moves_the_slot(client):
    booking = _book(client, godzina="14:00")
    stary = booking["confirmation_id"]

    body = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": stary,
            "service_name": SERVICE,
            "new_date": DAY,
            "new_time": "11:00",
            "guest_name": GUEST,
            "language": "pl",
        },
    ).json()
    assert body["success"] is True
    assert body["previous_confirmation_id"] == stary
    assert body["confirmation_id"] != stary
    assert body["new_time"] == "11:00"

    free = _free_slots(client)
    assert "14:00" in free, "stary slot wraca do puli"
    assert "11:00" not in free, "nowy slot jest zajęty"


def test_old_number_is_gone_after_reschedule(client):
    booking = _book(client, godzina="14:00")
    stary = booking["confirmation_id"]
    client.post(
        RESCHEDULE,
        json={
            "confirmation_id": stary,
            "service_name": SERVICE,
            "new_date": DAY,
            "new_time": "11:00",
            "guest_name": GUEST,
            "language": "pl",
        },
    )
    body = client.post(CANCEL, json={"confirmation_id": stary, "language": "pl"}).json()
    assert body["found"] is False, "po przełożeniu stary numer nie wskazuje żadnej rezerwacji"


def test_rescheduled_booking_can_be_cancelled_with_its_new_number(client, monkeypatch):
    _zegar(monkeypatch, datetime(2026, 11, 15, 8, 0))
    booking = _book(client, godzina="14:00")
    nowy = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": booking["confirmation_id"],
            "service_name": SERVICE,
            "new_date": DAY,
            "new_time": "11:00",
            "guest_name": GUEST,
            "language": "pl",
        },
    ).json()["confirmation_id"]

    body = client.post(
        CANCEL,
        json={"confirmation_id": nowy, "appointment_datetime": f"{DAY}T11:00", "language": "pl"},
    ).json()
    assert body["success"] is True
    assert body["fee"] == 0.0, "3 h przed nową godziną — bezpłatnie"
    assert "11:00" in _free_slots(client)


def test_reschedule_to_taken_slot_is_rejected_and_keeps_the_old_booking(client):
    _book(client, godzina="10:00", gosc="Anna Nowak")
    moja = _book(client, godzina="11:00")["confirmation_id"]

    body = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": moja,
            "service_name": SERVICE,
            "new_date": DAY,
            "new_time": "10:00",
            "guest_name": GUEST,
            "language": "pl",
        },
    ).json()
    assert body["success"] is False
    assert "zajęty" in body["message"]
    assert SPA_STORE.rezerwacja(moja) is not None, "nieudane przełożenie nie może zgubić rezerwacji"
    assert "11:00" not in _free_slots(client)


def test_reschedule_of_unknown_number_is_rejected_without_creating_a_booking(client):
    free_before = _free_slots(client)
    body = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": "SPA-9999",
            "service_name": SERVICE,
            "new_date": DAY,
            "new_time": "11:00",
            "guest_name": GUEST,
            "language": "pl",
        },
    ).json()
    assert body["success"] is False
    assert body["found"] is False
    assert _free_slots(client) == free_before, "odmowa nie może zajmować żadnego slotu"


def test_reschedule_to_a_time_outside_the_service_schedule_is_rejected(client):
    moja = _book(client, godzina="14:00")["confirmation_id"]
    body = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": moja,
            "service_name": SERVICE,
            "new_date": DAY,
            "new_time": "03:00",
            "guest_name": GUEST,
            "language": "pl",
        },
    ).json()
    assert body["success"] is False
    assert SPA_STORE.rezerwacja(moja) is not None
    assert "14:00" not in _free_slots(client)
