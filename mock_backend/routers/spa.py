"""Endpointy obsługi zabiegów SPA (dostępność, rezerwacja, anulacja, zmiana terminu).

Router robi tylko transport: walidację (Pydantic w ``schemas``) → usługa (``services.spa``)
→ mapowanie na odpowiedź (``responses``) → zdarzenie wychodzące (``events``, po odpowiedzi).
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends

import events
import responses
from routers.security import require_webhook_secret
from schemas import (
    AnulowanieSPA,
    PrzelozenieSPA,
    RezerwacjaSPA,
    ZapytanieSPA,
)
from services import spa
from services.spa import Potwierdzenie, Przeniesienie, WynikAnulowania

router = APIRouter(tags=["spa"], dependencies=[Depends(require_webhook_secret)])


@router.post("/check_spa_availability")
async def check_spa_availability(request: ZapytanieSPA):
    """Sprawdza dostępność zabiegu SPA dla podanego dnia (symulacja zapytania do PMS)."""
    wynik = spa.sprawdz_dostepnosc(request.service_name, request.date)
    return responses.dostepnosc(request, wynik)


@router.post("/book_spa_appointment")
async def book_spa_appointment(request: RezerwacjaSPA, background: BackgroundTasks):
    """Rezerwuje zabieg SPA i zajmuje slot w kalendarzu (stan w SQLite lub pamięci procesu)."""
    wynik = spa.zarezerwuj(
        request.service_name,
        request.date,
        request.time,
        request.guest_name,
        idempotency_key=request.idempotency_key,
    )
    # Ponowienie tej samej rezerwacji (idempotencja) nie tworzy drugiego zdarzenia.
    if isinstance(wynik, Potwierdzenie) and wynik.nowa:
        events.schedule(background, "booking.created", _dane_rezerwacji(wynik))
    return responses.rezerwacja(request, wynik)


@router.post("/cancel_spa_appointment")
async def cancel_spa_appointment(request: AnulowanieSPA, background: BackgroundTasks):
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
    if wynik.znaleziona and wynik.oplata is not None:
        events.schedule(background, "booking.cancelled", _dane_anulowania(request.confirmation_id, wynik))
    return responses.anulowanie(request, wynik)


@router.post("/reschedule_spa_appointment")
async def reschedule_spa_appointment(request: PrzelozenieSPA, background: BackgroundTasks):
    """Przenosi rezerwację na nowy termin: stary slot wraca do puli, nowy zostaje zajęty."""
    wynik = spa.przenies_rezerwacje(
        request.confirmation_id,
        request.service_name,
        request.new_date,
        request.new_time,
        request.guest_name,
    )
    if isinstance(wynik, Przeniesienie):
        events.schedule(background, "booking.rescheduled", _dane_przeniesienia(wynik))
    return responses.przelozenie(request, wynik)


# ─────────────────────────────────────────────────────────────────────────────
# Dane zdarzeń wychodzących (kontrakt: events.py)
# ─────────────────────────────────────────────────────────────────────────────

def _dane_rezerwacji(wynik: Potwierdzenie) -> dict:
    rezerwacja = wynik.rezerwacja
    return {
        "confirmation_id": rezerwacja.confirmation_id,
        "service_code": wynik.usluga.kod,
        "service_name": wynik.usluga.nazwa,
        "date": rezerwacja.data,
        "time": rezerwacja.godzina,
        "guest_name": rezerwacja.gosc,
    }


def _dane_anulowania(numer: str, wynik: WynikAnulowania) -> dict:
    oplata = wynik.oplata
    assert oplata is not None, "zdarzenie anulowania wymaga obliczonej opłaty"
    return {
        "confirmation_id": numer,
        "fee": oplata.ulamek,
        "free_of_charge": oplata.ulamek == 0.0,
        "fee_rule": oplata.regula.value,
    }


def _dane_przeniesienia(wynik: Przeniesienie) -> dict:
    nowa = wynik.nowa
    return {
        "previous_confirmation_id": wynik.stara_numer,
        "confirmation_id": nowa.confirmation_id,
        "service_code": wynik.usluga.kod,
        "service_name": wynik.usluga.nazwa,
        "new_date": nowa.data,
        "new_time": nowa.godzina,
        "guest_name": nowa.gosc,
    }
