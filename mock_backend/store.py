"""Stan w pamięci backendu: rezerwacje SPA, zajętość slotów i katalog pokoi.

Wszystkie operacje są synchroniczne i wykonują się bez ``await`` między
odczytem a zapisem stanu, więc w jednym procesie asyncio są efektywnie
atomowe (event loop nie przełączy zadania w środku metody).
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Sequence

from catalog import DATA_DIR, Usluga, normalizuj


def _wczytaj_json(sciezka: Path) -> dict:
    with sciezka.open(encoding="utf-8") as plik:
        return json.load(plik)


@dataclass(frozen=True)
class Rezerwacja:
    """Rezerwacja zabiegu zapisana w pamięci procesu."""

    confirmation_id: str
    kod_uslugi: str
    data: str
    godzina: str
    gosc: str

    @property
    def klucz_slotu(self) -> str:
        """Klucz zasobu = sama DATA (godzina jest w zbiorze zajętych godzin dnia).

        Model zasobu (świadome ograniczenie PoC): w uzdrowisku jest JEDEN
        gabinet zabiegowy / jeden fizjoterapeuta na daną godzinę, wspólny dla
        wszystkich zabiegów. Dlatego klucz nie zawiera kodu zabiegu — inaczej
        dałoby się sprzedać tę samą osobę dwóm gościom na dwie różne usługi
        o 14:00. Konsekwencja: kalendarz jest celowo bardziej restrykcyjny niż
        realne SPA z kilkoma gabinetami (tam klucz byłby (gabinet, data)).
        """

        return self.data


class SpaStore:
    """Kalendarz SPA: 14-dniowe okno przewijane od dzisiejszej daty + zajęte sloty.

    Zajętość trzymamy jako ``{data_iso: {godzina, ...}}`` — jeden wspólny
    kalendarz zabiegowy, patrz ``Rezerwacja.klucz_slotu``.
    """

    def __init__(self, uslugi: Sequence[Usluga], horyzont_dni: int = 14) -> None:
        self.uslugi = list(uslugi)
        self.horyzont_dni = horyzont_dni
        self._zajete: dict[str, set[str]] = {}
        self._rezerwacje: dict[str, Rezerwacja] = {}

    # ── okno czasowe ────────────────────────────────────────────────────────
    @property
    def dzisiaj(self) -> date:
        return date.today()

    @property
    def ostatni_dzien(self) -> date:
        return self.dzisiaj + timedelta(days=self.horyzont_dni - 1)

    def w_oknie(self, data_iso: str) -> bool:
        try:
            dzien = date.fromisoformat(data_iso)
        except ValueError:
            return False
        return self.dzisiaj <= dzien <= self.ostatni_dzien

    # ── sloty ───────────────────────────────────────────────────────────────
    def sloty_dnia(self, usluga: Usluga, data_iso: str) -> list[str]:
        """Wolne godziny dla zabiegu i dnia (pusta lista gdy brak lub poza oknem)."""
        if not self.w_oknie(data_iso):
            return []
        zajete = self._zajete.get(data_iso, set())
        return [godzina for godzina in usluga.sloty if godzina not in zajete]

    def czy_wolny(self, usluga: Usluga, data_iso: str, godzina: str) -> bool:
        return godzina in self.sloty_dnia(usluga, data_iso)

    def zajmij(self, rezerwacja: Rezerwacja) -> bool:
        """Rezerwuje slot. Zwraca False, jeśli slot jest już zajęty.

        Sprawdzenie i zapis są w jednej sekcji bez ``await``, a klucz jest
        wspólny dla wszystkich zabiegów — drugi gość na tę samą godzinę
        (nawet na inny zabieg) dostaje False.
        """
        klucz = rezerwacja.klucz_slotu
        zajete = self._zajete.setdefault(klucz, set())
        if rezerwacja.godzina in zajete:
            return False
        zajete.add(rezerwacja.godzina)
        self._rezerwacje[rezerwacja.confirmation_id] = rezerwacja
        return True

    def zwolnij(self, confirmation_id: str) -> Rezerwacja | None:
        """Usuwa rezerwację i zwraca jej slot do puli wolnych terminów."""
        rezerwacja = self._rezerwacje.pop(confirmation_id, None)
        if rezerwacja is None:
            return None
        zajete = self._zajete.get(rezerwacja.klucz_slotu)
        if zajete is not None:
            zajete.discard(rezerwacja.godzina)
            if not zajete:
                self._zajete.pop(rezerwacja.klucz_slotu, None)
        return rezerwacja

    def rezerwacja(self, confirmation_id: str) -> Rezerwacja | None:
        return self._rezerwacje.get(confirmation_id)

    def nowy_numer(self) -> str:
        """Unikalny numer potwierdzenia w formacie SPA-XXXX."""
        istniejace = self._rezerwacje.keys()
        for _ in range(1000):
            numer = f"SPA-{random.randint(1000, 9999)}"
            if numer not in istniejace:
                return numer
        return f"SPA-{len(istniejace) + 1000}"

    def reset(self) -> None:
        """Czyści stan (używane w testach)."""
        self._zajete.clear()
        self._rezerwacje.clear()


@dataclass(frozen=True)
class TypPokoju:
    kod: str
    nazwa: str
    cena_za_noc: float
    waluta: str


class KatalogPokoi:
    """Typy pokoi, ceny i terminy zablokowane — wczytywane z data/rooms.json."""

    def __init__(self, sciezka: Path | None = None) -> None:
        dane = _wczytaj_json(sciezka or DATA_DIR / "rooms.json")

        def _cena(wartosc: float) -> float:
            """Ceny całkowite trzymamy jako int, żeby JSON był czytelny (350, nie 350.0)."""
            return int(wartosc) if float(wartosc).is_integer() else float(wartosc)

        self.typy: dict[str, TypPokoju] = {
            kod: TypPokoju(
                kod=kod,
                nazwa=wpis["nazwa"],
                cena_za_noc=_cena(wpis["cena_za_noc"]),
                waluta=wpis.get("waluta", "PLN"),
            )
            for kod, wpis in dane["typy_pokoi"].items()
        }

        self.zablokowane: dict[str, set[str]] = {kod: set() for kod in self.typy}
        # Etykiety blokad trzymamy osobno, żeby opis w odpowiedzi był generowany
        # z danych, a nie przepisywany ręcznie obok nich.
        self.etykiety_blokad: list[str] = []
        self._daty_blokad: set[str] = set()
        for blokada in dane.get("zajete_terminy", []):
            daty = set(blokada.get("daty", []))
            self._daty_blokad.update(daty)
            etykieta = str(blokada.get("opis", "")).strip()
            if daty and etykieta and etykieta not in self.etykiety_blokad:
                self.etykiety_blokad.append(etykieta)
            dotyczy = list(blokada.get("dotyczy") or ()) or self.kody  # brak listy = wszystkie typy
            for kod in dotyczy:
                if kod in self.zablokowane:
                    self.zablokowane[kod].update(daty)

    @property
    def kody(self) -> list[str]:
        return list(self.typy)

    @property
    def nazwy(self) -> list[str]:
        return [typ.nazwa for typ in self.typy.values()]

    def znajdz(self, room_type: str) -> TypPokoju | None:
        """Dopasowuje typ pokoju po kodzie lub nazwie (bez diakrytyków)."""
        zapytanie = normalizuj(room_type)
        if not zapytanie:
            return None
        if zapytanie in self.typy:
            return self.typy[zapytanie]

        kandydaci = [
            typ
            for typ in self.typy.values()
            if zapytanie in normalizuj(typ.nazwa) or normalizuj(typ.kod) in zapytanie
        ]
        return kandydaci[0] if len(kandydaci) == 1 else None

    def daty_zablokowane(self, kod: str) -> set[str]:
        return self.zablokowane.get(kod, set())

    def opis_blokady(self) -> str:
        """Zakres dat blokad GENEROWANY z JSON-a (np. ``28-29.12.2026``).

        Wcześniej ten string był zaszyty w kodzie obok dat z ``rooms.json``,
        więc obie wartości mogły się rozjechać. Teraz jedynym źródłem jest
        pole ``daty`` w pliku.
        """
        return ", ".join(_zakresy_dat(sorted(self._daty_blokad)))

    def etykieta_blokady(self) -> str:
        """Czytelny powód blokady z JSON-a (np. przerwa świąteczno-noworoczna)."""
        return "; ".join(self.etykiety_blokad)


def _zakresy_dat(daty: Sequence[str]) -> list[str]:
    """Skleja kolejne dni w zakresy: ['2026-12-28','2026-12-29'] → ['28-29.12.2026']."""
    dni = sorted(date.fromisoformat(wpis) for wpis in daty)
    zakresy: list[str] = []
    poczatek = poprzedni = None
    for dzien in dni:
        if poczatek is None:
            poczatek = poprzedni = dzien
            continue
        if (dzien - poprzedni).days == 1:
            poprzedni = dzien
            continue
        zakresy.append(_formatuj_zakres(poczatek, poprzedni))
        poczatek = poprzedni = dzien
    if poczatek is not None:
        zakresy.append(_formatuj_zakres(poczatek, poprzedni))
    return zakresy


def _formatuj_zakres(poczatek: date, koniec: date) -> str:
    if poczatek == koniec:
        return f"{poczatek.day:02d}.{poczatek.month:02d}.{poczatek.year}"
    if (poczatek.year, poczatek.month) == (koniec.year, koniec.month):
        return f"{poczatek.day:02d}-{koniec.day:02d}.{koniec.month:02d}.{koniec.year}"
    return (
        f"{poczatek.day:02d}.{poczatek.month:02d}.{poczatek.year}"
        f" – {koniec.day:02d}.{koniec.month:02d}.{koniec.year}"
    )


def daty_pobytu(check_in: str, check_out: str) -> Iterable[str]:
    """Kolejne daty noclegów (bez dnia wymeldowania)."""
    start = date.fromisoformat(check_in)
    noce = (date.fromisoformat(check_out) - start).days
    for przesuniecie in range(max(noce, 0)):
        yield (start + timedelta(days=przesuniecie)).isoformat()
