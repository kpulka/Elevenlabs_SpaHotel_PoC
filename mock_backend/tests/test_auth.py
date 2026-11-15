"""Uwierzytelnianie webhooków: X-Webhook-Secret (hmac.compare_digest), tryb HMAC i fail-closed w prod."""

from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient
from helpers import BOOK, CANCEL, HANDOFF, RESCHEDULE, ROOM, SMS, SPA, dzien

import config
import events
import main

SECRET = "tajny-sekret-123"
TOOL_POSTS = [SPA, BOOK, CANCEL, RESCHEDULE, ROOM, SMS, HANDOFF]


@pytest.fixture()
def secured(client, monkeypatch) -> TestClient:
    monkeypatch.setattr(config.settings, "webhook_secret", SECRET)
    return client


@pytest.mark.parametrize("sciezka", TOOL_POSTS)
def test_brak_sekretu_daje_401_gdy_auth_wlaczony(secured, sciezka):
    odpowiedz = secured.post(sciezka, json={})
    assert odpowiedz.status_code == 401


@pytest.mark.parametrize("sciezka", TOOL_POSTS)
def test_zly_sekret_daje_401(secured, sciezka):
    odpowiedz = secured.post(sciezka, json={}, headers={"X-Webhook-Secret": "zly"})
    assert odpowiedz.status_code == 401


@pytest.mark.parametrize("sciezka", TOOL_POSTS)
def test_poprawny_sekret_przechodzi_do_walidacji(secured, sciezka):
    # Auth przepuszcza żądanie: pusty body to 422 (wymagane pola) albo 200 (handoff bez pól wymaganych).
    odpowiedz = secured.post(sciezka, json={}, headers={"X-Webhook-Secret": SECRET})
    assert odpowiedz.status_code != 401


def test_poprawny_sekret_zwraca_normalna_odpowiedz(secured):
    odpowiedz = secured.post(
        SPA,
        json={"service_name": "masaż klasyczny", "date": "2999-01-01"},
        headers={"X-Webhook-Secret": SECRET},
    )
    assert odpowiedz.status_code == 200
    assert odpowiedz.json()["service_name"] == "masaż klasyczny"


def test_401_nie_zdradza_sekretu(secured):
    odpowiedz = secured.post(SPA, json={}, headers={"X-Webhook-Secret": "zly"})
    assert SECRET not in odpowiedz.text


@pytest.mark.parametrize("sciezka", ["/health", "/metrics", "/", "/openapi.json", "/docs"])
def test_endpointy_operacyjne_bez_sekretu_dzialaja(secured, sciezka):
    assert secured.get(sciezka).status_code == 200


def test_bez_sekretu_w_konfiguracji_auth_wylaczone(client, monkeypatch):
    monkeypatch.setattr(config.settings, "webhook_secret", "")
    odpowiedz = client.post(SPA, json={"service_name": "masaż klasyczny", "date": "2999-01-01"})
    assert odpowiedz.status_code == 200


def test_ostrzezenie_przy_starcie_gdy_auth_wylaczone(monkeypatch, capsys):
    monkeypatch.setattr(config.settings, "webhook_secret", "")
    monkeypatch.setattr(config.settings, "demo_logs", True)
    monkeypatch.setattr(config.settings, "log_format", "demo")
    with TestClient(main.app):
        pass
    assert "WYŁĄCZONE" in capsys.readouterr().out


def test_brak_ostrzezenia_gdy_sekret_ustawiony(monkeypatch, capsys):
    monkeypatch.setattr(config.settings, "webhook_secret", SECRET)
    monkeypatch.setattr(config.settings, "demo_logs", True)
    monkeypatch.setattr(config.settings, "log_format", "demo")
    with TestClient(main.app):
        pass
    assert "WYŁĄCZONE" not in capsys.readouterr().out


# ── ANNA_ENV=prod: fail-closed startup ──────────────────────────────────────

def test_prod_refuses_to_start_without_webhook_secret(monkeypatch):
    monkeypatch.setattr(config.settings, "env", "prod")
    monkeypatch.setattr(config.settings, "webhook_secret", "")
    with pytest.raises(RuntimeError, match="ANNA_WEBHOOK_SECRET"):
        with TestClient(main.app):
            pass


def test_prod_starts_with_webhook_secret(monkeypatch, capsys):
    monkeypatch.setattr(config.settings, "env", "prod")
    monkeypatch.setattr(config.settings, "webhook_secret", SECRET)
    monkeypatch.setattr(config.settings, "events_webhook_url", "")
    with TestClient(main.app) as klient:
        assert klient.get("/health").status_code == 200


def test_prod_refuses_events_url_without_signing_secret(monkeypatch):
    monkeypatch.setattr(config.settings, "env", "prod")
    monkeypatch.setattr(config.settings, "webhook_secret", SECRET)
    monkeypatch.setattr(config.settings, "events_webhook_url", "https://crm.example.test/hook")
    monkeypatch.setattr(config.settings, "events_signing_secret", "")
    with pytest.raises(RuntimeError, match="ANNA_EVENTS_SIGNING_SECRET"):
        with TestClient(main.app):
            pass


def test_dev_warns_when_events_url_has_no_signing_secret(monkeypatch, capsys):
    monkeypatch.setattr(config.settings, "env", "dev")
    monkeypatch.setattr(config.settings, "webhook_secret", SECRET)
    monkeypatch.setattr(config.settings, "events_webhook_url", "https://crm.example.test/hook")
    monkeypatch.setattr(config.settings, "events_signing_secret", "")
    monkeypatch.setattr(config.settings, "demo_logs", True)
    monkeypatch.setattr(config.settings, "log_format", "demo")
    with TestClient(main.app):
        pass
    assert "zdarzenia wyłączone" in capsys.readouterr().out


def test_env_parsing(monkeypatch):
    monkeypatch.delenv("ANNA_ENV", raising=False)
    assert config.Settings.from_env().env == "dev"
    monkeypatch.setenv("ANNA_ENV", " PROD ")
    assert config.Settings.from_env().env == "prod"
    assert config.Settings.from_env().is_prod is True
    monkeypatch.setenv("ANNA_ENV", "staging")
    with pytest.raises(ValueError, match="ANNA_ENV"):
        config.Settings.from_env()


# ── HMAC mode: X-Anna-Signature + X-Anna-Timestamp ──────────────────────────

def _podpisane(body: bytes, *, ts: str | None = None, secret: str = SECRET, extra: dict | None = None) -> dict:
    znacznik = ts if ts is not None else str(int(time.time()))
    naglowki = {
        "Content-Type": "application/json",
        "X-Anna-Timestamp": znacznik,
        "X-Anna-Signature": events.sign(secret, znacznik, body),
    }
    naglowki.update(extra or {})
    return naglowki


def _cialo(**zmiany) -> bytes:
    dane = {"service_name": "masaż klasyczny", "date": dzien(3), **zmiany}
    return json.dumps(dane, ensure_ascii=False).encode("utf-8")


def test_hmac_signed_request_is_accepted(secured):
    body = _cialo()
    odpowiedz = secured.post(SPA, content=body, headers=_podpisane(body))
    assert odpowiedz.status_code == 200
    assert odpowiedz.json()["service_name"] == "masaż klasyczny"


def test_hmac_wrong_signature_is_rejected(secured):
    body = _cialo()
    naglowki = _podpisane(body, secret="inny-sekret")
    assert secured.post(SPA, content=body, headers=naglowki).status_code == 401


def test_hmac_signature_bound_to_body(secured):
    podpisane = _cialo(service_name="masaż klasyczny")
    inne = _cialo(service_name="masaż leczniczy")
    assert secured.post(SPA, content=inne, headers=_podpisane(podpisane)).status_code == 401


def test_hmac_stale_timestamp_is_rejected(secured):
    body = _cialo()
    stary = str(int(time.time()) - 400)  # outside the 300 s replay window
    assert secured.post(SPA, content=body, headers=_podpisane(body, ts=stary)).status_code == 401


def test_hmac_signature_without_timestamp_is_rejected(secured):
    body = _cialo()
    naglowki = {"Content-Type": "application/json", "X-Anna-Signature": events.sign(SECRET, "1", body)}
    assert secured.post(SPA, content=body, headers=naglowki).status_code == 401


def test_timestamp_without_signature_is_rejected(secured):
    body = _cialo()
    naglowki = {"Content-Type": "application/json", "X-Anna-Timestamp": str(int(time.time()))}
    assert secured.post(SPA, content=body, headers=naglowki).status_code == 401


def test_hmac_headers_take_precedence_over_shared_secret(secured):
    # Once signature headers are sent, only the HMAC is checked; a valid X-Webhook-Secret does not rescue it.
    body = _cialo()
    naglowki = _podpisane(body, secret="zly", extra={"X-Webhook-Secret": SECRET})
    assert secured.post(SPA, content=body, headers=naglowki).status_code == 401


def test_hmac_signed_booking_reads_body_once(secured):
    body = json.dumps(
        {"service_name": "masaż klasyczny", "date": dzien(3), "time": "14:00", "guest_name": "Jan Kowalski"}
    ).encode("utf-8")
    odpowiedz = secured.post(BOOK, content=body, headers=_podpisane(body))
    assert odpowiedz.status_code == 200 and odpowiedz.json()["success"] is True
