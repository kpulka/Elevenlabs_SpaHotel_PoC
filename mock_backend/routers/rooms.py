"""Endpointy obsługi dostępności i wyceny pokoi."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from data import POKOJE
from logs import log_demo, log_event
from routers.security import require_webhook_secret
from schemas import SprawdzeniePokoj
from store import daty_pobytu, dzisiaj_warszawa

router = APIRouter(tags=["rooms"], dependencies=[Depends(require_webhook_secret)])


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 5: Sprawdzenie dostępności pokoju
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/check_room_availability")
async def check_room_availability(request: SprawdzeniePokoj):
    """Sprawdza dostępność pokoju i liczy cenę pobytu (cennik z data/rooms.json)."""
    log_demo(
        "🏨 [POKOJE] SPRAWDZENIE DOSTĘPNOŚCI (demo log)",
        f"   Typ pokoju  : {request.room_type}",
        f"   Check-in    : {request.check_in}",
        f"   Check-out   : {request.check_out}",
    )

    typ = POKOJE.znajdz(request.room_type)
    if typ is None:
        log_event(
            "unknown_room_type",
            demo=f"   ⚠️  Nieznany/niejednoznaczny typ pokoju: '{request.room_type}'",
            room_type=request.room_type,
        )
        return {
            "available": False,
            "room_type": request.room_type,
            "available_room_types": POKOJE.kody,
            "available_room_type_names": POKOJE.nazwy,
            "message": (
                f"Typ pokoju '{request.room_type}' nie istnieje lub jest niejednoznaczny. "
                f"Dostępne typy: {', '.join(POKOJE.kody)} "
                f"({'; '.join(POKOJE.nazwy)}). Zapytaj gościa, który typ wybiera."
            ),
        }

    data_in = date.fromisoformat(request.check_in)
    data_out = date.fromisoformat(request.check_out)
    liczba_nocy = (data_out - data_in).days

    if liczba_nocy <= 0:
        return {
            "available": False,
            "room_type": typ.kod,
            "price_per_night": typ.cena_za_noc,
            "check_in": request.check_in,
            "check_out": request.check_out,
            "total_nights": 0,
            "total_price": 0,
            "message": "Data wymeldowania musi być późniejsza niż data zameldowania.",
        }

    if data_in < dzisiaj_warszawa():
        return {
            "available": False,
            "room_type": typ.kod,
            "price_per_night": typ.cena_za_noc,
            "check_in": request.check_in,
            "check_out": request.check_out,
            "total_nights": liczba_nocy,
            "total_price": typ.cena_za_noc * liczba_nocy,
            "message": f"Data zameldowania {request.check_in} jest w przeszłości.",
        }

    cena_calkowita = typ.cena_za_noc * liczba_nocy
    zajete = POKOJE.daty_zablokowane(typ.kod)
    kolizja = sorted(set(daty_pobytu(request.check_in, request.check_out)) & zajete)

    if kolizja:
        log_event(
            "room_blocked",
            demo=f"   ❌ ZAJĘTE — kolizja z blokadą {POKOJE.opis_blokady()}: {', '.join(kolizja)}",
            room_type=typ.kod,
        )
        return {
            "available": False,
            "room_type": typ.kod,
            "price_per_night": typ.cena_za_noc,
            "check_in": request.check_in,
            "check_out": request.check_out,
            "total_nights": liczba_nocy,
            "total_price": cena_calkowita,
            "message": (
                "Brak dostępności w wybranym terminie "
                f"(blokada {POKOJE.opis_blokady()} — {POKOJE.etykieta_blokady()}). "
                "Wszystkie pokoje w tym terminie są zajęte."
            ),
        }

    log_event(
        "room_available",
        demo=(
            f"   ✅ DOSTĘPNY — {liczba_nocy} noc(y) × {typ.cena_za_noc:g} {typ.waluta} "
            f"= {cena_calkowita:g} {typ.waluta} łącznie."
        ),
        room_type=typ.kod,
        total_price=cena_calkowita,
    )
    return {
        "available": True,
        "room_type": typ.kod,
        "price_per_night": typ.cena_za_noc,
        "check_in": request.check_in,
        "check_out": request.check_out,
        "total_nights": liczba_nocy,
        "total_price": cena_calkowita,
        "message": (
            f"Pokój dostępny. Cena: {cena_calkowita:g} {typ.waluta} za {liczba_nocy} noc(y)."
        ),
    }
