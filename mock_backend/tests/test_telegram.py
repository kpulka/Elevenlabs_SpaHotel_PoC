"""Telegram helper: success, HTTP error and network error paths (no network: the POST is faked)."""

from __future__ import annotations

import asyncio

import httpx
import pytest

import telegram


@pytest.fixture()
def telegram_on(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:SEKRET-TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")


def _fake_post(monkeypatch, *, status: int | None = None, error: Exception | None = None, sent: list | None = None):
    async def post(self, url, json=None, timeout=None, **_kwargs):  # noqa: A002 - mirrors httpx's signature
        if sent is not None:
            sent.append((url, json))
        if error is not None:
            raise error
        return httpx.Response(status, request=httpx.Request("POST", url))

    monkeypatch.setattr(telegram.httpx.AsyncClient, "post", post)


def test_not_configured_sends_nothing(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    sent: list = []
    _fake_post(monkeypatch, status=200, sent=sent)
    assert telegram.skonfigurowany() is False
    assert asyncio.run(telegram.wyslij_wiadomosc("tekst")) is False
    assert sent == []


def test_success_posts_markdown_to_configured_chat(telegram_on, monkeypatch, capsys):
    sent: list = []
    _fake_post(monkeypatch, status=200, sent=sent)

    assert asyncio.run(telegram.wyslij_wiadomosc("Hej", etykieta="SMS")) is True
    url, payload = sent[0]
    assert url.endswith("/bot123:SEKRET-TOKEN/sendMessage")
    assert payload == {"chat_id": "42", "text": "Hej", "parse_mode": "Markdown"}
    assert "wysłany na Telegram" in capsys.readouterr().out


def test_http_error_returns_false_with_status_only(telegram_on, monkeypatch, capsys):
    _fake_post(monkeypatch, status=401)

    assert asyncio.run(telegram.wyslij_wiadomosc("Hej", etykieta="Alert handoff")) is False
    assert "401" in capsys.readouterr().out


def test_network_error_returns_false_and_never_logs_the_token(telegram_on, monkeypatch, capsys):
    _fake_post(monkeypatch, error=httpx.ConnectError("https://api.telegram.org/bot123:SEKRET-TOKEN"))

    assert asyncio.run(telegram.wyslij_wiadomosc("Hej")) is False
    wyjscie = capsys.readouterr().out
    assert "ConnectError" in wyjscie
    assert "SEKRET-TOKEN" not in wyjscie
