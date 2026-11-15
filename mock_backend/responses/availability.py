"""Odpowiedzi HTTP dla endpointu check_spa_availability."""

from __future__ import annotations

from data import NAZWY_USLUG
from logs import log_demo, log_event
from schemas import ZapytanieSPA
from services.spa import Dostepnosc, Powod, cennik, poza_oknem


def dostepnosc(request: ZapytanieSPA, wynik: Dostepnosc) -> dict:
    log_demo(
        "📅 [SPA] SPRAWDZENIE DOSTĘPNOŚCI (demo log)",
        f"   Zabieg : {request.service_name}",
        f"   Data   : {request.date}",
    )
    usluga = wynik.usluga
    if usluga is None:
        return _nierozpoznany_zabieg(request, wynik)

    ceny = cennik(usluga)
    if wynik.powod is Powod.PRZESZLOSC:
        komunikat = f"Data {request.date} jest w przeszłości — nie można sprawdzić terminu."
    elif wynik.powod is Powod.POZA_OKNEM:
        komunikat = poza_oknem(request.date)
    elif wynik.powod is Powod.BRAK_SLOTOW:
        log_event(
            "no_free_slots",
            demo=f"   ❌ Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}.",
            service=usluga.nazwa,
            date=request.date,
        )
        komunikat = f"Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}."
    else:
        sloty = list(wynik.wolne)
        log_event("slots_available", demo=f"   ✅ Dostępne sloty: {', '.join(sloty)}", slots=sloty)
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
    return {
        "available": False,
        "slots": [],
        "service_name": usluga.nazwa,
        "date": request.date,
        "available_services": NAZWY_USLUG,
        "message": komunikat,
        **ceny,
    }


def _nierozpoznany_zabieg(request: ZapytanieSPA, wynik: Dostepnosc) -> dict:
    """Odpowiedź 200 dla nieznanego / niejednoznacznego zabiegu (agent ma dopytać)."""
    log_event(
        "unknown_service",
        demo=f"   ⚠️  Zabieg '{request.service_name}' — status: {wynik.status}",
        status=wynik.status,
    )
    bazowe = {
        "available": False,
        "slots": [],
        "service_name": request.service_name,
        "date": request.date,
    }
    if wynik.powod is Powod.NIEJEDNOZNACZNY:
        nazwy = list(wynik.kandydaci)
        return {
            **bazowe,
            "ambiguous": nazwy,
            "available_services": NAZWY_USLUG,
            "message": (
                f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}. "
                "Dopytaj gościa, który z nich wybiera."
            ),
        }
    return {
        **bazowe,
        "available_services": NAZWY_USLUG,
        "message": f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
    }
