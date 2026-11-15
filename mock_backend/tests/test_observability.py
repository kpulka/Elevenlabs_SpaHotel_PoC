"""Obserwowalność: X-Request-ID, access log, metryki, błąd 500 bez stack trace i maskowanie telefonu."""

from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient
from helpers import BOOK, SMS, SPA, dzien

import config
import main
import responses
import telegram
from metrics import METRICS

HEX32 = re.compile(r"[0-9a-f]{32}")


@pytest.fixture(autouse=True)
def czyste_metryki():
    METRICS.reset()
    yield
    METRICS.reset()


def _linie_json(capsys) -> list[dict]:
    wynik = []
    for linia in capsys.readouterr().out.splitlines():
        try:
            wynik.append(json.loads(linia))
        except ValueError:
            continue
    return wynik


@pytest.fixture()
def json_logs(monkeypatch):
    monkeypatch.setattr(config.settings, "log_format", "json")
    monkeypatch.setattr(config.settings, "demo_logs", False)


# ── X-Request-ID ────────────────────────────────────────────────────────────

def test_request_id_generowany_gdy_brak_naglowka(client):
    odpowiedz = client.get("/health")
    assert HEX32.fullmatch(odpowiedz.headers["X-Request-ID"])


def test_request_id_przenoszony_od_klienta(client):
    odpowiedz = client.get("/health", headers={"X-Request-ID": "trace-abc.123"})
    assert odpowiedz.headers["X-Request-ID"] == "trace-abc.123"


@pytest.mark.parametrize("zly", ["zla wartosc ze spacjami", "x" * 200, "<script>"])
def test_niebezpieczny_request_id_jest_zastepowany(client, zly):
    odpowiedz = client.get("/health", headers={"X-Request-ID": zly})
    identyfikator = odpowiedz.headers["X-Request-ID"]
    assert identyfikator != zly
    assert HEX32.fullmatch(identyfikator)


def test_request_id_na_odpowiedzi_404(client):
    odpowiedz = client.get("/nie-ma-takiej-sciezki")
    assert odpowiedz.status_code == 404
    assert "X-Request-ID" in odpowiedz.headers


# ── access log ──────────────────────────────────────────────────────────────

def test_access_log_w_formacie_json(client, json_logs, capsys):
    odpowiedz = client.get("/health", headers={"X-Request-ID": "req-42"})
    assert odpowiedz.status_code == 200

    wpisy = [w for w in _linie_json(capsys) if w.get("event") == "http_request"]
    assert len(wpisy) == 1
    wpis = wpisy[0]
    assert wpis["method"] == "GET"
    assert wpis["path"] == "/health"
    assert wpis["status"] == 200
    assert wpis["request_id"] == "req-42"
    assert isinstance(wpis["duration_ms"], float)
    assert wpis["duration_ms"] >= 0


def test_access_log_nie_zawiera_numeru_telefonu(client, json_logs, capsys):
    client.post(SMS, json={"phone_number": "+48600100200", "summary_text": "Test"})
    surowe = capsys.readouterr().out
    assert "+48600100200" not in surowe
    assert "600100200" not in surowe


# ── metryki ─────────────────────────────────────────────────────────────────

def test_metrics_zlicza_zadania_i_bledy_walidacji(client):
    client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)})
    client.post(SPA, json={"service_name": "", "date": "zla-data"})

    trasa = client.get("/metrics").json()["routes"]["/check_spa_availability"]
    assert trasa["requests"] == 2
    assert trasa["errors"]["validation_422"] == 1
    assert trasa["latency_ms"]["samples"] == 2


def test_metrics_liczy_odmowy_biznesowe(client):
    dane = {"service_name": "masaż klasyczny", "date": dzien(3), "time": "14:00", "guest_name": "Jan"}
    client.post(BOOK, json=dane)
    client.post(BOOK, json={**dane, "guest_name": "Anna Nowak"})  # slot zajęty -> HTTP 200, success false

    trasa = client.get("/metrics").json()["routes"]["/book_spa_appointment"]
    assert trasa["requests"] == 2
    assert trasa["business_rejections"] == 1


def test_metrics_nieznana_sciezka_w_jednej_etykiecie(client):
    client.get("/losowa/1")
    client.get("/losowa/2")
    routes = client.get("/metrics").json()["routes"]
    assert routes["unmatched"]["requests"] == 2
    assert not any(klucz.startswith("/losowa") for klucz in routes)


def test_metrics_endpoint_zwraca_json(client):
    odpowiedz = client.get("/metrics")
    assert odpowiedz.status_code == 200
    assert "uptime_seconds" in odpowiedz.json()


# ── błąd nieobsłużony: 500 bez stack trace ──────────────────────────────────

def test_nieobsluzony_wyjatek_daje_json_500_z_request_id(monkeypatch, json_logs, capsys):
    def wybuch(*_args, **_kwargs):
        raise RuntimeError("SEKRET-WEWNETRZNY-1234")

    monkeypatch.setattr(responses, "dostepnosc", wybuch)
    with TestClient(main.app, raise_server_exceptions=False) as klient:
        odpowiedz = klient.post(
            SPA,
            json={"service_name": "masaż klasyczny", "date": dzien(3)},
            headers={"X-Request-ID": "blad-777"},
        )

    assert odpowiedz.status_code == 500
    body = odpowiedz.json()
    assert body["success"] is False
    assert body["request_id"] == "blad-777"
    assert "message" in body
    assert odpowiedz.headers["X-Request-ID"] == "blad-777"
    assert "Traceback" not in odpowiedz.text
    assert "SEKRET-WEWNETRZNY-1234" not in odpowiedz.text

    zdarzenia = {w["event"]: w for w in _linie_json(capsys) if "event" in w}
    assert zdarzenia["unhandled_exception"]["request_id"] == "blad-777"
    assert zdarzenia["unhandled_exception"]["error_type"] == "RuntimeError"
    assert zdarzenia["http_request"]["status"] == 500

    assert METRICS.snapshot()["routes"]["/check_spa_availability"]["errors"]["server_5xx"] == 1


# ── Telegram w tle i maskowanie telefonu (RODO) ─────────────────────────────

def test_sms_wysyla_na_telegram_w_tle_z_zamaskowanym_numerem(client, monkeypatch):
    wyslane: list[tuple[str, str]] = []

    async def falszywy_telegram(tekst: str, etykieta: str = "") -> bool:
        wyslane.append((tekst, etykieta))
        return True

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(telegram, "wyslij_wiadomosc", falszywy_telegram)

    odpowiedz = client.post(SMS, json={"phone_number": "+48600100200", "summary_text": "Potwierdzenie"})

    assert odpowiedz.status_code == 200
    assert odpowiedz.json()["delivered_to"] == "********200"  # maskowany także w odpowiedzi
    assert len(wyslane) == 1
    tekst, etykieta = wyslane[0]
    assert etykieta == "SMS"
    assert "+48600100200" not in tekst
    assert "********200" in tekst


def test_blad_telegrama_nie_psuje_odpowiedzi(client, monkeypatch):
    async def wybuch_sieci(*_args, **_kwargs):
        raise ConnectionError("niedostępny")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TEST")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(telegram.httpx.AsyncClient, "post", wybuch_sieci)

    odpowiedz = client.post(SMS, json={"phone_number": "+48600100200", "summary_text": "Test"})
    assert odpowiedz.status_code == 200
    assert odpowiedz.json()["success"] is True


def test_wyjscie_demo_maskuje_telefon(client, monkeypatch, capsys):
    monkeypatch.setattr(config.settings, "demo_logs", True)
    monkeypatch.setattr(config.settings, "log_format", "demo")
    client.post(SMS, json={"phone_number": "+48600100200", "summary_text": "Test"})
    wyjscie = capsys.readouterr().out
    assert "+48600100200" not in wyjscie
    assert "********200" in wyjscie


# ── conversation_id: korelacja rozmowa → wywołania narzędzi ─────────────────

def test_conversation_id_z_naglowka_trafia_do_logu_i_do_odpowiedzi(client, json_logs, capsys):
    odpowiedz = client.get("/health", headers={"X-Conversation-Id": "conv_abc123"})
    assert odpowiedz.headers["X-Conversation-Id"] == "conv_abc123"

    wpis = [w for w in _linie_json(capsys) if w.get("event") == "http_request"][0]
    assert wpis["conversation_id"] == "conv_abc123"


def test_conversation_id_z_parametru_zapytania(client, json_logs, capsys):
    client.get("/health?conversation_id=conv_q1")
    wpis = [w for w in _linie_json(capsys) if w.get("event") == "http_request"][0]
    assert wpis["conversation_id"] == "conv_q1"


def test_naglowek_ma_pierwszenstwo_przed_parametrem(client, json_logs, capsys):
    client.get("/health?conversation_id=z-query", headers={"X-Conversation-Id": "z-header"})
    wpis = [w for w in _linie_json(capsys) if w.get("event") == "http_request"][0]
    assert wpis["conversation_id"] == "z-header"


@pytest.mark.parametrize("zly", ["<script>", "zla wartosc", "x" * 200])
def test_niebezpieczny_conversation_id_jest_ignorowany(client, json_logs, capsys, zly):
    odpowiedz = client.get("/health", headers={"X-Conversation-Id": zly})
    assert "X-Conversation-Id" not in odpowiedz.headers
    wpis = [w for w in _linie_json(capsys) if w.get("event") == "http_request"][0]
    assert "conversation_id" not in wpis


def test_brak_conversation_id_nie_dodaje_pola(client, json_logs, capsys):
    client.get("/health")
    wpis = [w for w in _linie_json(capsys) if w.get("event") == "http_request"][0]
    assert "conversation_id" not in wpis


def test_conversation_id_obecny_w_logach_narzedzi(client, json_logs, capsys):
    """A tool call's own log lines (here: a business rejection) carry the same conversation id."""
    dane = {"service_name": "masaż klasyczny", "date": dzien(3), "time": "14:00", "guest_name": "Jan"}
    client.post(BOOK, json=dane)
    capsys.readouterr()
    client.post(BOOK, json={**dane, "guest_name": "Anna Nowak"}, headers={"X-Conversation-Id": "conv_xyz"})

    linie = [w for w in _linie_json(capsys) if w.get("request_id")]
    assert linie, "expected JSON log lines for the tool call"
    assert {w.get("conversation_id") for w in linie} == {"conv_xyz"}
    assert any(w.get("event") == "business_rejection" and w.get("tool") == "book_spa_appointment" for w in linie)


def test_conversation_id_w_odpowiedzi_bledu_500(monkeypatch, json_logs, capsys):
    def wybuch(*_args, **_kwargs):
        raise RuntimeError("wewnetrzny")

    monkeypatch.setattr(responses, "dostepnosc", wybuch)
    with TestClient(main.app, raise_server_exceptions=False) as klient:
        klient.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)},
                    headers={"X-Conversation-Id": "conv_500"})
    zdarzenia = {w["event"]: w for w in _linie_json(capsys) if "event" in w}
    assert zdarzenia["unhandled_exception"]["conversation_id"] == "conv_500"
