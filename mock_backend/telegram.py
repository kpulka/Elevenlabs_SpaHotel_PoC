"""Wysyłka wiadomości na Telegram — jeden wspólny helper dla SMS i handoffu.

Integracja jest opcjonalna: bez ``TELEGRAM_BOT_TOKEN`` i ``TELEGRAM_CHAT_ID``
funkcja nic nie wysyła i zwraca False (demo działa dalej na konsoli).
Konfiguracja czytana jest w momencie wywołania, dzięki czemu testy nie
potrzebują sieci ani sekretów.
"""

from __future__ import annotations

import os

import httpx

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
TIMEOUT_S = 5.0


def konfiguracja() -> tuple[str, str]:
    """Zwraca (token, chat_id) — puste ciągi, jeśli integracja nieaktywna."""
    return (
        os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        os.getenv("TELEGRAM_CHAT_ID", "").strip(),
    )


def skonfigurowany() -> bool:
    token, chat_id = konfiguracja()
    return bool(token and chat_id)


async def wyslij_wiadomosc(tekst: str, etykieta: str = "wiadomość") -> bool:
    """Wysyła tekst (Markdown) na skonfigurowany czat. Nigdy nie rzuca wyjątku.

    ``etykieta`` służy tylko do logów (np. "SMS", "handoff").
    """
    token, chat_id = konfiguracja()
    if not (token and chat_id):
        return False

    payload = {"chat_id": chat_id, "text": tekst, "parse_mode": "Markdown"}
    try:
        async with httpx.AsyncClient() as klient:
            odpowiedz = await klient.post(
                TELEGRAM_API.format(token=token), json=payload, timeout=TIMEOUT_S
            )
        if odpowiedz.status_code == 200:
            print(f"   ✅ {etykieta} wysłany na Telegram (chat_id: {chat_id})")
            return True
        print(f"   ⚠️  Błąd Telegram API: {odpowiedz.status_code} — {odpowiedz.text}")
    except Exception as blad:  # noqa: BLE001 — demo nie może się wywalić na sieci
        print(f"   ⚠️  Nie udało się wysłać na Telegram: {blad}")
    return False
