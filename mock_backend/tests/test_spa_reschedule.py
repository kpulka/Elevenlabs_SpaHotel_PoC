"""Zmiana terminu zabiegu SPA (reschedule): przeniesienie slotu i odmowy."""

from __future__ import annotations

from helpers import (
    RESCHEDULE,
    SPA,
    dzien,
    rezerwuj,
)

from data import SPA_STORE


def test_reschedule_moves_slot(client):
    identyfikator = rezerwuj(client, dzien_iso=dzien(3), godzina="14:00").json()["confirmation_id"]

    odpowiedz = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": identyfikator,
            "service_name": "masaż klasyczny",
            "new_date": dzien(4),
            "new_time": "11:00",
            "guest_name": "Jan Kowalski",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is True
    assert body["confirmation_id"] != identyfikator
    assert body["new_date"] == dzien(4)

    stare = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    nowe = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(4)}).json()
    assert "14:00" in stare["slots"], "stary slot powinien wrócić do puli"
    assert "11:00" not in nowe["slots"], "nowy slot powinien być zajęty"


def test_reschedule_to_taken_slot_fails(client):
    rezerwuj(client, dzien_iso=dzien(3), godzina="10:00")
    druga = rezerwuj(client, dzien_iso=dzien(3), godzina="11:00").json()["confirmation_id"]

    odpowiedz = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": druga,
            "service_name": "masaż klasyczny",
            "new_date": dzien(3),
            "new_time": "10:00",
            "guest_name": "Jan Kowalski",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is False
    assert "zajęty" in body["message"]
    # stara rezerwacja nadal zajmuje swój slot
    wolne = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "11:00" not in wolne["slots"]


def test_reschedule_unknown_reservation_is_refused_without_creating_booking(client):
    """Przełożenie numeru, którego nie ma, nie może utworzyć nowej rezerwacji (defekt #2)."""
    body = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": "SPA-0000",
            "service_name": "masaż klasyczny",
            "new_date": dzien(4),
            "new_time": "11:00",
            "guest_name": "Anna Nowak",
        },
    ).json()

    assert body["success"] is False
    assert body["found"] is False
    assert body["confirmation_id"] == "SPA-0000", "nie generujemy nowego numeru"
    assert "Nie znaleziono rezerwacji" in body["message"]
    assert SPA_STORE.rezerwacja(body["confirmation_id"]) is None

    wolne = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(4)}).json()
    assert "11:00" in wolne["slots"], "żaden slot nie może zostać zajęty przez odmowę"
