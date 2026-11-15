"""Idempotencja rezerwacji SPA (idempotency_key + dedupe bez klucza) oraz limity długości pól."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from helpers import BOOK, CANCEL, HANDOFF, dzien

import store
from schemas import Handoff


def _dane(**zmiany):
    bazowe = {"service_name": "masaż klasyczny", "date": dzien(3), "time": "14:00", "guest_name": "Jan Kowalski"}
    return {**bazowe, **zmiany}


def test_ponowienie_bez_klucza_zwraca_oryginalne_potwierdzenie(client):
    pierwsza = client.post(BOOK, json=_dane()).json()
    retry = client.post(BOOK, json=_dane()).json()
    assert pierwsza["success"] is True
    assert retry["success"] is True
    assert retry["confirmation_id"] == pierwsza["confirmation_id"]


def test_ponowienie_z_kluczem_zwraca_ten_sam_spa_numer(client):
    pierwsza = client.post(BOOK, json=_dane(idempotency_key="rez-001")).json()
    retry = client.post(BOOK, json=_dane(idempotency_key="rez-001")).json()
    assert retry["success"] is True
    assert retry["confirmation_id"] == pierwsza["confirmation_id"]
    assert retry["confirmation_id"].startswith("SPA-")


def test_fallback_ignoruje_wielkosc_liter_i_nadmiarowe_spacje(client):
    pierwsza = client.post(BOOK, json=_dane()).json()
    retry = client.post(BOOK, json=_dane(guest_name="  jan   KOWALSKI ")).json()
    assert retry["success"] is True
    assert retry["confirmation_id"] == pierwsza["confirmation_id"]


def test_inny_gosc_na_zajety_slot_dostaje_odmowe(client):
    client.post(BOOK, json=_dane())
    druga = client.post(BOOK, json=_dane(guest_name="Anna Nowak")).json()
    assert druga["success"] is False
    assert "zajęty" in druga["message"]


def test_ten_sam_klucz_z_innym_payloadem_to_konflikt(client):
    client.post(BOOK, json=_dane(idempotency_key="rez-002"))
    konflikt = client.post(BOOK, json=_dane(time="15:00", idempotency_key="rez-002")).json()
    assert konflikt["success"] is False
    assert "idempotencji" in konflikt["message"]


def test_nowy_klucz_dla_zajetego_slotu_nadal_dostaje_odmowe(client):
    client.post(BOOK, json=_dane(idempotency_key="rez-003"))
    druga = client.post(BOOK, json=_dane(guest_name="Anna Nowak", idempotency_key="rez-004")).json()
    assert druga["success"] is False


def test_anulowana_rezerwacja_nie_jest_zwracana_przy_ponowieniu(client):
    pierwsza = client.post(BOOK, json=_dane(idempotency_key="rez-005")).json()
    client.post(CANCEL, json={"confirmation_id": pierwsza["confirmation_id"], "medical_release": True})
    nowa = client.post(BOOK, json=_dane(idempotency_key="rez-005")).json()
    assert nowa["success"] is True
    assert nowa["confirmation_id"] != pierwsza["confirmation_id"]


def test_ponowienie_po_uplywie_dnia_nadal_zwraca_oryginal(client, monkeypatch):
    pierwsza = client.post(BOOK, json=_dane(idempotency_key="rez-006")).json()
    po_terminie = date.today() + timedelta(days=10)
    monkeypatch.setattr(store, "dzisiaj_warszawa", lambda: po_terminie)
    retry = client.post(BOOK, json=_dane(idempotency_key="rez-006")).json()
    assert retry["success"] is True
    assert retry["confirmation_id"] == pierwsza["confirmation_id"]


def test_pusty_klucz_jest_traktowany_jak_brak(client):
    pierwsza = client.post(BOOK, json=_dane(idempotency_key="   ")).json()
    retry = client.post(BOOK, json=_dane(idempotency_key="")).json()
    assert retry["confirmation_id"] == pierwsza["confirmation_id"]


def test_klucz_dluzszy_niz_128_znakow_daje_422(client):
    odpowiedz = client.post(BOOK, json=_dane(idempotency_key="k" * 129))
    assert odpowiedz.status_code == 422


# ── limity długości pól tekstowych ──────────────────────────────────────────

def test_powod_handoffu_ponad_limit_daje_422(client):
    assert client.post(HANDOFF, json={"reason": "x" * 501}).status_code == 422


def test_powod_handoffu_na_limicie_przechodzi(client):
    assert client.post(HANDOFF, json={"reason": "x" * 500}).status_code == 200


def test_dzial_ponad_limit_odrzucony_przez_model():
    with pytest.raises(ValueError):
        Handoff(department="d" * 41)


def test_imie_goscia_ponad_limit_daje_422(client):
    assert client.post(BOOK, json=_dane(guest_name="J" * 121)).status_code == 422


def test_dzisiaj_liczone_w_strefie_warszawskiej():
    assert store.dzisiaj_warszawa() == datetime.now(ZoneInfo("Europe/Warsaw")).date()
