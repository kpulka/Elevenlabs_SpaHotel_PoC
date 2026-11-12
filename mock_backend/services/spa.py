"""Reguły biznesowe zabiegów SPA.

Moduł nie zna FastAPI ani formatu odpowiedzi: zwraca wyniki domenowe (dataclass / Enum).
Teksty dla agenta, słowniki odpowiedzi, ``print`` i logi demo buduje ``responses.py``.
Jedyny stan zmieniany tutaj to kalendarz w ``SPA_STORE`` (zajmij / zwolnij).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from catalog import Usluga, WynikDopasowania, dopasuj
from state import SPA_STORE, USLUGI, wolne_sloty
from store import Rezerwacja

# Próg bezpłatnej anulacji: odwołanie ściśle ponad 2 h przed zabiegiem jest bezpłatne.
PROG_BEZPLATNEJ_ANULACJI_H = 2
ULAMEK_OPLATY_ANULACJI = 0.5


class Powod(str, Enum):
    """Dlaczego usługa odrzuciła żądanie (tekst komunikatu buduje ``responses.py``)."""

    NIEJEDNOZNACZNY = "niejednoznaczny"
    NIEZNANY = "nieznany"
    PRZESZLOSC = "przeszlosc"
    POZA_OKNEM = "poza_oknem"
    BRAK_SLOTOW = "brak_slotow"
    POZA_GRAFIKIEM = "poza_grafikiem"
    ZAJETY = "zajety"
    WYSCIG = "wyscig"  # slot zajęty między sprawdzeniem a zapisem
    NIE_ZNALEZIONO = "nie_znaleziono"


class RegulaOplaty(str, Enum):
    MEDYCZNA = "medyczna"
    BRAK_GODZINY = "brak_godziny"
    PONAD_2H = "ponad_2h"
    PONIZEJ_2H = "ponizej_2h"


@dataclass(frozen=True)
class Oplata:
    ulamek: float  # 0.0 albo 0.5 — kontrakt z agentem
    regula: RegulaOplaty


@dataclass(frozen=True)
class Dostepnosc:
    usluga: Usluga | None
    status: str  # status dopasowania: "dopasowano" | "niejednoznaczne" | "nieznane"
    powod: Powod | None  # None = są wolne sloty
    kandydaci: tuple[str, ...] = ()
    wolne: tuple[str, ...] = ()


@dataclass(frozen=True)
class Potwierdzenie:
    rezerwacja: Rezerwacja
    usluga: Usluga


@dataclass(frozen=True)
class WynikAnulowania:
    znaleziona: bool
    oplata: Oplata | None = None
    zwolniona: bool = False


@dataclass(frozen=True)
class Przeniesienie:
    stara_numer: str
    nowa: Rezerwacja
    usluga: Usluga


@dataclass(frozen=True)
class Odmowa:
    powod: Powod
    usluga: Usluga | None = None
    kandydaci: tuple[str, ...] = ()
    wolne: tuple[str, ...] = ()
    stara: Rezerwacja | None = None  # rezerwacja przenoszona (tylko przełożenie)


# ─────────────────────────────────────────────────────────────────────────────
# Dopasowanie zabiegu i dostępność
# ─────────────────────────────────────────────────────────────────────────────

def znajdz_zabieg(zapytanie: str) -> WynikDopasowania:
    """Rozpoznaje zabieg z katalogu po nazwie podanej przez agenta."""
    return dopasuj(USLUGI, zapytanie)


def _w_przeszlosci(data_iso: str) -> bool:
    return date.fromisoformat(data_iso) < SPA_STORE.dzisiaj


def _nazwy(uslugi) -> tuple[str, ...]:
    return tuple(usluga.nazwa for usluga in uslugi)


def sprawdz_dostepnosc(zapytanie: str, data_iso: str) -> Dostepnosc:
    wynik = znajdz_zabieg(zapytanie)
    if not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            return Dostepnosc(None, wynik.status, Powod.NIEJEDNOZNACZNY, kandydaci=_nazwy(wynik.kandydaci))
        return Dostepnosc(None, wynik.status, Powod.NIEZNANY)

    usluga = wynik.usluga
    if _w_przeszlosci(data_iso):
        return Dostepnosc(usluga, wynik.status, Powod.PRZESZLOSC)
    if not SPA_STORE.w_oknie(data_iso):
        return Dostepnosc(usluga, wynik.status, Powod.POZA_OKNEM)

    wolne = tuple(wolne_sloty(usluga, data_iso))
    if not wolne:
        return Dostepnosc(usluga, wynik.status, Powod.BRAK_SLOTOW)
    return Dostepnosc(usluga, wynik.status, None, wolne=wolne)


# ─────────────────────────────────────────────────────────────────────────────
# Rezerwacja
# ─────────────────────────────────────────────────────────────────────────────

def zarezerwuj(zapytanie: str, data_iso: str, godzina: str, gosc: str) -> Odmowa | Potwierdzenie:
    wynik = znajdz_zabieg(zapytanie)
    if not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            return Odmowa(Powod.NIEJEDNOZNACZNY, kandydaci=_nazwy(wynik.kandydaci))
        return Odmowa(Powod.NIEZNANY)

    usluga = wynik.usluga
    if _w_przeszlosci(data_iso):
        return Odmowa(Powod.PRZESZLOSC, usluga)
    if not SPA_STORE.w_oknie(data_iso):
        return Odmowa(Powod.POZA_OKNEM, usluga)

    wolne = tuple(wolne_sloty(usluga, data_iso))
    if godzina not in usluga.sloty:
        return Odmowa(Powod.POZA_GRAFIKIEM, usluga, wolne=wolne)
    if godzina not in wolne:
        return Odmowa(Powod.ZAJETY, usluga, wolne=wolne)

    # Odczyt i zapis stanu bez `await` — w jednym event loopie operacja jest atomowa.
    rezerwacja = Rezerwacja(
        confirmation_id=SPA_STORE.nowy_numer(),
        kod_uslugi=usluga.kod,
        data=data_iso,
        godzina=godzina,
        gosc=gosc,
    )
    if not SPA_STORE.zajmij(rezerwacja):
        return Odmowa(Powod.WYSCIG, usluga, wolne=tuple(wolne_sloty(usluga, data_iso)))
    return Potwierdzenie(rezerwacja, usluga)


# ─────────────────────────────────────────────────────────────────────────────
# Anulowanie i opłaty
# ─────────────────────────────────────────────────────────────────────────────

def oblicz_oplate_anulowania(
    medical_release: bool,
    appointment_datetime: str | None,
    teraz: datetime | None = None,
) -> Oplata:
    """Reguła opłat: zwolnienie medyczne = 0; brak godziny = 50%;
    > 2 h przed zabiegiem = 0; ≤ 2 h (w tym termin już minął) = 50%.

    Jedyny próg w kodzie to 2 h (docs/elevenlabs_agent_procedures.md); 24 h i 48 h
    nie mają tu osobnych stawek.
    """
    if medical_release:
        return Oplata(0.0, RegulaOplaty.MEDYCZNA)
    if appointment_datetime is None:
        return Oplata(ULAMEK_OPLATY_ANULACJI, RegulaOplaty.BRAK_GODZINY)

    termin = datetime.fromisoformat(appointment_datetime)
    if termin.tzinfo is not None:
        termin = termin.astimezone().replace(tzinfo=None)
    punkt_odniesienia = datetime.now() if teraz is None else teraz
    godziny_przed = (termin - punkt_odniesienia).total_seconds() / 3600

    if godziny_przed > PROG_BEZPLATNEJ_ANULACJI_H:
        return Oplata(0.0, RegulaOplaty.PONAD_2H)
    return Oplata(ULAMEK_OPLATY_ANULACJI, RegulaOplaty.PONIZEJ_2H)


def anuluj_rezerwacje(
    numer: str,
    medical_release: bool,
    appointment_datetime: str | None,
    teraz: datetime | None = None,
) -> WynikAnulowania:
    if SPA_STORE.rezerwacja(numer) is None:
        return WynikAnulowania(znaleziona=False)
    oplata = oblicz_oplate_anulowania(medical_release, appointment_datetime, teraz)
    zwolniona = SPA_STORE.zwolnij(numer) is not None
    return WynikAnulowania(znaleziona=True, oplata=oplata, zwolniona=zwolniona)


# ─────────────────────────────────────────────────────────────────────────────
# Przełożenie terminu
# ─────────────────────────────────────────────────────────────────────────────

def przenies_rezerwacje(
    numer: str,
    zapytanie: str,
    nowa_data: str,
    nowa_godzina: str,
    gosc: str,
) -> Odmowa | Przeniesienie:
    """Stary slot wraca do puli, nowy zostaje zajęty. Przy błędzie zapisu stary slot jest przywracany."""
    stara = SPA_STORE.rezerwacja(numer)
    if stara is None:
        return Odmowa(Powod.NIE_ZNALEZIONO)

    wynik = znajdz_zabieg(zapytanie)
    if not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            return Odmowa(Powod.NIEJEDNOZNACZNY, kandydaci=_nazwy(wynik.kandydaci), stara=stara)
        return Odmowa(Powod.NIEZNANY, stara=stara)

    usluga = wynik.usluga
    if _w_przeszlosci(nowa_data):
        return Odmowa(Powod.PRZESZLOSC, usluga, stara=stara)
    if not SPA_STORE.w_oknie(nowa_data):
        return Odmowa(Powod.POZA_OKNEM, usluga, stara=stara)
    if nowa_godzina not in usluga.sloty:
        return Odmowa(Powod.POZA_GRAFIKIEM, usluga, stara=stara)

    wolne = tuple(wolne_sloty(usluga, nowa_data))
    if nowa_godzina not in wolne:
        return Odmowa(Powod.ZAJETY, usluga, wolne=wolne, stara=stara)

    # Zwolnienie starego i zajęcie nowego slotu — sekcja bez `await`, więc atomowa.
    SPA_STORE.zwolnij(numer)
    nowa = Rezerwacja(
        confirmation_id=SPA_STORE.nowy_numer(),
        kod_uslugi=usluga.kod,
        data=nowa_data,
        godzina=nowa_godzina,
        gosc=gosc or stara.gosc,
    )
    if not SPA_STORE.zajmij(nowa):
        SPA_STORE.zajmij(stara)  # przywracamy stary slot, żeby nie zgubić rezerwacji
        return Odmowa(
            Powod.WYSCIG,
            usluga,
            wolne=tuple(wolne_sloty(usluga, nowa_data)),
            stara=stara,
        )
    return Przeniesienie(stara_numer=numer, nowa=nowa, usluga=usluga)
