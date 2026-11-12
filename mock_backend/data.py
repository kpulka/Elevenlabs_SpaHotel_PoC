"""Współdzielone dane demo i singletony magazynu dla backendu (PoC)."""

from __future__ import annotations

from catalog import wczytaj_uslugi
from config import settings
from store import KatalogPokoi, SpaStore

SEPARATOR = "=" * 60


def demo_log(*linie: str) -> None:
    """Log demonstracyjny na konsolę — efekt live na prezentacji (nie log strukturalny)."""
    if not settings.demo_logs:
        return
    print(SEPARATOR)
    for linia in linie:
        print(linia)
    print(SEPARATOR)


# Dane demo — katalog SPA i pokoje (seed: data/*.json)
USLUGI, _SLOTY_DOMYSLNE, HORYZONT_DNI = wczytaj_uslugi()
SPA_STORE = SpaStore(USLUGI, horyzont_dni=HORYZONT_DNI)
POKOJE = KatalogPokoi()

NAZWY_USLUG = [usluga.nazwa for usluga in USLUGI]
