"""Reguły biznesowe zabiegów SPA.

Moduł nie zna FastAPI ani formatu odpowiedzi: zwraca wyniki domenowe (dataclass / Enum).
Teksty dla agenta, słowniki odpowiedzi i logi demo buduje ``responses.py``.
Jedyny stan zmieniany tutaj to kalendarz w ``data.SPA_STORE`` (zajmij / zwolnij).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

import data
from catalog import Usluga, WynikDopasowania, dopasuj
from data import USLUGI
from store import STREFA_ZAKLADU, Rezerwacja, SpaStore, klucz_goscia, teraz_warszawa

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
    KLUCZ_KONFLIKT = "klucz_konflikt"  # ten sam idempotency_key użyty do innej rezerwacji


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
    nowa: bool = True  # False = ponowienie istniejącej rezerwacji (idempotencja), bez nowego zdarzenia


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
    return date.fromisoformat(data_iso) < data.SPA_STORE.dzisiaj


def _nazwy(uslugi: Iterable[Usluga]) -> tuple[str, ...]:
    return tuple(usluga.nazwa for usluga in uslugi)


def sprawdz_dostepnosc(zapytanie: str, data_iso: str) -> Dostepnosc:
    wynik = znajdz_zabieg(zapytanie)
    # `usluga is None` zawęża typ dla mypy; `dopasowano` implikuje `usluga is not None`,
    # więc warunek jest równoważny samemu `not wynik.dopasowano`.
    usluga = wynik.usluga
    if usluga is None or not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            return Dostepnosc(None, wynik.status, Powod.NIEJEDNOZNACZNY, kandydaci=_nazwy(wynik.kandydaci))
        return Dostepnosc(None, wynik.status, Powod.NIEZNANY)

    if _w_przeszlosci(data_iso):
        return Dostepnosc(usluga, wynik.status, Powod.PRZESZLOSC)
    if not data.SPA_STORE.w_oknie(data_iso):
        return Dostepnosc(usluga, wynik.status, Powod.POZA_OKNEM)

    wolne = tuple(wolne_sloty(usluga, data_iso))
    if not wolne:
        return Dostepnosc(usluga, wynik.status, Powod.BRAK_SLOTOW)
    return Dostepnosc(usluga, wynik.status, None, wolne=wolne)


# ─────────────────────────────────────────────────────────────────────────────
# Rezerwacja
# ─────────────────────────────────────────────────────────────────────────────

def zarezerwuj(
    zapytanie: str,
    data_iso: str,
    godzina: str,
    gosc: str,
    idempotency_key: str | None = None,
) -> Odmowa | Potwierdzenie:
    wynik = znajdz_zabieg(zapytanie)
    usluga = wynik.usluga  # zawężenie typu: patrz sprawdz_dostepnosc
    if usluga is None or not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            return Odmowa(Powod.NIEJEDNOZNACZNY, kandydaci=_nazwy(wynik.kandydaci))
        return Odmowa(Powod.NIEZNANY)

    # Ponowne wysłanie tej samej rezerwacji (retry) ma zwrócić ORYGINALNE potwierdzenie,
    # a nie "slot zajęty" — sprawdzamy to przed regułami czasu, bo dzień mógł już minąć.
    powtorka = _powtorka_rezerwacji(usluga, data_iso, godzina, gosc, idempotency_key)
    if powtorka is not None:
        return powtorka

    if _w_przeszlosci(data_iso):
        return Odmowa(Powod.PRZESZLOSC, usluga)
    if not data.SPA_STORE.w_oknie(data_iso):
        return Odmowa(Powod.POZA_OKNEM, usluga)

    wolne = tuple(wolne_sloty(usluga, data_iso))
    if godzina not in usluga.sloty:
        return Odmowa(Powod.POZA_GRAFIKIEM, usluga, wolne=wolne)
    if godzina not in wolne:
        return Odmowa(Powod.ZAJETY, usluga, wolne=wolne)

    # Odczyt i zapis stanu bez `await` — w jednym event loopie operacja jest atomowa.
    rezerwacja = Rezerwacja(
        confirmation_id=data.SPA_STORE.nowy_numer(),
        kod_uslugi=usluga.kod,
        data=data_iso,
        godzina=godzina,
        gosc=gosc,
    )
    # Rezerwacja i klucz idempotencji zapisywane razem (w SQLite w jednej transakcji).
    if not data.SPA_STORE.zajmij(rezerwacja, idempotency_key=idempotency_key):
        return Odmowa(Powod.WYSCIG, usluga, wolne=tuple(wolne_sloty(usluga, data_iso)))
    return Potwierdzenie(rezerwacja, usluga)


def _powtorka_rezerwacji(
    usluga: Usluga,
    data_iso: str,
    godzina: str,
    gosc: str,
    idempotency_key: str | None,
) -> Potwierdzenie | Odmowa | None:
    """Zwraca istniejące potwierdzenie, gdy żądanie powtarza już zapisaną rezerwację.

    1. ``idempotency_key`` znany -> ta sama rezerwacja (zgodny payload) albo konflikt klucza.
    2. Brak klucza / nieznany klucz -> fallback: ta sama usługa, data, godzina i gość (po normalizacji).
    """
    if idempotency_key:
        znana = data.SPA_STORE.rezerwacja_po_kluczu(idempotency_key)
        if znana is not None:
            oryginal = (znana.kod_uslugi, znana.data, znana.godzina, klucz_goscia(znana.gosc))
            if oryginal == (usluga.kod, data_iso, godzina, klucz_goscia(gosc)):
                return Potwierdzenie(znana, usluga, nowa=False)
            return Odmowa(Powod.KLUCZ_KONFLIKT, usluga)

    duplikat = data.SPA_STORE.duplikat(usluga.kod, data_iso, godzina, gosc)
    if duplikat is not None:
        return Potwierdzenie(duplikat, usluga, nowa=False)
    return None


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
        termin = termin.astimezone(STREFA_ZAKLADU).replace(tzinfo=None)
    punkt_odniesienia = teraz_warszawa() if teraz is None else teraz
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
    if data.SPA_STORE.rezerwacja(numer) is None:
        return WynikAnulowania(znaleziona=False)
    oplata = oblicz_oplate_anulowania(medical_release, appointment_datetime, teraz)
    zwolniona = data.SPA_STORE.zwolnij(numer) is not None
    return WynikAnulowania(znaleziona=True, oplata=oplata, zwolniona=zwolniona)


# ─────────────────────────────────────────────────────────────────────────────
# Przełożenie terminu
# ─────────────────────────────────────────────────────────────────────────────

def przenies_rezerwacje(
    numer: str,
    zapytanie: str,
    nowa_data: str,
    nowa_godzina: str,
    gosc: str | None,  # None (brak w zapytaniu) -> zostaje gość z poprzedniej rezerwacji
) -> Odmowa | Przeniesienie:
    """Stary slot wraca do puli, nowy zostaje zajęty. Przy błędzie zapisu stary slot jest przywracany."""
    stara = data.SPA_STORE.rezerwacja(numer)
    if stara is None:
        return Odmowa(Powod.NIE_ZNALEZIONO)

    wynik = znajdz_zabieg(zapytanie)
    usluga = wynik.usluga  # zawężenie typu: patrz sprawdz_dostepnosc
    if usluga is None or not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            return Odmowa(Powod.NIEJEDNOZNACZNY, kandydaci=_nazwy(wynik.kandydaci), stara=stara)
        return Odmowa(Powod.NIEZNANY, stara=stara)

    if _w_przeszlosci(nowa_data):
        return Odmowa(Powod.PRZESZLOSC, usluga, stara=stara)
    if not data.SPA_STORE.w_oknie(nowa_data):
        return Odmowa(Powod.POZA_OKNEM, usluga, stara=stara)
    if nowa_godzina not in usluga.sloty:
        return Odmowa(Powod.POZA_GRAFIKIEM, usluga, stara=stara)

    wolne = tuple(wolne_sloty(usluga, nowa_data))
    if nowa_godzina not in wolne:
        return Odmowa(Powod.ZAJETY, usluga, wolne=wolne, stara=stara)

    # Zwolnienie starego i zajęcie nowego slotu — sekcja bez `await`, więc atomowa.
    data.SPA_STORE.zwolnij(numer)
    nowa = Rezerwacja(
        confirmation_id=data.SPA_STORE.nowy_numer(),
        kod_uslugi=usluga.kod,
        data=nowa_data,
        godzina=nowa_godzina,
        gosc=gosc or stara.gosc,
    )
    if not data.SPA_STORE.zajmij(nowa):
        data.SPA_STORE.zajmij(stara)  # przywracamy stary slot, żeby nie zgubić rezerwacji
        return Odmowa(
            Powod.WYSCIG,
            usluga,
            wolne=tuple(wolne_sloty(usluga, nowa_data)),
            stara=stara,
        )
    return Przeniesienie(stara_numer=numer, nowa=nowa, usluga=usluga)


def wolne_sloty(usluga: Usluga, data_iso: str, store: SpaStore | None = None) -> list[str]:
    magazyn = data.SPA_STORE if store is None else store
    return magazyn.sloty_dnia(usluga, data_iso)


def cennik(usluga: Usluga) -> dict[str, int]:
    """Cena i czas zabiegu wprost z katalogu — te same liczby mówi Anna na głos."""
    return {"price_pln": usluga.cena_pln, "duration_min": usluga.czas_min}


def poza_oknem(data_iso: str, store: SpaStore | None = None) -> str:
    magazyn = data.SPA_STORE if store is None else store
    return (
        f"Termin {data_iso} jest poza oknem rezerwacji "
        f"({magazyn.dzisiaj.isoformat()} – {magazyn.ostatni_dzien.isoformat()})."
    )

