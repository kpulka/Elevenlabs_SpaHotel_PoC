"""Modele żądań (Pydantic) i walidacja formatów danych wejściowych.

Kontrakt z agentem ElevenLabs: nazwy pól i ich znaczenie muszą pozostać zgodne
z docs/elevenlabs_agent_procedures.md. Nowe pola są wyłącznie opcjonalne.

Zasada: błędy FORMATU (zła data, zła godzina, puste imię) to HTTP 422 —
agent dostaje czytelny błąd walidacji. Błędy BIZNESOWE (termin w przeszłości,
zajęty slot, nieznany zabieg) zwracają HTTP 200 z ``available/success: false``
i wyjaśnieniem w ``message``, bo agent głosowy radzi sobie z tym znacznie lepiej.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Godziny w formacie HH:MM — "99:99" nie przejdzie walidacji formatu.
FORMAT_GODZINY = "%H:%M"


def _waliduj_date(wartosc: str) -> str:
    """Wymusza ISO 8601 (YYYY-MM-DD); "31/08/2026" to błąd formatu, nie brak terminów."""
    oczyszczona = wartosc.strip()
    try:
        date.fromisoformat(oczyszczona)
    except ValueError as blad:
        raise ValueError(
            f"Nieprawidłowa data '{wartosc}'. Wymagany format ISO 8601: YYYY-MM-DD."
        ) from blad
    return oczyszczona


def _waliduj_godzine(wartosc: str) -> str:
    oczyszczona = wartosc.strip()
    try:
        datetime.strptime(oczyszczona, FORMAT_GODZINY)
    except ValueError as blad:
        raise ValueError(
            f"Nieprawidłowa godzina '{wartosc}'. Wymagany format HH:MM (np. 14:30)."
        ) from blad
    return oczyszczona


def _waliduj_date_czasu(wartosc: str) -> str:
    """Data i godzina zabiegu (ISO 8601, np. 2026-11-09T18:30) — podstawa reguły opłat."""
    oczyszczona = wartosc.strip().replace("Z", "+00:00")
    if len(oczyszczona) == 10:  # sama data bez godziny
        raise ValueError(
            "appointment_datetime wymaga godziny, np. 2026-11-09T18:30 (ISO 8601)."
        )
    try:
        datetime.fromisoformat(oczyszczona)
    except ValueError as blad:
        raise ValueError(
            f"Nieprawidłowy appointment_datetime '{wartosc}'. Wymagany ISO 8601, np. 2026-11-09T18:30."
        ) from blad
    return oczyszczona


def _waliduj_jezyk(wartosc: Optional[str]) -> str:
    return "en" if (wartosc or "").strip().lower().startswith("en") else "pl"


class _ModelZJezykiem(BaseModel):
    language: Optional[str] = "pl"

    @field_validator("language")
    @classmethod
    def _jezyk(cls, wartosc: Optional[str]) -> str:
        return _waliduj_jezyk(wartosc)


class ZapytanieSPA(BaseModel):
    """Żądanie sprawdzenia dostępności zabiegu SPA."""

    service_name: str = Field(..., min_length=1, max_length=120)
    date: str

    @field_validator("service_name")
    @classmethod
    def _nazwa(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError("service_name nie może być pusty.")
        return oczyszczona

    @field_validator("date")
    @classmethod
    def _data(cls, wartosc: str) -> str:
        return _waliduj_date(wartosc)


class RezerwacjaSPA(ZapytanieSPA):
    """Żądanie rezerwacji zabiegu SPA."""

    time: str
    guest_name: str = Field(..., min_length=1, max_length=120)

    @field_validator("time")
    @classmethod
    def _godzina(cls, wartosc: str) -> str:
        return _waliduj_godzine(wartosc)

    @field_validator("guest_name")
    @classmethod
    def _gosc(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError("guest_name nie może być pusty — potrzebne do rezerwacji.")
        return oczyszczona


class AnulowanieSPA(_ModelZJezykiem):
    """Żądanie anulowania rezerwacji zabiegu SPA.

    Reguła (docs/elevenlabs_agent_procedures.md): odwołanie >2h przed terminem
    jest bezpłatne, <2h = 50% opłaty, chyba że powód jest medyczny.
    ``appointment_datetime`` jest opcjonalny (kompatybilność ze starymi
    wywołaniami agenta), ale bez niego backend nie zna godziny zabiegu.
    """

    confirmation_id: str = Field(..., min_length=1, max_length=40)
    reason: Optional[str] = ""
    medical_release: Optional[bool] = False
    appointment_datetime: Optional[str] = None

    @field_validator("confirmation_id")
    @classmethod
    def _numer(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError("confirmation_id nie może być pusty.")
        return oczyszczona.upper()

    @field_validator("appointment_datetime")
    @classmethod
    def _termin(cls, wartosc: Optional[str]) -> Optional[str]:
        return None if wartosc is None or not wartosc.strip() else _waliduj_date_czasu(wartosc)


class PrzelozenieSPA(_ModelZJezykiem):
    """Żądanie zmiany terminu zabiegu SPA (reschedule)."""

    confirmation_id: str = Field(..., min_length=1, max_length=40)
    service_name: str = Field(..., min_length=1, max_length=120)
    new_date: str
    new_time: str
    guest_name: Optional[str] = ""

    @field_validator("confirmation_id")
    @classmethod
    def _numer(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError("confirmation_id nie może być pusty.")
        return oczyszczona.upper()

    @field_validator("service_name")
    @classmethod
    def _nazwa(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError("service_name nie może być pusty.")
        return oczyszczona

    @field_validator("new_date")
    @classmethod
    def _data(cls, wartosc: str) -> str:
        return _waliduj_date(wartosc)

    @field_validator("new_time")
    @classmethod
    def _godzina(cls, wartosc: str) -> str:
        return _waliduj_godzine(wartosc)


class SprawdzeniePokoj(BaseModel):
    """Żądanie sprawdzenia dostępności pokoju."""

    room_type: str = Field(..., min_length=1, max_length=80)
    check_in: str
    check_out: str

    @field_validator("room_type")
    @classmethod
    def _typ(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError("room_type nie może być pusty.")
        return oczyszczona

    @field_validator("check_in", "check_out")
    @classmethod
    def _data(cls, wartosc: str) -> str:
        return _waliduj_date(wartosc)


class WysylkaSMS(_ModelZJezykiem):
    """Żądanie wysłania podsumowania SMS/Telegram."""

    phone_number: str = Field(..., min_length=3, max_length=32)
    summary_text: str = Field(..., min_length=1, max_length=2000)
    confirmation_id: Optional[str] = ""

    @field_validator("phone_number")
    @classmethod
    def _telefon(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if sum(znak.isdigit() for znak in oczyszczona) < 6:
            raise ValueError(
                "phone_number musi zawierać co najmniej 6 cyfr (np. +48600100200)."
            )
        return oczyszczona

    @field_validator("summary_text")
    @classmethod
    def _tresc(cls, wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError("summary_text nie może być pusty.")
        return oczyszczona


class Handoff(_ModelZJezykiem):
    """Żądanie symulowanego przekazania rozmowy do człowieka (PoC).

    Używane zamiast natywnego transfer_to_number, który wymaga realnej
    telefonii (SIP/telefonia). W PoC agent wywołuje ten webhook, a backend
    loguje zdarzenie do konsoli i (opcjonalnie) wysyła alert na Telegram.
    """

    department: Optional[str] = "recepcja"  # recepcja | dyzurka_medyczna
    reason: Optional[str] = ""
    guest_name: Optional[str] = ""
