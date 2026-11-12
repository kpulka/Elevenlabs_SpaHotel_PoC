"""Kontrakt API: wygenerowany schemat OpenAPI musi być identyczny z zatwierdzonym snapshotem.

Zmiana nazwy lub typu pola w schematach (np. schemas.py) rozjeżdża narzędzia agenta
ElevenLabs, które są zdefiniowane po stronie platformy. Ten test sprawia, że taka zmiana
jest świadoma: trzeba zaktualizować snapshot i opisać to w PR.

Aktualizacja po świadomej zmianie kontraktu:
    UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest -q tests/test_openapi_contract.py
"""

from __future__ import annotations

import difflib
import json
import os
from pathlib import Path

import main

SNAPSHOT = Path(__file__).resolve().parent / "openapi.snapshot.json"


def _render(schemat: dict) -> str:
    """Stabilna serializacja: posortowane klucze, wcięcia, UTF-8 bez escapowania, końcowy \n."""
    return json.dumps(schemat, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def test_openapi_matches_snapshot():
    aktualny = _render(main.app.openapi())

    if os.getenv("UPDATE_OPENAPI_SNAPSHOT") == "1":
        with SNAPSHOT.open("w", encoding="utf-8", newline="\n") as plik:
            plik.write(aktualny)
        return

    assert SNAPSHOT.exists(), (
        f"Brak {SNAPSHOT.name}. Wygeneruj: UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest -q tests/test_openapi_contract.py"
    )
    zatwierdzony = SNAPSHOT.read_text(encoding="utf-8")
    if aktualny != zatwierdzony:
        roznice = "".join(
            difflib.unified_diff(
                zatwierdzony.splitlines(keepends=True),
                aktualny.splitlines(keepends=True),
                fromfile=SNAPSHOT.name,
                tofile="app.openapi() (bieżący kod)",
                n=2,
            )
        )
        komunikat = (
            "Kontrakt OpenAPI zmieniony względem snapshotu.\n"
            "Jeśli zmiana jest zamierzona, zaktualizuj snapshot:\n"
            "    UPDATE_OPENAPI_SNAPSHOT=1 python -m pytest -q tests/test_openapi_contract.py\n"
            "i opisz zmianę kontraktu w PR (patrz mock_backend/README.md).\n\n"
            + roznice[:4000]
        )
        raise AssertionError(komunikat)
