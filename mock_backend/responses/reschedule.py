"""Odpowiedzi HTTP dla endpointu reschedule_spa_appointment."""

from __future__ import annotations

from data import NAZWY_USLUG
from i18n import lang_of, pick
from logs import log_demo
from responses._common import odmowa
from schemas import PrzelozenieSPA
from services.spa import Odmowa, Powod, Przeniesienie, poza_oknem


def przelozenie(request: PrzelozenieSPA, wynik: Odmowa | Przeniesienie) -> dict:
    lang = lang_of(request)
    if isinstance(wynik, Odmowa):
        return _odmowa_przelozenia(request, wynik, lang)

    nowa = wynik.nowa
    log_demo(
        "🔁 [SPA] ZMIANA TERMINU ZABIEGU (demo log)",
        f"   ID Potwierdzenia : {request.confirmation_id} → {nowa.confirmation_id}",
        f"   Zabieg           : {wynik.usluga.nazwa}",
        f"   Nowy termin      : {request.new_date} {request.new_time}",
    )
    return {
        "success": True,
        "confirmation_id": nowa.confirmation_id,
        "previous_confirmation_id": request.confirmation_id,
        "service_name": wynik.usluga.nazwa,
        "new_date": request.new_date,
        "new_time": request.new_time,
        "guest_name": nowa.gosc,
        "found": True,
        "message": pick(lang, "Termin zabiegu zmieniony.", "Appointment rescheduled."),
        "note": pick(lang, "Zmiana terminu jest bezpłatna.", "Rescheduling is free of charge."),
    }


def _odmowa_przelozenia(request: PrzelozenieSPA, wynik_odmowy: Odmowa, lang: str) -> dict:
    stara = wynik_odmowy.stara
    przed = {
        "confirmation_id": request.confirmation_id,
        "service_name": request.service_name,
        "new_date": request.new_date,
        "new_time": request.new_time,
        "guest_name": request.guest_name or (stara.gosc if stara else ""),
        "found": stara is not None,
    }
    note = pick(lang, "Termin nie został zmieniony.", "Appointment was not changed.")
    nazwa_uslugi = wynik_odmowy.usluga.nazwa if wynik_odmowy.usluga else ""
    wolne = list(wynik_odmowy.wolne)

    if wynik_odmowy.powod is Powod.NIE_ZNALEZIONO:
        komunikat = pick(
            lang,
            f"Nie znaleziono rezerwacji o numerze {request.confirmation_id}. "
            "Poproś gościa o sprawdzenie numeru albo zarezerwuj nowy termin.",
            f"No reservation found with number {request.confirmation_id}. "
            "Ask the guest to re-check the number, or book a new appointment.",
        )
        return odmowa(przed, komunikat, {"note": note, "available_services": NAZWY_USLUG})
    if wynik_odmowy.powod is Powod.NIEJEDNOZNACZNY:
        nazwy = list(wynik_odmowy.kandydaci)
        return odmowa(
            przed,
            f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}.",
            {"note": note, "ambiguous": nazwy},
        )
    if wynik_odmowy.powod is Powod.NIEZNANY:
        return odmowa(
            przed,
            f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            {"note": note},
        )
    if wynik_odmowy.powod is Powod.PRZESZLOSC:
        return odmowa(przed, f"Data {request.new_date} jest w przeszłości.", {"note": note})
    if wynik_odmowy.powod is Powod.POZA_OKNEM:
        return odmowa(przed, poza_oknem(request.new_date), {"note": note})
    if wynik_odmowy.powod is Powod.POZA_GRAFIKIEM:
        return odmowa(
            przed,
            f"Godzina {request.new_time} nie jest w grafiku zabiegu '{nazwa_uslugi}'.",
            {"note": note},
        )
    if wynik_odmowy.powod is Powod.ZAJETY:
        return odmowa(
            przed,
            f"Termin {request.new_date} {request.new_time} jest zajęty. "
            f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
            {"note": note, "slots": wolne},
        )
    # Powod.WYSCIG — slot zajęty między sprawdzeniem a zapisem (stary slot przywrócony)
    return odmowa(
        przed,
        f"Termin {request.new_date} {request.new_time} został właśnie zarezerwowany.",
        {"note": note, "slots": wolne},
    )
