"""Endpointy obsługi zabiegów SPA (dostępność, rezerwacja, anulacja, zmiana terminu)."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter

from catalog import dopasuj
from schemas import (
    AnulowanieSPA,
    PrzelozenieSPA,
    RezerwacjaSPA,
    ZapytanieSPA,
)
from state import (
    NAZWY_USLUG,
    SPA_STORE,
    USLUGI,
    cennik,
    demo_log,
    poza_oknem,
    wolne_sloty,
)
from store import Rezerwacja

router = APIRouter(tags=["spa"])


def _zagubiony_zabieg(zapytanie: str, data_iso: str, wynik) -> dict:
    """Odpowiedź 200 dla nieznanego / niejednoznacznego zabiegu (agent ma dopytać)."""
    if wynik.status == "niejednoznaczne":
        nazwy = [kandydat.nazwa for kandydat in wynik.kandydaci]
        return {
            "available": False,
            "slots": [],
            "service_name": zapytanie,
            "date": data_iso,
            "ambiguous": nazwy,
            "available_services": NAZWY_USLUG,
            "message": (
                f"'{zapytanie}' może oznaczać kilka zabiegów: {', '.join(nazwy)}. "
                "Dopytaj gościa, który z nich wybiera."
            ),
        }
    return {
        "available": False,
        "slots": [],
        "service_name": zapytanie,
        "date": data_iso,
        "available_services": NAZWY_USLUG,
        "message": f"Zabieg '{zapytanie}' nie jest oferowany w naszym SPA.",
    }


def _oplata_anulowania(
    medical_release: bool, appointment_datetime: str | None, is_en: bool
) -> tuple[float, str]:
    """Reguła opłat: >2h = 0, <2h = 50%, zwolnienie medyczne = zawsze 0.

    Zwraca (ułamek opłaty, opis reguły w języku gościa).
    """
    if medical_release:
        return 0.0, (
            "Medical release — free of charge (0%)."
            if is_en
            else "Zwolnienie medyczne — anulacja bezpłatna (0%)."
        )
    if appointment_datetime is None:
        return 0.5, (
            "Appointment time unknown (no appointment_datetime) — 50% fee applied."
            if is_en
            else "Brak godziny zabiegu (appointment_datetime) — przyjęto opłatę 50%."
        )

    termin = datetime.fromisoformat(appointment_datetime)
    if termin.tzinfo is not None:
        termin = termin.astimezone().replace(tzinfo=None)
    godziny_przed = (termin - datetime.now()).total_seconds() / 3600

    if godziny_przed > 2:
        return 0.0, (
            "Cancelled more than 2h before the appointment — free of charge (0%)."
            if is_en
            else "Anulacja ponad 2h przed zabiegiem — bezpłatna (0%)."
        )
    if is_en:
        return 0.5, "Cancelled less than 2h before the appointment — 50% fee applies."
    return 0.5, "Anulacja poniżej 2h przed zabiegiem — obowiązuje opłata 50%."


def _odmowa_rezerwacji(request: RezerwacjaSPA, message: str, **extra) -> dict:
    print(f"   ❌ {message}")
    return {
        "success": False,
        "confirmation_id": None,
        "service_name": request.service_name,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
        "message": message,
        **extra,
    }


def _odmowa_przelozenia(
    request: PrzelozenieSPA, stara: Rezerwacja | None, is_en: bool, message: str, **extra
) -> dict:
    print(f"   ❌ {message}")
    return {
        "success": False,
        "confirmation_id": request.confirmation_id,
        "service_name": request.service_name,
        "new_date": request.new_date,
        "new_time": request.new_time,
        "guest_name": request.guest_name or (stara.gosc if stara else ""),
        "found": stara is not None,
        "message": message,
        "note": "Appointment was not changed." if is_en else "Termin nie został zmieniony.",
        **extra,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 1: Sprawdzenie dostępności zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/check_spa_availability")
async def check_spa_availability(request: ZapytanieSPA):
    """Sprawdza dostępność zabiegu SPA dla podanego dnia (symulacja zapytania do PMS)."""
    wynik = dopasuj(USLUGI, request.service_name)
    demo_log(
        "📅 [SPA] SPRAWDZENIE DOSTĘPNOŚCI (demo log)",
        f"   Zabieg : {request.service_name}",
        f"   Data   : {request.date}",
    )

    if not wynik.dopasowano:
        print(f"   ⚠️  Zabieg '{request.service_name}' — status: {wynik.status}")
        return _zagubiony_zabieg(request.service_name, request.date, wynik)

    usluga = wynik.usluga
    ceny = cennik(usluga)
    if date.fromisoformat(request.date) < SPA_STORE.dzisiaj:
        return {
            "available": False,
            "slots": [],
            "service_name": usluga.nazwa,
            "date": request.date,
            "available_services": NAZWY_USLUG,
            "message": f"Data {request.date} jest w przeszłości — nie można sprawdzić terminu.",
            **ceny,
        }

    if not SPA_STORE.w_oknie(request.date):
        return {
            "available": False,
            "slots": [],
            "service_name": usluga.nazwa,
            "date": request.date,
            "available_services": NAZWY_USLUG,
            "message": poza_oknem(request.date),
            **ceny,
        }

    sloty = wolne_sloty(usluga, request.date)
    if sloty:
        print(f"   ✅ Dostępne sloty: {', '.join(sloty)}")
        return {
            "available": True,
            "slots": sloty,
            "service_name": usluga.nazwa,
            "date": request.date,
            "available_services": NAZWY_USLUG,
            "message": (
                f"Zabieg '{usluga.nazwa}' dostępny w dniu {request.date}. "
                f"Wolne godziny: {', '.join(sloty)}. "
                f"Cena {usluga.cena_pln} PLN, czas trwania {usluga.czas_min} min."
            ),
            **ceny,
        }

    print(f"   ❌ Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}.")
    return {
        "available": False,
        "slots": [],
        "service_name": usluga.nazwa,
        "date": request.date,
        "available_services": NAZWY_USLUG,
        "message": f"Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}.",
        **ceny,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2: Rezerwacja zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/book_spa_appointment")
async def book_spa_appointment(request: RezerwacjaSPA):
    """Rezerwuje zabieg SPA i zajmuje slot w kalendarzu (stan w pamięci procesu)."""
    wynik = dopasuj(USLUGI, request.service_name)
    demo_log(
        "✍️  [SPA] NOWA REZERWACJA ZABIEGU (demo log)",
        f"   Gość    : {request.guest_name}",
        f"   Zabieg  : {request.service_name}",
        f"   Termin  : {request.date} {request.time}",
    )

    if not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            nazwy = [kandydat.nazwa for kandydat in wynik.kandydaci]
            return _odmowa_rezerwacji(
                request,
                f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}. "
                "Dopytaj gościa, który z nich wybiera.",
                ambiguous=nazwy,
                available_services=NAZWY_USLUG,
            )
        return _odmowa_rezerwacji(
            request,
            f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            available_services=NAZWY_USLUG,
        )

    usluga = wynik.usluga
    if date.fromisoformat(request.date) < SPA_STORE.dzisiaj:
        return _odmowa_rezerwacji(
            request, f"Data {request.date} jest w przeszłości — nie można zarezerwować terminu."
        )

    if not SPA_STORE.w_oknie(request.date):
        return _odmowa_rezerwacji(request, poza_oknem(request.date))

    wolne = wolne_sloty(usluga, request.date)
    if request.time not in usluga.sloty:
        return _odmowa_rezerwacji(
            request,
            f"Godzina {request.time} nie jest w grafiku zabiegu '{usluga.nazwa}'.",
            slots=wolne,
        )
    if request.time not in wolne:
        return _odmowa_rezerwacji(
            request,
            f"Termin {request.date} {request.time} jest już zajęty. "
            f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
            slots=wolne,
        )

    # Odczyt i zapis stanu bez `await` — w jednym event loopie operacja jest atomowa.
    rezerwacja = Rezerwacja(
        confirmation_id=SPA_STORE.nowy_numer(),
        kod_uslugi=usluga.kod,
        data=request.date,
        godzina=request.time,
        gosc=request.guest_name,
    )
    if not SPA_STORE.zajmij(rezerwacja):
        pozostale = wolne_sloty(usluga, request.date)
        return _odmowa_rezerwacji(
            request,
            f"Termin {request.date} {request.time} został właśnie zarezerwowany. "
            f"Wolne godziny: {', '.join(pozostale) or 'brak'}.",
            slots=pozostale,
        )

    print(f"   ✅ Potwierdzenie: {rezerwacja.confirmation_id}")
    return {
        "success": True,
        "confirmation_id": rezerwacja.confirmation_id,
        "service_name": usluga.nazwa,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
        "message": f"Rezerwacja potwierdzona. Numer: {rezerwacja.confirmation_id}.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 3: Anulowanie rezerwacji zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

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
    is_en = request.language == "en"
    rezerwacja = SPA_STORE.rezerwacja(request.confirmation_id)
    appointment_datetime = request.appointment_datetime

    if rezerwacja is None:
        print(f"   ❌ Nie znaleziono rezerwacji '{request.confirmation_id}' — nie anulowano.")
        return {
            "success": False,
            "confirmation_id": request.confirmation_id,
            "cancelled": False,
            "fee": 0.0,
            "medical_release": bool(request.medical_release),
            "free_of_charge": True,
            "fee_rule": (
                "Reservation not found — no fee charged (0%)."
                if is_en
                else "Nie znaleziono rezerwacji — nie naliczono opłaty (0%)."
            ),
            "found": False,
            "message": (
                f"No reservation found with number {request.confirmation_id}. "
                "Ask the guest to re-check the confirmation number."
                if is_en
                else f"Nie znaleziono rezerwacji o numerze {request.confirmation_id}. "
                "Poproś gościa o ponowne sprawdzenie numeru potwierdzenia."
            ),
            "note": "Reservation was not cancelled." if is_en else "Rezerwacja nie została anulowana.",
        }

    oplata, regula = _oplata_anulowania(
        bool(request.medical_release), appointment_datetime, is_en
    )
    bezplatna = oplata == 0.0

    zwolniona = SPA_STORE.zwolnij(request.confirmation_id)

    demo_log(
        "🗑️  [SPA] ANULOWANIE REZERWACJI (demo log)",
        f"   ID Potwierdzenia : {request.confirmation_id}",
        f"   Powód            : {request.reason or '-'}",
        f"   Termin zabiegu   : {appointment_datetime or 'nieznany'}",
        f"   Zwolnienie med.  : {'TAK' if request.medical_release else 'NIE'}",
        f"   Reguła           : {regula}",
        f"   Slot zwolniony   : {'TAK' if zwolniona else 'nie (brak w pamięci)'}",
    )

    if is_en:
        notatka = "Free of charge." if bezplatna else "Cancellation fee applies (50% of the service price)."
    else:
        notatka = "Bezpłatna." if bezplatna else "Obowiązuje opłata 50% ceny zabiegu."

    return {
        "success": True,
        "confirmation_id": request.confirmation_id,
        "cancelled": True,
        "fee": oplata,
        "medical_release": bool(request.medical_release),
        "free_of_charge": bezplatna,
        "fee_rule": regula,
        "found": True,
        "message": "Reservation cancelled." if is_en else "Rezerwacja anulowana.",
        "note": notatka,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 4: Zmiana terminu zabiegu SPA (reschedule)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/reschedule_spa_appointment")
async def reschedule_spa_appointment(request: PrzelozenieSPA):
    """Przenosi rezerwację na nowy termin: stary slot wraca do puli, nowy zostaje zajęty."""
    is_en = request.language == "en"
    wynik = dopasuj(USLUGI, request.service_name)
    stara = SPA_STORE.rezerwacja(request.confirmation_id)

    if stara is None:
        return _odmowa_przelozenia(
            request,
            stara,
            is_en,
            f"No reservation found with number {request.confirmation_id}. "
            "Ask the guest to re-check the number, or book a new appointment."
            if is_en
            else f"Nie znaleziono rezerwacji o numerze {request.confirmation_id}. "
            "Poproś gościa o sprawdzenie numeru albo zarezerwuj nowy termin.",
            available_services=NAZWY_USLUG,
        )

    if not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            nazwy = [kandydat.nazwa for kandydat in wynik.kandydaci]
            return _odmowa_przelozenia(
                request,
                stara,
                is_en,
                f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}.",
                ambiguous=nazwy,
            )
        return _odmowa_przelozenia(
            request, stara, is_en, f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA."
        )

    usluga = wynik.usluga
    if date.fromisoformat(request.new_date) < SPA_STORE.dzisiaj:
        return _odmowa_przelozenia(request, stara, is_en, f"Data {request.new_date} jest w przeszłości.")
    if not SPA_STORE.w_oknie(request.new_date):
        return _odmowa_przelozenia(request, stara, is_en, poza_oknem(request.new_date))
    if request.new_time not in usluga.sloty:
        return _odmowa_przelozenia(
            request, stara, is_en, f"Godzina {request.new_time} nie jest w grafiku zabiegu '{usluga.nazwa}'."
        )

    wolne = wolne_sloty(usluga, request.new_date)
    if request.new_time not in wolne:
        return _odmowa_przelozenia(
            request,
            stara,
            is_en,
            f"Termin {request.new_date} {request.new_time} jest zajęty. "
            f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
            slots=wolne,
        )

    # Zwolnienie starego i zajęcie nowego slotu — sekcja bez `await`, więc atomowa.
    SPA_STORE.zwolnij(request.confirmation_id)
    nowa = Rezerwacja(
        confirmation_id=SPA_STORE.nowy_numer(),
        kod_uslugi=usluga.kod,
        data=request.new_date,
        godzina=request.new_time,
        gosc=request.guest_name or stara.gosc,
    )
    if not SPA_STORE.zajmij(nowa):
        SPA_STORE.zajmij(stara)  # przywracamy stary slot, żeby nie zgubić rezerwacji
        return _odmowa_przelozenia(
            request,
            stara,
            is_en,
            f"Termin {request.new_date} {request.new_time} został właśnie zarezerwowany.",
            slots=wolne_sloty(usluga, request.new_date),
        )

    demo_log(
        "🔁 [SPA] ZMIANA TERMINU ZABIEGU (demo log)",
        f"   ID Potwierdzenia : {request.confirmation_id} → {nowa.confirmation_id}",
        f"   Zabieg           : {usluga.nazwa}",
        f"   Nowy termin      : {request.new_date} {request.new_time}",
    )

    return {
        "success": True,
        "confirmation_id": nowa.confirmation_id,
        "previous_confirmation_id": request.confirmation_id,
        "service_name": usluga.nazwa,
        "new_date": request.new_date,
        "new_time": request.new_time,
        "guest_name": nowa.gosc,
        "found": True,
        "message": "Appointment rescheduled." if is_en else "Termin zabiegu zmieniony.",
        "note": "Rescheduling is free of charge." if is_en else "Zmiana terminu jest bezpłatna.",
    }
