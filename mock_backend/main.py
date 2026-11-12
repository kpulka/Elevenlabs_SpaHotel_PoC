"""
Mock Backend — Wirtualny Recepcjonista AI
Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Cel: Symulacja integracji z systemem PMS (Property Management System)
     oraz obsługa webhooków z agenta ElevenLabs Conversational AI.

Uruchomienie:
    uvicorn main:app --reload --port 8011
"""

from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from data import POKOJE, USLUGI
from routers import comms, rooms, spa

APP_VERSION = settings.app_version
START_TIME = time.monotonic()

app = FastAPI(
    title="Mock PMS — Bukowy Dwór",
    description="Mock backendu dla PoC Wirtualnego Recepcjonisty AI (ElevenLabs Agent).",
    version=APP_VERSION,
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

# Podpięcie wydzielonych routerów domenowych
app.include_router(spa.router)
app.include_router(rooms.router)
app.include_router(comms.router)


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTY OPERACYJNE — /health i /
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Szybki health-check dla tunelu, Podmana i monitoringu."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "uptime_seconds": round(time.monotonic() - START_TIME, 3),
    }


@app.get("/")
async def root():
    """Prosty endpoint do weryfikacji działania serwera."""
    return {
        "status": "OK",
        "projekt": "Wirtualny Recepcjonista AI — Bukowy Dwór",
        "wersja": f"{APP_VERSION} (PoC)",
        "endpointy": [
            "GET  /health",
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
