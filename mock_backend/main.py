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
from datetime import date, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import telegram
from catalog import dopasuj, wczytaj_uslugi
from schemas import (
    AnulowanieSPA,
    Handoff,
    PrzelozenieSPA,
    RezerwacjaSPA,
    SprawdzeniePokoj,
    WysylkaSMS,
    ZapytanieSPA,
)
from store import KatalogPokoi, Rezerwacja, SpaStore, daty_pobytu

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURACJA APLIKACJI
# ─────────────────────────────────────────────────────────────────────────────

APP_VERSION = "1.1.0"
START_TIME = time.monotonic()

SEPARATOR = "=" * 60

# Logi demo (konsola na prezentacji) — celowo zostawione, wyłączenie: ANNA_DEMO_LOGS=0
DEMO_LOGS = os.getenv("ANNA_DEMO_LOGS", "1").strip().lower() not in {"0", "false", "no", "off"}


def demo_log(*linie: str) -> None:
    """Log demonstracyjny na konsolę — efekt live na prezentacji (nie log strukturalny)."""
    if not DEMO_LOGS:
        return
    print(SEPARATOR)
    for linia in linie:
        print(linia)
    print(SEPARATOR)


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

# ─────────────────────────────────────────────────────────────────────────────
# DANE DEMO — katalog SPA i pokoje (seed: data/*.json)
# ─────────────────────────────────────────────────────────────────────────────

USLUGI, _SLOTY_DOMYSLNE, HORYZONT_DNI = wczytaj_uslugi()
SPA_STORE = SpaStore(USLUGI, horyzont_dni=HORYZONT_DNI)
POKOJE = KatalogPokoi()

NAZWY_USLUG = [usluga.nazwa for usluga in USLUGI]


def _wolne_sloty(usluga, data_iso: str) -> list[str]:
    return SPA_STORE.sloty_dnia(usluga, data_iso)


def _cennik(usluga) -> dict:
    """Cena i czas zabiegu wprost z katalogu — te same liczby mówi Anna na głos."""
    return {"price_pln": usluga.cena_pln, "duration_min": usluga.czas_min}


def _poza_oknem(data_iso: str) -> str:
    return (
        f"Termin {data_iso} jest poza oknem rezerwacji "
        f"({SPA_STORE.dzisiaj.isoformat()} – {SPA_STORE.ostatni_dzien.isoformat()})."
    )


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


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 1: Sprawdzenie dostępności zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/check_spa_availability")
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
    cennik = _cennik(usluga)
    if date.fromisoformat(request.date) < SPA_STORE.dzisiaj:
        return {
            "available": False,
            "slots": [],
            "service_name": usluga.nazwa,
            "date": request.date,
            "available_services": NAZWY_USLUG,
            "message": f"Data {request.date} jest w przeszłości — nie można sprawdzić terminu.",
            **cennik,
        }

    if not SPA_STORE.w_oknie(request.date):
        return {
            "available": False,
            "slots": [],
            "service_name": usluga.nazwa,
            "date": request.date,
            "available_services": NAZWY_USLUG,
            "message": _poza_oknem(request.date),
            **cennik,
        }

    sloty = _wolne_sloty(usluga, request.date)
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
            **cennik,
        }

    print(f"   ❌ Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}.")
    return {
        "available": False,
        "slots": [],
        "service_name": usluga.nazwa,
        "date": request.date,
        "available_services": NAZWY_USLUG,
        "message": f"Brak wolnych terminów dla '{usluga.nazwa}' w dniu {request.date}.",
        **cennik,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2: Rezerwacja zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/book_spa_appointment")
async def book_spa_appointment(request: RezerwacjaSPA):
    """Rezerwuje zabieg SPA i zajmuje slot w kalendarzu (stan w pamięci procesu)."""
    wynik = dopasuj(USLUGI, request.service_name)
    demo_log(
        "✍️  [SPA] NOWA REZERWACJA ZABIEGU (demo log)",
        f"   Gość    : {request.guest_name}",
        f"   Zabieg  : {request.service_name}",
        f"   Termin  : {request.date} {request.time}",
    )

    def _odmowa(message: str, **extra) -> dict:
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

    if not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            nazwy = [kandydat.nazwa for kandydat in wynik.kandydaci]
            return _odmowa(
                f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}. "
                "Dopytaj gościa, który z nich wybiera.",
                ambiguous=nazwy,
                available_services=NAZWY_USLUG,
            )
        return _odmowa(
            f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            available_services=NAZWY_USLUG,
        )

    usluga = wynik.usluga
    if date.fromisoformat(request.date) < SPA_STORE.dzisiaj:
        return _odmowa(f"Data {request.date} jest w przeszłości — nie można zarezerwować terminu.")

    if not SPA_STORE.w_oknie(request.date):
        return _odmowa(_poza_oknem(request.date))

    wolne = _wolne_sloty(usluga, request.date)
    if request.time not in usluga.sloty:
        return _odmowa(
            f"Godzina {request.time} nie jest w grafiku zabiegu '{usluga.nazwa}'.",
            slots=wolne,
        )
    if request.time not in wolne:
        return _odmowa(
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
        pozostale = _wolne_sloty(usluga, request.date)
        return _odmowa(
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

@app.post("/cancel_spa_appointment")
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
    # Reguła opłat liczy się WYŁĄCZNIE z godziny podanej w żądaniu. Bez niej
    # backend nie zna terminu (agent musi przekazać appointment_datetime).
    appointment_datetime = request.appointment_datetime

    if rezerwacja is None:
        # Nieznany numer to NIE udane anulowanie. Wcześniej backend zwracał
        # success/cancelled=True i Anna potwierdzała gościowi zdjęcie
        # rezerwacji-widma. Teraz agent dostaje wyraźny sygnał, żeby dopytać.
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

    # Zwolnienie slotu — bez `await`, więc odczyt i zapis stanu są atomowe.
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
    if rezerwacja is None:
        notatka += (
            " Note: reservation not found in the in-memory store (PoC)."
            if is_en
            else " Uwaga: rezerwacji nie ma w pamięci serwera (PoC) — zwolnienie slotu pominięte."
        )

    return {
        "success": True,
        "confirmation_id": request.confirmation_id,
        "cancelled": True,
        "fee": oplata,
        "medical_release": bool(request.medical_release),
        "free_of_charge": bezplatna,
        "fee_rule": regula,
        "found": rezerwacja is not None,
        "message": "Reservation cancelled." if is_en else "Rezerwacja anulowana.",
        "note": notatka,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 4: Zmiana terminu zabiegu SPA (reschedule)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/reschedule_spa_appointment")
async def reschedule_spa_appointment(request: PrzelozenieSPA):
    """Przenosi rezerwację na nowy termin: stary slot wraca do puli, nowy zostaje zajęty."""
    is_en = request.language == "en"
    wynik = dopasuj(USLUGI, request.service_name)
    stara = SPA_STORE.rezerwacja(request.confirmation_id)

    def _odmowa(message: str, **extra) -> dict:
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

    if stara is None:
        # Bez tego sprawdzenia reschedule NIEISTNIEJĄCEJ rezerwacji tworzył nową
        # (nowy numer potwierdzenia) — czyli przełożenie działało jak rezerwacja.
        return _odmowa(
            f"No reservation found with number {request.confirmation_id}. "
            "Ask the guest to re-check the number, or book a new appointment."
            if is_en
            else f"Nie znaleziono rezerwacji o numerze {request.confirmation_id}. "
            "Poproś gościa o sprawdzenie numeru albo zarezerwuj nowy termin.",
            found=False,
            available_services=NAZWY_USLUG,
        )

    if not wynik.dopasowano:
        if wynik.status == "niejednoznaczne":
            nazwy = [kandydat.nazwa for kandydat in wynik.kandydaci]
            return _odmowa(
                f"'{request.service_name}' może oznaczać kilka zabiegów: {', '.join(nazwy)}.",
                ambiguous=nazwy,
            )
        return _odmowa(f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.")

    usluga = wynik.usluga
    if date.fromisoformat(request.new_date) < SPA_STORE.dzisiaj:
        return _odmowa(f"Data {request.new_date} jest w przeszłości.")
    if not SPA_STORE.w_oknie(request.new_date):
        return _odmowa(_poza_oknem(request.new_date))
    if request.new_time not in usluga.sloty:
        return _odmowa(f"Godzina {request.new_time} nie jest w grafiku zabiegu '{usluga.nazwa}'.")

    wolne = _wolne_sloty(usluga, request.new_date)
    if request.new_time not in wolne:
        return _odmowa(
            f"Termin {request.new_date} {request.new_time} jest zajęty. "
            f"Wolne godziny: {', '.join(wolne) or 'brak'}.",
            slots=wolne,
        )

    # Zwolnienie starego i zajęcie nowego slotu — sekcja bez `await`, więc atomowa.
    if stara is not None:
        SPA_STORE.zwolnij(request.confirmation_id)
    nowa = Rezerwacja(
        confirmation_id=SPA_STORE.nowy_numer(),
        kod_uslugi=usluga.kod,
        data=request.new_date,
        godzina=request.new_time,
        gosc=request.guest_name or (stara.gosc if stara else ""),
    )
    if not SPA_STORE.zajmij(nowa):
        if stara is not None:  # przywracamy stary slot, żeby nie zgubić rezerwacji
            SPA_STORE.zajmij(stara)
        return _odmowa(
            f"Termin {request.new_date} {request.new_time} został właśnie zarezerwowany.",
            slots=_wolne_sloty(usluga, request.new_date),
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


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 5: Sprawdzenie dostępności pokoju
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/check_room_availability")
async def check_room_availability(request: SprawdzeniePokoj):
    """Sprawdza dostępność pokoju i liczy cenę pobytu (cennik z data/rooms.json)."""
    demo_log(
        "🏨 [POKOJE] SPRAWDZENIE DOSTĘPNOŚCI (demo log)",
        f"   Typ pokoju  : {request.room_type}",
        f"   Check-in    : {request.check_in}",
        f"   Check-out   : {request.check_out}",
    )

    typ = POKOJE.znajdz(request.room_type)
    if typ is None:
        # Agent musi móc zaproponować realne opcje — sama informacja "nie istnieje"
        # zostawiała go z niczym (dotyczy też niejednoznacznych wartości, np. "pokój").
        print(f"   ⚠️  Nieznany/niejednoznaczny typ pokoju: '{request.room_type}'")
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

    if data_in < date.today():
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
        print(f"   ❌ ZAJĘTE — kolizja z blokadą {POKOJE.opis_blokady()}: {', '.join(kolizja)}")
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

    print(
        f"   ✅ DOSTĘPNY — {liczba_nocy} noc(y) × {typ.cena_za_noc:g} {typ.waluta} "
        f"= {cena_calkowita:g} {typ.waluta} łącznie."
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


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 6: Wysyłka SMS / Podsumowanie przez Telegram
# ─────────────────────────────────────────────────────────────────────────────

def _tekst_sms_na_telegram(request: WysylkaSMS) -> str:
    tekst = f"🏨 *Bukowy Dwór — Potwierdzenie Rezerwacji*\n\n📞 Gość: `{request.phone_number}`\n"
    if request.confirmation_id:
        tekst += f"🔖 Nr ref.: `{request.confirmation_id}`\n"
    return tekst + f"\n📋 {request.summary_text}"


@app.post("/send_sms_summary")
async def send_sms_summary(request: WysylkaSMS):
    """Symuluje wysyłkę SMS: drukuje treść (demo) i opcjonalnie wysyła na Telegram."""
    is_en = request.language == "en"
    demo_log(
        "📱 [SMS] WYSYŁKA PODSUMOWANIA (demo log)",
        f"   Odbiorca : {request.phone_number}",
        f"   Nr ref.  : {request.confirmation_id or '-'}",
        f"   Język    : {'EN' if is_en else 'PL'}",
        "   📩 TREŚĆ SMS:",
        f"   {request.summary_text}",
    )

    if telegram.skonfigurowany():
        await telegram.wyslij_wiadomosc(_tekst_sms_na_telegram(request), etykieta="SMS")
    else:
        print(
            "   ℹ️  Telegram not configured — SMS printed to console only."
            if is_en
            else "   ℹ️  Telegram nie skonfigurowany — SMS tylko w konsoli "
            "(ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID)."
        )

    return {
        "success": True,
        "message": "Message sent." if is_en else "Wiadomość wysłana.",
        "delivered_to": request.phone_number,
        "language": request.language,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 7: Symulowany handoff — przekazanie rozmowy do człowieka (PoC)
# ─────────────────────────────────────────────────────────────────────────────

DZIALY = {
    "recepcja": "Recepcja główna",
    "dyzurka_medyczna": "Dyżurka medyczna (gabinet 101)",
}


def _tekst_handoffu(request: Handoff, dzial: str) -> str:
    tekst = f"🛎️ *Anna prosi o asystę — {dzial}*\n\n"
    if request.guest_name:
        tekst += f"👤 Gość: `{request.guest_name}`\n"
    if request.reason:
        tekst += f"📋 Powód: {request.reason}\n"
    return tekst + "\n_(To symulacja handoffu — na produkcji ustaw realne przekierowanie.)_"


@app.post("/transfer_to_simulated_handoff")
async def transfer_to_simulated_handoff(request: Handoff):
    """Symuluje przekazanie rozmowy do żywego pracownika (PoC, bez telefonii)."""
    dzial = DZIALY.get((request.department or "").strip().lower(), request.department or "Recepcja")
    is_en = request.language == "en"
    demo_log(
        "🛎️  [HANDOFF] PRZEKAZANIE DO CZŁOWIEKA (demo log)",
        f"   Dział : {dzial}",
        f"   Gość  : {request.guest_name or '-'}",
        f"   Powód : {request.reason or '-'}",
        f"   Język : {'EN' if is_en else 'PL'}",
    )

    if telegram.skonfigurowany():
        await telegram.wyslij_wiadomosc(_tekst_handoffu(request, dzial), etykieta="Alert handoff")
    else:
        print(
            "   ℹ️  Telegram not configured — handoff logged to console only."
            if is_en
            else "   ℹ️  Telegram nie skonfigurowany — handoff tylko w konsoli "
            "(ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID)."
        )

    return {
        "success": True,
        "simulated": True,
        "message": "Handoff to a human simulated (PoC — no telephony)."
        if is_en
        else "Przekazanie do człowieka zasymulowane (PoC — brak telefonii).",
        "department": dzial,
        "reason": request.reason,
        "guest_name": request.guest_name,
        "language": request.language,
        "note": "On production: wire transfer_to_number (SIP) or notify live reception staff."
        if is_en
        else "Na produkcji: podpiąć transfer_to_number (SIP) lub powiadomienie do recepcji.",
    }


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
