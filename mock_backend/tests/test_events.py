"""Outbound integration events: signing contract, delivery (retry, dead letter), payload hygiene.

Offline: ``httpx.MockTransport`` replaces the network and the retry pause is a no-op, so the suite
makes no HTTP calls and takes no time.

Signing test vector (other services can reuse it to check their verifier)::

    secret    = "whsec_test_vector_0123"
    timestamp = "1767225600"
    body      = b'{"data":{"confirmation_id":"SPA-1001"},"event_id":"6f1c2b9e-0d4a-4c8e-9a51-2b7d3e4f5a6b",'
                b'"event_type":"booking.created"}'
    header    = "sha256=e228d9d329e6d9898c0c0820487e48cff1279de3fc9468ca097ef1455672c7da"
"""

from __future__ import annotations

import json

import httpx
import pytest
from helpers import BOOK, CANCEL, HANDOFF, RESCHEDULE, dzien

import config
import events
from metrics import METRICS

VECTOR_SECRET = "whsec_test_vector_0123"
VECTOR_TIMESTAMP = "1767225600"
VECTOR_BODY = (
    b'{"data":{"confirmation_id":"SPA-1001"},"event_id":"6f1c2b9e-0d4a-4c8e-9a51-2b7d3e4f5a6b",'
    b'"event_type":"booking.created"}'
)
VECTOR_SIGNATURE = "sha256=e228d9d329e6d9898c0c0820487e48cff1279de3fc9468ca097ef1455672c7da"

URL = "https://receiver.test/anna/events"
SECRET = "whsec_delivery_test"


# ── signing contract (pure functions) ───────────────────────────────────────

def test_sign_matches_documented_test_vector():
    assert events.sign(VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY) == VECTOR_SIGNATURE


def test_verify_accepts_test_vector_inside_window():
    assert events.verify(VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY, VECTOR_SIGNATURE, now=1767225610)


def test_verify_replay_window_boundaries():
    sent_at = int(VECTOR_TIMESTAMP)
    assert events.verify(VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY, VECTOR_SIGNATURE, now=sent_at + 300)
    assert not events.verify(VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY, VECTOR_SIGNATURE, now=sent_at + 301)
    assert not events.verify(VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY, VECTOR_SIGNATURE, now=sent_at - 301)


@pytest.mark.parametrize(
    "secret,timestamp,body,signature",
    [
        ("inny-sekret", VECTOR_TIMESTAMP, VECTOR_BODY, VECTOR_SIGNATURE),  # wrong key
        (VECTOR_SECRET, "1767225601", VECTOR_BODY, VECTOR_SIGNATURE),  # timestamp is part of the MAC
        (VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY + b" ", VECTOR_SIGNATURE),  # one byte changed
        (VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY, VECTOR_SIGNATURE.replace("sha256=", "sha1=")),
        (VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY, "sha256=zzz"),
        (VECTOR_SECRET, "", VECTOR_BODY, VECTOR_SIGNATURE),  # missing header
        (VECTOR_SECRET, VECTOR_TIMESTAMP, VECTOR_BODY, ""),  # missing header
        ("", VECTOR_TIMESTAMP, VECTOR_BODY, VECTOR_SIGNATURE),  # no secret configured: fail closed
        (VECTOR_SECRET, "12a", VECTOR_BODY, VECTOR_SIGNATURE),  # not a decimal timestamp
        (VECTOR_SECRET, "١٢٣", VECTOR_BODY, VECTOR_SIGNATURE),  # non-ASCII digits are not accepted
    ],
)
def test_verify_rejects_bad_inputs(secret, timestamp, body, signature):
    assert not events.verify(secret, timestamp, body, signature, now=int(VECTOR_TIMESTAMP))


def test_encode_body_is_compact_sorted_and_utf8():
    envelope = events.build_envelope(
        "handoff.requested", {"zeta": "ż", "alfa": 1}, request_id="r1", conversation_id=None
    )
    body = events.encode_body(envelope)
    assert body == json.dumps(envelope, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")
    assert b" " not in body  # no pretty-print whitespace
    assert '"zeta":"ż"'.encode("utf-8") in body


def test_build_envelope_rejects_unknown_event_type():
    with pytest.raises(ValueError):
        events.build_envelope("booking.exploded", {}, request_id=None, conversation_id=None)


# ── delivery: fixtures ──────────────────────────────────────────────────────

class Receiver:
    """Scripted HTTP receiver: each entry of ``script`` is a status code, or "error" for a transport error."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.script: list[int | str] = []
        self.pauses: list[float] = []  # retry pauses requested by the emitter

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        step = self.script.pop(0) if self.script else 200
        if step == "error":
            raise httpx.ConnectError("receiver unreachable", request=request)
        return httpx.Response(int(step), json={"ok": True})


@pytest.fixture()
def receiver(monkeypatch) -> Receiver:
    rec = Receiver()

    async def fake_sleep(delay: float) -> None:
        rec.pauses.append(delay)

    monkeypatch.setattr(config.settings, "events_webhook_url", URL)
    monkeypatch.setattr(config.settings, "events_signing_secret", SECRET)
    monkeypatch.setattr(events, "_transport", httpx.MockTransport(rec.handle))
    monkeypatch.setattr(events, "_sleep", fake_sleep)
    return rec


@pytest.fixture(autouse=True)
def czyste_metryki():
    METRICS.reset()
    yield
    METRICS.reset()


def _dane_rezerwacji(**zmiany):
    bazowe = {"service_name": "masaż klasyczny", "date": dzien(3), "time": "14:00", "guest_name": "Jan Kowalski"}
    return {**bazowe, **zmiany}


def _zdarzenia(receiver: Receiver) -> list[dict]:
    return [json.loads(req.content) for req in receiver.requests]


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


# ── delivery: envelope, headers and signature ───────────────────────────────

def test_booking_created_is_delivered_with_verifiable_signature(client, receiver):
    odpowiedz = client.post(
        BOOK,
        json=_dane_rezerwacji(),
        headers={"X-Request-ID": "req-evt-1", "X-Conversation-Id": "conv_abc123"},
    )
    assert odpowiedz.status_code == 200 and odpowiedz.json()["success"] is True

    assert len(receiver.requests) == 1
    wyslane = receiver.requests[0]
    assert wyslane.method == "POST"
    assert wyslane.headers["content-type"] == "application/json"
    event_id = wyslane.headers["X-Anna-Event-Id"]
    timestamp = wyslane.headers["X-Anna-Timestamp"]
    signature = wyslane.headers["X-Anna-Signature"]
    assert events.verify(SECRET, timestamp, wyslane.content, signature)

    envelope = json.loads(wyslane.content)
    assert envelope["event_id"] == event_id
    assert envelope["event_type"] == "booking.created"
    assert envelope["request_id"] == "req-evt-1"
    assert envelope["conversation_id"] == "conv_abc123"
    assert envelope["occurred_at"].endswith("Z")
    assert envelope["data"]["confirmation_id"] == odpowiedz.json()["confirmation_id"]
    assert envelope["data"]["service_name"] == "masaż klasyczny"
    assert wyslane.content == events.encode_body(envelope)  # the bytes that were signed are canonical


def test_idempotent_replay_does_not_emit_a_second_event(client, receiver):
    client.post(BOOK, json=_dane_rezerwacji(idempotency_key="evt-key-1"))
    retry = client.post(BOOK, json=_dane_rezerwacji(idempotency_key="evt-key-1")).json()
    assert retry["success"] is True
    assert len(receiver.requests) == 1


def test_rejected_booking_emits_nothing(client, receiver):
    client.post(BOOK, json=_dane_rezerwacji())
    client.post(BOOK, json=_dane_rezerwacji(guest_name="Anna Nowak"))  # slot taken
    assert [e["event_type"] for e in _zdarzenia(receiver)] == ["booking.created"]


def test_cancellation_and_reschedule_emit_events(client, receiver):
    booked = client.post(BOOK, json=_dane_rezerwacji()).json()
    moved = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": booked["confirmation_id"],
            "service_name": "masaż klasyczny",
            "new_date": dzien(4),
            "new_time": "15:00",
        },
    ).json()
    client.post(CANCEL, json={"confirmation_id": moved["confirmation_id"], "medical_release": True})

    typy = [e["event_type"] for e in _zdarzenia(receiver)]
    assert typy == ["booking.created", "booking.rescheduled", "booking.cancelled"]
    przeniesienie = _zdarzenia(receiver)[1]["data"]
    assert przeniesienie["previous_confirmation_id"] == booked["confirmation_id"]
    assert przeniesienie["confirmation_id"] == moved["confirmation_id"]
    anulowanie = _zdarzenia(receiver)[2]["data"]
    assert anulowanie == {
        "confirmation_id": moved["confirmation_id"],
        "fee": 0.0,
        "free_of_charge": True,
        "fee_rule": "medyczna",
    }


def test_handoff_event_masks_phone_and_guest_name(client, receiver):
    client.post(
        HANDOFF,
        json={
            "department": "dyzurka_medyczna",
            "reason": "Proszę oddzwonić na +48 600 100 200",
            "guest_name": "Jan Kowalski",
            "language": "pl",
        },
    )
    surowe = receiver.requests[0].content.decode("utf-8")
    envelope = json.loads(surowe)
    assert envelope["event_type"] == "handoff.requested"
    assert envelope["data"]["guest_name"] == "Jan K."
    assert envelope["data"]["reason"] == "Proszę oddzwonić na ********200"
    for raw in ("600 100 200", "600100200", "+48600100200", "Jan Kowalski"):
        assert raw not in surowe


# ── delivery: retry, dead letter, failure isolation ─────────────────────────

def test_retry_then_success(client, receiver):
    receiver.script = [503, 200]
    odpowiedz = client.post(BOOK, json=_dane_rezerwacji())
    assert odpowiedz.json()["success"] is True  # the tool call is unaffected

    assert len(receiver.requests) == 2
    assert receiver.pauses == [0.5]  # backoff before the second attempt
    for req in receiver.requests:
        assert events.verify(SECRET, req.headers["X-Anna-Timestamp"], req.content, req.headers["X-Anna-Signature"])
    assert receiver.requests[0].content == receiver.requests[1].content  # same event, same body
    assert receiver.requests[0].headers["X-Anna-Event-Id"] == receiver.requests[1].headers["X-Anna-Event-Id"]

    counters = METRICS.snapshot()["counters"]
    assert counters["events.delivered"] == 1
    assert "events.failed" not in counters


def test_dead_letter_after_three_attempts(client, receiver, json_logs, capsys):
    receiver.script = [500, 500, 500]
    odpowiedz = client.post(BOOK, json=_dane_rezerwacji())
    assert odpowiedz.status_code == 200 and odpowiedz.json()["success"] is True

    assert len(receiver.requests) == 3
    assert receiver.pauses == [0.5, 1.0]
    counters = METRICS.snapshot()["counters"]
    assert counters["events.failed"] == 1
    assert "events.delivered" not in counters

    dead = [w for w in _linie_json(capsys) if w.get("event") == "events.dead_letter"]
    assert len(dead) == 1
    assert dead[0]["level"] == "error"
    assert dead[0]["attempts"] == 3
    assert dead[0]["event_type"] == "booking.created"
    assert dead[0]["reason"] == "HTTP 500"


def test_transport_errors_are_retried_and_never_fail_the_call(client, receiver):
    receiver.script = ["error", "error", "error"]
    odpowiedz = client.post(BOOK, json=_dane_rezerwacji())
    assert odpowiedz.status_code == 200 and odpowiedz.json()["success"] is True
    assert len(receiver.requests) == 3
    assert METRICS.snapshot()["counters"]["events.failed"] == 1


def test_disabled_when_url_is_empty(client, receiver, monkeypatch):
    monkeypatch.setattr(config.settings, "events_webhook_url", "")
    odpowiedz = client.post(BOOK, json=_dane_rezerwacji())
    assert odpowiedz.json()["success"] is True
    assert receiver.requests == []


def test_disabled_without_signing_secret(client, receiver, monkeypatch):
    monkeypatch.setattr(config.settings, "events_signing_secret", "")
    client.post(BOOK, json=_dane_rezerwacji())
    assert receiver.requests == []


def test_schedule_returns_none_when_disabled(monkeypatch):
    from fastapi import BackgroundTasks

    monkeypatch.setattr(config.settings, "events_webhook_url", "")
    assert events.schedule(BackgroundTasks(), "booking.created", {}) is None


def test_deliver_returns_false_when_not_configured(monkeypatch):
    import asyncio

    monkeypatch.setattr(config.settings, "events_webhook_url", "")
    assert asyncio.run(events.deliver("id", "booking.created", b"{}")) is False


def test_payload_redaction_walks_lists_and_nested_objects():
    envelope = events.build_envelope(
        "handoff.requested",
        {
            "notatki": ["zadzwoń 600 100 299", ("+48 601 602 603",)],
            "zagniezdzone": {"pole": "ok 2026-11-15"},
            "liczba": 7,
        },
        request_id=None,
        conversation_id=None,
    )
    surowe = json.dumps(envelope)
    assert "600 100 299" not in surowe and "601 602 603" not in surowe
    assert envelope["data"]["notatki"][0] == "zadzwoń ******299"
    assert envelope["data"]["zagniezdzone"] == {"pole": "ok 2026-11-15"}  # dates are not phone numbers
    assert envelope["data"]["liczba"] == 7
