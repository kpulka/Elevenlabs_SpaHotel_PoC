"""
Mock Backend — Wirtualny Recepcjonista AI
Uzdrowisko Bukowy Dwór, Krynica-Zdrój

Cel: Symulacja integracji z systemem PMS (Property Management System)
     oraz obsługa webhooków z agenta ElevenLabs Conversational AI.

Uruchomienie:
    uvicorn main:app --reload --port 8000
"""

import os
import random
import json
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURACJA APLIKACJI
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mock PMS — Bukowy Dwór",
    description="Mock backendu dla PoC Wirtualnego Recepcjonisty AI (ElevenLabs Agent).",
    version="1.0.0",
)

# CORS — zezwalamy na wszystkie originy (wymagane dla webhooków ElevenLabs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Opcjonalna integracja z Telegramem (zmienne środowiskowe)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SEPARATOR = "=" * 60

# ─────────────────────────────────────────────────────────────────────────────
# DANE MOCK — ZABIEGI SPA
# Generujemy harmonogram dynamicznie dla najbliższych 14 dni
# ─────────────────────────────────────────────────────────────────────────────

ZABIEGI_DOSTEPNE = [
    "kąpiel siarczkowa Ukojenie Stawów",
    "masaż leczniczy pleców",
    "kąpiel borowinowa",
    "jonoforeza",
    "masaż klasyczny",
]

SLOTY_GODZINOWE = ["10:00", "11:00", "14:00", "14:30", "15:00", "16:00"]


def generuj_harmonogram_spa() -> dict:
    """
    Generuje słownik dostępnych slotów SPA dla najbliższych 14 dni.
    Klucz: nazwa zabiegu → data (YYYY-MM-DD) → lista godzin.
    """
    harmonogram = {}
    dzisiaj = datetime.now().date()

    for zabieg in ZABIEGI_DOSTEPNE:
        harmonogram[zabieg] = {}
        for i in range(14):
            dzien = dzisiaj + timedelta(days=i)
            data_str = dzien.strftime("%Y-%m-%d")
            harmonogram[zabieg][data_str] = SLOTY_GODZINOWE.copy()

    return harmonogram


# Generujemy harmonogram przy starcie serwera
SPA_SCHEDULE = generuj_harmonogram_spa()

# ─────────────────────────────────────────────────────────────────────────────
# DANE MOCK — POKOJE
# ─────────────────────────────────────────────────────────────────────────────

CENY_POKOI = {
    "jednoosobowy": 350,
    "dwuosobowy": 500,
    "apartament": 750,
}

# Daty zajęte — weekend 30-31 sierpnia 2026 (wszystkie typy pokoi)
ZAJETE_DATY = {"2026-08-30", "2026-08-31"}


# ─────────────────────────────────────────────────────────────────────────────
# MODELE DANYCH (Pydantic)
# ─────────────────────────────────────────────────────────────────────────────

class SprazdzenieZabiegSPA(BaseModel):
    """Żądanie sprawdzenia dostępności zabiegu SPA."""
    service_name: str
    date: str


class RezerwacjaSPA(BaseModel):
    """Żądanie rezerwacji zabiegu SPA."""
    service_name: str
    date: str
    time: str
    guest_name: str


class AnulowanieSPA(BaseModel):
    """Żądanie anulowania rezerwacji zabiegu SPA.

    Zgodne z procedurą anulowania (docs/elevenlabs_agent_procedures.md):
    odwołanie >2h przed terminem = bezpłatne; <2h = 50% opłaty, chyba że
    powód medyczny (wtedy 100% bezpłatne).
    """
    confirmation_id: str  # numer rezerwacji SPA-XXXX
    reason: Optional[str] = ""  # np. "pogorszenie stanu zdrowia", "zmiana planów"
    medical_release: Optional[bool] = False  # True = zwolnienie medyczne (bez opłat)
    language: Optional[str] = "pl"


class PrzelozenieSPA(BaseModel):
    """Żądanie zmiany terminu zabiegu SPA (reschedule)."""
    confirmation_id: str  # numer rezerwacji SPA-XXXX
    service_name: str
    new_date: str
    new_time: str
    guest_name: Optional[str] = ""
    language: Optional[str] = "pl"


class SprawdzeniePokoj(BaseModel):
    """Żądanie sprawdzenia dostępności pokoju."""
    room_type: str
    check_in: str
    check_out: str


class WysylkaSMS(BaseModel):
    """Żądanie wysłania podsumowania SMS/Telegram."""
    phone_number: str
    summary_text: str
    confirmation_id: Optional[str] = ""
    language: Optional[str] = "pl"  # pl | en — język wybrany przez gościa na stronie


class Handoff(BaseModel):
    """Żądanie symulowanego przekazania rozmowy do człowieka (PoC).

    Używane zamiast natywnego transfer_to_number, który wymaga realnej
    telefonii (SIP/telefonia). W PoC agent wywołuje ten webhook, a backend
    loguje zdarzenie do konsoli i (opcjonalnie) wysyła alert na Telegram.
    """
    department: Optional[str] = "recepcja"  # recepcja | dyzurka_medyczna
    reason: Optional[str] = ""
    guest_name: Optional[str] = ""
    language: Optional[str] = "pl"  # pl | en — język wybrany przez gościa na stronie


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 1: Sprawdzenie dostępności zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/check_spa_availability")
async def check_spa_availability(request: SprazdzenieZabiegSPA):
    """
    Sprawdza dostępność zabiegu SPA dla podanego dnia.
    Symuluje zapytanie do systemu PMS uzdrowiska.
    """
    print(f"\n{SEPARATOR}")
    print(f"📅 [SPA] SPRAWDZENIE DOSTĘPNOŚCI")
    print(f"   Zabieg : {request.service_name}")
    print(f"   Data   : {request.date}")
    print(SEPARATOR)

    # Szukamy zabiegu (porównanie case-insensitive dla wygody demonstracji)
    zabieg_klucz = None
    for zabieg in ZABIEGI_DOSTEPNE:
        if request.service_name.lower().strip() in zabieg.lower():
            zabieg_klucz = zabieg
            break

    # Nieznany zabieg — zwracamy listę dostępnych
    if zabieg_klucz is None:
        print(f"   ⚠️  Zabieg '{request.service_name}' nieznany. Zwracam listę dostępnych.")
        return {
            "available": False,
            "message": f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            "available_services": ZABIEGI_DOSTEPNE,
        }

    # Pobieramy sloty dla danego dnia
    sloty = SPA_SCHEDULE.get(zabieg_klucz, {}).get(request.date, [])

    if sloty:
        print(f"   ✅ Dostępne sloty: {', '.join(sloty)}")
        return {
            "available": True,
            "slots": sloty,
            "service_name": zabieg_klucz,
            "date": request.date,
        }
    else:
        print(f"   ❌ Brak wolnych terminów dla '{zabieg_klucz}' w dniu {request.date}.")
        return {
            "available": False,
            "message": f"Brak wolnych terminów dla '{zabieg_klucz}' w dniu {request.date}.",
            "available_services": ZABIEGI_DOSTEPNE,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2: Rezerwacja zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/book_spa_appointment")
async def book_spa_appointment(request: RezerwacjaSPA):
    """
    Rezerwuje zabieg SPA dla gościa.
    Symuluje zapis do systemu PMS — zawsze zwraca sukces (PoC).
    Generuje losowy numer potwierdzenia SPA-XXXX.
    """
    # Losowy 4-cyfrowy numer potwierdzenia
    confirmation_id = f"SPA-{random.randint(1000, 9999)}"

    print(f"\n{SEPARATOR}")
    print(f"✍️  [SPA] NOWA REZERWACJA ZABIEGU")
    print(f"   ID Potwierdzenia : {confirmation_id}")
    print(f"   Gość             : {request.guest_name}")
    print(f"   Zabieg           : {request.service_name}")
    print(f"   Data             : {request.date}")
    print(f"   Godzina          : {request.time}")
    print(SEPARATOR)

    return {
        "success": True,
        "confirmation_id": confirmation_id,
        "service_name": request.service_name,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
        "message": "Rezerwacja potwierdzona.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2b: Anulowanie rezerwacji zabiegu SPA
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/cancel_spa_appointment")
async def cancel_spa_appointment(request: AnulowanieSPA):
    """
    Anuluje rezerwację zabiegu SPA.

    Zgodnie z procedurą (docs/elevenlabs_agent_procedures.md):
    - Odwołanie >2h przed terminem: bezpłatna anulacja.
    - Odwołanie <2h: 50% opłaty, CHYBA ŻE medical_release=True (zwolnienie
      medyczne — wtedy 100% bezpłatne).
    PoC: zawsze zwraca sukces (brak realnego PMS), loguje decyzję.
    """
    is_en = (request.language or "pl").lower() == "en"
    bezplatna = bool(request.medical_release)
    opłata = 0 if bezplatna else 0.5  # PoC: 50% opłaty gdy <2h bez zwolnienia

    print(f"\n{SEPARATOR}")
    print(f"🗑️  [SPA] ANULOWANIE REZERWACJI")
    print(f"   ID Potwierdzenia : {request.confirmation_id}")
    if request.reason:
        print(f"   Powód            : {request.reason}")
    print(f"   Zwolnienie med.  : {'TAK (bez opłat)' if bezplatna else 'NIE'}")
    print(f"   Opłata           : {'0 PLN (100% bezpłatne)' if bezplatna else '50% opłaty (anulacja <2h)'}")
    print(SEPARATOR)

    return {
        "success": True,
        "confirmation_id": request.confirmation_id,
        "cancelled": True,
        "fee": opłata,
        "medical_release": bezplatna,
        "message": "Reservation cancelled." if is_en else "Rezerwacja anulowana.",
        "note": "Free of charge." if bezplatna else "Standard cancellation fee applies (50%) if within 2h of the appointment.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2c: Zmiana terminu zabiegu SPA (reschedule)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/reschedule_spa_appointment")
async def reschedule_spa_appointment(request: PrzelozenieSPA):
    """
    Zmienia termin zabiegu SPA (reschedule).

    Zgodnie z procedurą: bezpłatna zmiana terminu w miarę dostępności
    grafiku fizjoterapeutów i balneologów.
    PoC: zawsze zwraca sukces, loguje nowy termin.
    """
    is_en = (request.language or "pl").lower() == "en"
    nowy_confirm = f"SPA-{random.randint(1000, 9999)}"

    print(f"\n{SEPARATOR}")
    print(f"🔁 [SPA] ZMIANA TERMINU ZABIEGU")
    print(f"   ID Potwierdzenia : {request.confirmation_id} → {nowy_confirm}")
    print(f"   Zabieg           : {request.service_name}")
    print(f"   Nowy termin      : {request.new_date} {request.new_time}")
    if request.guest_name:
        print(f"   Gość             : {request.guest_name}")
    print(SEPARATOR)

    return {
        "success": True,
        "confirmation_id": nowy_confirm,
        "service_name": request.service_name,
        "new_date": request.new_date,
        "new_time": request.new_time,
        "guest_name": request.guest_name,
        "message": "Appointment rescheduled." if is_en else "Termin zabiegu zmieniony.",
        "note": "Rescheduling is free of charge." if is_en else "Zmiana terminu jest bezpłatna.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 3: Sprawdzenie dostępności pokoju
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/check_room_availability")
async def check_room_availability(request: SprawdzeniePokoj):
    """
    Sprawdza dostępność pokoju w podanym przedziale czasowym.
    Logika: weekend 30-31.08.2026 → zawsze zajęte.
    Zwraca cenę całkowitą na podstawie liczby nocy.
    """
    print(f"\n{SEPARATOR}")
    print(f"🏨 [POKOJE] SPRAWDZENIE DOSTĘPNOŚCI")
    print(f"   Typ pokoju  : {request.room_type}")
    print(f"   Check-in    : {request.check_in}")
    print(f"   Check-out   : {request.check_out}")
    print(SEPARATOR)

    # Walidacja typu pokoju
    cena_za_noc = CENY_POKOI.get(request.room_type.lower())
    if cena_za_noc is None:
        print(f"   ⚠️  Nieznany typ pokoju: '{request.room_type}'")
        return {
            "available": False,
            "room_type": request.room_type,
            "message": f"Typ pokoju '{request.room_type}' nie istnieje. Dostępne: {list(CENY_POKOI.keys())}",
        }

    # Parsowanie dat i obliczenie liczby nocy
    try:
        data_in = datetime.strptime(request.check_in, "%Y-%m-%d").date()
        data_out = datetime.strptime(request.check_out, "%Y-%m-%d").date()
        liczba_nocy = (data_out - data_in).days
    except ValueError:
        return {
            "available": False,
            "message": "Nieprawidłowy format daty. Użyj formatu YYYY-MM-DD.",
        }

    if liczba_nocy <= 0:
        return {
            "available": False,
            "message": "Data wymeldowania musi być późniejsza niż data zameldowania.",
        }

    # Sprawdzenie czy termin nachodzi na zajęty weekend 30-31.08.2026
    # Generujemy zbiór dat dla całego pobytu
    daty_pobytu = set()
    for i in range(liczba_nocy):
        dzien = data_in + timedelta(days=i)
        daty_pobytu.add(dzien.strftime("%Y-%m-%d"))

    czy_zajete = bool(daty_pobytu & ZAJETE_DATY)

    cena_calkowita = cena_za_noc * liczba_nocy

    if czy_zajete:
        print(f"   ❌ ZAJĘTE — termin zachodzi na zablokowany weekend (30-31.08.2026).")
        return {
            "available": False,
            "room_type": request.room_type,
            "price_per_night": cena_za_noc,
            "check_in": request.check_in,
            "check_out": request.check_out,
            "total_nights": liczba_nocy,
            "total_price": cena_calkowita,
            "message": "Brak dostępności w wybranym terminie. Szczyt sezonu — wszystkie pokoje zajęte.",
        }

    print(f"   ✅ DOSTĘPNY — {liczba_nocy} noc(y) × {cena_za_noc} PLN = {cena_calkowita} PLN łącznie.")
    return {
        "available": True,
        "room_type": request.room_type,
        "price_per_night": cena_za_noc,
        "check_in": request.check_in,
        "check_out": request.check_out,
        "total_nights": liczba_nocy,
        "total_price": cena_calkowita,
        "message": f"Pokój dostępny. Cena: {cena_calkowita} PLN za {liczba_nocy} noc(y).",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 4: Wysyłka SMS / Podsumowanie przez Telegram
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/send_sms_summary")
async def send_sms_summary(request: WysylkaSMS):
    """
    Symuluje wysyłkę SMS z podsumowaniem rezerwacji.
    W wersji demo: drukuje treść SMS do konsoli (efekt live na prezentacji).
    Opcjonalnie: wysyła wiadomość na kanał Telegram (jeśli skonfigurowane env vars).
    """
    # Formatowanie treści SMS dla efektu demo
    is_en = (request.language or "pl").lower() == "en"
    print(f"\n{SEPARATOR}")
    print(f"📱 [SMS] WYSYŁKA PODSUMOWANIA")
    print(f"   Odbiorca : {request.phone_number}")
    if request.confirmation_id:
        print(f"   Nr ref.  : {request.confirmation_id}")
    print(f"   Język    : {'EN' if is_en else 'PL'}")
    print(f"   ─────────────────────────────────")
    print(f"   📩 TREŚĆ SMS:")
    print(f"   {request.summary_text}")
    print(SEPARATOR)

    # Opcjonalna integracja z Telegramem
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        await _wyslij_telegram(request)
    else:
        if is_en:
            print(f"   ℹ️  Telegram not configured — SMS printed to console only.")
        else:
            print(f"   ℹ️  Telegram nie skonfigurowany — SMS tylko w konsoli.")
            print(f"      (Ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID w env, aby wysyłać na Telegram)")

    return {
        "success": True,
        "message": "Message sent." if is_en else "Wiadomość wysłana.",
        "delivered_to": request.phone_number,
        "language": "en" if is_en else "pl",
    }


async def _wyslij_telegram(request: WysylkaSMS):
    """
    Pomocnicza funkcja — wysyła wiadomość na kanał Telegram.
    Wywoływana tylko gdy zmienne środowiskowe są skonfigurowane.
    """
    # Formatowanie estetycznej wiadomości Telegram z emoji
    tekst_telegram = (
        f"🏨 *Bukowy Dwór — Potwierdzenie Rezerwacji*\n\n"
        f"📞 Gość: `{request.phone_number}`\n"
    )
    if request.confirmation_id:
        tekst_telegram += f"🔖 Nr ref.: `{request.confirmation_id}`\n\n"
    tekst_telegram += f"📋 {request.summary_text}"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": tekst_telegram,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=5.0)
            if response.status_code == 200:
                print(f"   ✅ Wiadomość wysłana na Telegram (chat_id: {TELEGRAM_CHAT_ID})")
            else:
                print(f"   ⚠️  Błąd Telegram API: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"   ⚠️  Nie udało się wysłać na Telegram: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 5: Symulowany handoff — przekazanie rozmowy do człowieka (PoC)
# ─────────────────────────────────────────────────────────────────────────────

DZIALY = {
    "recepcja": "Recepcja główna",
    "dyzurka_medyczna": "Dyżurka medyczna (gabinet 101)",
}


@app.post("/transfer_to_simulated_handoff")
async def transfer_to_simulated_handoff(request: Handoff):
    """
    Symuluje przekazanie rozmowy do żywego pracownika (PoC).

    Zamiast realnego połączenia telefonicznego (które wymaga telefonii/SIP,
    niedostępnej na samym widgetcie) backend loguje zdarzenie do konsoli i —
    jeśli skonfigurowany — wysyła alert na Telegram. Efekt „wow" na demie:
    na drugim ekranie pojawia się informacja, że Anna prosi o asystę.
    """
    dzial = DZIALY.get((request.department or "").strip().lower(), request.department or "Recepcja")
    is_en = (request.language or "pl").lower() == "en"
    print(f"\n{SEPARATOR}")
    print(f"🛎️  [HANDOFF] PRZEKAZANIE DO CZŁOWIEKA")
    print(f"   Dział       : {dzial}")
    if request.guest_name:
        print(f"   Gość        : {request.guest_name}")
    if request.reason:
        print(f"   Powód       : {request.reason}")
    print(f"   Język       : {'EN' if is_en else 'PL'}")
    print(SEPARATOR)

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        await _wyslij_handoff_telegram(request, dzial)
    else:
        if is_en:
            print(f"   ℹ️  Telegram not configured — handoff logged to console only.")
        else:
            print(f"   ℹ️  Telegram nie skonfigurowany — handoff tylko w konsoli.")
            print(f"      (Ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID w env, aby wysyłać alert na Telegram)")

    return {
        "success": True,
        "simulated": True,
        "message": "Handoff to a human simulated (PoC — no telephony)." if is_en else "Przekazanie do człowieka zasymulowane (PoC — brak telefonii).",
        "department": dzial,
        "reason": request.reason,
        "guest_name": request.guest_name,
        "language": "en" if is_en else "pl",
        "note": "On production: wire transfer_to_number (SIP) or notify live reception staff." if is_en else "Na produkcji: podpiąć transfer_to_number (SIP) lub notyfikację do live receivable staff.",
    }


async def _wyslij_handoff_telegram(request: Handoff, dzial: str):
    """Wysyła alert o żądaniu asysty na kanał Telegram."""
    tekst = (
        f"🛎️ *Anna prosi o asystę — {dzial}*\n\n"
    )
    if request.guest_name:
        tekst += f"👤 Gość: `{request.guest_name}`\n"
    if request.reason:
        tekst += f"📋 Powód: {request.reason}\n"
    tekst += "\n_(To symulacja handoffu — na produkcji ustaw realne przekierowanie.)_"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": tekst,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=5.0)
            if response.status_code == 200:
                print(f"   ✅ Alert handoff wysłany na Telegram (chat_id: {TELEGRAM_CHAT_ID})")
            else:
                print(f"   ⚠️  Błąd Telegram API: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"   ⚠️  Nie udało się wysłać na Telegram: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT TESTOWY — weryfikacja że serwer działa
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Prosty endpoint do weryfikacji działania serwera."""
    return {
        "status": "OK",
        "projekt": "Wirtualny Recepcjonista AI — Bukowy Dwór",
        "wersja": "1.0.0 (PoC)",
        "endpointy": [
            "POST /check_spa_availability",
            "POST /book_spa_appointment",
            "POST /cancel_spa_appointment",
            "POST /reschedule_spa_appointment",
            "POST /check_room_availability",
            "POST /send_sms_summary",
            "POST /transfer_to_simulated_handoff",
        ],
        "docs": "http://localhost:8000/docs",
    }
