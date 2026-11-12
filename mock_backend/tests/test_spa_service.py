"""Testy jednostkowe warstwy usług SPA (`services/spa.py`) — bez HTTP, bez TestClient.

Granice opłaty anulowania sprawdzamy na faktycznej regule z kodu: opłata 0% wyłącznie
ściśle ponad 2 h przed zabiegiem, poniżej lub równo 2 h — 50%. Nie ma stawek 24 h ani 48 h.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from helpers import dzien

from services import spa
from state import USLUGI
from store import Rezerwacja

# Stały punkt odniesienia (naiwny czas lokalny) — granice nie zależą od zegara.
TERAZ = datetime(2026, 11, 12, 10, 0, 0)
PONAD_2H = spa.RegulaOplaty.PONAD_2H
PONIZEJ_2H = spa.RegulaOplaty.PONIZEJ_2H


def termin_za(delta: timedelta) -> str:
    return (TERAZ + delta).isoformat()


# ── granice opłaty anulowania ───────────────────────────────────────────────

@pytest.mark.parametrize(
    "delta,ulamek,regula",
    [
        (timedelta(hours=5), 0.0, PONAD_2H),
        (timedelta(hours=2, seconds=1), 0.0, PONAD_2H),  # tuż ponad 2 h → bezpłatnie
        (timedelta(hours=2), 0.5, PONIZEJ_2H),  # dokładnie 2 h → NIE „ponad” → 50%
        (timedelta(hours=1, minutes=59), 0.5, PONIZEJ_2H),
        (timedelta(hours=24), 0.0, PONAD_2H),  # 24 h nie ma osobnej stawki
        (timedelta(hours=48), 0.0, PONAD_2H),  # 48 h nie ma osobnej stawki
        (timedelta(0), 0.5, PONIZEJ_2H),  # zabieg „teraz”
        (timedelta(hours=-1), 0.5, PONIZEJ_2H),  # termin już minął
    ],
)
def test_granice_oplaty_anulowania_2h(delta, ulamek, regula):
    oplata = spa.oblicz_oplate_anulowania(False, termin_za(delta), teraz=TERAZ)
    assert oplata.ulamek == ulamek
    assert oplata.regula is regula


def test_zwolnienie_medyczne_zawsze_bezplatne_niezaleznie_od_czasu():
    oplata = spa.oblicz_oplate_anulowania(True, termin_za(timedelta(minutes=30)), teraz=TERAZ)
    assert oplata.ulamek == 0.0
    assert oplata.regula is spa.RegulaOplaty.MEDYCZNA


def test_brak_godziny_zabiegu_to_50_procent():
    oplata = spa.oblicz_oplate_anulowania(False, None, teraz=TERAZ)
    assert oplata == spa.Oplata(0.5, spa.RegulaOplaty.BRAK_GODZINY)


def test_termin_z_strefa_czasowa_przeliczany_na_czas_lokalny():
    """Termin aware jest zamieniany na czas lokalny przed porównaniem (jak w routerze)."""
    lokalny_naiwny = TERAZ + timedelta(hours=5)
    z_strefa = lokalny_naiwny.astimezone().isoformat()  # naiwny = lokalny → aware lokalny
    assert spa.oblicz_oplate_anulowania(False, z_strefa, teraz=TERAZ).ulamek == 0.0

    blisko = (TERAZ + timedelta(hours=1)).astimezone().isoformat()
    assert spa.oblicz_oplate_anulowania(False, blisko, teraz=TERAZ).ulamek == 0.5


def test_domyslny_zegar_uzywany_gdy_brak_teraz():
    """Bez `teraz` reguła liczy od datetime.now() — 5 h naprzód to zawsze „ponad 2 h”."""
    termin = (datetime.now() + timedelta(hours=5)).isoformat()
    assert spa.oblicz_oplate_anulowania(False, termin).regula is PONAD_2H


# ── dopasowanie i dostępność ────────────────────────────────────────────────

def test_znajdz_zabieg_zwraca_kandydatow_dla_niejednoznacznej_nazwy():
    wynik = spa.znajdz_zabieg("masaż")
    assert wynik.status == "niejednoznaczne"
    assert not wynik.dopasowano


def test_dostepnosc_przeszlosc(spa_stan):
    wynik = spa.sprawdz_dostepnosc("jonoforeza", dzien(-1))
    assert wynik.powod is spa.Powod.PRZESZLOSC
    assert wynik.usluga is not None


def test_dostepnosc_poza_oknem(spa_stan):
    wynik = spa.sprawdz_dostepnosc("jonoforeza", dzien(30))
    assert wynik.powod is spa.Powod.POZA_OKNEM


def test_dostepnosc_brak_slotow_gdy_dzien_zajety(spa_stan):
    usluga = spa.znajdz_zabieg("masaż klasyczny").usluga
    for godzina in usluga.sloty:
        assert spa_stan.zajmij(
            Rezerwacja(f"T-{godzina}", usluga.kod, dzien(3), godzina, "Test")
        )
    wynik = spa.sprawdz_dostepnosc("masaż klasyczny", dzien(3))
    assert wynik.powod is spa.Powod.BRAK_SLOTOW
    assert wynik.wolne == ()


def test_dostepnosc_zwraca_wolne_sloty_bez_powodu(spa_stan):
    usluga = spa.znajdz_zabieg("masaż klasyczny").usluga
    wynik = spa.sprawdz_dostepnosc("masaż klasyczny", dzien(3))
    assert wynik.powod is None
    assert wynik.wolne == tuple(usluga.sloty)


# ── rezerwacja ──────────────────────────────────────────────────────────────

def test_zarezerwuj_zajmuje_slot_i_drugi_raz_dostaje_odmowe(spa_stan):
    pierwsza = spa.zarezerwuj("masaż klasyczny", dzien(3), "14:00", "Jan")
    assert isinstance(pierwsza, spa.Potwierdzenie)
    assert spa_stan.rezerwacja(pierwsza.rezerwacja.confirmation_id) is not None

    druga = spa.zarezerwuj("jonoforeza", dzien(3), "14:00", "Anna")
    assert isinstance(druga, spa.Odmowa)
    assert druga.powod is spa.Powod.ZAJETY
    assert "14:00" not in druga.wolne


def test_zarezerwuj_poza_grafikiem_zwraca_wolne_i_nazwe_zabiegu(spa_stan):
    odmowa = spa.zarezerwuj("masaż klasyczny", dzien(3), "03:00", "Jan")
    assert odmowa.powod is spa.Powod.POZA_GRAFIKIEM
    assert odmowa.usluga.nazwa == "masaż klasyczny"


def test_zarezerwuj_niejednoznaczna_nazwa_nie_zajmuje_slotu(spa_stan):
    odmowa = spa.zarezerwuj("masaż", dzien(3), "14:00", "Jan")
    assert odmowa.powod is spa.Powod.NIEJEDNOZNACZNY
    assert len(odmowa.kandydaci) == 2
    assert "14:00" in spa.sprawdz_dostepnosc("masaż klasyczny", dzien(3)).wolne


# ── anulowanie ──────────────────────────────────────────────────────────────

def test_anuluj_nieistniejaca_rezerwacje_nie_rusza_kalendarza(spa_stan):
    spa.zarezerwuj("masaż klasyczny", dzien(3), "14:00", "Jan")
    wynik = spa.anuluj_rezerwacje("SPA-0000", False, None)
    assert wynik.znaleziona is False
    assert wynik.zwolniona is False
    assert "14:00" not in spa.sprawdz_dostepnosc("masaż klasyczny", dzien(3)).wolne


def test_anuluj_zwalnia_slot(spa_stan):
    numer = spa.zarezerwuj("masaż klasyczny", dzien(3), "14:00", "Jan").rezerwacja.confirmation_id
    wynik = spa.anuluj_rezerwacje(numer, False, termin_za(timedelta(hours=5)), teraz=TERAZ)
    assert wynik.znaleziona is True
    assert wynik.zwolniona is True
    assert wynik.oplata.ulamek == 0.0
    assert spa_stan.rezerwacja(numer) is None
    assert "14:00" in spa.sprawdz_dostepnosc("masaż klasyczny", dzien(3)).wolne


# ── przełożenie ─────────────────────────────────────────────────────────────

def test_przenies_nieistniejaca_rezerwacje_to_odmowa(spa_stan):
    odmowa = spa.przenies_rezerwacje("SPA-0000", "masaż klasyczny", dzien(4), "11:00", "Jan")
    assert odmowa.powod is spa.Powod.NIE_ZNALEZIONO
    assert odmowa.stara is None


def test_przenies_zwalnia_stary_i_zajmuje_nowy_slot(spa_stan):
    stara = spa.zarezerwuj("masaż klasyczny", dzien(3), "14:00", "Jan").rezerwacja
    wynik = spa.przenies_rezerwacje(stara.confirmation_id, "masaż klasyczny", dzien(4), "11:00", "")
    assert isinstance(wynik, spa.Przeniesienie)
    assert wynik.nowa.gosc == "Jan", "pusty gość w żądaniu → nazwisko z rezerwacji"
    assert spa_stan.rezerwacja(stara.confirmation_id) is None
    assert "14:00" in spa.sprawdz_dostepnosc("masaż klasyczny", dzien(3)).wolne
    assert "11:00" not in spa.sprawdz_dostepnosc("masaż klasyczny", dzien(4)).wolne


def test_przenies_na_zajety_slot_zachowuje_stara_rezerwacje(spa_stan):
    stara = spa.zarezerwuj("masaż klasyczny", dzien(3), "14:00", "Jan").rezerwacja
    spa.zarezerwuj("masaż klasyczny", dzien(3), "11:00", "Anna")
    odmowa = spa.przenies_rezerwacje(stara.confirmation_id, "masaż klasyczny", dzien(3), "11:00", "Jan")
    assert odmowa.powod is spa.Powod.ZAJETY
    assert odmowa.stara is not None
    assert spa_stan.rezerwacja(stara.confirmation_id) is not None


# ── kontrakt architektury ───────────────────────────────────────────────────

def test_warstwa_usług_nie_importuje_fastapi():
    """Usługi mają być czystymi regułami: import ich nie może ciągnąć FastAPI."""
    katalog_backendu = Path(__file__).resolve().parents[1]
    kod = "import sys, services.spa; assert 'fastapi' not in sys.modules"
    wynik = subprocess.run(
        [sys.executable, "-c", kod], cwd=katalog_backendu, capture_output=True, text=True
    )
    assert wynik.returncode == 0, wynik.stderr


def test_katalog_ma_kod_uslugi_dla_kazdego_zabiegu():
    """Smoke: każdy zabieg z katalogu da się rozpoznać po własnym kodzie."""
    for usluga in USLUGI:
        assert spa.znajdz_zabieg(usluga.kod).usluga.kod == usluga.kod
