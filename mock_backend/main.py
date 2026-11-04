"""
Mock PMS (Property Management System) backend for the AI voice receptionist PoC.

Hotel:    Uzdrowisko Bukowy Dwór, Krynica-Zdrój (Poland)
Purpose:  Simulates the hotel's booking system (PMS) and receives tool webhooks
          from the ElevenLabs Conversational AI agent ("Anna").

All data in this service is synthetic.

Run locally:
    uvicorn main:app --reload --port 8011
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
# APPLICATION SETUP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Mock PMS — Bukowy Dwór",
    description="Mock backend for the AI voice receptionist PoC (ElevenLabs Agent).",
    version="1.0.0",
)

# CORS: allow all origins (required for ElevenLabs webhook calls)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional Telegram integration (configured via environment variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SEPARATOR = "=" * 60

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA: SPA TREATMENTS
# The schedule is generated dynamically for the next 14 days.
# Treatment names are domain data in Polish and are matched by the agent's prompt.
# ─────────────────────────────────────────────────────────────────────────────

AVAILABLE_TREATMENTS = [
    "kąpiel siarczkowa Ukojenie Stawów",  # sulphur bath
    "masaż leczniczy pleców",             # therapeutic back massage
    "kąpiel borowinowa",                  # peat (mud) bath
    "jonoforeza",                         # iontophoresis
    "masaż klasyczny",                    # classic massage
]

TIME_SLOTS = ["10:00", "11:00", "14:00", "14:30", "15:00", "16:00"]


def generate_spa_schedule() -> dict:
    """
    Generates a dictionary of available SPA slots for the next 14 days.
    Structure: treatment name -> date (YYYY-MM-DD) -> list of time slots.
    """
    schedule = {}
    today = datetime.now().date()

    for treatment in AVAILABLE_TREATMENTS:
        schedule[treatment] = {}
        for i in range(14):
            day = today + timedelta(days=i)
            date_str = day.strftime("%Y-%m-%d")
            schedule[treatment][date_str] = TIME_SLOTS.copy()

    return schedule


# Generate the schedule once at server startup
SPA_SCHEDULE = generate_spa_schedule()

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA: ROOMS
# ─────────────────────────────────────────────────────────────────────────────

# Room type keys are domain data (Polish) and must match the agent's tool calls.
ROOM_PRICES = {
    "jednoosobowy": 350,  # single room, PLN per night
    "dwuosobowy": 500,    # double room, PLN per night
    "apartament": 750,    # apartment, PLN per night
}

# Blocked dates: summer weekend 30-31 August 2026 (all room types)
BLOCKED_DATES = {"2026-08-30", "2026-08-31"}


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS (Pydantic)
# ─────────────────────────────────────────────────────────────────────────────

class SpaAvailabilityRequest(BaseModel):
    """Request to check SPA treatment availability."""
    service_name: str
    date: str


class SpaBookingRequest(BaseModel):
    """Request to book an SPA treatment."""
    service_name: str
    date: str
    time: str
    guest_name: str


class SpaCancellationRequest(BaseModel):
    """Request to cancel an SPA treatment booking.

    Follows the cancellation procedure (docs/elevenlabs_agent_procedures.md):
    cancellation more than 2h before the appointment is free of charge; less than
    2h before, a 50% fee applies unless there is a medical reason (then 100% free).
    """
    confirmation_id: str  # booking reference, format SPA-XXXX
    reason: Optional[str] = ""  # e.g. "deterioration of health", "change of plans"
    medical_release: Optional[bool] = False  # True = medical release (no fee)
    language: Optional[str] = "pl"


class SpaRescheduleRequest(BaseModel):
    """Request to change the date/time of an SPA treatment (reschedule)."""
    confirmation_id: str  # booking reference, format SPA-XXXX
    service_name: str
    new_date: str
    new_time: str
    guest_name: Optional[str] = ""
    language: Optional[str] = "pl"


class RoomAvailabilityRequest(BaseModel):
    """Request to check room availability."""
    room_type: str
    check_in: str
    check_out: str


class SmsSummaryRequest(BaseModel):
    """Request to send a booking summary via SMS / Telegram."""
    phone_number: str
    summary_text: str
    confirmation_id: Optional[str] = ""
    language: Optional[str] = "pl"  # pl | en: language selected by the guest on the website


class HandoffRequest(BaseModel):
    """Request for a simulated handoff of the call to a human (PoC).

    Used instead of the native transfer_to_number tool, which requires real
    telephony (SIP). In the PoC the agent calls this webhook; the backend logs
    the event to the console and, optionally, sends an alert via Telegram.
    """
    department: Optional[str] = "recepcja"  # recepcja (reception) | dyzurka_medyczna (medical duty room)
    reason: Optional[str] = ""
    guest_name: Optional[str] = ""
    language: Optional[str] = "pl"  # pl | en: language selected by the guest on the website


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 1: Check SPA treatment availability
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/check_spa_availability")
async def check_spa_availability(request: SpaAvailabilityRequest):
    """
    Checks SPA treatment availability for a given day.
    Simulates a query to the spa's PMS.
    """
    print(f"\n{SEPARATOR}")
    print(f"📅 [SPA] AVAILABILITY CHECK")
    print(f"   Treatment : {request.service_name}")
    print(f"   Date      : {request.date}")
    print(SEPARATOR)

    # Case-insensitive, substring match for demo convenience
    treatment_key = None
    for treatment in AVAILABLE_TREATMENTS:
        if request.service_name.lower().strip() in treatment.lower():
            treatment_key = treatment
            break

    # Unknown treatment: return the list of available treatments
    if treatment_key is None:
        print(f"   ⚠️  Unknown treatment '{request.service_name}'. Returning the list of available treatments.")
        return {
            "available": False,
            # Guest-facing text in Polish, read out by the agent.
            # EN: "The treatment '<name>' is not offered in our SPA."
            "message": f"Zabieg '{request.service_name}' nie jest oferowany w naszym SPA.",
            "available_services": AVAILABLE_TREATMENTS,
        }

    # Fetch the slots for the requested day
    slots = SPA_SCHEDULE.get(treatment_key, {}).get(request.date, [])

    if slots:
        print(f"   ✅ Available slots: {', '.join(slots)}")
        return {
            "available": True,
            "slots": slots,
            "service_name": treatment_key,
            "date": request.date,
        }
    else:
        print(f"   ❌ No free slots for '{treatment_key}' on {request.date}.")
        return {
            "available": False,
            # EN: "No free slots for '<name>' on <date>."
            "message": f"Brak wolnych terminów dla '{treatment_key}' w dniu {request.date}.",
            "available_services": AVAILABLE_TREATMENTS,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2: Book an SPA treatment
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/book_spa_appointment")
async def book_spa_appointment(request: SpaBookingRequest):
    """
    Books an SPA treatment for a guest.
    Simulates a write to the PMS; always succeeds (PoC).
    Generates a random confirmation number in the format SPA-XXXX.
    """
    # Random 4-digit confirmation number
    confirmation_id = f"SPA-{random.randint(1000, 9999)}"

    print(f"\n{SEPARATOR}")
    print(f"✍️  [SPA] NEW TREATMENT BOOKING")
    print(f"   Confirmation ID : {confirmation_id}")
    print(f"   Guest           : {request.guest_name}")
    print(f"   Treatment       : {request.service_name}")
    print(f"   Date            : {request.date}")
    print(f"   Time            : {request.time}")
    print(SEPARATOR)

    return {
        "success": True,
        "confirmation_id": confirmation_id,
        "service_name": request.service_name,
        "date": request.date,
        "time": request.time,
        "guest_name": request.guest_name,
        # Guest-facing text in Polish, read out by the agent.
        # EN: "Booking confirmed."
        "message": "Rezerwacja potwierdzona.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2b: Cancel an SPA treatment booking
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/cancel_spa_appointment")
async def cancel_spa_appointment(request: SpaCancellationRequest):
    """
    Cancels an SPA treatment booking.

    Per the cancellation procedure (docs/elevenlabs_agent_procedures.md):
    - Cancellation more than 2h before the appointment: free of charge.
    - Cancellation less than 2h before: 50% fee, UNLESS medical_release=True
      (medical release: 100% free of charge).
    PoC: always succeeds (no real PMS); logs the decision.
    """
    is_en = (request.language or "pl").lower() == "en"
    is_free = bool(request.medical_release)
    fee = 0 if is_free else 0.5  # PoC: 50% fee when cancelled <2h before, without medical release

    print(f"\n{SEPARATOR}")
    print(f"🗑️  [SPA] BOOKING CANCELLATION")
    print(f"   Confirmation ID  : {request.confirmation_id}")
    if request.reason:
        print(f"   Reason           : {request.reason}")
    print(f"   Medical release  : {'YES (no fee)' if is_free else 'NO'}")
    print(f"   Fee              : {'0 PLN (100% free)' if is_free else '50% fee (cancelled <2h before)'}")
    print(SEPARATOR)

    return {
        "success": True,
        "confirmation_id": request.confirmation_id,
        "cancelled": True,
        "fee": fee,
        "medical_release": is_free,
        "message": "Reservation cancelled." if is_en else "Rezerwacja anulowana.",
        "note": "Free of charge." if is_free else "Standard cancellation fee applies (50%) if within 2h of the appointment.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2c: Reschedule an SPA treatment
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/reschedule_spa_appointment")
async def reschedule_spa_appointment(request: SpaRescheduleRequest):
    """
    Changes the date/time of an SPA treatment (reschedule).

    Per procedure: rescheduling is free of charge, subject to the availability
    of physiotherapists and balneologists.
    PoC: always succeeds; logs the new slot.
    """
    is_en = (request.language or "pl").lower() == "en"
    new_confirmation_id = f"SPA-{random.randint(1000, 9999)}"

    print(f"\n{SEPARATOR}")
    print(f"🔁 [SPA] TREATMENT RESCHEDULE")
    print(f"   Confirmation ID : {request.confirmation_id} → {new_confirmation_id}")
    print(f"   Treatment       : {request.service_name}")
    print(f"   New slot        : {request.new_date} {request.new_time}")
    if request.guest_name:
        print(f"   Guest           : {request.guest_name}")
    print(SEPARATOR)

    return {
        "success": True,
        "confirmation_id": new_confirmation_id,
        "service_name": request.service_name,
        "new_date": request.new_date,
        "new_time": request.new_time,
        "guest_name": request.guest_name,
        # Guest-facing text in Polish, read out by the agent (EN branch provided).
        "message": "Appointment rescheduled." if is_en else "Termin zabiegu zmieniony.",
        "note": "Rescheduling is free of charge." if is_en else "Zmiana terminu jest bezpłatna.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 3: Check room availability
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/check_room_availability")
async def check_room_availability(request: RoomAvailabilityRequest):
    """
    Checks room availability for a given date range and returns the total price.
    Logic: the weekend of 30-31 Aug 2026 is always fully booked.
    """
    print(f"\n{SEPARATOR}")
    print(f"🏨 [ROOMS] AVAILABILITY CHECK")
    print(f"   Room type : {request.room_type}")
    print(f"   Check-in  : {request.check_in}")
    print(f"   Check-out : {request.check_out}")
    print(SEPARATOR)

    # Validate the room type
    price_per_night = ROOM_PRICES.get(request.room_type.lower())
    if price_per_night is None:
        print(f"   ⚠️  Unknown room type: '{request.room_type}'")
        return {
            "available": False,
            "room_type": request.room_type,
            # Guest-facing text in Polish, read out by the agent.
            # EN: "Room type '<type>' does not exist. Available: [...]"
            "message": f"Typ pokoju '{request.room_type}' nie istnieje. Dostępne: {list(ROOM_PRICES.keys())}",
        }

    # Parse dates and compute the number of nights
    try:
        check_in_date = datetime.strptime(request.check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(request.check_out, "%Y-%m-%d").date()
        nights = (check_out_date - check_in_date).days
    except ValueError:
        return {
            "available": False,
            # EN: "Invalid date format. Use YYYY-MM-DD."
            "message": "Nieprawidłowy format daty. Użyj formatu YYYY-MM-DD.",
        }

    if nights <= 0:
        return {
            "available": False,
            # EN: "The check-out date must be after the check-in date."
            "message": "Data wymeldowania musi być późniejsza niż data zameldowania.",
        }

    # Check whether the stay overlaps the blocked weekend 30-31 Aug 2026.
    # Build the set of nights covered by the stay.
    stay_dates = set()
    for i in range(nights):
        day = check_in_date + timedelta(days=i)
        stay_dates.add(day.strftime("%Y-%m-%d"))

    is_booked = bool(stay_dates & BLOCKED_DATES)

    total_price = price_per_night * nights

    if is_booked:
        print(f"   ❌ BOOKED: the stay overlaps the blocked weekend (30-31.08.2026).")
        return {
            "available": False,
            "room_type": request.room_type,
            "price_per_night": price_per_night,
            "check_in": request.check_in,
            "check_out": request.check_out,
            "total_nights": nights,
            "total_price": total_price,
            # EN: "No availability for the selected dates. Peak season: all rooms booked."
            "message": "Brak dostępności w wybranym terminie. Szczyt sezonu — wszystkie pokoje zajęte.",
        }

    print(f"   ✅ AVAILABLE: {nights} night(s) × {price_per_night} PLN = {total_price} PLN total.")
    return {
        "available": True,
        "room_type": request.room_type,
        "price_per_night": price_per_night,
        "check_in": request.check_in,
        "check_out": request.check_out,
        "total_nights": nights,
        "total_price": total_price,
        # EN: "Room available. Price: <total> PLN for <n> night(s)."
        "message": f"Pokój dostępny. Cena: {total_price} PLN za {nights} noc(y).",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 4: SMS / booking summary via Telegram
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/send_sms_summary")
async def send_sms_summary(request: SmsSummaryRequest):
    """
    Simulates sending an SMS with a booking summary.
    Demo mode: prints the SMS body to the console (visible during live demos).
    Optionally forwards the message to a Telegram chat if env vars are set.
    """
    is_en = (request.language or "pl").lower() == "en"
    print(f"\n{SEPARATOR}")
    print(f"📱 [SMS] SENDING SUMMARY")
    print(f"   Recipient : {request.phone_number}")
    if request.confirmation_id:
        print(f"   Ref. no.  : {request.confirmation_id}")
    print(f"   Language  : {'EN' if is_en else 'PL'}")
    print(f"   ─────────────────────────────────")
    print(f"   📩 SMS BODY:")
    print(f"   {request.summary_text}")
    print(SEPARATOR)

    # Optional Telegram integration
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        await _send_telegram_message(request)
    else:
        print(f"   ℹ️  Telegram not configured — SMS printed to console only.")
        print(f"      (Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment to send to Telegram)")

    return {
        "success": True,
        # Guest-facing text in Polish (EN branch provided).
        "message": "Message sent." if is_en else "Wiadomość wysłana.",
        "delivered_to": request.phone_number,
        "language": "en" if is_en else "pl",
    }


async def _send_telegram_message(request: SmsSummaryRequest):
    """
    Sends the booking summary to the configured Telegram chat.
    Only called when TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set.
    The message body is intentionally in Polish: it is shown to hotel staff.
    """
    telegram_text = (
        f"🏨 *Bukowy Dwór — Potwierdzenie Rezerwacji*\n\n"
        f"📞 Gość: `{request.phone_number}`\n"
    )
    if request.confirmation_id:
        telegram_text += f"🔖 Nr ref.: `{request.confirmation_id}`\n\n"
    telegram_text += f"📋 {request.summary_text}"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": telegram_text,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=5.0)
            if response.status_code == 200:
                print(f"   ✅ Message sent to Telegram (chat_id: {TELEGRAM_CHAT_ID})")
            else:
                print(f"   ⚠️  Telegram API error: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"   ⚠️  Failed to send to Telegram: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 5: Simulated handoff to a human (PoC)
# ─────────────────────────────────────────────────────────────────────────────

# Department keys are domain data; display names are shown to staff/guests.
DEPARTMENTS = {
    "recepcja": "Recepcja główna",                    # main reception
    "dyzurka_medyczna": "Dyżurka medyczna (gabinet 101)",  # medical duty room (room 101)
}


@app.post("/transfer_to_simulated_handoff")
async def transfer_to_simulated_handoff(request: HandoffRequest):
    """
    Simulates handing the conversation over to a live staff member (PoC).

    Instead of a real phone transfer (which needs telephony/SIP and is not
    available in the website widget), the backend logs the event to the console
    and, if configured, sends an alert via Telegram. Demo effect: a second screen
    shows that Anna is requesting assistance.
    """
    department = DEPARTMENTS.get((request.department or "").strip().lower(), request.department or "Recepcja")
    is_en = (request.language or "pl").lower() == "en"
    print(f"\n{SEPARATOR}")
    print(f"🛎️  [HANDOFF] HANDOFF TO HUMAN STAFF")
    print(f"   Department : {department}")
    if request.guest_name:
        print(f"   Guest      : {request.guest_name}")
    if request.reason:
        print(f"   Reason     : {request.reason}")
    print(f"   Language   : {'EN' if is_en else 'PL'}")
    print(SEPARATOR)

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        await _send_handoff_telegram_alert(request, department)
    else:
        print(f"   ℹ️  Telegram not configured — handoff logged to console only.")
        print(f"      (Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment to send a Telegram alert)")

    return {
        "success": True,
        "simulated": True,
        # Guest-facing text in Polish (EN branch provided).
        "message": "Handoff to a human simulated (PoC — no telephony)." if is_en else "Przekazanie do człowieka zasymulowane (PoC — brak telefonii).",
        "department": department,
        "reason": request.reason,
        "guest_name": request.guest_name,
        "language": "en" if is_en else "pl",
        # Polish text (EN branch provided). Note: the Polish phrase "live receivable staff"
        # is a typo for "live reception staff" and is kept as-is to keep behavior identical.
        "note": "On production: wire transfer_to_number (SIP) or notify live reception staff." if is_en else "Na produkcji: podpiąć transfer_to_number (SIP) lub notyfikację do live receivable staff.",
    }


async def _send_handoff_telegram_alert(request: HandoffRequest, department: str):
    """Sends an alert about the assistance request to the Telegram chat.
    The message body is intentionally in Polish: it is shown to hotel staff."""
    text = (
        f"🛎️ *Anna prosi o asystę — {department}*\n\n"
    )
    if request.guest_name:
        text += f"👤 Gość: `{request.guest_name}`\n"
    if request.reason:
        text += f"📋 Powód: {request.reason}\n"
    text += "\n_(To symulacja handoffu — na produkcji ustaw realne przekierowanie.)_"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=5.0)
            if response.status_code == 200:
                print(f"   ✅ Handoff alert sent to Telegram (chat_id: {TELEGRAM_CHAT_ID})")
            else:
                print(f"   ⚠️  Telegram API error: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"   ⚠️  Failed to send to Telegram: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK: verify the server is running
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Simple endpoint to verify that the server is running."""
    return {
        "status": "OK",
        # Response keys "projekt", "wersja" and "endpointy" are Polish and kept
        # intentionally (they are part of the response contract).
        "projekt": "Wirtualny Recepcjonista AI — Bukowy Dwór",  # "Virtual AI Receptionist — Bukowy Dwór"
        "wersja": "1.0.0 (PoC)",  # "version 1.0.0 (PoC)"
        "endpointy": [  # "endpoints"
            "POST /check_spa_availability",
            "POST /book_spa_appointment",
            "POST /cancel_spa_appointment",
            "POST /reschedule_spa_appointment",
            "POST /check_room_availability",
            "POST /send_sms_summary",
            "POST /transfer_to_simulated_handoff",
        ],
        "docs": "http://localhost:8011/docs",
    }
