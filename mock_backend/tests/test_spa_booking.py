"""Dostępność i rezerwacja zabiegów SPA oraz rozpoznawanie katalogu (aliasy, ceny, gimnastyka)."""

from __future__ import annotations

import pytest
from helpers import (
    BOOK,
    SPA,
    dzien,
    rezerwuj,
)

import main

# ── walidacja formatu (HTTP 422) ─────────────────────────────────────────────

@pytest.mark.parametrize("zla_data", ["31/08/2026", "2026-13-01", "jutro", ""])
def test_malformed_date_is_schema_error(client, zla_data):
    odpowiedz = client.post(SPA, json={"service_name": "jonoforeza", "date": zla_data})
    assert odpowiedz.status_code == 422
    assert odpowiedz.json()["detail"][0]["loc"] == ["body", "date"]


def test_malformed_booking_payload_is_schema_error(client):
    """Defekt #1: data z przeszłości, godzina 99:99 i puste imię muszą dać 422."""
    odpowiedz = client.post(
        BOOK,
        json={
            "service_name": "masaż klasyczny",
            "date": "1999-01-01",
            "time": "99:99",
            "guest_name": "",
        },
    )
    assert odpowiedz.status_code == 422
    pola = {blad["loc"][-1] for blad in odpowiedz.json()["detail"]}
    assert pola == {"time", "guest_name"}


# ── daty z przeszłości (200 + available/success false) ───────────────────────

def test_past_date_spa_check_is_domain_rejection(client):
    odpowiedz = client.post(SPA, json={"service_name": "jonoforeza", "date": dzien(-1)})
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert "przeszłości" in body["message"]


def test_past_date_booking_is_domain_rejection(client):
    odpowiedz = rezerwuj(client, dzien_iso=dzien(-1))
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is False
    assert body["confirmation_id"] is None
    assert "przeszłości" in body["message"]


def test_date_outside_rolling_window_is_domain_rejection(client):
    odpowiedz = client.post(SPA, json={"service_name": "jonoforeza", "date": dzien(30)})
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert "oknem rezerwacji" in body["message"]


# ── stan slotów ─────────────────────────────────────────────────────────────

def test_booking_consumes_slot(client):
    przed = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" in przed["slots"]

    odpowiedz = rezerwuj(client)
    assert odpowiedz.status_code == 200
    assert odpowiedz.json()["success"] is True
    assert odpowiedz.json()["confirmation_id"].startswith("SPA-")

    po = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" not in po["slots"]
    assert len(po["slots"]) == len(przed["slots"]) - 1


def test_double_booking_same_slot_fails_with_remaining_slots(client):
    assert rezerwuj(client).json()["success"] is True
    druga = rezerwuj(client)
    body = druga.json()
    assert druga.status_code == 200
    assert body["success"] is False
    assert "już zajęty" in body["message"]
    assert "14:00" not in body["slots"]
    assert len(body["slots"]) == 5


def test_booking_outside_service_schedule_fails(client):
    odpowiedz = rezerwuj(client, godzina="03:00")
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is False
    assert "grafiku" in body["message"]


# ── katalog i dopasowanie usług ─────────────────────────────────────────────

def test_ambiguous_service_name_returns_candidates(client):
    body = client.post(SPA, json={"service_name": "masaż", "date": dzien(3)}).json()
    assert body["available"] is False
    assert len(body["ambiguous"]) == 2
    assert "masaż klasyczny" in body["ambiguous"]
    assert "masaż leczniczy pleców" in body["ambiguous"]
    # 6 zabiegów: 5 z bazy wiedzy + gimnastyka lecznicza ze strony
    assert len(body["available_services"]) == 6
    assert "Dopytaj" in body["message"]


def test_ambiguous_booking_is_rejected_without_consuming_slot(client):
    body = rezerwuj(client, usluga="masaż").json()
    assert body["success"] is False
    assert "ambiguous" in body
    assert client.post(SPA, json={"service_name": "masaż", "date": dzien(3)}).json()[
        "available"
    ] is False
    # slot 14:00 nadal wolny
    assert "14:00" in client.post(
        SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}
    ).json()["slots"]


@pytest.mark.parametrize(
    "zapytanie,oczekiwana",
    [
        ("jonoforeza", "jonoforeza"),
        ("MASAŻ KLASYCZNY", "masaż klasyczny"),
        ("masaz klasyczny", "masaż klasyczny"),
        ("kąpiel borowinowa", "kąpiel borowinowa"),
        ("borowina", "kąpiel borowinowa"),
        ("sulphur bath", "kąpiel siarczkowa Ukojenie Stawów"),
        ("masaż pleców", "masaż leczniczy pleców"),
        ("swedish massage", "masaż klasyczny"),
    ],
)
def test_alias_and_accent_insensitive_resolution(client, zapytanie, oczekiwana):
    body = client.post(SPA, json={"service_name": zapytanie, "date": dzien(2)}).json()
    assert body["available"] is True
    assert body["service_name"] == oczekiwana


def test_unknown_service_returns_available_services(client):
    body = client.post(SPA, json={"service_name": "krioterapia", "date": dzien(2)}).json()
    assert body["available"] is False
    assert len(body["available_services"]) == 6
    assert "nie jest oferowany" in body["message"]
    # kształt odpowiedzi pozostaje stały także na ścieżce odmowy
    assert {"available", "slots", "service_name", "date", "message"} <= set(body)


def test_same_hour_cannot_be_sold_twice_for_different_treatments(client):
    """Jeden gabinet/fizjoterapeuta na godzinę — drugi zabieg o 14:00 musi dostać odmowę (defekt #3)."""
    pierwsza = rezerwuj(client, godzina="14:00", usluga="masaż klasyczny")
    assert pierwsza.json()["success"] is True

    druga = rezerwuj(client, godzina="14:00", usluga="jonoforeza")
    body = druga.json()
    assert druga.status_code == 200
    assert body["success"] is False
    assert "zajęty" in body["message"]
    assert "14:00" not in body["slots"]

    # wspólny kalendarz: jonoforeza również nie widzi 14:00 jako wolnej godziny
    wolne = client.post(SPA, json={"service_name": "jonoforeza", "date": dzien(3)}).json()
    assert "14:00" not in wolne["slots"]


def test_availability_reports_price_and_duration(client):
    body = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert body["available"] is True
    assert body["price_pln"] == 160
    assert body["duration_min"] == 50
    assert "160 PLN" in body["message"]
    assert "50 min" in body["message"]


def test_every_catalogue_entry_has_price_and_duration():
    for usluga in main.USLUGI:
        assert usluga.cena_pln > 0, f"{usluga.kod} bez ceny"
        assert usluga.czas_min > 0, f"{usluga.kod} bez czasu trwania"
        assert usluga.zrodlo_ceny == "baza_wiedzy", usluga.kod


def test_catalogue_prices_are_the_knowledge_base_values():
    """Ceny kanoniczne = baza wiedzy agenta (80/120/100/70/160/30); strona generuje je z backendu."""
    cennik = {usluga.kod: (usluga.cena_pln, usluga.czas_min) for usluga in main.USLUGI}
    assert cennik["kapiel_siarczkowa"] == (80, 20)
    assert cennik["masaz_leczniczy"] == (120, 30)
    assert cennik["kapiel_borowinowa"] == (100, 25)
    assert cennik["jonoforeza"] == (70, 20)
    assert cennik["masaz_klasyczny"] == (160, 50)
    # gimnastyki nie ma w bazie wiedzy — cena i czas ze strony marketingowej
    assert cennik["gimnastyka_lecznicza"] == (30, 45)


@pytest.mark.parametrize(
    "zapytanie",
    ["gimnastyka", "Gimnastyka lecznicza (grupowa)", "gimnastyka dla seniorów", "group gymnastics"],
)
def test_gimnastyka_resolves_by_name_and_alias(client, zapytanie):
    body = client.post(SPA, json={"service_name": zapytanie, "date": dzien(2)}).json()
    assert body["available"] is True
    assert body["service_name"] == "gimnastyka lecznicza (grupowa)"
    assert (body["price_pln"], body["duration_min"]) == (30, 45)


def test_gimnastyka_can_be_booked(client):
    odpowiedz = rezerwuj(client, godzina="15:00", usluga="gimnastyka")
    body = odpowiedz.json()
    assert body["success"] is True
    assert body["service_name"] == "gimnastyka lecznicza (grupowa)"
