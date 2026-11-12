"""Pokoje: ceny, noclegi, nieznane typy, blokady z data/rooms.json."""

from __future__ import annotations

import json
from datetime import date

import pytest
from helpers import (
    ROOM,
    dzien,
)

import main
import store

# Blokada z data/rooms.json (przerwa świąteczno-noworoczna). Pobyt 28→30.12.2026
# obejmuje obie zablokowane noce.
BLOKADA_OD, BLOKADA_DO = "2026-12-28", "2026-12-30"


def test_reversed_room_dates_is_domain_rejection(client):
    odpowiedz = client.post(
        ROOM, json={"room_type": "dwuosobowy", "check_in": dzien(5), "check_out": dzien(4)}
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert body["total_nights"] == 0
    assert "późniejsza" in body["message"]


def test_past_check_in_room_is_domain_rejection(client):
    odpowiedz = client.post(
        ROOM, json={"room_type": "apartament", "check_in": dzien(-2), "check_out": dzien(-1)}
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert "przeszłości" in body["message"]


# ── pokoje: ceny i dostępność ───────────────────────────────────────────────

def test_price_math_for_n_nights(client):
    body = client.post(
        ROOM, json={"room_type": "dwuosobowy", "check_in": dzien(10), "check_out": dzien(14)}
    ).json()
    assert body["available"] is True
    assert body["price_per_night"] == 500
    assert body["total_nights"] == 4
    assert body["total_price"] == 2000
    assert body["check_in"] == dzien(10)


def test_room_prices_come_from_data_file(client):
    """Ceny pochodzą z data/rooms.json i muszą zgadzać się z frontendem."""
    assert main.POKOJE.typy["jednoosobowy"].cena_za_noc == 350
    assert main.POKOJE.typy["dwuosobowy"].cena_za_noc == 500
    assert main.POKOJE.typy["apartament"].cena_za_noc == 750

    body = client.post(
        ROOM, json={"room_type": "Apartament", "check_in": dzien(2), "check_out": dzien(3)}
    ).json()
    assert body["available"] is True
    assert body["price_per_night"] == 750
    assert body["total_price"] == 750


def test_unknown_room_type(client):
    body = client.post(
        ROOM, json={"room_type": "penthouse", "check_in": dzien(2), "check_out": dzien(3)}
    ).json()
    assert body["available"] is False
    assert "nie istnieje" in body["message"]
    assert "apartament" in body["message"]
    # agent musi dostać realne opcje do zaproponowania, nie samą odmowę
    assert body["available_room_types"] == ["jednoosobowy", "dwuosobowy", "apartament"]
    assert len(body["available_room_type_names"]) == 3


@pytest.mark.parametrize("niejasny", ["pokój", "pokoj", "jakiś pokój"])
def test_vague_room_type_returns_available_types(client, niejasny):
    body = client.post(
        ROOM, json={"room_type": niejasny, "check_in": dzien(2), "check_out": dzien(3)}
    ).json()
    assert body["available"] is False
    assert body["available_room_types"] == ["jednoosobowy", "dwuosobowy", "apartament"]
    assert "niejednoznaczny" in body["message"]


def test_blocked_window_is_future_and_rejects_room(client):
    """Ścieżka demo 'wszystko zajęte' musi działać na realnych danych z JSON-a."""
    body = client.post(
        ROOM, json={"room_type": "dwuosobowy", "check_in": BLOKADA_OD, "check_out": BLOKADA_DO}
    ).json()
    assert body["available"] is False
    assert "Brak dostępności" in body["message"]
    assert "28-29.12.2026" in body["message"], "opis blokady musi pochodzić z dat w JSON-ie"
    assert "przerwa świąteczno-noworoczna" in body["message"]
    assert body["total_price"] == 500 * 2, "cena policzona także dla odrzuconego terminu"


def test_blocked_window_dates_are_in_the_future():
    """Blokada w przeszłości = demo nigdy nie zadziała; wtedy przesuń okno w rooms.json."""
    blokady = {data for daty in main.POKOJE.zablokowane.values() for data in daty}
    assert blokady, "rooms.json nie ma żadnej blokady"
    najwczesniejsza = min(date.fromisoformat(wpis) for wpis in blokady)
    assert najwczesniejsza > date.today(), (
        f"blokada {najwczesniejsza} jest w przeszłości — przesuń okno w data/rooms.json"
    )


def test_blocked_description_is_generated_from_json(tmp_path):
    """Opis zakresu dat jest generowany z JSON-a, więc nie może się rozjechać z danymi."""
    dane = {
        "typy_pokoi": {"apartament": {"nazwa": "Apartament", "cena_za_noc": 750}},
        "zajete_terminy": [
            {"opis": "testowa przerwa", "daty": ["2027-01-05", "2027-01-06", "2027-01-08"]}
        ],
    }
    plik = tmp_path / "rooms.json"
    plik.write_text(json.dumps(dane), encoding="utf-8")

    katalog = store.KatalogPokoi(plik)

    assert katalog.opis_blokady() == "05-06.01.2027, 08.01.2027"
    assert katalog.etykieta_blokady() == "testowa przerwa"


def test_blocked_description_has_no_hardcoded_dates():
    assert main.POKOJE.opis_blokady() == "28-29.12.2026"
    assert "30-31.08.2026" not in main.POKOJE.opis_blokady()
