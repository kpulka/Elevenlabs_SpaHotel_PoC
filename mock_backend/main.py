"""
Mock Backend — Wirtualny Recepcjonista AI
Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Cel: Symulacja integracji z systemem PMS (Property Management System)
     oraz obsługa webhooków z agenta ElevenLabs Conversational AI.

Uruchomienie:
    uvicorn main:app --reload --port 8011
"""

from __future__ import annotations

import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import comms, rooms, spa

# Re-eksporty dla zachowania pełnej wstecznej zgodności z modułami testów
# (zapis `X as X` to jawny re-eksport, ruff nie zgłasza go jako nieużywany import)
from state import (
    DEMO_LOGS as DEMO_LOGS,
    NAZWY_USLUG as NAZWY_USLUG,
    POKOJE,
    SPA_STORE as SPA_STORE,
    USLUGI,
    demo_log as demo_log,
)

APP_VERSION = "1.1.0"
START_TIME = time.monotonic()

app = FastAPI(
    title="Mock PMS — Bukowy Dwór",
    description="Mock backendu dla PoC Wirtualnego Recepcjonisty AI (ElevenLabs Agent).",
    version=APP_VERSION,
)

# CORS — domyślnie "*" (webhooki ElevenLabs nie używają ciasteczek). Jeśli podasz
# konkretne originy w CORS_ORIGINS (po przecinku), włączamy credentials, bo
# połączenie "*" + allow_credentials=True jest niezgodne ze specyfikacją CORS.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()] or ["*"]
CORS_WILDCARD = "*" in CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=not CORS_WILDCARD,
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
