"""Katalog zabiegów SPA — jedno źródło prawdy dla nazw, aliasów i godzin.

Dane wczytywane są z ``data/spa_schedule.json`` (seed). Plik nie jest nadpisywany:
stan rezerwacji żyje wyłącznie w pamięci procesu (``store.SpaStore``).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DATA_DIR = Path(__file__).resolve().parent / "data"

# NFKD nie rozkłada polskiego "ł", więc mapujemy je ręcznie.
_TRANSLITERACJA = str.maketrans({"ł": "l", "Ł": "L"})


def normalizuj(tekst: str) -> str:
    """Normalizuje tekst do porównań: małe litery, bez diakrytyków, bez interpunkcji.

    Dzięki temu "Masaż Klasyczny" i "masaz  klasyczny!" trafiają w ten sam wpis.
    """
    obnizony = (tekst or "").translate(_TRANSLITERACJA).strip().lower()
    bez_ogonkow = "".join(
        znak for znak in unicodedata.normalize("NFKD", obnizony) if not unicodedata.combining(znak)
    )
    bez_interpunkcji = re.sub(r"[\"'`.,;:!?()\[\]/\\]", " ", bez_ogonkow)
    return re.sub(r"\s+", " ", bez_interpunkcji).strip()


@dataclass(frozen=True)
class Usluga:
    """Pojedynczy zabieg z katalogu."""

    kod: str
    nazwa: str
    aliasy: tuple[str, ...]
    sloty: tuple[str, ...]

    @property
    def nazwy_do_dopasowania(self) -> tuple[str, ...]:
        return (self.nazwa, *self.aliasy)


@dataclass(frozen=True)
class WynikDopasowania:
    """Rezultat rozpoznania nazwy zabiegu podanej przez agenta."""

    status: str  # "dopasowano" | "niejednoznaczne" | "nieznane"
    usluga: Usluga | None = None
    kandydaci: tuple[Usluga, ...] = ()

    @property
    def dopasowano(self) -> bool:
        return self.status == "dopasowano" and self.usluga is not None


def _wczytaj_seed(sciezka: Path) -> dict:
    with sciezka.open(encoding="utf-8") as plik:
        return json.load(plik)


def wczytaj_uslugi(sciezka: Path | None = None) -> tuple[list[Usluga], list[str], int]:
    """Wczytuje katalog zabiegów, domyślne godziny i horyzont dni z pliku seed."""
    dane = _wczytaj_seed(sciezka or DATA_DIR / "spa_schedule.json")
    domyslne_sloty = list(dane["sloty_domyslne"])
    horyzont = int(dane.get("horyzont_dni", 14))

    uslugi: list[Usluga] = []
    for wpis in dane["zabiegi"]:
        uslugi.append(
            Usluga(
                kod=wpis["kod"],
                nazwa=wpis["nazwa"],
                aliasy=tuple(wpis.get("aliasy", ())),
                sloty=tuple(wpis.get("sloty") or domyslne_sloty),
            )
        )
    return uslugi, domyslne_sloty, horyzont


def _unikalne(uslugi: Iterable[Usluga]) -> tuple[Usluga, ...]:
    widziane: dict[str, Usluga] = {}
    for usluga in uslugi:
        widziane.setdefault(usluga.kod, usluga)
    return tuple(widziane.values())


def dopasuj(uslugi: Sequence[Usluga], zapytanie: str) -> WynikDopasowania:
    """Rozpoznaje zabieg w trzech krokach: dokładnie → alias → podciąg.

    Zwraca ``niejednoznaczne`` gdy podciąg (np. "masaż") pasuje do kilku
    zabiegów — wtedy agent musi dopytać gościa, którego szuka.
    """
    zapytanie_norm = normalizuj(zapytanie)
    if not zapytanie_norm:
        return WynikDopasowania(status="nieznane")

    dokladne = [
        usluga
        for usluga in uslugi
        if zapytanie_norm in (normalizuj(usluga.nazwa), normalizuj(usluga.kod))
    ]
    if len(dokladne) == 1:
        return WynikDopasowania(status="dopasowano", usluga=dokladne[0])

    aliasowe = [
        usluga
        for usluga in uslugi
        if any(zapytanie_norm == normalizuj(alias) for alias in usluga.aliasy)
    ]
    aliasowe = _unikalne(aliasowe)
    if len(aliasowe) == 1:
        return WynikDopasowania(status="dopasowano", usluga=aliasowe[0])
    if len(aliasowe) > 1:
        return WynikDopasowania(status="niejednoznaczne", kandydaci=aliasowe)

    podciagi = _unikalne(
        usluga
        for usluga in uslugi
        if any(
            zapytanie_norm in normalizuj(nazwa) or normalizuj(nazwa) in zapytanie_norm
            for nazwa in usluga.nazwy_do_dopasowania
        )
    )
    if len(podciagi) == 1:
        return WynikDopasowania(status="dopasowano", usluga=podciagi[0])
    if len(podciagi) > 1:
        return WynikDopasowania(status="niejednoznaczne", kandydaci=podciagi)
    return WynikDopasowania(status="nieznane")
