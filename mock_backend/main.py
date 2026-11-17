"""
Mock Backend — Wirtualny Recepcjonista AI
Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Cel: Symulacja integracji z systemem PMS (Property Management System)
     oraz obsługa webhooków z agenta ElevenLabs Conversational AI.

Uruchomienie:
    uvicorn main:app --reload --port 8011
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.routing import Route

from config import Settings, settings
from data import POKOJE, USLUGI
from logs import log_event
from metrics import METRICS
from middleware import REQUEST_ID_HEADER, ObservabilityMiddleware
from routers import comms, rooms, spa

APP_VERSION = settings.app_version
START_TIME = time.monotonic()

# Known application paths: metric labels. Anything else goes to "unmatched" (cardinality guard).
KNOWN_PATHS: set[str] = set()


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
