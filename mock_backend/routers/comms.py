"""Endpointy komunikacji: SMS / Telegram oraz symulowany handoff do personelu.

PII: numer telefonu w odpowiedzi, logach i na Telegramie jest maskowany (``mask_phone``), imię gościa
w alertach i logach jest skracane (``mask_name``), a numery wpisane w wolnym tekście powodu są
redagowane (``redact_phones``). Zdarzenie ``handoff.requested`` używa tej samej maskowanej postaci.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends

import events
import telegram
from i18n import lang_of, pick
from logs import log_demo, log_event, mask_name, mask_phone, redact_phones
from routers.security import require_webhook_secret
from schemas import Handoff, WysylkaSMS

router = APIRouter(tags=["comms"], dependencies=[Depends(require_webhook_secret)])

DZIALY = {
    "recepcja": "Recepcja główna",
    "dyzurka_medyczna": "Dyżurka medyczna (gabinet 101)",
}


def _tekst_sms_na_telegram(request: WysylkaSMS) -> str:
    tekst = f"🏨 *Bukowy Dwór — Potwierdzenie Rezerwacji*\n\n📞 Gość: `{mask_phone(request.phone_number)}`\n"
    if request.confirmation_id:
        tekst += f"🔖 Nr ref.: `{request.confirmation_id}`\n"
    return tekst + f"\n📋 {request.summary_text}"


def _tekst_handoffu(request: Handoff, dzial: str) -> str:
    tekst = f"🛎️ *Anna prosi o asystę — {dzial}*\n\n"
    if request.guest_name:
        tekst += f"👤 Gość: `{mask_name(request.guest_name)}`\n"
    if request.reason:
        tekst += f"📋 Powód: {redact_phones(request.reason)}\n"
    return tekst + "\n_(To symulacja handoffu — na produkcji ustaw realne przekierowanie.)_"


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 6: Wysyłka SMS / Podsumowanie przez Telegram
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/send_sms_summary")
async def send_sms_summary(request: WysylkaSMS, background: BackgroundTasks):
    """Symuluje wysyłkę SMS: drukuje treść (demo) i opcjonalnie wysyła na Telegram w tle."""
    lang = lang_of(request)
    telegram_wlaczony = telegram.skonfigurowany()
    log_event(
        "sms_summary_requested",
        phone=mask_phone(request.phone_number),
        confirmation_id=request.confirmation_id or None,
        telegram=telegram_wlaczony,
    )
    log_demo(
        "📱 [SMS] WYSYŁKA PODSUMOWANIA (demo log)",
        f"   Odbiorca : {mask_phone(request.phone_number)}",
        f"   Nr ref.  : {request.confirmation_id or '-'}",
        f"   Język    : {pick(lang, 'PL', 'EN')}",
        "   📩 TREŚĆ SMS:",
        f"   {request.summary_text}",
    )

    if telegram_wlaczony:
        # Wysyłka w tle: odpowiedź dla agenta nie czeka na Telegram; błędy tylko w logu.
        background.add_task(telegram.wyslij_wiadomosc, _tekst_sms_na_telegram(request), etykieta="SMS")
    else:
        log_event(
            "telegram_not_configured",
            demo=pick(
                lang,
                "   ℹ️  Telegram nie skonfigurowany — SMS tylko w konsoli "
                "(ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID).",
                "   ℹ️  Telegram not configured — SMS printed to console only.",
            ),
            channel="SMS",
        )

    return {
        "success": True,
        "message": pick(lang, "Wiadomość wysłana.", "Message sent."),
        "delivered_to": mask_phone(request.phone_number),
        "language": request.language,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 7: Symulowany handoff — przekazanie rozmowy do człowieka (PoC)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/transfer_to_simulated_handoff")
async def transfer_to_simulated_handoff(request: Handoff, background: BackgroundTasks):
    """Symuluje przekazanie rozmowy do żywego pracownika (PoC, bez telefonii)."""
    dzial = DZIALY.get((request.department or "").strip().lower(), request.department or "Recepcja")
    lang = lang_of(request)
    telegram_wlaczony = telegram.skonfigurowany()
    log_event("handoff_requested", department=dzial, telegram=telegram_wlaczony)
    log_demo(
        "🛎️  [HANDOFF] PRZEKAZANIE DO CZŁOWIEKA (demo log)",
        f"   Dział : {dzial}",
        f"   Gość  : {mask_name(request.guest_name) or '-'}",
        f"   Powód : {redact_phones(request.reason) or '-'}",
        f"   Język : {pick(lang, 'PL', 'EN')}",
    )

    if telegram_wlaczony:
        background.add_task(telegram.wyslij_wiadomosc, _tekst_handoffu(request, dzial), etykieta="Alert handoff")
    else:
        log_event(
            "telegram_not_configured",
            demo=pick(
                lang,
                "   ℹ️  Telegram nie skonfigurowany — handoff tylko w konsoli "
                "(ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID).",
                "   ℹ️  Telegram not configured — handoff logged to console only.",
            ),
            channel="handoff",
        )

    events.schedule(
        background,
        "handoff.requested",
        {
            "department": dzial,
            "reason": redact_phones(request.reason or ""),
            "guest_name": mask_name(request.guest_name or ""),
            "language": lang,
        },
    )

    return {
        "success": True,
        "simulated": True,
        "message": pick(
            lang,
            "Przekazanie do człowieka zasymulowane (PoC — brak telefonii).",
            "Handoff to a human simulated (PoC — no telephony).",
        ),
        "department": dzial,
        "reason": request.reason,
        "guest_name": request.guest_name,
        "language": request.language,
        "note": pick(
            lang,
            "Na produkcji: podpiąć transfer_to_number (SIP) lub powiadomienie do recepcji.",
            "On production: wire transfer_to_number (SIP) or notify live reception staff.",
        ),
    }
