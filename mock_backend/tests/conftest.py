"""Wspólne fixture testów: czysty stan w pamięci i cisza w konsoli."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    """Klient HTTP z wyzerowanym stanem SPA i wyłączonymi logami demo."""
    monkeypatch.setattr(main, "DEMO_LOGS", False)
    main.SPA_STORE.reset()
    with TestClient(main.app) as test_client:
        yield test_client
    main.SPA_STORE.reset()
