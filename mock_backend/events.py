"""Outbound integration events (CRM / automation, e.g. n8n) and the shared HMAC signature.

Contract (receivers rely on it; keep ``README.md`` and ``integrations/`` in sync):

* ``POST`` to ``ANNA_EVENTS_WEBHOOK_URL`` with ``Content-Type: application/json``.
* Body: compact JSON (sorted keys, no whitespace, UTF-8) of::

      {"event_id": "<uuid4>", "event_type": "<type>", "occurred_at": "<ISO 8601 UTC>",
       "request_id": "...", "conversation_id": "..." | null, "data": {...}}

  ``event_type`` is one of ``EVENT_TYPES``. ``data`` never carries a raw phone number.
* Headers:

  - ``X-Anna-Event-Id``: the ``event_id``;
  - ``X-Anna-Timestamp``: unix time in seconds, as a decimal string;
  - ``X-Anna-Signature``: ``sha256=<hex>`` where ``hex = HMAC-SHA256(key=ANNA_EVENTS_SIGNING_SECRET,
    msg=f"{timestamp}.{body}")`` over the exact bytes sent (see ``sign``).

* Delivery: after the response, up to ``MAX_ATTEMPTS`` attempts with a pause before each retry.
  Every attempt has a fresh timestamp and signature; the body and ``event_id`` do not change, so a
  receiver de-duplicates by ``event_id``. Failure never fails the tool call; a final failure is
  logged as ``events.dead_letter``.
* Disabled unless BOTH the URL and the signing secret are set.

The same ``sign``/``verify`` pair protects inbound tool calls (``routers/security.py``, HMAC mode)
with ``ANNA_WEBHOOK_SECRET``.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import BackgroundTasks

from config import settings
from logs import current_context, log_event, redact_phones
from metrics import METRICS

EVENT_TYPES = frozenset({"booking.created", "booking.cancelled", "booking.rescheduled", "handoff.requested"})

HEADER_EVENT_ID = "X-Anna-Event-Id"
HEADER_TIMESTAMP = "X-Anna-Timestamp"
HEADER_SIGNATURE = "X-Anna-Signature"
SIGNATURE_PREFIX = "sha256="
DEFAULT_TOLERANCE_S = 300  # replay window for verify()

MAX_ATTEMPTS = 3
# Pause before attempt 2 and before attempt 3 (exponential). Must hold MAX_ATTEMPTS - 1 values.
RETRY_DELAYS_S: tuple[float, ...] = (0.5, 1.0)
DELIVERY_TIMEOUT_S = 5.0

# Test seams: tests replace the sleep with a no-op and the HTTP transport with httpx.MockTransport.
_sleep = asyncio.sleep
_transport: httpx.AsyncBaseTransport | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Signature (pure functions)
# ─────────────────────────────────────────────────────────────────────────────

def sign(secret: str, timestamp: str, body: bytes) -> str:
    """Returns the ``X-Anna-Signature`` header value: ``sha256=<hex>`` over ``f"{timestamp}.{body}"``."""
    message = f"{timestamp}.".encode("ascii") + body
    return SIGNATURE_PREFIX + hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify(
    secret: str,
    timestamp: str,
    body: bytes,
    signature: str,
    tolerance_s: int = DEFAULT_TOLERANCE_S,
    now: float | None = None,
) -> bool:
    """True when ``signature`` matches ``body`` and ``timestamp`` is within ``tolerance_s`` of now.

    Fails closed: an empty secret, a missing header, a non-numeric timestamp, a stale timestamp or a
    mismatch all return False. The comparison is constant-time.
    """
    if not (secret and timestamp and signature):
        return False
    if not (timestamp.isascii() and timestamp.isdigit()):
        return False
    current = time.time() if now is None else now
    if abs(current - int(timestamp)) > tolerance_s:
        return False
    expected = sign(secret, timestamp, body).encode("ascii")
    return hmac.compare_digest(expected, signature.encode("utf-8"))


# ─────────────────────────────────────────────────────────────────────────────
# Envelope and scheduling
# ─────────────────────────────────────────────────────────────────────────────

def _redact_strings(value: Any) -> Any:
    """Defence in depth: masks phone-like runs in every string of the payload."""
    if isinstance(value, str):
        return redact_phones(value)
    if isinstance(value, Mapping):
        return {key: _redact_strings(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_redact_strings(item) for item in value]
    return value


def build_envelope(
    event_type: str,
    data: Mapping[str, Any],
    *,
    request_id: str | None,
    conversation_id: str | None,
) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unknown event type: {event_type!r}")
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "occurred_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "request_id": request_id,
        "conversation_id": conversation_id,
        "data": _redact_strings(dict(data)),
    }


def encode_body(envelope: Mapping[str, Any]) -> bytes:
    """The exact bytes that are signed and sent (compact, sorted keys, UTF-8)."""
    return json.dumps(envelope, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")


def is_enabled() -> bool:
    return settings.events_enabled


def schedule(background: BackgroundTasks, event_type: str, data: Mapping[str, Any]) -> str | None:
    """Queues one event for delivery after the response. Returns its ``event_id``, or None when disabled.

    The request and conversation ids are captured now, while the request context is still set.
    """
    if not is_enabled():
        return None
    context = current_context()
    envelope = build_envelope(
        event_type,
        data,
        request_id=context.request_id if context else None,
        conversation_id=context.conversation_id if context else None,
    )
    background.add_task(deliver, envelope["event_id"], event_type, encode_body(envelope))
    return envelope["event_id"]


async def deliver(event_id: str, event_type: str, body: bytes) -> bool:
    """POSTs one encoded event with retries. Never raises; returns True when a 2xx was received."""
    url = settings.events_webhook_url
    secret = settings.events_signing_secret
    if not (url and secret):
        return False

    failure = "unknown"
    async with httpx.AsyncClient(transport=_transport, timeout=DELIVERY_TIMEOUT_S) as klient:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            timestamp = str(int(time.time()))
            headers = {
                "Content-Type": "application/json",
                HEADER_EVENT_ID: event_id,
                HEADER_TIMESTAMP: timestamp,
                HEADER_SIGNATURE: sign(secret, timestamp, body),
            }
            try:
                odpowiedz = await klient.post(url, content=body, headers=headers)
            except Exception as blad:  # a delivery problem must never reach the tool call
                # Only the exception type: httpx messages can echo the URL.
                failure = type(blad).__name__
            else:
                if odpowiedz.is_success:
                    METRICS.increment("events.delivered")
                    log_event("events.delivered", event_id=event_id, event_type=event_type, attempt=attempt)
                    return True
                failure = f"HTTP {odpowiedz.status_code}"

            log_event(
                "events.attempt_failed",
                level=logging.WARNING,
                event_id=event_id,
                event_type=event_type,
                attempt=attempt,
                reason=failure,
            )
            if attempt < MAX_ATTEMPTS:
                await _sleep(RETRY_DELAYS_S[attempt - 1])

    METRICS.increment("events.failed")
    log_event(
        "events.dead_letter",
        level=logging.ERROR,
        event_id=event_id,
        event_type=event_type,
        attempts=MAX_ATTEMPTS,
        reason=failure,
    )
    return False
