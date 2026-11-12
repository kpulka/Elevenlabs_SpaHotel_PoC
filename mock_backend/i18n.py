"""Obsługa języka odpowiedzi backendu (kontrakt dwujęzyczny z agentem)."""

from __future__ import annotations

from typing import Any, Literal, TypeVar

Lang = Literal["pl", "en"]
T = TypeVar("T")


def lang_of(request: Any) -> Lang:
    """Zwraca znormalizowany kod języka z obiektu żądania (domyślnie 'pl')."""
    raw = getattr(request, "language", None)
    if isinstance(raw, str) and raw.strip().lower() == "en":
        return "en"
    return "pl"


def is_en(lang: str | None) -> bool:
    """Sprawdza, czy podany kod języka to angielski."""
    return isinstance(lang, str) and lang.strip().lower() == "en"


def pick(lang: Lang | str | None, pl: T, en: T) -> T:
    """Wybiera wariant tekstu (pl lub en) na podstawie kodu języka."""
    if is_en(lang):
        return en
    return pl
