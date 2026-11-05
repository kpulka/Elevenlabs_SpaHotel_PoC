"""Contract tests for the mock PMS webhooks used by the ElevenLabs agent."""
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import app  # noqa: E402

client = TestClient(app)
TOMORROW = (date.today() + timedelta(days=1)).isoformat()


def post(path, body):
    return client.post(path, json=body)


def test_root_lists_service():
    assert client.get("/").status_code == 200


def test_spa_availability_returns_json():
    r = post("/check_spa_availability", {"service_name": "masaż klasyczny", "date": TOMORROW})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_spa_availability_validates_payload():
    assert post("/check_spa_availability", {"date": TOMORROW}).status_code == 422


def test_room_availability_contract():
    r = post("/check_room_availability",
             {"room_type": "dwuosobowy", "check_in": "2026-08-24", "check_out": "2026-08-26"})
    assert r.status_code == 200
    assert "available" in r.json()


def test_booking_then_cancel_flow():
    book = post("/book_spa_appointment", {
        "service_name": "masaż klasyczny", "date": TOMORROW,
        "time": "10:00", "guest_name": "Test Guest"})
    assert book.status_code == 200
    body = book.json()
    conf = body.get("confirmation_id")
    if conf:  # slot may be unavailable depending on the generated schedule
        cancel = post("/cancel_spa_appointment", {"confirmation_id": conf, "reason": "change of plans"})
        assert cancel.status_code == 200


def test_sms_and_handoff_work_without_telegram():
    sms = post("/send_sms_summary", {"phone_number": "+48123456789", "summary_text": "Test"})
    assert sms.status_code == 200
    handoff = post("/transfer_to_simulated_handoff", {"department": "recepcja", "reason": "test"})
    assert handoff.status_code == 200


@pytest.mark.parametrize("path", ["/check_room_availability", "/send_sms_summary"])
def test_empty_body_rejected(path):
    assert post(path, {}).status_code == 422
