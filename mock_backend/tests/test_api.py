"""Testy API mock backendu — bez sieci i bez sekretów.

Uruchomienie (z katalogu mock_backend):
    python -m pytest -q
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import pytest

import main
import store

SPA = "/check_spa_availability"
BOOK = "/book_spa_appointment"
CANCEL = "/cancel_spa_appointment"
RESCHEDULE = "/reschedule_spa_appointment"
ROOM = "/check_room_availability"
SMS = "/send_sms_summary"
HANDOFF = "/transfer_to_simulated_handoff"


def dzien(przesuniecie: int) -> str:
    return (date.today() + timedelta(days=przesuniecie)).isoformat()


def godzina_od_teraz(minuty: int) -> str:
    return (datetime.now() + timedelta(minutes=minuty)).isoformat(timespec="minutes")


def rezerwuj(client, dzien_iso: str | None = None, godzina: str = "14:00", usluga: str = "masaż klasyczny"):
    return client.post(
        BOOK,
        json={
            "service_name": usluga,
            "date": dzien_iso or dzien(3),
            "time": godzina,
            "guest_name": "Jan Kowalski",
        },
    )


# ── walidacja formatu (HTTP 422) ─────────────────────────────────────────────

@pytest.mark.parametrize("zla_data", ["31/08/2026", "2026-13-01", "jutro", ""])
def test_malformed_date_is_schema_error(client, zla_data):
    odpowiedz = client.post(SPA, json={"service_name": "jonoforeza", "date": zla_data})
    assert odpowiedz.status_code == 422
    assert odpowiedz.json()["detail"][0]["loc"] == ["body", "date"]


def test_malformed_booking_payload_is_schema_error(client):
    """Defekt #1: data z przeszłości, godzina 99:99 i puste imię muszą dać 422."""
    odpowiedz = client.post(
        BOOK,
        json={
            "service_name": "masaż klasyczny",
            "date": "1999-01-01",
            "time": "99:99",
            "guest_name": "",
        },
    )
    assert odpowiedz.status_code == 422
    pola = {blad["loc"][-1] for blad in odpowiedz.json()["detail"]}
    assert pola == {"time", "guest_name"}


def test_malformed_appointment_datetime_is_schema_error(client):
    odpowiedz = client.post(
        CANCEL,
        json={"confirmation_id": "SPA-1234", "appointment_datetime": "9 listopada 2026"},
    )
    assert odpowiedz.status_code == 422


def test_reversed_room_dates_is_domain_rejection(client):
    odpowiedz = client.post(
        ROOM, json={"room_type": "dwuosobowy", "check_in": dzien(5), "check_out": dzien(4)}
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert body["total_nights"] == 0
    assert "późniejsza" in body["message"]


# ── daty z przeszłości (200 + available/success false) ───────────────────────

def test_past_date_spa_check_is_domain_rejection(client):
    odpowiedz = client.post(SPA, json={"service_name": "jonoforeza", "date": dzien(-1)})
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert "przeszłości" in body["message"]


def test_past_date_booking_is_domain_rejection(client):
    odpowiedz = rezerwuj(client, dzien_iso=dzien(-1))
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is False
    assert body["confirmation_id"] is None
    assert "przeszłości" in body["message"]


def test_past_check_in_room_is_domain_rejection(client):
    odpowiedz = client.post(
        ROOM, json={"room_type": "apartament", "check_in": dzien(-2), "check_out": dzien(-1)}
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert "przeszłości" in body["message"]


def test_date_outside_rolling_window_is_domain_rejection(client):
    odpowiedz = client.post(SPA, json={"service_name": "jonoforeza", "date": dzien(30)})
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["available"] is False
    assert "oknem rezerwacji" in body["message"]


# ── stan slotów ─────────────────────────────────────────────────────────────

def test_booking_consumes_slot(client):
    przed = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" in przed["slots"]

    odpowiedz = rezerwuj(client)
    assert odpowiedz.status_code == 200
    assert odpowiedz.json()["success"] is True
    assert odpowiedz.json()["confirmation_id"].startswith("SPA-")

    po = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" not in po["slots"]
    assert len(po["slots"]) == len(przed["slots"]) - 1


def test_double_booking_same_slot_fails_with_remaining_slots(client):
    assert rezerwuj(client).json()["success"] is True
    druga = rezerwuj(client)
    body = druga.json()
    assert druga.status_code == 200
    assert body["success"] is False
    assert "już zajęty" in body["message"]
    assert "14:00" not in body["slots"]
    assert len(body["slots"]) == 5


def test_booking_outside_service_schedule_fails(client):
    odpowiedz = rezerwuj(client, godzina="03:00")
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is False
    assert "grafiku" in body["message"]


def test_cancel_restores_slot(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    assert client.post(CANCEL, json={"confirmation_id": identyfikator}).status_code == 200

    po = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" in po["slots"]

    # slot jest znowu wolny — można go zarezerwować ponownie
    assert rezerwuj(client).json()["success"] is True


def test_reschedule_moves_slot(client):
    identyfikator = rezerwuj(client, dzien_iso=dzien(3), godzina="14:00").json()["confirmation_id"]

    odpowiedz = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": identyfikator,
            "service_name": "masaż klasyczny",
            "new_date": dzien(4),
            "new_time": "11:00",
            "guest_name": "Jan Kowalski",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is True
    assert body["confirmation_id"] != identyfikator
    assert body["new_date"] == dzien(4)

    stare = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    nowe = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(4)}).json()
    assert "14:00" in stare["slots"], "stary slot powinien wrócić do puli"
    assert "11:00" not in nowe["slots"], "nowy slot powinien być zajęty"


def test_reschedule_to_taken_slot_fails(client):
    rezerwuj(client, dzien_iso=dzien(3), godzina="10:00")
    druga = rezerwuj(client, dzien_iso=dzien(3), godzina="11:00").json()["confirmation_id"]

    odpowiedz = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": druga,
            "service_name": "masaż klasyczny",
            "new_date": dzien(3),
            "new_time": "10:00",
            "guest_name": "Jan Kowalski",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is False
    assert "zajęty" in body["message"]
    # stara rezerwacja nadal zajmuje swój slot
    wolne = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "11:00" not in wolne["slots"]


# ── reguła opłat przy anulacji ───────────────────────────────────────────────

def test_cancel_more_than_2h_before_is_free_of_charge(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    odpowiedz = client.post(
        CANCEL,
        json={
            "confirmation_id": identyfikator,
            "reason": "zmiana planów",
            "appointment_datetime": godzina_od_teraz(300),  # 5h przed zabiegiem
            "language": "pl",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is True
    assert body["cancelled"] is True
    assert body["fee"] == 0.0
    assert body["free_of_charge"] is True
    assert body["found"] is True
    assert "ponad 2h" in body["fee_rule"]


def test_cancel_less_than_2h_before_charges_50_percent(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    odpowiedz = client.post(
        CANCEL,
        json={"confirmation_id": identyfikator, "appointment_datetime": godzina_od_teraz(90)},
    )
    body = odpowiedz.json()
    assert body["fee"] == 0.5
    assert body["free_of_charge"] is False
    assert "poniżej 2h" in body["fee_rule"]


def test_cancel_with_medical_release_is_always_free(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    odpowiedz = client.post(
        CANCEL,
        json={
            "confirmation_id": identyfikator,
            "medical_release": True,
            "appointment_datetime": godzina_od_teraz(30),
            "language": "pl",
        },
    )
    body = odpowiedz.json()
    assert body["fee"] == 0.0
    assert body["free_of_charge"] is True
    assert body["medical_release"] is True
    assert "medyczne" in body["fee_rule"].lower()


def test_cancel_without_appointment_datetime_reports_unknown_timing(client):
    """Bez appointment_datetime backend nie zna terminu → 50% + jawny fee_rule."""
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    body = client.post(CANCEL, json={"confirmation_id": identyfikator}).json()
    assert body["fee"] == 0.5
    assert body["free_of_charge"] is False
    assert body["found"] is True
    assert "Brak godziny zabiegu" in body["fee_rule"]


def test_cancel_english_language_uses_english_rule(client):
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    body = client.post(
        CANCEL,
        json={
            "confirmation_id": identyfikator,
            "appointment_datetime": godzina_od_teraz(300),
            "language": "en",
        },
    ).json()
    assert body["message"] == "Reservation cancelled."
    assert body["fee_rule"].startswith("Cancelled more than 2h")
    assert body["found"] is True


# ── katalog i dopasowanie usług ─────────────────────────────────────────────

def test_ambiguous_service_name_returns_candidates(client):
    body = client.post(SPA, json={"service_name": "masaż", "date": dzien(3)}).json()
    assert body["available"] is False
    assert len(body["ambiguous"]) == 2
    assert "masaż klasyczny" in body["ambiguous"]
    assert "masaż leczniczy pleców" in body["ambiguous"]
    # 6 zabiegów: 5 z bazy wiedzy + gimnastyka lecznicza ze strony
    assert len(body["available_services"]) == 6
    assert "Dopytaj" in body["message"]


def test_ambiguous_booking_is_rejected_without_consuming_slot(client):
    body = rezerwuj(client, usluga="masaż").json()
    assert body["success"] is False
    assert "ambiguous" in body
    assert client.post(SPA, json={"service_name": "masaż", "date": dzien(3)}).json()[
        "available"
    ] is False
    # slot 14:00 nadal wolny
    assert "14:00" in client.post(
        SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}
    ).json()["slots"]


@pytest.mark.parametrize(
    "zapytanie,oczekiwana",
    [
        ("jonoforeza", "jonoforeza"),
        ("MASAŻ KLASYCZNY", "masaż klasyczny"),
        ("masaz klasyczny", "masaż klasyczny"),
        ("kąpiel borowinowa", "kąpiel borowinowa"),
        ("borowina", "kąpiel borowinowa"),
        ("sulphur bath", "kąpiel siarczkowa Ukojenie Stawów"),
        ("masaż pleców", "masaż leczniczy pleców"),
        ("swedish massage", "masaż klasyczny"),
    ],
)
def test_alias_and_accent_insensitive_resolution(client, zapytanie, oczekiwana):
    body = client.post(SPA, json={"service_name": zapytanie, "date": dzien(2)}).json()
    assert body["available"] is True
    assert body["service_name"] == oczekiwana


def test_unknown_service_returns_available_services(client):
    body = client.post(SPA, json={"service_name": "krioterapia", "date": dzien(2)}).json()
    assert body["available"] is False
    assert len(body["available_services"]) == 6
    assert "nie jest oferowany" in body["message"]
    # kształt odpowiedzi pozostaje stały także na ścieżce odmowy
    assert {"available", "slots", "service_name", "date", "message"} <= set(body)


# ── pokoje: ceny i dostępność ───────────────────────────────────────────────

def test_price_math_for_n_nights(client):
    body = client.post(
        ROOM, json={"room_type": "dwuosobowy", "check_in": dzien(10), "check_out": dzien(14)}
    ).json()
    assert body["available"] is True
    assert body["price_per_night"] == 500
    assert body["total_nights"] == 4
    assert body["total_price"] == 2000
    assert body["check_in"] == dzien(10)


def test_room_prices_come_from_data_file(client):
    """Ceny pochodzą z data/rooms.json i muszą zgadzać się z frontendem."""
    assert main.POKOJE.typy["jednoosobowy"].cena_za_noc == 350
    assert main.POKOJE.typy["dwuosobowy"].cena_za_noc == 500
    assert main.POKOJE.typy["apartament"].cena_za_noc == 750

    body = client.post(
        ROOM, json={"room_type": "Apartament", "check_in": dzien(2), "check_out": dzien(3)}
    ).json()
    assert body["available"] is True
    assert body["price_per_night"] == 750
    assert body["total_price"] == 750


def test_unknown_room_type(client):
    body = client.post(
        ROOM, json={"room_type": "penthouse", "check_in": dzien(2), "check_out": dzien(3)}
    ).json()
    assert body["available"] is False
    assert "nie istnieje" in body["message"]
    assert "apartament" in body["message"]
    # agent musi dostać realne opcje do zaproponowania, nie samą odmowę
    assert body["available_room_types"] == ["jednoosobowy", "dwuosobowy", "apartament"]
    assert len(body["available_room_type_names"]) == 3


@pytest.mark.parametrize("niejasny", ["pokój", "pokoj", "jakiś pokój"])
def test_vague_room_type_returns_available_types(client, niejasny):
    body = client.post(
        ROOM, json={"room_type": niejasny, "check_in": dzien(2), "check_out": dzien(3)}
    ).json()
    assert body["available"] is False
    assert body["available_room_types"] == ["jednoosobowy", "dwuosobowy", "apartament"]
    assert "niejednoznaczny" in body["message"]


# Blokada z data/rooms.json (przerwa świąteczno-noworoczna). Pobyt 28→30.12.2026
# obejmuje obie zablokowane noce.
BLOKADA_OD, BLOKADA_DO = "2026-12-28", "2026-12-30"


def test_blocked_window_is_future_and_rejects_room(client):
    """Ścieżka demo 'wszystko zajęte' musi działać na realnych danych z JSON-a."""
    body = client.post(
        ROOM, json={"room_type": "dwuosobowy", "check_in": BLOKADA_OD, "check_out": BLOKADA_DO}
    ).json()
    assert body["available"] is False
    assert "Brak dostępności" in body["message"]
    assert "28-29.12.2026" in body["message"], "opis blokady musi pochodzić z dat w JSON-ie"
    assert "przerwa świąteczno-noworoczna" in body["message"]
    assert body["total_price"] == 500 * 2, "cena policzona także dla odrzuconego terminu"


def test_blocked_window_dates_are_in_the_future():
    """Blokada w przeszłości = demo nigdy nie zadziała; wtedy przesuń okno w rooms.json."""
    blokady = {data for daty in main.POKOJE.zablokowane.values() for data in daty}
    assert blokady, "rooms.json nie ma żadnej blokady"
    najwczesniejsza = min(date.fromisoformat(wpis) for wpis in blokady)
    assert najwczesniejsza > date.today(), (
        f"blokada {najwczesniejsza} jest w przeszłości — przesuń okno w data/rooms.json"
    )


def test_blocked_description_is_generated_from_json(tmp_path):
    """Opis zakresu dat jest generowany z JSON-a, więc nie może się rozjechać z danymi."""
    dane = {
        "typy_pokoi": {"apartament": {"nazwa": "Apartament", "cena_za_noc": 750}},
        "zajete_terminy": [
            {"opis": "testowa przerwa", "daty": ["2027-01-05", "2027-01-06", "2027-01-08"]}
        ],
    }
    plik = tmp_path / "rooms.json"
    plik.write_text(json.dumps(dane), encoding="utf-8")

    katalog = store.KatalogPokoi(plik)

    assert katalog.opis_blokady() == "05-06.01.2027, 08.01.2027"
    assert katalog.etykieta_blokady() == "testowa przerwa"


def test_blocked_description_has_no_hardcoded_dates():
    assert main.POKOJE.opis_blokady() == "28-29.12.2026"
    assert "30-31.08.2026" not in main.POKOJE.opis_blokady()


# ── SMS, handoff, health, kontrakt ──────────────────────────────────────────

def test_send_sms_summary_en(client):
    odpowiedz = client.post(
        SMS,
        json={
            "phone_number": "+48600100200",
            "summary_text": "Booking confirmed.",
            "confirmation_id": "SPA-1234",
            "language": "en",
        },
    )
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["success"] is True
    assert body["delivered_to"] == "+48600100200"
    assert body["language"] == "en"
    assert body["message"] == "Message sent."


def test_send_sms_rejects_bad_phone(client):
    odpowiedz = client.post(SMS, json={"phone_number": "12", "summary_text": "x"})
    assert odpowiedz.status_code == 422


def test_transfer_to_simulated_handoff(client):
    body = client.post(
        HANDOFF,
        json={"department": "dyzurka_medyczna", "reason": "ból", "guest_name": "Anna", "language": "pl"},
    ).json()
    assert body["success"] is True
    assert body["simulated"] is True
    assert body["department"] == "Dyżurka medyczna (gabinet 101)"
    assert body["language"] == "pl"


def test_health_endpoint(client):
    odpowiedz = client.get("/health")
    body = odpowiedz.json()
    assert odpowiedz.status_code == 200
    assert body["status"] == "ok"
    assert body["version"] == main.APP_VERSION
    assert body["uptime_seconds"] >= 0


def test_cors_wildcard_disables_credentials():
    """CORS "*" + allow_credentials=True jest niezgodne ze spec — ustawiamy False."""
    opcje = {m.cls: m.kwargs for m in main.app.user_middleware}
    cors = opcje[__import__("fastapi.middleware.cors", fromlist=["CORSMiddleware"]).CORSMiddleware]
    assert cors["allow_origins"] == ["*"]
    assert cors["allow_credentials"] is False


@pytest.mark.parametrize(
    "sciezka,payload,wymagane_pola",
    [
        (SPA, {"service_name": "jonoforeza", "date": dzien(3)}, {"available", "slots", "service_name", "date", "message", "available_services", "price_pln", "duration_min"}),
        (BOOK, {"service_name": "jonoforeza", "date": dzien(3), "time": "10:00", "guest_name": "Anna"}, {"success", "confirmation_id", "service_name", "date", "time", "guest_name", "message"}),
        (CANCEL, {"confirmation_id": "SPA-1111"}, {"success", "confirmation_id", "cancelled", "fee", "medical_release", "message", "note", "free_of_charge", "fee_rule"}),
        (RESCHEDULE, {"confirmation_id": "SPA-2222", "service_name": "jonoforeza", "new_date": dzien(4), "new_time": "11:00", "guest_name": "Anna"}, {"success", "confirmation_id", "service_name", "new_date", "new_time", "guest_name", "message", "note", "found"}),
        (ROOM, {"room_type": "dwuosobowy", "check_in": dzien(8), "check_out": dzien(10)}, {"available", "room_type", "price_per_night", "check_in", "check_out", "total_nights", "total_price", "message"}),
        (SMS, {"phone_number": "+48600100200", "summary_text": "ok", "confirmation_id": "SPA-1111", "language": "pl"}, {"success", "message", "delivered_to", "language"}),
        (HANDOFF, {"department": "recepcja", "reason": "pomoc", "guest_name": "Anna", "language": "pl"}, {"success", "simulated", "message", "department", "reason", "guest_name", "language", "note"}),
    ],
)
def test_contract_fields_are_preserved(client, sciezka, payload, wymagane_pola):
    """Kontrakt z agentem ElevenLabs: te pola muszą istnieć w każdej odpowiedzi 200."""
    odpowiedz = client.post(sciezka, json=payload)
    assert odpowiedz.status_code == 200
    brakujace = wymagane_pola - set(odpowiedz.json())
    assert not brakujace, f"{sciezka} nie zwraca pól: {brakujace}"


# ── druga tura hardeningu: nieistniejące rezerwacje, wspólny kalendarz, cennik ──


def test_cancel_unknown_reservation_is_refused(client):
    """Anulowanie numeru, którego nie ma, nie może raportować sukcesu (defekt #1)."""
    body = client.post(CANCEL, json={"confirmation_id": "SPA-0000"}).json()
    assert body["success"] is False
    assert body["cancelled"] is False
    assert body["found"] is False
    assert body["fee"] == 0.0, "za nieistniejącą rezerwację nie naliczamy opłaty"
    assert "SPA-0000" in body["message"]
    assert "sprawdzenie numeru potwierdzenia" in body["message"]


def test_cancel_unknown_reservation_message_in_english(client):
    body = client.post(
        CANCEL, json={"confirmation_id": "SPA-0000", "language": "en"}
    ).json()
    assert body["success"] is False
    assert body["cancelled"] is False
    assert body["found"] is False
    assert "No reservation found" in body["message"]


def test_cancel_unknown_reservation_does_not_touch_existing_booking(client):
    """Odmowa dla obcego numeru nie może zwolnić slotu prawdziwej rezerwacji."""
    identyfikator = rezerwuj(client).json()["confirmation_id"]
    client.post(CANCEL, json={"confirmation_id": "SPA-0000"})

    wolne = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert "14:00" not in wolne["slots"], "slot prawdziwej rezerwacji musi zostać zajęty"
    assert main.SPA_STORE.rezerwacja(identyfikator) is not None


def test_reschedule_unknown_reservation_is_refused_without_creating_booking(client):
    """Przełożenie numeru, którego nie ma, nie może utworzyć nowej rezerwacji (defekt #2)."""
    body = client.post(
        RESCHEDULE,
        json={
            "confirmation_id": "SPA-0000",
            "service_name": "masaż klasyczny",
            "new_date": dzien(4),
            "new_time": "11:00",
            "guest_name": "Anna Nowak",
        },
    ).json()

    assert body["success"] is False
    assert body["found"] is False
    assert body["confirmation_id"] == "SPA-0000", "nie generujemy nowego numeru"
    assert "Nie znaleziono rezerwacji" in body["message"]
    assert main.SPA_STORE.rezerwacja(body["confirmation_id"]) is None

    wolne = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(4)}).json()
    assert "11:00" in wolne["slots"], "żaden slot nie może zostać zajęty przez odmowę"


def test_same_hour_cannot_be_sold_twice_for_different_treatments(client):
    """Jeden gabinet/fizjoterapeuta na godzinę — drugi zabieg o 14:00 musi dostać odmowę (defekt #3)."""
    pierwsza = rezerwuj(client, godzina="14:00", usluga="masaż klasyczny")
    assert pierwsza.json()["success"] is True

    druga = rezerwuj(client, godzina="14:00", usluga="jonoforeza")
    body = druga.json()
    assert druga.status_code == 200
    assert body["success"] is False
    assert "zajęty" in body["message"]
    assert "14:00" not in body["slots"]

    # wspólny kalendarz: jonoforeza również nie widzi 14:00 jako wolnej godziny
    wolne = client.post(SPA, json={"service_name": "jonoforeza", "date": dzien(3)}).json()
    assert "14:00" not in wolne["slots"]


def test_availability_reports_price_and_duration(client):
    body = client.post(SPA, json={"service_name": "masaż klasyczny", "date": dzien(3)}).json()
    assert body["available"] is True
    assert body["price_pln"] == 160
    assert body["duration_min"] == 50
    assert "160 PLN" in body["message"]
    assert "50 min" in body["message"]


def test_every_catalogue_entry_has_price_and_duration():
    for usluga in main.USLUGI:
        assert usluga.cena_pln > 0, f"{usluga.kod} bez ceny"
        assert usluga.czas_min > 0, f"{usluga.kod} bez czasu trwania"
        assert usluga.zrodlo_ceny in {"baza_wiedzy", "strona_www"}, usluga.kod


def test_catalogue_prices_are_the_knowledge_base_values():
    """Ceny kanoniczne = baza wiedzy agenta (80/120/100/70/160), nie strona (65/70/45/90/30)."""
    cennik = {usluga.kod: (usluga.cena_pln, usluga.czas_min) for usluga in main.USLUGI}
    assert cennik["kapiel_siarczkowa"] == (80, 20)
    assert cennik["masaz_leczniczy"] == (120, 30)
    assert cennik["kapiel_borowinowa"] == (100, 25)
    assert cennik["jonoforeza"] == (70, 20)
    assert cennik["masaz_klasyczny"] == (160, 50)
    # gimnastyki nie ma w bazie wiedzy — cena i czas ze strony marketingowej
    assert cennik["gimnastyka_lecznicza"] == (30, 45)


@pytest.mark.parametrize(
    "zapytanie",
    ["gimnastyka", "Gimnastyka lecznicza (grupowa)", "gimnastyka dla seniorów", "group gymnastics"],
)
def test_gimnastyka_resolves_by_name_and_alias(client, zapytanie):
    body = client.post(SPA, json={"service_name": zapytanie, "date": dzien(2)}).json()
    assert body["available"] is True
    assert body["service_name"] == "gimnastyka lecznicza (grupowa)"
    assert (body["price_pln"], body["duration_min"]) == (30, 45)


def test_gimnastyka_can_be_booked(client):
    odpowiedz = rezerwuj(client, godzina="15:00", usluga="gimnastyka")
    body = odpowiedz.json()
    assert body["success"] is True
    assert body["service_name"] == "gimnastyka lecznicza (grupowa)"
