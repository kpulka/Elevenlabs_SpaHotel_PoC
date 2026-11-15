"""Modele żądań (Pydantic) i walidacja formatów danych wejściowych.

Kontrakt z agentem ElevenLabs: nazwy pól i ich znaczenie muszą pozostać zgodne
z docs/elevenlabs_agent_procedures.md. Nowe pola są wyłącznie opcjonalne.

Zasada: błędy FORMATU (zła data, zła godzina, puste imię) to HTTP 422 —
agent dostaje czytelny błąd walidacji. Błędy BIZNESOWE (termin w przeszłości,
zajęty slot, nieznany zabieg) zwracają HTTP 200 z ``available/success: false``
i wyjaśnieniem w ``message``, bo agent głosowy radzi sobie z tym znacznie lepiej.

Wspólne reguły są zdefiniowane raz jako typy ``Annotated`` (np. ``NazwaUslugi``, ``DataISO``)
i używane we wszystkich modelach, które ich potrzebują.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

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


def _waliduj_jezyk(wartosc: str | None) -> str:
    return "en" if (wartosc or "").strip().lower().startswith("en") else "pl"


def _niepusty(pole: str, komunikat: str | None = None) -> Callable[[str], str]:
    """Fabryka walidatora: przycina wartość i odrzuca pusty ciąg."""

    def _waliduj(wartosc: str) -> str:
        oczyszczona = wartosc.strip()
        if not oczyszczona:
            raise ValueError(komunikat or f"{pole} nie może być pusty.")
        return oczyszczona

    return _waliduj


def _numer_potwierdzenia(wartosc: str) -> str:
    return _niepusty("confirmation_id")(wartosc).upper()


def _klucz_idempotencji(wartosc: str | None) -> str | None:
    if wartosc is None or not wartosc.strip():
        return None
    return wartosc.strip()


def _telefon(wartosc: str) -> str:
    oczyszczona = wartosc.strip()
    if sum(znak.isdigit() for znak in oczyszczona) < 6:
        raise ValueError("phone_number musi zawierać co najmniej 6 cyfr (np. +48600100200).")
    return oczyszczona


def _termin_zabiegu(wartosc: str | None) -> str | None:
    return None if wartosc is None or not wartosc.strip() else _waliduj_date_czasu(wartosc)


# ─────────────────────────────────────────────────────────────────────────────
# Typy wspólne (raz zdefiniowane, używane w wielu modelach)
# ─────────────────────────────────────────────────────────────────────────────

NazwaUslugi = Annotated[
    str,
    Field(min_length=1, max_length=120),
    AfterValidator(_niepusty("service_name")),
]
DataISO = Annotated[str, AfterValidator(_waliduj_date)]
GodzinaHHMM = Annotated[str, AfterValidator(_waliduj_godzine)]
Jezyk = Annotated[str | None, AfterValidator(_waliduj_jezyk)]
NumerPotwierdzenia = Annotated[
    str,
    Field(min_length=1, max_length=40),
    AfterValidator(_numer_potwierdzenia),
]


class _ModelZJezykiem(BaseModel):
    language: Jezyk = "pl"


class _ModelZPotwierdzeniem(_ModelZJezykiem):
    """Bazowy model dla żądań wymagających identyfikatora potwierdzenia rezerwacji."""

    confirmation_id: NumerPotwierdzenia


class ZapytanieSPA(BaseModel):
    """Żądanie sprawdzenia dostępności zabiegu SPA."""

    service_name: NazwaUslugi
    date: DataISO


class RezerwacjaSPA(ZapytanieSPA):
    """Żądanie rezerwacji zabiegu SPA.

    ``idempotency_key`` (opcjonalny) pozwala bezpiecznie ponowić to samo żądanie: backend
    zwróci wtedy oryginalne potwierdzenie zamiast odmowy "slot zajęty".
    """

    time: GodzinaHHMM
    guest_name: Annotated[
        str,
        Field(min_length=1, max_length=120),
        AfterValidator(_niepusty("guest_name", "guest_name nie może być pusty — potrzebne do rezerwacji.")),
    ]
    idempotency_key: Annotated[str | None, Field(max_length=128), AfterValidator(_klucz_idempotencji)] = None


class AnulowanieSPA(_ModelZPotwierdzeniem):
    """Żądanie anulowania rezerwacji zabiegu SPA.

    Reguła (docs/elevenlabs_agent_procedures.md): odwołanie >2h przed terminem
    jest bezpłatne, <2h = 50% opłaty, chyba że powód jest medyczny.
    ``appointment_datetime`` jest opcjonalny (kompatybilność ze starymi
    wywołaniami agenta), ale bez niego backend nie zna godziny zabiegu.
    """

    reason: str | None = Field(default="", max_length=500)
    medical_release: bool | None = False
    appointment_datetime: Annotated[str | None, AfterValidator(_termin_zabiegu)] = None


class PrzelozenieSPA(_ModelZPotwierdzeniem):
    """Żądanie zmiany terminu zabiegu SPA (reschedule)."""

    service_name: NazwaUslugi
    new_date: DataISO
    new_time: GodzinaHHMM
    guest_name: str | None = Field(default="", max_length=120)


class SprawdzeniePokoj(BaseModel):
    """Żądanie sprawdzenia dostępności pokoju."""

    room_type: Annotated[
        str,
        Field(min_length=1, max_length=80),
        AfterValidator(_niepusty("room_type")),
    ]
    check_in: DataISO
    check_out: DataISO


class WysylkaSMS(_ModelZJezykiem):
    """Żądanie wysłania podsumowania SMS/Telegram."""

    phone_number: Annotated[str, Field(min_length=3, max_length=32), AfterValidator(_telefon)]
    summary_text: Annotated[
        str,
        Field(min_length=1, max_length=2000),
        AfterValidator(_niepusty("summary_text")),
    ]
    confirmation_id: str | None = ""


class Handoff(_ModelZJezykiem):
    """Żądanie symulowanego przekazania rozmowy do człowieka (PoC).

    Używane zamiast natywnego transfer_to_number, który wymaga realnej
    telefonii (SIP/telefonia). W PoC agent wywołuje ten webhook, a backend
    loguje zdarzenie do konsoli i (opcjonalnie) wysyła alert na Telegram.
    """

    department: str | None = Field(default="recepcja", max_length=40)  # recepcja | dyzurka_medyczna
    reason: str | None = Field(default="", max_length=500)
    guest_name: str | None = Field(default="", max_length=120)
