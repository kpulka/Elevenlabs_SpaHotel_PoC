"""Logging and request context for the mock backend.

Two output modes, selected by ``ANNA_LOG_FORMAT``:

* ``demo`` (default) - the human-friendly console blocks shown on a side screen during live
  demos. ``ANNA_DEMO_LOGS=0`` silences them; warnings and errors are still printed.
* ``json`` - one JSON object per line (timestamp, level, event, request_id, conversation_id
  and event-specific fields) for log shippers. No emoji, phone numbers masked, no guest names.

Call sites use ``log_event()`` and pass both representations: the ``demo`` text for the console
and structured ``fields`` for JSON. Console-only blocks use ``log_demo()`` and never reach JSON.
The request id and conversation id come from a context variable set by
``middleware.ObservabilityMiddleware``, so lines written deep inside a handler are correlated without
passing ids around.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Sequence
from contextvars import ContextVar, Token
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from config import settings

LOGGER_NAME = "anna"
SEPARATOR = "=" * 60  # the only definition; framed demo blocks use it


@dataclass
class RequestContext:
    """Per-request correlation data (one mutable object shared by the whole request)."""

    request_id: str
    conversation_id: str | None = None
    tool: str | None = None


_context: ContextVar[RequestContext | None] = ContextVar("anna_request_context", default=None)


def set_context(context: RequestContext | None) -> Token[RequestContext | None]:
    return _context.set(context)


def reset_context(token: Token[RequestContext | None]) -> None:
    _context.reset(token)


def current_context() -> RequestContext | None:
    return _context.get()


# ─────────────────────────────────────────────────────────────────────────────
# Masking of personal data (GDPR): phone numbers and guest names
# ─────────────────────────────────────────────────────────────────────────────

def mask_phone(phone: str | None) -> str:
    """Keep only the last three digits: ``+48600100200`` -> ``*********200``."""
    digits = [char for char in (phone or "") if char.isdigit()]
    if len(digits) <= 3:
        return "*" * len(digits)
    return "*" * (len(digits) - 3) + "".join(digits[-3:])


def mask_name(name: str | None) -> str:
    """Keep the first name and reduce every further part to an initial: ``Jan Kowalski`` -> ``Jan K.``."""
    first, *rest = (name or "").split() or [""]
    return " ".join([first, *(f"{part[:1].upper()}." for part in rest)]).strip()


# A run of digits with optional separators; only runs with at least nine digits count as a phone number.
_PHONE_CANDIDATE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
_MIN_PHONE_DIGITS = 9


def redact_phones(text: str | None) -> str:
    """Mask phone-number-like runs inside free text (guest's ``reason``, notes)."""

    def _mask(match: re.Match[str]) -> str:
        candidate = match.group(0)
        if sum(char.isdigit() for char in candidate) < _MIN_PHONE_DIGITS:
            return candidate
        return mask_phone(candidate)

    return _PHONE_CANDIDATE.sub(_mask, text or "")


# ─────────────────────────────────────────────────────────────────────────────
# Formatting and handler
# ─────────────────────────────────────────────────────────────────────────────

def _json_line(record: logging.LogRecord) -> str:
    payload: dict[str, Any] = {
        "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
        "level": record.levelname.lower(),
        "event": getattr(record, "event", record.getMessage()),
    }
    context = current_context()
    if context is not None:
        payload["request_id"] = context.request_id
        if context.conversation_id:
            payload["conversation_id"] = context.conversation_id
        if context.tool:
            payload["tool"] = context.tool
    payload.update(getattr(record, "fields", {}))
    return json.dumps(payload, ensure_ascii=False, default=str)


def _demo_text(record: logging.LogRecord) -> str | None:
    """Console text for demo mode, or ``None`` when the record should stay silent."""
    demo = getattr(record, "demo", None)
    if demo is not None:
        return demo if settings.demo_logs else None
    if record.levelno < logging.WARNING:
        return None  # structured-only events (e.g. the access log) would clutter the demo console
    fields = getattr(record, "fields", {})
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    return f"   [{record.levelname}] {getattr(record, 'event', record.getMessage())} {details}".rstrip()


class AnnaHandler(logging.Handler):
    """Writes to the *current* ``sys.stdout`` and picks the format per record.

    Both are resolved at emit time (not at configuration time) so that pytest's ``capsys`` and a
    monkeypatched ``settings.log_format`` work without reconfiguring logging.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if settings.log_format == "json":
                # Console-only demo blocks have no structured meaning; keep them out of JSON.
                text = None if getattr(record, "demo_only", False) else _json_line(record)
            else:
                text = _demo_text(record)
            if text is not None:
                sys.stdout.write(text + "\n")
                sys.stdout.flush()
        except Exception:  # logging must never break a tool call
            self.handleError(record)


def configure_logging() -> logging.Logger:
    """Attach the handler to the ``anna`` logger exactly once (idempotent)."""
    logger = logging.getLogger(LOGGER_NAME)
    if not any(isinstance(handler, AnnaHandler) for handler in logger.handlers):
        logger.addHandler(AnnaHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False  # uvicorn configures its own loggers; avoid duplicate lines
    return logger


def log_event(
    event: str,
    *,
    level: int = logging.INFO,
    demo: str | Sequence[str] | None = None,
    demo_only: bool = False,
    **fields: Any,
) -> None:
    """Log one event in both representations.

    ``demo`` is the console text (a string, or a sequence of lines); ``fields`` are the
    structured attributes for JSON mode. ``None`` values are dropped from the JSON output.
    ``demo_only`` marks console-only output that JSON mode must skip.
    """
    text = demo if demo is None or isinstance(demo, str) else "\n".join(demo)
    extra = {
        "event": event,
        "demo": text,
        "demo_only": demo_only,
        "fields": {key: value for key, value in fields.items() if value is not None},
    }
    configure_logging().log(level, event, extra=extra)


def log_demo(*lines: str) -> None:
    """Framed console block for the live demo screen (console only, never structured)."""
    log_event("demo_block", demo=[SEPARATOR, *lines, SEPARATOR], demo_only=True)
