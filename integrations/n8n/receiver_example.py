"""Reference receiver for signed Anna events (stdlib only, runnable locally).

Implements the outbound events contract that the Anna backend emits and that the
n8n workflow (``anna_events_workflow.example.json``) verifies in its Code node:

* body      - compact JSON (sorted keys, ``separators=(",", ":")``) with
              ``event_id``, ``event_type``, ``occurred_at``, ``request_id``,
              ``conversation_id`` (or null) and ``data`` (already masked)
* headers   - ``X-Anna-Event-Id``, ``X-Anna-Timestamp`` (unix seconds),
              ``X-Anna-Signature`` = ``"sha256=" + hex(HMAC-SHA256(secret, f"{timestamp}.{body}"))``
* replay    - timestamps further than 300 s from the receiver clock are rejected

The signature covers the RAW bytes that arrived on the wire. Never re-serialize the
JSON before verifying it: the byte sequence is what was signed.

Run locally:

    ANNA_EVENTS_SIGNING_SECRET=change-me python receiver_example.py --port 8787
    ANNA_EVENTS_SIGNING_SECRET=change-me python receiver_example.py --print-sample

Only the standard library is used; the module has no third-party dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import sys
import time
from collections.abc import Callable, Mapping, MutableSet
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOLERANCE_S = 300
MAX_BODY_BYTES = 64 * 1024
SIGNATURE_PREFIX = "sha256="
ENDPOINT_PATH = "/webhook/anna/events"
EVENT_TYPES = frozenset(
    {
        "booking.created",
        "booking.cancelled",
        "booking.rescheduled",
        "handoff.requested",
    }
)
_DIGITS = re.compile(r"[0-9]{1,12}")

log = logging.getLogger("anna_events_receiver")


def sign(secret: str, timestamp: str, body: bytes) -> str:
    """Signature exactly as the emitter computes it: ``sha256=<hex>``."""
    mac = hmac.new(secret.encode("utf-8"), timestamp.encode("ascii") + b"." + body, hashlib.sha256)
    return SIGNATURE_PREFIX + mac.hexdigest()


def verify(
    secret: str,
    timestamp: str | None,
    signature: str | None,
    body: bytes,
    now: int,
    tolerance: int = TOLERANCE_S,
) -> str:
    """Return ``"ok"`` or the reason the request must be rejected.

    Reasons: ``missing_secret``, ``missing_headers``, ``bad_timestamp``,
    ``stale_timestamp``, ``bad_signature``.
    """
    if not secret:
        return "missing_secret"
    if not timestamp or not signature:
        return "missing_headers"
    if not _DIGITS.fullmatch(timestamp):
        return "bad_timestamp"
    if abs(now - int(timestamp)) > tolerance:
        return "stale_timestamp"
    expected = sign(secret, timestamp, body)
    if not hmac.compare_digest(expected.encode("ascii"), signature.encode("utf-8", "replace")):
        return "bad_signature"
    return "ok"


class AnnaEventsReceiver:
    """Transport-free core: takes headers and raw bytes, returns (status, payload)."""

    def __init__(
        self,
        secret: str,
        clock: Callable[[], float] = time.time,
        seen: MutableSet[str] | None = None,
    ) -> None:
        self.secret = secret
        self.clock = clock
        self.seen: MutableSet[str] = set() if seen is None else seen

    def handle(self, headers: Mapping[str, str], body: bytes) -> tuple[int, dict]:
        if len(body) > MAX_BODY_BYTES:
            return 413, {"error": "payload_too_large"}

        reason = verify(
            self.secret,
            headers.get("X-Anna-Timestamp"),
            headers.get("X-Anna-Signature"),
            body,
            now=int(self.clock()),
        )
        if reason != "ok":
            log.warning("rejected event: %s", reason)
            return 401, {"error": "unauthorized"}  # generic body: do not reveal which check failed

        try:
            event = json.loads(body)
        except ValueError:
            return 400, {"error": "invalid_json"}
        if not isinstance(event, dict):
            return 400, {"error": "invalid_event"}

        event_id = event.get("event_id")
        if not isinstance(event_id, str) or headers.get("X-Anna-Event-Id") != event_id:
            return 400, {"error": "event_id_mismatch"}
        if event.get("event_type") not in EVENT_TYPES:
            return 400, {"error": "unknown_event_type"}

        if event_id in self.seen:  # at-least-once delivery: retries are acknowledged, not re-processed
            return 200, {"accepted": True, "duplicate": True, "event_id": event_id}
        self.seen.add(event_id)

        # Real consumer goes here: CRM upsert, calendar update, etc. (see the n8n workflow).
        log.info("accepted %s %s", event["event_type"], event_id)
        return 200, {"accepted": True, "duplicate": False, "event_id": event_id}


def make_server(receiver: AnnaEventsReceiver, host: str = "127.0.0.1", port: int = 8787) -> ThreadingHTTPServer:
    handler = _make_handler(receiver)
    return ThreadingHTTPServer((host, port), handler)


def _make_handler(receiver: AnnaEventsReceiver) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "AnnaEventsReceiver/1.0"

        def do_POST(self) -> None:  # noqa: N802 - stdlib naming
            if self.path != ENDPOINT_PATH:
                self._send(404, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self._send(400, {"error": "bad_content_length"})
                return
            if length > MAX_BODY_BYTES:
                self._send(413, {"error": "payload_too_large"})
                return
            body = self.rfile.read(length)
            status, payload = receiver.handle(self.headers, body)
            self._send(status, payload)

        def _send(self, status: int, payload: dict) -> None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - stdlib signature
            log.debug("%s - %s", self.address_string(), format % args)

    return Handler


def _sample_event() -> tuple[dict[str, str], bytes]:
    """A masked sample event, signed with the current time (for curl tests)."""
    event = {
        "event_id": "evt_sample_0001",
        "event_type": "booking.created",
        "occurred_at": "2026-11-15T10:00:00Z",
        "request_id": "req_sample_0001",
        "conversation_id": None,
        "data": {"confirmation_id": "SPA-1001", "service": "masaz klasyczny", "guest_name": "J*** K*******"},
    }
    body = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    secret = os.environ.get("ANNA_EVENTS_SIGNING_SECRET", "")
    headers = {
        "X-Anna-Event-Id": event["event_id"],
        "X-Anna-Timestamp": timestamp,
        "X-Anna-Signature": sign(secret, timestamp, body),
    }
    return headers, body


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Reference receiver for signed Anna events.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--print-sample", action="store_true", help="print a signed sample request and exit")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    secret = os.environ.get("ANNA_EVENTS_SIGNING_SECRET", "")

    if args.print_sample:
        headers, body = _sample_event()
        for name, value in headers.items():
            print(f"{name}: {value}")
        print(body.decode("utf-8"))
        return 0

    if not secret:
        print("ANNA_EVENTS_SIGNING_SECRET is not set; refusing to start (fail-closed).", file=sys.stderr)
        return 2

    server = make_server(AnnaEventsReceiver(secret), args.host, args.port)
    print(f"Listening on http://{args.host}:{args.port}{ENDPOINT_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
