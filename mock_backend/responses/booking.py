"""Odpowiedzi HTTP dla endpointu book_spa_appointment."""

from __future__ import annotations

from data import NAZWY_USLUG
from logs import log_demo, log_event
from responses._common import odmowa
from schemas import RezerwacjaSPA
from services.spa import Odmowa, Potwierdzenie, Powod, poza_oknem


def rezerwacja(request: RezerwacjaSPA, wynik: Odmowa | Potwierdzenie) -> dict:
    log_demo(
        "✍️  [SPA] NOWA REZERWACJA ZABIEGU (demo log)",
        f"   Gość    : {request.guest_name}",
        f"   Zabieg  : {request.service_name}",
        f"   Termin  : {request.date} {request.time}",
    )
    if isinstance(wynik, Odmowa):
        return _odmowa_rezerwacji(request, wynik)

    rezerwacja_ = wynik.rezerwacja
    log_event("booking_confirmed", demo=f"   ✅ Potwierdzenie: {rezerwacja_.confirmation_id}",
              confirmation_id=rezerwacja_.confirmation_id)
    return {
        "success": True,
        "confirmation_id": rezerwacja_.confirmation_id,
        "service_name": wynik.usluga.nazwa,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
        "message": f"Rezerwacja potwierdzona. Numer: {rezerwacja_.confirmation_id}.",
    }


def _odmowa_rezerwacji(request: RezerwacjaSPA, wynik_odmowy: Odmowa) -> dict:
    przed = {
        "confirmation_id": None,
        "service_name": request.service_name,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
    }
    nazwa_uslugi = wynik_odmowy.usluga.nazwa if wynik_odmowy.usluga else ""
    wolne = list(wynik_odmowy.wolne)

    if wynik_odmowy.powod is Powod.NIEJEDNOZNACZNY:
        nazwy = list(wynik_odmowy.kandydaci)
        return odmowa(
            przed,
            f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}. "
            "Dopytaj gościa, który z nich wybiera.",
            {"ambiguous": nazwy, "available_services": NAZWY_USLUG},
        )
    if wynik_odmowy.powod is Powod.NIEZNANY:
        return odmowa(
            przed,
            f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            {"available_services": NAZWY_USLUG},
        )
    if wynik_odmowy.powod is Powod.KLUCZ_KONFLIKT:
        return odmowa(przed, "Ten klucz idempotencji był już użyty do innej rezerwacji. Wygeneruj nowy klucz.")
    if wynik_odmowy.powod is Powod.PRZESZLOSC:
        return odmowa(przed, f"Data {request.date} jest w przeszłości — nie można zarezerwować terminu.")
    if wynik_odmowy.powod is Powod.POZA_OKNEM:
        return odmowa(przed, poza_oknem(request.date))
    if wynik_odmowy.powod is Powod.POZA_GRAFIKIEM:
        return odmowa(
            przed,
            f"Godzina {request.time} nie jest w grafiku zabiegu '{nazwa_uslugi}'.",
            {"slots": wolne},
        )
    if wynik_odmowy.powod is Powod.ZAJETY:
        return odmowa(
            przed,
            f"Termin {request.date} {request.time} jest już zajęty. "
            f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
            {"slots": wolne},
        )
    # Powod.WYSCIG — slot zajęty między sprawdzeniem a zapisem
    return odmowa(
        przed,
        f"Termin {request.date} {request.time} został właśnie zarezerwowany. "
        f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
        {"slots": wolne},
    )
