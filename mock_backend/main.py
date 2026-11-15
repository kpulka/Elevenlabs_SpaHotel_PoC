"""
Mock Backend — Wirtualny Recepcjonista AI
Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Cel: Symulacja integracji z systemem PMS (Property Management System)
     oraz obsługa webhooków z agenta ElevenLabs Conversational AI.

Uruchomienie:
    uvicorn main:app --reload --port 8011
"""

from __future__ import annotations

import json
import logging
import re
import time
import traceback
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.datastructures import MutableHeaders
from starlette.routing import Route
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from config import Settings, settings
from data import POKOJE, USLUGI
from logs import RequestContext, log_event, reset_context, set_context
from metrics import METRICS
from routers import comms, rooms, spa

APP_VERSION = settings.app_version
START_TIME = time.monotonic()

REQUEST_ID_HEADER = "X-Request-ID"
CONVERSATION_HEADER = "X-Conversation-Id"
CONVERSATION_QUERY_PARAM = "conversation_id"
# Identifiers from the client/proxy are accepted only in this safe format (also used for conversation ids).
_SAFE_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}")
# Known application paths: metric labels. Anything else goes to "unmatched" (cardinality guard).
KNOWN_PATHS: set[str] = set()


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


async def _unhandled_error(request: Request, _error: Exception) -> JSONResponse:
    """500 response without a stack trace; the client gets a request id to quote in a bug report."""
    request_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Wewnętrzny błąd serwera. Podaj request_id przy zgłoszeniu.",
            "request_id": request_id,
        },
        headers={REQUEST_ID_HEADER: request_id},
    )


def check_startup_config(cfg: Settings) -> None:
    """Fail-closed in production, loud warnings in development.

    ``ANNA_ENV=prod`` refuses to start without ``ANNA_WEBHOOK_SECRET`` (tool webhooks would be open),
    and refuses to send events to a URL without a signing secret (events would be unsigned).
    """
    if cfg.is_prod:
        if not cfg.webhook_secret:
            raise RuntimeError(
                "ANNA_ENV=prod requires ANNA_WEBHOOK_SECRET; refusing to start with webhook auth disabled."
            )
        if cfg.events_webhook_url and not cfg.events_signing_secret:
            raise RuntimeError(
                "ANNA_EVENTS_WEBHOOK_URL is set but ANNA_EVENTS_SIGNING_SECRET is empty; "
                "refusing to start, because events must be signed in prod."
            )
        return
    if not cfg.webhook_secret:
        log_event(
            "webhook_auth_disabled",
            level=logging.WARNING,
            demo=(
                "   [WARNING] ANNA_WEBHOOK_SECRET nie ustawiony — uwierzytelnianie webhooków "
                "WYŁĄCZONE (tryb demo). Nie wystawiaj tak backendu na zewnątrz."
            ),
        )
    if cfg.events_webhook_url and not cfg.events_signing_secret:
        log_event(
            "events_disabled_no_secret",
            level=logging.WARNING,
            demo="   [WARNING] ANNA_EVENTS_WEBHOOK_URL bez ANNA_EVENTS_SIGNING_SECRET — zdarzenia wyłączone.",
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    check_startup_config(settings)
    yield


app = FastAPI(
    title="Mock PMS — Bukowy Dwór",
    description="Mock backendu dla PoC Wirtualnego Recepcjonisty AI (ElevenLabs Agent).",
    version=APP_VERSION,
    lifespan=lifespan,
)

# CORS — domyślnie "*" (webhooki ElevenLabs nie używają ciasteczek). Jeśli podasz
# konkretne originy w CORS_ORIGINS (po przecinku), włączamy credentials, bo
# połączenie "*" + allow_credentials=True jest niezgodne ze specyfikacją CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not settings.cors_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Added last = outermost: it also wraps CORS and 500 responses.
app.add_middleware(ObservabilityMiddleware, known_paths=KNOWN_PATHS)
app.add_exception_handler(Exception, _unhandled_error)

app.include_router(spa.router)
app.include_router(rooms.router)
app.include_router(comms.router)


# ─────────────────────────────────────────────────────────────────────────────
# OPERATIONAL ENDPOINTS — /health, /metrics and /
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Szybki health-check dla tunelu, Podmana i monitoringu."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "uptime_seconds": round(time.monotonic() - START_TIME, 3),
    }


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Metryki procesu w JSON: liczba żądań, błędy (401/422/5xx), odmowy biznesowe, p50/p95."""
    return METRICS.snapshot()


@app.get("/")
async def root():
    """Prosty endpoint do weryfikacji działania serwera."""
    return {
        "status": "OK",
        "projekt": "Wirtualny Recepcjonista AI — Bukowy Dwór",
        "wersja": f"{APP_VERSION} (PoC)",
        "endpointy": [
            "GET  /health",
            "GET  /metrics",
            "POST /check_spa_availability",
            "POST /book_spa_appointment",
            "POST /cancel_spa_appointment",
            "POST /reschedule_spa_appointment",
            "POST /check_room_availability",
            "POST /send_sms_summary",
            "POST /transfer_to_simulated_handoff",
        ],
        "catalog": {
            "uslugi": [
                {
                    "kod": u.kod,
                    "nazwa": u.nazwa,
                    "sloty": list(u.sloty),
                    "price_pln": u.cena_pln,
                    "duration_min": u.czas_min,
                }
                for u in USLUGI
            ],
            "pokoje": [
                {"kod": t.kod, "nazwa": t.nazwa, "cena_za_noc": t.cena_za_noc}
                for t in POKOJE.typy.values()
            ],
        },
        "docs": "http://localhost:8011/docs",
    }


KNOWN_PATHS.update(route.path for route in app.routes if isinstance(route, (APIRoute, Route)))
