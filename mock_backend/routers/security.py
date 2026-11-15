"""Authentication of the agent's tool webhooks.

Two modes, both optional and both disabled when ``ANNA_WEBHOOK_SECRET`` is empty (demo and tests):

* **Shared secret** (default, backward compatible): the request carries ``X-Webhook-Secret`` equal
  to the configured value. Compared in constant time.
* **HMAC** (opt-in per request): if the request carries ``X-Anna-Signature`` or ``X-Anna-Timestamp``,
  both must be present and verify against the exact body bytes (``events.verify``, same algorithm
  as the outbound events, replay window 300 s). The shared-secret header is then not consulted.

Startup refuses to run without a secret when ``ANNA_ENV=prod`` (see ``main.py``).
"""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

import events
from config import settings

NAGLOWEK_SEKRETU = "X-Webhook-Secret"


async def require_webhook_secret(
    request: Request,
    x_webhook_secret: Annotated[str | None, Header(include_in_schema=False)] = None,
    x_anna_signature: Annotated[str | None, Header(include_in_schema=False)] = None,
    x_anna_timestamp: Annotated[str | None, Header(include_in_schema=False)] = None,
) -> None:
    oczekiwany = settings.webhook_secret
    if not oczekiwany:
        return  # auth wyłączone — tryb demo i testy

    if x_anna_signature is not None or x_anna_timestamp is not None:
        body = await request.body()  # Starlette caches the body, so the endpoint can still read it
        if not events.verify(oczekiwany, x_anna_timestamp or "", body, x_anna_signature or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nieprawidłowy podpis X-Anna-Signature lub znacznik czasu X-Anna-Timestamp.",
            )
        return

    if x_webhook_secret is None or not hmac.compare_digest(
        x_webhook_secret.encode("utf-8"), oczekiwany.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Brak lub nieprawidłowy nagłówek {NAGLOWEK_SEKRETU}.",
        )
