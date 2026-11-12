"""Wspólne fixture testów: czysty stan w pamięci i cisza w konsoli."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main
from state import SPA_STORE


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    """Klient HTTP z wyzerowanym stanem SPA i wyłączonymi logami demo."""
    monkeypatch.setattr(main, "DEMO_LOGS", False)
    main.SPA_STORE.reset()
    with TestClient(main.app) as test_client:
        yield test_client
    main.SPA_STORE.reset()


@pytest.fixture()
def spa_stan():
    """Czysty kalendarz SPA dla testów usług (bez klienta HTTP)."""
    SPA_STORE.reset()
    yield SPA_STORE
    SPA_STORE.reset()
