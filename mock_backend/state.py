"""Współdzielony stan i dane demo dla backendu (PoC)."""

from __future__ import annotations

import os
from catalog import wczytaj_uslugi
from store import KatalogPokoi, SpaStore

SEPARATOR = "=" * 60

DEMO_LOGS = os.getenv("ANNA_DEMO_LOGS", "1").strip().lower() not in {"0", "false", "no", "off"}


def demo_log(*linie: str) -> None:
    """Log demonstracyjny na konsolę — efekt live na prezentacji (nie log strukturalny)."""
    # Sprawdzamy dynamicznie z main jeśli podmienione w testach
    import sys
    main_mod = sys.modules.get("main")
    active = getattr(main_mod, "DEMO_LOGS", DEMO_LOGS) if main_mod else DEMO_LOGS
    if not active:
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


def wolne_sloty(usluga, data_iso: str) -> list[str]:
    return SPA_STORE.sloty_dnia(usluga, data_iso)


def cennik(usluga) -> dict:
    """Cena i czas zabiegu wprost z katalogu — te same liczby mówi Anna na głos."""
    return {"price_pln": usluga.cena_pln, "duration_min": usluga.czas_min}


def poza_oknem(data_iso: str) -> str:
    return (
        f"Termin {data_iso} jest poza oknem rezerwacji "
        f"({SPA_STORE.dzisiaj.isoformat()} – {SPA_STORE.ostatni_dzien.isoformat()})."
    )
