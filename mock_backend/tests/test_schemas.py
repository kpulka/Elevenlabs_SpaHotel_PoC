"""Validators shared through the Annotated types in ``schemas.py``: formats (422) and normalisation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import AnulowanieSPA, PrzelozenieSPA, RezerwacjaSPA, WysylkaSMS, ZapytanieSPA, _ModelZJezykiem


def test_appointment_datetime_requires_a_time():
    with pytest.raises(ValidationError, match="wymaga godziny"):
        AnulowanieSPA(confirmation_id="SPA-1", appointment_datetime="2026-11-09")


def test_appointment_datetime_must_be_iso():
    with pytest.raises(ValidationError, match="Nieprawidłowy appointment_datetime"):
        AnulowanieSPA(confirmation_id="SPA-1", appointment_datetime="jutro po obiedzie")


def test_appointment_datetime_accepts_zulu_suffix_and_blank_becomes_none():
    assert AnulowanieSPA(confirmation_id="SPA-1", appointment_datetime="2026-11-09T18:30Z").appointment_datetime == (
        "2026-11-09T18:30+00:00"  # the validated text, with "Z" replaced by an explicit offset
    )
    assert AnulowanieSPA(confirmation_id="SPA-1", appointment_datetime="   ").appointment_datetime is None


def test_confirmation_id_is_trimmed_and_uppercased():
    assert AnulowanieSPA(confirmation_id="  spa-1001 ").confirmation_id == "SPA-1001"


@pytest.mark.parametrize("model", [ZapytanieSPA, PrzelozenieSPA])
def test_service_name_validator_is_shared_by_availability_and_reschedule(model):
    dane = {"service_name": "   ", "date": "2026-11-20"}
    if model is PrzelozenieSPA:
        dane = {"confirmation_id": "SPA-1", "service_name": "   ", "new_date": "2026-11-20", "new_time": "10:00"}
    with pytest.raises(ValidationError, match="service_name nie może być pusty"):
        model(**dane)


def test_date_validator_rejects_non_iso_for_both_date_fields():
    with pytest.raises(ValidationError, match="ISO 8601"):
        ZapytanieSPA(service_name="masaż klasyczny", date="31/08/2026")
    with pytest.raises(ValidationError, match="ISO 8601"):
        PrzelozenieSPA(confirmation_id="SPA-1", service_name="masaż", new_date="31/08/2026", new_time="10:00")


def test_time_validator_rejects_out_of_range_hour():
    with pytest.raises(ValidationError, match="HH:MM"):
        RezerwacjaSPA(
            service_name="masaż klasyczny", date="2026-11-20", time="99:99", guest_name="Jan"
        )


def test_guest_name_blank_has_dedicated_message():
    with pytest.raises(ValidationError, match="potrzebne do rezerwacji"):
        RezerwacjaSPA(service_name="masaż klasyczny", date="2026-11-20", time="10:00", guest_name="   ")


def test_blank_idempotency_key_becomes_none():
    rezerwacja = RezerwacjaSPA(
        service_name="masaż klasyczny", date="2026-11-20", time="10:00", guest_name="Jan", idempotency_key="  "
    )
    assert rezerwacja.idempotency_key is None


@pytest.mark.parametrize("wejscie,oczekiwane", [("EN-gb", "en"), ("pl", "pl"), (None, "pl"), ("de", "pl")])
def test_language_is_normalised_to_pl_or_en(wejscie, oczekiwane):
    assert _ModelZJezykiem(language=wejscie).language == oczekiwane


def test_sms_phone_needs_six_digits_and_summary_is_required():
    with pytest.raises(ValidationError, match="co najmniej 6 cyfr"):
        WysylkaSMS(phone_number="+48 12", summary_text="ok")
    with pytest.raises(ValidationError, match="summary_text nie może być pusty"):
        WysylkaSMS(phone_number="+48600100200", summary_text="   ")
