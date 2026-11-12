"""Wspólne stałe i funkcje pomocnicze testów HTTP.

Osobny moduł (a nie conftest.py), bo conftest nie jest importowany przez testy.
Fixture (klient, czysty stan) są w conftest.py.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

SPA = "/check_spa_availability"
BOOK = "/book_spa_appointment"
CANCEL = "/cancel_spa_appointment"
RESCHEDULE = "/reschedule_spa_appointment"
ROOM = "/check_room_availability"
SMS = "/send_sms_summary"
HANDOFF = "/transfer_to_simulated_handoff"


def dzien(przesuniecie: int) -> str:
    return (date.today() + timedelta(days=przesuniecie)).isoformat()


def godzina_od_teraz(minuty: int) -> str:
    return (datetime.now() + timedelta(minutes=minuty)).isoformat(timespec="minutes")


def rezerwuj(client, dzien_iso: str | None = None, godzina: str = "14:00", usluga: str = "masaż klasyczny"):
    return client.post(
        BOOK,
        json={
            "service_name": usluga,
            "date": dzien_iso or dzien(3),
            "time": godzina,
            "guest_name": "Jan Kowalski",
        },
    )
