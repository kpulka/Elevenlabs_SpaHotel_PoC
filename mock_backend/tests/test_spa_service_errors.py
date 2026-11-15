"""Failure branches of the SPA service that the HTTP suite does not reach (reschedule, sqlite cancel)."""

from __future__ import annotations

import pytest
from helpers import dzien

from services import spa
from store import Rezerwacja


def _zarezerwuj(spa_stan, godzina: str = "10:00", dzien_iso: str | None = None) -> str:
    wynik = spa.zarezerwuj("masaż klasyczny", dzien_iso or dzien(3), godzina, "Jan Kowalski")
    assert isinstance(wynik, spa.Potwierdzenie)
    return wynik.rezerwacja.confirmation_id


def test_reschedule_unknown_reservation(spa_stan):
    wynik = spa.przenies_rezerwacje("SPA-9999", "masaż klasyczny", dzien(4), "11:00", None)
    assert isinstance(wynik, spa.Odmowa) and wynik.powod is spa.Powod.NIE_ZNALEZIONO


def test_reschedule_unknown_or_ambiguous_service_keeps_old_slot(spa_stan):
    numer = _zarezerwuj(spa_stan)
    nieznany = spa.przenies_rezerwacje(numer, "lot balonem", dzien(4), "11:00", None)
    assert nieznany.powod is spa.Powod.NIEZNANY and nieznany.stara is not None

    niejednoznaczny = spa.przenies_rezerwacje(numer, "masaż", dzien(4), "11:00", None)
    assert niejednoznaczny.powod is spa.Powod.NIEJEDNOZNACZNY and niejednoznaczny.kandydaci
    assert spa_stan.rezerwacja(numer) is not None


@pytest.mark.parametrize(
    "nowa_data,nowa_godzina,powod",
    [
        ("2000-01-01", "11:00", spa.Powod.PRZESZLOSC),
        ("2999-01-01", "11:00", spa.Powod.POZA_OKNEM),
        (None, "13:33", spa.Powod.POZA_GRAFIKIEM),
    ],
)
def test_reschedule_rejections_keep_the_original(spa_stan, nowa_data, nowa_godzina, powod):
    numer = _zarezerwuj(spa_stan)
    wynik = spa.przenies_rezerwacje(numer, "masaż klasyczny", nowa_data or dzien(4), nowa_godzina, None)
    assert isinstance(wynik, spa.Odmowa) and wynik.powod is powod
    assert wynik.stara is not None
    assert spa_stan.rezerwacja(numer) is not None


def test_reschedule_onto_taken_slot_reports_taken(spa_stan):
    numer = _zarezerwuj(spa_stan)
    _zarezerwuj(spa_stan, godzina="11:00", dzien_iso=dzien(4))
    wynik = spa.przenies_rezerwacje(numer, "masaż klasyczny", dzien(4), "11:00", None)
    assert wynik.powod is spa.Powod.ZAJETY and wynik.wolne


def test_reschedule_race_restores_the_original_reservation(spa_stan, monkeypatch):
    numer = _zarezerwuj(spa_stan)
    prawdziwe_zajmij = spa_stan.zajmij
    wywolania = {"n": 0}

    def zajmij_z_wyscigiem(rezerwacja: Rezerwacja, idempotency_key=None) -> bool:
        # The first call (new slot) loses the race; the second call restores the old slot.
        wywolania["n"] += 1
        if wywolania["n"] == 1:
            return False
        return prawdziwe_zajmij(rezerwacja, idempotency_key=idempotency_key)

    monkeypatch.setattr(spa_stan, "zajmij", zajmij_z_wyscigiem)
    wynik = spa.przenies_rezerwacje(numer, "masaż klasyczny", dzien(4), "11:00", None)
    assert isinstance(wynik, spa.Odmowa) and wynik.powod is spa.Powod.WYSCIG
    assert spa_stan.rezerwacja(numer) is not None  # the old reservation is back
    assert wywolania["n"] == 2


def test_wolne_sloty_and_poza_oknem_accept_an_explicit_store(spa_stan):
    usluga = spa.znajdz_zabieg("masaż klasyczny").usluga
    assert spa.wolne_sloty(usluga, dzien(3), store=spa_stan) == list(usluga.sloty)
    assert "poza oknem" in spa.poza_oknem("2999-01-01", store=spa_stan)


def test_sqlite_cancel_of_unknown_reservation_returns_none(tmp_path):
    from data import HORYZONT_DNI, USLUGI
    from sqlite_store import SqliteSpaStore

    magazyn = SqliteSpaStore(tmp_path / "anuluj.db", USLUGI, horyzont_dni=HORYZONT_DNI)
    try:
        assert magazyn.zwolnij("SPA-0000") is None
    finally:
        magazyn.close()
