"""Odpowiedzi HTTP dla endpointu cancel_spa_appointment."""

from __future__ import annotations

from i18n import lang_of, pick
from logs import log_demo, log_event
from responses._common import REGULY_OPLAT
from schemas import AnulowanieSPA
from services.spa import WynikAnulowania


def anulowanie(request: AnulowanieSPA, wynik: WynikAnulowania) -> dict:
    lang = lang_of(request)
    if not wynik.znaleziona:
        log_event(
            "reservation_not_found",
            demo=f"   ❌ Nie znaleziono rezerwacji '{request.confirmation_id}' — nie anulowano.",
            confirmation_id=request.confirmation_id,
        )
        return {
            "success": False,
            "confirmation_id": request.confirmation_id,
            "cancelled": False,
            "fee": 0.0,
            "medical_release": bool(request.medical_release),
            "free_of_charge": True,
            "fee_rule": pick(
                lang,
                "Nie znaleziono rezerwacji — nie naliczono opłaty (0%).",
                "Reservation not found — no fee charged (0%).",
            ),
            "found": False,
            "message": pick(
                lang,
                f"Nie znaleziono rezerwacji o numerze {request.confirmation_id}. "
                "Poproś gościa o ponowne sprawdzenie numeru potwierdzenia.",
                f"No reservation found with number {request.confirmation_id}. "
                "Ask the guest to re-check the confirmation number.",
            ),
            "note": pick(lang, "Rezerwacja nie została anulowana.", "Reservation was not cancelled."),
        }

    oplata = wynik.oplata
    assert oplata is not None, "znaleziona rezerwacja musi mieć obliczoną opłatę"
    regula_pl, regula_en = REGULY_OPLAT[oplata.regula]
    regula = pick(lang, regula_pl, regula_en)
    bezplatna = oplata.ulamek == 0.0

    log_demo(
        "🗑️  [SPA] ANULOWANIE REZERWACJI (demo log)",
        f"   ID Potwierdzenia : {request.confirmation_id}",
        f"   Powód            : {request.reason or '-'}",
        f"   Termin zabiegu   : {request.appointment_datetime or 'nieznany'}",
        f"   Zwolnienie med.  : {'TAK' if request.medical_release else 'NIE'}",
        f"   Reguła           : {regula}",
        f"   Slot zwolniony   : {'TAK' if wynik.zwolniona else 'nie (brak w pamięci)'}",
    )

    notatka = pick(
        lang,
        "Bezpłatna." if bezplatna else "Obowiązuje opłata 50% ceny zabiegu.",
        "Free of charge." if bezplatna else "Cancellation fee applies (50% of the service price).",
    )

    return {
        "success": True,
        "confirmation_id": request.confirmation_id,
        "cancelled": True,
        "fee": oplata.ulamek,
        "medical_release": bool(request.medical_release),
        "free_of_charge": bezplatna,
        "fee_rule": regula,
        "found": True,
        "message": pick(lang, "Rezerwacja anulowana.", "Reservation cancelled."),
        "note": notatka,
    }
