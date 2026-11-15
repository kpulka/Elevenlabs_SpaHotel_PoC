"""Logging helpers: masking of personal data (GDPR) and the demo-console / JSON split."""

from __future__ import annotations

import json

import pytest

import config
import logs
from logs import log_demo, log_event, mask_name, mask_phone, redact_phones


@pytest.mark.parametrize(
    "wejscie,oczekiwane",
    [
        ("+48600100200", "********200"),
        ("+48 600 100 200", "********200"),
        ("600-100-200", "******200"),
        ("12", "**"),
        (None, ""),
    ],
)
def test_mask_phone(wejscie, oczekiwane):
    assert mask_phone(wejscie) == oczekiwane


@pytest.mark.parametrize(
    "wejscie,oczekiwane",
    [
        ("Jan Kowalski", "Jan K."),
        ("  anna   maria  nowak ", "anna M. N."),
        ("Jan", "Jan"),
        ("", ""),
        (None, ""),
        ("   ", ""),
    ],
)
def test_mask_name_keeps_first_name_and_initials(wejscie, oczekiwane):
    assert mask_name(wejscie) == oczekiwane


def test_redact_phones_masks_long_numbers_in_free_text():
    tekst = "Proszę oddzwonić na +48 600 100 200 albo 600100299."
    wynik = redact_phones(tekst)
    assert "600" not in wynik and "100" not in wynik
    assert wynik == "Proszę oddzwonić na ********200 albo ******299."


def test_redact_phones_leaves_dates_and_short_numbers_alone():
    tekst = "Termin 2026-11-15 o 14:30, pokój 101, SPA-1001."
    assert redact_phones(tekst) == tekst


def test_redact_phones_handles_empty_input():
    assert redact_phones(None) == ""
    assert redact_phones("") == ""


@pytest.fixture()
def demo_logs(monkeypatch):
    monkeypatch.setattr(config.settings, "log_format", "demo")
    monkeypatch.setattr(config.settings, "demo_logs", True)


@pytest.fixture()
def json_mode(monkeypatch):
    monkeypatch.setattr(config.settings, "log_format", "json")
    monkeypatch.setattr(config.settings, "demo_logs", True)


def test_log_demo_prints_framed_block_in_demo_mode(demo_logs, capsys):
    log_demo("tytuł", "linia 1")
    wyjscie = capsys.readouterr().out.splitlines()
    assert wyjscie == [logs.SEPARATOR, "tytuł", "linia 1", logs.SEPARATOR]


def test_log_demo_is_silent_when_demo_logs_disabled(demo_logs, monkeypatch, capsys):
    monkeypatch.setattr(config.settings, "demo_logs", False)
    log_demo("ukryte")
    assert capsys.readouterr().out == ""


def test_log_demo_never_reaches_json_output(json_mode, capsys):
    log_demo("tylko konsola")
    log_event("zwykle_zdarzenie", klucz="wartosc")
    linie = [json.loads(linia) for linia in capsys.readouterr().out.splitlines()]
    assert [linia["event"] for linia in linie] == ["zwykle_zdarzenie"]


def test_log_event_prefers_demo_text_in_demo_mode(demo_logs, capsys):
    log_event("cokolwiek", demo="   ✅ tekst dla konsoli", pole=1)
    assert capsys.readouterr().out == "   ✅ tekst dla konsoli\n"


def test_warnings_without_demo_text_are_printed_in_demo_mode(demo_logs, capsys):
    log_event("cos_zlego", level=30, powod="test")  # logging.WARNING
    assert capsys.readouterr().out == "   [WARNING] cos_zlego powod=test\n"


def test_info_without_demo_text_is_silent_in_demo_mode(demo_logs, capsys):
    log_event("tylko_json", pole=1)
    assert capsys.readouterr().out == ""


def test_json_line_includes_context_and_drops_none_fields(json_mode, capsys):
    token = logs.set_context(logs.RequestContext(request_id="rid-1", conversation_id="conv-1", tool="t"))
    try:
        log_event("zdarzenie", brak=None, wartosc=2)
    finally:
        logs.reset_context(token)
    linia = json.loads(capsys.readouterr().out)
    assert linia["request_id"] == "rid-1"
    assert linia["conversation_id"] == "conv-1"
    assert linia["tool"] == "t"
    assert linia["wartosc"] == 2
    assert "brak" not in linia


def test_a_failing_formatter_never_breaks_the_caller(json_mode, monkeypatch):
    zgloszone: list = []

    def zepsuty_format(record):
        raise RuntimeError("format error")

    monkeypatch.setattr(logs, "_json_line", zepsuty_format)
    monkeypatch.setattr(logs.AnnaHandler, "handleError", lambda self, record: zgloszone.append(record.getMessage()))
    log_event("zdarzenie_z_bledem")  # must not raise
    assert zgloszone == ["zdarzenie_z_bledem"]
