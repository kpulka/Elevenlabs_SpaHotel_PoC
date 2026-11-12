"""Endpointy obsługi zabiegów SPA (dostępność, rezerwacja, anulacja, zmiana terminu).

Router robi tylko transport: walidację (Pydantic w ``schemas``) → usługa (``services.spa``)
→ mapowanie na odpowiedź (``responses``).
"""

from __future__ import annotations

from fastapi import APIRouter

import responses
from schemas import (
    AnulowanieSPA,
    PrzelozenieSPA,
    RezerwacjaSPA,
    ZapytanieSPA,
)
from services import spa

router = APIRouter(tags=["spa"])


@router.post("/check_spa_availability")
async def check_spa_availability(request: ZapytanieSPA):
    """Sprawdza dostępność zabiegu SPA dla podanego dnia (symulacja zapytania do PMS)."""
    wynik = spa.sprawdz_dostepnosc(request.service_name, request.date)
    return responses.dostepnosc(request, wynik)


@router.post("/book_spa_appointment")
async def book_spa_appointment(request: RezerwacjaSPA):
    """Rezerwuje zabieg SPA i zajmuje slot w kalendarzu (stan w pamięci procesu)."""
    wynik = spa.zarezerwuj(request.service_name, request.date, request.time, request.guest_name)
    return responses.rezerwacja(request, wynik)


@router.post("/cancel_spa_appointment")
async def cancel_spa_appointment(request: AnulowanieSPA):
    """Anuluje rezerwację i zwalnia slot.

    Reguła opłat (docs/elevenlabs_agent_procedures.md):
    - >2h przed terminem: bezpłatnie,
    - <2h: 50% opłaty,
    - zwolnienie medyczne: zawsze bezpłatnie.
    ``fee`` pozostaje UŁAMKIEM (0.0 / 0.5) dla zgodności z agentem;
    ``free_of_charge`` i ``fee_rule`` mówią wprost, która reguła zadziałała.
    """
    wynik = spa.anuluj_rezerwacje(
        request.confirmation_id,
        bool(request.medical_release),
        request.appointment_datetime,
    )
    return responses.anulowanie(request, wynik)


@router.post("/reschedule_spa_appointment")
async def reschedule_spa_appointment(request: PrzelozenieSPA):
    """Przenosi rezerwację na nowy termin: stary slot wraca do puli, nowy zostaje zajęty."""
    wynik = spa.przenies_rezerwacje(
        request.confirmation_id,
        request.service_name,
        request.new_date,
        request.new_time,
        request.guest_name,
    )
    return responses.przelozenie(request, wynik)
