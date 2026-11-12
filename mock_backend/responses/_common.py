"""Wspólne definicje dla pakietu responses."""

from __future__ import annotations

from services.spa import RegulaOplaty

# (wersja polska, wersja angielska) — tekst reguły opłat trafia do odpowiedzi i logu demo.
REGULY_OPLAT = {
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


def odmowa(przed: dict, komunikat: str, po: dict | None = None) -> dict:
    """Jedna fabryka odmowy: wspólny kształt `success: False` + `message`, reszta z kontekstu endpointu."""
    print(f"   ❌ {komunikat}")
    return {"success": False, **przed, "message": komunikat, **(po or {})}
