"""Endpointy komunikacji: SMS / Telegram oraz symulowany handoff do personelu."""

from __future__ import annotations

from fastapi import APIRouter

from schemas import Handoff, WysylkaSMS
from state import demo_log
import telegram

router = APIRouter(tags=["comms"])

DZIALY = {
    "recepcja": "Recepcja główna",
    "dyzurka_medyczna": "Dyżurka medyczna (gabinet 101)",
}


def _tekst_sms_na_telegram(request: WysylkaSMS) -> str:
    tekst = f"🏨 *Bukowy Dwór — Potwierdzenie Rezerwacji*\n\n📞 Gość: `{request.phone_number}`\n"
    if request.confirmation_id:
        tekst += f"🔖 Nr ref.: `{request.confirmation_id}`\n"
    return tekst + f"\n📋 {request.summary_text}"


def _tekst_handoffu(request: Handoff, dzial: str) -> str:
    tekst = f"🛎️ *Anna prosi o asystę — {dzial}*\n\n"
    if request.guest_name:
        tekst += f"👤 Gość: `{request.guest_name}`\n"
    if request.reason:
        tekst += f"📋 Powód: {request.reason}\n"
    return tekst + "\n_(To symulacja handoffu — na produkcji ustaw realne przekierowanie.)_"


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 6: Wysyłka SMS / Podsumowanie przez Telegram
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/send_sms_summary")
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

@router.post("/transfer_to_simulated_handoff")
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
