"""Concurrent bookings of one slot, through the real ASGI app, for the in-memory and the SQLite store.

Expected: exactly one booking wins. The requests are fired together with ``asyncio.gather``. The
service layer checks and writes the calendar without an ``await`` in between, so one event loop never
interleaves two bookings; the SQLite UNIQUE index is the second line of defence.

Single-worker constraint: this proves correctness inside ONE process. Multiple uvicorn workers would
each hold their own in-memory calendar (and the service-level check is not transactional across
processes); see ``mock_backend/README.md``.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
from helpers import BOOK, dzien

import data
import main
from data import HORYZONT_DNI, USLUGI
from sqlite_store import SqliteSpaStore
from store import SpaStore

N_CONCURRENT = 20


@pytest.fixture(params=["memory", "sqlite"])
def magazyn(request, tmp_path, monkeypatch):
    if request.param == "memory":
        store = SpaStore(USLUGI, horyzont_dni=HORYZONT_DNI)
    else:
        store = SqliteSpaStore(tmp_path / "concurrency.db", USLUGI, horyzont_dni=HORYZONT_DNI)
    monkeypatch.setattr(data, "SPA_STORE", store)
    yield store
    if isinstance(store, SqliteSpaStore):
        store.close()


async def _rownolegle(payloads: list[dict]) -> list[httpx.Response]:
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as klient:
        return await asyncio.gather(*(klient.post(BOOK, json=payload) for payload in payloads))


def _payload(guest: str, **extra) -> dict:
    return {
        "service_name": "masaż klasyczny",
        "date": dzien(3),
        "time": "14:00",
        "guest_name": guest,
        **extra,
    }


def test_twenty_different_guests_one_slot_exactly_one_success(magazyn):
    payloads = [_payload(f"Gość {i}") for i in range(N_CONCURRENT)]
    odpowiedzi = asyncio.run(_rownolegle(payloads))

    wyniki = [o.json() for o in odpowiedzi]
    assert all(o.status_code == 200 for o in odpowiedzi)
    sukcesy = [w for w in wyniki if w["success"]]
    odmowy = [w for w in wyniki if not w["success"]]
    assert len(sukcesy) == 1
    assert len(odmowy) == N_CONCURRENT - 1
    assert all("zajęty" in w["message"] or "zarezerwowany" in w["message"] for w in odmowy)
    assert magazyn.rezerwacja(sukcesy[0]["confirmation_id"]) is not None
    assert magazyn._zajete_godziny(dzien(3)) == {"14:00"}  # the calendar holds exactly the winner


def test_twenty_identical_retries_share_one_reservation(magazyn):
    payloads = [_payload("Jan Kowalski") for _ in range(N_CONCURRENT)]
    wyniki = [o.json() for o in asyncio.run(_rownolegle(payloads))]

    assert all(w["success"] for w in wyniki)
    assert len({w["confirmation_id"] for w in wyniki}) == 1


def test_twenty_retries_with_one_idempotency_key_share_one_reservation(magazyn):
    payloads = [_payload("Jan Kowalski", idempotency_key="rownolegly-klucz") for _ in range(N_CONCURRENT)]
    wyniki = [o.json() for o in asyncio.run(_rownolegle(payloads))]

    assert all(w["success"] for w in wyniki)
    assert len({w["confirmation_id"] for w in wyniki}) == 1


def test_sqlite_thread_hammering_matches_single_winner(tmp_path):
    """Raw store level: 20 threads race for one slot; the UNIQUE index keeps exactly one row."""
    from concurrent.futures import ThreadPoolExecutor

    from store import Rezerwacja

    store = SqliteSpaStore(tmp_path / "threads.db", USLUGI, horyzont_dni=HORYZONT_DNI)
    try:
        def probuj(i: int) -> bool:
            return store.zajmij(Rezerwacja(f"SPA-R{i}", "k", dzien(3), "09:00", f"G{i}"))

        with ThreadPoolExecutor(max_workers=N_CONCURRENT) as pula:
            assert sum(pula.map(probuj, range(N_CONCURRENT))) == 1
    finally:
        store.close()
