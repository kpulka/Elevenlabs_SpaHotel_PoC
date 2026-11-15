"""Shared demo data and the process-wide SPA store singleton.

Services read the singleton as ``data.SPA_STORE`` at call time (never via a copied name), so tests
can swap the store with ``monkeypatch.setattr(data, "SPA_STORE", ...)``.
"""

from __future__ import annotations

from catalog import wczytaj_uslugi
from config import settings
from sqlite_store import SqliteSpaStore
from store import KatalogPokoi, SpaStore

# Dane demo — katalog SPA i pokoje (seed: data/*.json)
USLUGI, _SLOTY_DOMYSLNE, HORYZONT_DNI = wczytaj_uslugi()
POKOJE = KatalogPokoi()


def _zbuduj_magazyn() -> SpaStore:
    """SQLite when ``ANNA_DB_PATH`` is set, otherwise the in-memory store (default, demo and tests)."""
    if settings.db_path == ":memory:":
        return SpaStore(USLUGI, horyzont_dni=HORYZONT_DNI)
    return SqliteSpaStore(settings.db_path, USLUGI, horyzont_dni=HORYZONT_DNI)


SPA_STORE: SpaStore = _zbuduj_magazyn()

NAZWY_USLUG = [usluga.nazwa for usluga in USLUGI]
