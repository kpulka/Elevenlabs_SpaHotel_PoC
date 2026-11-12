"""Odpowiedzi HTTP dla endpointów SPA: słowniki, komunikaty dla agenta i logi konsolowe.

Wszystkie teksty (PL/EN) tutaj są kontraktem z promptem agenta
(docs/anna_system_prompt_v3.md) — zmiana treści wymaga zgody. Moduł nie zawiera reguł
biznesowych; te są w ``services/spa.py``.
"""

from __future__ import annotations

from schemas import AnulowanieSPA, PrzelozenieSPA, RezerwacjaSPA, ZapytanieSPA
from services.spa import (
    Dostepnosc,
    Odmowa,
    Potwierdzenie,
    Powod,
    Przeniesienie,
    RegulaOplaty,
    WynikAnulowania,
)
from state import NAZWY_USLUG, cennik, demo_log, poza_oknem

# (wersja polska, wersja angielska) — tekst reguły opłat trafia do odpowiedzi i logu demo.
_REGULY_OPLAT = {
    RegulaOplaty.MEDYCZNA: (
        "Zwolnienie medyczne — anulacja bezpłatna (0%).",
        "Medical release — free of charge (0%).",
    ),
    RegulaOplaty.BRAK_GODZINY: (
        "Brak godziny zabiegu (appointment_datetime) — przyjęto opłatę 50%.",
        "Appointment time unknown (no appointment_datetime) — 50% fee applied.",
    ),
    RegulaOplaty.PONAD_2H: (
        "Anulacja ponad 2h przed zabiegiem — bezpłatna (0%).",
        "Cancelled more than 2h before the appointment — free of charge (0%).",
    ),
    RegulaOplaty.PONIZEJ_2H: (
        "Anulacja poniżej 2h przed zabiegiem — obowiązuje opłata 50%.",
        "Cancelled less than 2h before the appointment — 50% fee applies.",
    ),
}


def _odmowa(przed: dict, komunikat: str, po: dict | None = None) -> dict:
    """Jedna fabryka odmowy: wspólny kształt `success: False` + `message`, reszta z kontekstu endpointu."""
    print(f"   ❌ {komunikat}")
    return {"success": False, **przed, "message": komunikat, **(po or {})}


# ─────────────────────────────────────────────────────────────────────────────
# check_spa_availability
# ─────────────────────────────────────────────────────────────────────────────

def dostepnosc(request: ZapytanieSPA, wynik: Dostepnosc) -> dict:
    demo_log(
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
        print(f"   ❌ Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}.")
        komunikat = f"Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}."
    else:
        sloty = list(wynik.wolne)
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
    print(f"   ⚠️  Zabieg '{request.service_name}' — status: {wynik.status}")
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


# ─────────────────────────────────────────────────────────────────────────────
# book_spa_appointment
# ─────────────────────────────────────────────────────────────────────────────

def rezerwacja(request: RezerwacjaSPA, wynik: Odmowa | Potwierdzenie) -> dict:
    demo_log(
        "✍️  [SPA] NOWA REZERWACJA ZABIEGU (demo log)",
        f"   Gość    : {request.guest_name}",
        f"   Zabieg  : {request.service_name}",
        f"   Termin  : {request.date} {request.time}",
    )
    if isinstance(wynik, Odmowa):
        return _odmowa_rezerwacji(request, wynik)

    rezerwacja_ = wynik.rezerwacja
    print(f"   ✅ Potwierdzenie: {rezerwacja_.confirmation_id}")
    return {
        "success": True,
        "confirmation_id": rezerwacja_.confirmation_id,
        "service_name": wynik.usluga.nazwa,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
        "message": f"Rezerwacja potwierdzona. Numer: {rezerwacja_.confirmation_id}.",
    }


def _odmowa_rezerwacji(request: RezerwacjaSPA, odmowa: Odmowa) -> dict:
    przed = {
        "confirmation_id": None,
        "service_name": request.service_name,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
    }
    nazwa_uslugi = odmowa.usluga.nazwa if odmowa.usluga else ""
    wolne = list(odmowa.wolne)

    if odmowa.powod is Powod.NIEJEDNOZNACZNY:
        nazwy = list(odmowa.kandydaci)
        return _odmowa(
            przed,
            f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}. "
            "Dopytaj gościa, który z nich wybiera.",
            {"ambiguous": nazwy, "available_services": NAZWY_USLUG},
        )
    if odmowa.powod is Powod.NIEZNANY:
        return _odmowa(
            przed,
            f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            {"available_services": NAZWY_USLUG},
        )
    if odmowa.powod is Powod.PRZESZLOSC:
        return _odmowa(przed, f"Data {request.date} jest w przeszłości — nie można zarezerwować terminu.")
    if odmowa.powod is Powod.POZA_OKNEM:
        return _odmowa(przed, poza_oknem(request.date))
    if odmowa.powod is Powod.POZA_GRAFIKIEM:
        return _odmowa(
            przed,
            f"Godzina {request.time} nie jest w grafiku zabiegu '{nazwa_uslugi}'.",
            {"slots": wolne},
        )
    if odmowa.powod is Powod.ZAJETY:
        return _odmowa(
            przed,
            f"Termin {request.date} {request.time} jest już zajęty. "
            f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
            {"slots": wolne},
        )
    # Powod.WYSCIG — slot zajęty między sprawdzeniem a zapisem
    return _odmowa(
        przed,
        f"Termin {request.date} {request.time} został właśnie zarezerwowany. "
        f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
        {"slots": wolne},
    )


# ─────────────────────────────────────────────────────────────────────────────
# cancel_spa_appointment
# ─────────────────────────────────────────────────────────────────────────────

def anulowanie(request: AnulowanieSPA, wynik: WynikAnulowania) -> dict:
    is_en = request.language == "en"
    if not wynik.znaleziona:
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

    oplata = wynik.oplata
    regula_pl, regula_en = _REGULY_OPLAT[oplata.regula]
    regula = regula_en if is_en else regula_pl
    bezplatna = oplata.ulamek == 0.0

    demo_log(
        "🗑️  [SPA] ANULOWANIE REZERWACJI (demo log)",
        f"   ID Potwierdzenia : {request.confirmation_id}",
        f"   Powód            : {request.reason or '-'}",
        f"   Termin zabiegu   : {request.appointment_datetime or 'nieznany'}",
        f"   Zwolnienie med.  : {'TAK' if request.medical_release else 'NIE'}",
        f"   Reguła           : {regula}",
        f"   Slot zwolniony   : {'TAK' if wynik.zwolniona else 'nie (brak w pamięci)'}",
    )

    if is_en:
        notatka = "Free of charge." if bezplatna else "Cancellation fee applies (50% of the service price)."
    else:
        notatka = "Bezpłatna." if bezplatna else "Obowiązuje opłata 50% ceny zabiegu."

    return {
        "success": True,
        "confirmation_id": request.confirmation_id,
        "cancelled": True,
        "fee": oplata.ulamek,
        "medical_release": bool(request.medical_release),
        "free_of_charge": bezplatna,
        "fee_rule": regula,
        "found": True,
        "message": "Reservation cancelled." if is_en else "Rezerwacja anulowana.",
        "note": notatka,
    }


# ─────────────────────────────────────────────────────────────────────────────
# reschedule_spa_appointment
# ─────────────────────────────────────────────────────────────────────────────

def przelozenie(request: PrzelozenieSPA, wynik: Odmowa | Przeniesienie) -> dict:
    is_en = request.language == "en"
    if isinstance(wynik, Odmowa):
        return _odmowa_przelozenia(request, wynik, is_en)

    nowa = wynik.nowa
    demo_log(
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
        "message": "Appointment rescheduled." if is_en else "Termin zabiegu zmieniony.",
        "note": "Rescheduling is free of charge." if is_en else "Zmiana terminu jest bezpłatna.",
    }


def _odmowa_przelozenia(request: PrzelozenieSPA, odmowa: Odmowa, is_en: bool) -> dict:
    stara = odmowa.stara
    przed = {
        "confirmation_id": request.confirmation_id,
        "service_name": request.service_name,
        "new_date": request.new_date,
        "new_time": request.new_time,
        "guest_name": request.guest_name or (stara.gosc if stara else ""),
        "found": stara is not None,
    }
    note = "Appointment was not changed." if is_en else "Termin nie został zmieniony."
    nazwa_uslugi = odmowa.usluga.nazwa if odmowa.usluga else ""
    wolne = list(odmowa.wolne)

    if odmowa.powod is Powod.NIE_ZNALEZIONO:
        komunikat = (
            f"No reservation found with number {request.confirmation_id}. "
            "Ask the guest to re-check the number, or book a new appointment."
            if is_en
            else f"Nie znaleziono rezerwacji o numerze {request.confirmation_id}. "
            "Poproś gościa o sprawdzenie numeru albo zarezerwuj nowy termin."
        )
        return _odmowa(przed, komunikat, {"note": note, "available_services": NAZWY_USLUG})
    if odmowa.powod is Powod.NIEJEDNOZNACZNY:
        nazwy = list(odmowa.kandydaci)
        return _odmowa(
            przed,
            f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}.",
            {"note": note, "ambiguous": nazwy},
        )
    if odmowa.powod is Powod.NIEZNANY:
        return _odmowa(
            przed,
            f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            {"note": note},
        )
    if odmowa.powod is Powod.PRZESZLOSC:
        return _odmowa(przed, f"Data {request.new_date} jest w przeszłości.", {"note": note})
    if odmowa.powod is Powod.POZA_OKNEM:
        return _odmowa(przed, poza_oknem(request.new_date), {"note": note})
    if odmowa.powod is Powod.POZA_GRAFIKIEM:
        return _odmowa(
            przed,
            f"Godzina {request.new_time} nie jest w grafiku zabiegu '{nazwa_uslugi}'.",
            {"note": note},
        )
    if odmowa.powod is Powod.ZAJETY:
        return _odmowa(
            przed,
            f"Termin {request.new_date} {request.new_time} jest zajęty. "
            f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
            {"note": note, "slots": wolne},
        )
    # Powod.WYSCIG — slot zajęty między sprawdzeniem a zapisem (stary slot przywrócony)
    return _odmowa(
        przed,
        f"Termin {request.new_date} {request.new_time} został właśnie zarezerwowany.",
        {"note": note, "slots": wolne},
    )
