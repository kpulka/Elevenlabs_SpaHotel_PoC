"""SQLite persistence: migrations, slot uniqueness, idempotency keys, restarts and thread safety.

Every database file lives under ``tmp_path``; nothing is written into the repository.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from helpers import dzien

import data
import sqlite_store
from data import HORYZONT_DNI, USLUGI
from services import spa
from sqlite_store import SqliteSpaStore, migrate
from store import Rezerwacja

USLUGA = spa.znajdz_zabieg("masaż klasyczny").usluga
KOD = USLUGA.kod
GOSC = "Jan Kowalski"


@pytest.fixture()
def db(tmp_path):
    return tmp_path / "anna-test.db"


def _otworz(path) -> SqliteSpaStore:
    return SqliteSpaStore(path, USLUGI, horyzont_dni=HORYZONT_DNI)


def _rezerwacja(numer: str, godzina: str = "10:00", gosc: str = GOSC, dzien_iso: str | None = None) -> Rezerwacja:
    return Rezerwacja(confirmation_id=numer, kod_uslugi=KOD, data=dzien_iso or dzien(3), godzina=godzina, gosc=gosc)


@pytest.fixture()
def uzyj(monkeypatch):
    """Points the service layer at a given store (services read ``data.SPA_STORE`` at call time)."""

    def _ustaw(magazyn):
        monkeypatch.setattr(data, "SPA_STORE", magazyn)
        return magazyn

    return _ustaw


# ── migrations ──────────────────────────────────────────────────────────────

def test_migrate_is_idempotent(db):
    _otworz(db).close()
    conn = sqlite3.connect(db)
    try:
        assert migrate(conn) == 1
        assert migrate(conn) == 1
        wersje = conn.execute("SELECT version FROM schema_version ORDER BY version").fetchall()
    finally:
        conn.close()
    assert wersje == [(1,)]


def test_reopening_database_does_not_reapply_migrations(db):
    _otworz(db).close()
    magazyn = _otworz(db)
    try:
        assert magazyn.schema_version == 1
        assert magazyn._conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 1
    finally:
        magazyn.close()


def test_schema_contains_expected_objects(db):
    _otworz(db).close()
    conn = sqlite3.connect(db)
    try:
        nazwy = {wiersz[0] for wiersz in conn.execute("SELECT name FROM sqlite_master")}
    finally:
        conn.close()
    assert {"rezerwacje", "klucze_idempotencji", "sekwencja", "schema_version"} <= nazwy
    assert "ux_rezerwacje_slot" in nazwy


def test_failed_migration_rolls_back_and_keeps_previous_version(db, monkeypatch):
    broken = ((1, sqlite_store.SCHEMA_V1), (2, "CREATE TABLE czesciowa (x INTEGER); INSERT INTO nie_ma VALUES (1);"))
    monkeypatch.setattr(sqlite_store, "MIGRATIONS", broken)
    with pytest.raises(sqlite3.Error):
        _otworz(db)

    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 1
        assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'czesciowa'").fetchall() == []
    finally:
        conn.close()


def test_store_creates_missing_parent_directory(tmp_path):
    magazyn = _otworz(tmp_path / "zagniezdzony" / "katalog" / "anna.db")
    try:
        assert magazyn.zajmij(_rezerwacja("SPA-T1"))
    finally:
        magazyn.close()


def test_in_memory_database_path_works():
    magazyn = _otworz(":memory:")
    try:
        assert magazyn.zajmij(_rezerwacja("SPA-M1"))
        assert magazyn.rezerwacja("SPA-M1") is not None
    finally:
        magazyn.close()


# ── slot exclusivity (UNIQUE index) ─────────────────────────────────────────

def test_unique_index_rejects_second_booking_of_same_slot(db):
    magazyn = _otworz(db)
    try:
        assert magazyn.zajmij(_rezerwacja("SPA-1001", gosc="Jan Kowalski"))
        assert magazyn.zajmij(_rezerwacja("SPA-1002", gosc="Anna Nowak")) is False
        assert magazyn.rezerwacja("SPA-1002") is None
        assert "10:00" not in magazyn.sloty_dnia(USLUGA, dzien(3))
    finally:
        magazyn.close()


# ── persistence across restarts ─────────────────────────────────────────────

def test_booking_survives_restart(db, uzyj):
    magazyn = uzyj(_otworz(db))
    wynik = spa.zarezerwuj("masaż klasyczny", dzien(3), "10:00", GOSC)
    assert isinstance(wynik, spa.Potwierdzenie)
    numer = wynik.rezerwacja.confirmation_id
    magazyn.close()

    ponownie = uzyj(_otworz(db))
    try:
        assert ponownie.rezerwacja(numer) is not None
        assert "10:00" not in ponownie.sloty_dnia(USLUGA, dzien(3))
        odmowa = spa.zarezerwuj("masaż klasyczny", dzien(3), "10:00", "Anna Nowak")
        assert isinstance(odmowa, spa.Odmowa) and odmowa.powod is spa.Powod.ZAJETY
    finally:
        ponownie.close()


def test_slot_stays_taken_after_restart_for_service_listing(db, uzyj):
    pierwszy = _otworz(db)
    pierwszy.zajmij(_rezerwacja("SPA-2001", godzina="11:00"))
    pierwszy.close()
    magazyn = _otworz(db)
    try:
        usluga = spa.znajdz_zabieg("masaż klasyczny").usluga
        assert "11:00" not in magazyn.sloty_dnia(usluga, dzien(3))
    finally:
        magazyn.close()


def test_idempotency_key_dedupes_and_survives_restart(db, uzyj):
    magazyn = uzyj(_otworz(db))
    pierwsza = spa.zarezerwuj("masaż klasyczny", dzien(3), "10:00", GOSC, idempotency_key="sql-key-1")
    assert isinstance(pierwsza, spa.Potwierdzenie) and pierwsza.nowa
    magazyn.close()

    ponownie = uzyj(_otworz(db))
    try:
        retry = spa.zarezerwuj("masaż klasyczny", dzien(3), "10:00", GOSC, idempotency_key="sql-key-1")
        assert isinstance(retry, spa.Potwierdzenie)
        assert retry.nowa is False
        assert retry.rezerwacja.confirmation_id == pierwsza.rezerwacja.confirmation_id

        konflikt = spa.zarezerwuj("masaż klasyczny", dzien(3), "12:00", GOSC, idempotency_key="sql-key-1")
        assert isinstance(konflikt, spa.Odmowa) and konflikt.powod is spa.Powod.KLUCZ_KONFLIKT
    finally:
        ponownie.close()


def test_cancel_persists_and_frees_slot(db, uzyj):
    magazyn = uzyj(_otworz(db))
    numer = spa.zarezerwuj("masaż klasyczny", dzien(3), "10:00", GOSC).rezerwacja.confirmation_id
    wynik = spa.anuluj_rezerwacje(numer, medical_release=True, appointment_datetime=None)
    assert wynik.znaleziona and wynik.zwolniona
    magazyn.close()

    ponownie = uzyj(_otworz(db))
    try:
        assert ponownie.rezerwacja(numer) is None
        usluga = spa.znajdz_zabieg("masaż klasyczny").usluga
        assert "10:00" in ponownie.sloty_dnia(usluga, dzien(3))
        assert spa.anuluj_rezerwacje(numer, medical_release=False, appointment_datetime=None).znaleziona is False
    finally:
        ponownie.close()


def test_reschedule_persists_both_sides(db, uzyj):
    magazyn = uzyj(_otworz(db))
    stara = spa.zarezerwuj("masaż klasyczny", dzien(3), "10:00", GOSC).rezerwacja.confirmation_id
    wynik = spa.przenies_rezerwacje(stara, "masaż klasyczny", dzien(4), "11:00", None)
    assert isinstance(wynik, spa.Przeniesienie)
    nowa = wynik.nowa.confirmation_id
    magazyn.close()

    ponownie = uzyj(_otworz(db))
    try:
        assert ponownie.rezerwacja(stara) is None
        przeniesiona = ponownie.rezerwacja(nowa)
        assert przeniesiona is not None
        assert (przeniesiona.data, przeniesiona.godzina, przeniesiona.gosc) == (dzien(4), "11:00", GOSC)
        usluga = spa.znajdz_zabieg("masaż klasyczny").usluga
        assert "10:00" in ponownie.sloty_dnia(usluga, dzien(3))
        assert "11:00" not in ponownie.sloty_dnia(usluga, dzien(4))
    finally:
        ponownie.close()


def test_confirmation_numbers_keep_increasing_across_restarts(db):
    magazyn = _otworz(db)
    pierwszy = magazyn.nowy_numer()
    magazyn.close()
    ponownie = _otworz(db)
    try:
        drugi = ponownie.nowy_numer()
    finally:
        ponownie.close()
    assert pierwszy == "SPA-1001"
    assert drugi == "SPA-1002"


# ── idempotency-key TTL ─────────────────────────────────────────────────────

def test_purge_removes_only_expired_idempotency_keys(db):
    magazyn = _otworz(db)
    try:
        magazyn.zajmij(_rezerwacja("SPA-3001"), idempotency_key="stary-klucz")
        dwa_dni_pozniej = datetime.now(timezone.utc) + timedelta(days=2)

        assert magazyn.purge_klucze(timedelta(days=1), teraz=dwa_dni_pozniej) == 1
        assert magazyn.purge_klucze(timedelta(days=1), teraz=dwa_dni_pozniej) == 0
        # the reservation itself is not touched by the purge
        assert magazyn.rezerwacja("SPA-3001") is not None
        assert magazyn.rezerwacja_po_kluczu("stary-klucz") is None
    finally:
        magazyn.close()


def test_key_younger_than_ttl_is_kept(db):
    magazyn = _otworz(db)
    try:
        magazyn.zajmij(_rezerwacja("SPA-3002"), idempotency_key="swiezy-klucz")
        assert magazyn.purge_klucze(timedelta(days=1)) == 0
        assert magazyn.rezerwacja_po_kluczu("swiezy-klucz") is not None
    finally:
        magazyn.close()


# ── reset and thread safety ─────────────────────────────────────────────────

def test_reset_clears_reservations_keys_and_sequence(db):
    magazyn = _otworz(db)
    try:
        magazyn.zajmij(_rezerwacja("SPA-4001"), idempotency_key="reset-key")
        magazyn.nowy_numer()
        magazyn.reset()
        assert magazyn.rezerwacja("SPA-4001") is None
        assert magazyn.rezerwacja_po_kluczu("reset-key") is None
        assert magazyn.nowy_numer() == "SPA-1001"
    finally:
        magazyn.close()


def test_concurrent_threads_produce_exactly_one_winner(db):
    magazyn = _otworz(db)
    try:
        def probuj(i: int) -> bool:
            return magazyn.zajmij(_rezerwacja(f"SPA-T{i}", gosc=f"Gość {i}"))

        with ThreadPoolExecutor(max_workers=20) as pula:
            wyniki = list(pula.map(probuj, range(20)))
        assert sum(wyniki) == 1
        assert len(magazyn._zajete_godziny(dzien(3))) == 1
    finally:
        magazyn.close()
