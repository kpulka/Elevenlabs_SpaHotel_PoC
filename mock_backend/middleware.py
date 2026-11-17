"""Pure ASGI middleware: request/conversation ids, access log (JSON or demo), metrics, 500 logging.

Extracted from ``main.py`` so the application module is wiring only. The middleware sits
outside routing and CORS, so every response (including preflight and 500) carries
``X-Request-ID`` and is counted in the metrics.

``main.ObservabilityMiddleware`` moved here; see ``logs.py`` for the context that makes
lines written deep inside a handler correlate with the request that caused them.
"""

from __future__ import annotations

import json
import logging
import re
import time
import traceback
import uuid
from urllib.parse import parse_qs

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from logs import RequestContext, log_event, reset_context, set_context
from metrics import METRICS

REQUEST_ID_HEADER = "X-Request-ID"
CONVERSATION_HEADER = "X-Conversation-Id"
CONVERSATION_QUERY_PARAM = "conversation_id"
# Identifiers from the client/proxy are accepted only in this safe format (also used for conversation ids).
_SAFE_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}")


def _header(scope: Scope, name: bytes) -> str | None:
    for header_name, value in scope.get("headers", []):
        if header_name == name:
            return value.decode("latin-1")
    return None


def _safe_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    candidate = raw.strip()
    return candidate if _SAFE_ID_PATTERN.fullmatch(candidate) else None


def _incoming_request_id(scope: Scope) -> str | None:
    return _safe_id(_header(scope, b"x-request-id"))


def _incoming_conversation_id(scope: Scope) -> str | None:
    """Conversation id from the ``X-Conversation-Id`` header, else from the ``conversation_id`` query parameter."""
    from_header = _safe_id(_header(scope, b"x-conversation-id"))
    if from_header is not None:
        return from_header
    query = parse_qs(scope.get("query_string", b"").decode("latin-1"))
    return _safe_id(query.get(CONVERSATION_QUERY_PARAM, [None])[0])


def _is_business_rejection(body: bytes) -> bool:
    """HTTP 200 with ``success: false`` is a business rejection (e.g. the slot is taken)."""
    try:
        data = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return False
    return isinstance(data, dict) and data.get("success") is False


class ObservabilityMiddleware:
    """Pure ASGI middleware: request and conversation ids, access log (JSON or demo), metrics, and 500 logging.

    It sits outside routing and CORS, so every response (including preflight and 500) carries
    ``X-Request-ID`` and is counted in the metrics. It buffers nothing except a short JSON 200 body,
    which it inspects to detect business rejections.
    """

    def __init__(self, app: ASGIApp, known_paths: set[str]) -> None:
        self.app = app
        self.known_paths = known_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _incoming_request_id(scope) or uuid.uuid4().hex
        conversation_id = _incoming_conversation_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id
        path: str = scope.get("path", "")
        method: str = scope.get("method", "")
        tool = path.lstrip("/") if method == "POST" and path in self.known_paths else None
        token = set_context(RequestContext(request_id=request_id, conversation_id=conversation_id, tool=tool))

        started = time.perf_counter()
        status = 500  # overwritten by the status of the response
        track_body = False
        body = bytearray()

        async def send_with_headers(message: Message) -> None:
            nonlocal status, track_body
            if message["type"] == "http.response.start":
                status = int(message["status"])
                headers = MutableHeaders(scope=message)
                headers[REQUEST_ID_HEADER] = request_id
                if conversation_id:
                    headers[CONVERSATION_HEADER] = conversation_id
                track_body = status == 200 and headers.get("content-type", "").startswith("application/json")
            elif message["type"] == "http.response.body" and track_body:
                body.extend(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception as error:
            status = 500
            log_event(
                "unhandled_exception",
                level=logging.ERROR,
                demo=f"   [ERROR] Nieobsłużony błąd {type(error).__name__} (request_id={request_id})",
                error_type=type(error).__name__,
                traceback=traceback.format_exc(),
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            rejected = status == 200 and track_body and _is_business_rejection(bytes(body))
            METRICS.observe(
                path if path in self.known_paths else "unmatched",
                status,
                duration_ms,
                rejected=rejected,
            )
            log_event(
                "http_request",
                method=method,
                path=path,
                status=status,
                duration_ms=duration_ms,
                request_id=request_id,
            )
            reset_context(token)
