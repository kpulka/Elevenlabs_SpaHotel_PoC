"""Mock backend configuration (environment variables and runtime flags).

Everything is read once at import time into ``settings``. Code reads ``settings.<field>`` at
call time (never caches a copy), so tests can flip a single field with ``monkeypatch.setattr``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

ENV_DEV = "dev"
ENV_PROD = "prod"
_ENVIRONMENTS = frozenset({ENV_DEV, ENV_PROD})


def _parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _parse_origins(value: str | None) -> list[str]:
    raw = value if value is not None else "*"
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["*"]


def _parse_log_format(value: str | None) -> str:
    return "json" if (value or "").strip().lower() == "json" else "demo"


def _parse_env(value: str | None) -> str:
    """``ANNA_ENV``: ``dev`` (default) or ``prod``. Anything else fails at import (loud, not silent)."""
    normalized = (value or "").strip().lower() or ENV_DEV
    if normalized not in _ENVIRONMENTS:
        raise ValueError(f"ANNA_ENV must be 'dev' or 'prod', got {value!r}")
    return normalized


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


@dataclass
class Settings:
    demo_logs: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    app_version: str = "1.2.0"
    # "dev" = start with warnings when secrets are missing; "prod" = refuse to start without them.
    env: str = ENV_DEV
    # Shared secret for the X-Webhook-Secret header (and the HMAC mode). "" = auth disabled.
    webhook_secret: str = ""
    # "demo" = human-friendly console blocks, "json" = one JSON object per line.
    log_format: str = "demo"
    # SQLite database file; ":memory:" keeps the calendar in the process (lost on restart).
    db_path: str = ":memory:"
    # Outbound integration events (CRM / n8n). Events are sent only when BOTH are set.
    events_webhook_url: str = ""
    events_signing_secret: str = ""

    @property
    def cors_wildcard(self) -> bool:
        return "*" in self.cors_origins

    @property
    def is_prod(self) -> bool:
        return self.env == ENV_PROD

    @property
    def events_enabled(self) -> bool:
        return bool(self.events_webhook_url and self.events_signing_secret)

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            demo_logs=_parse_bool(os.getenv("ANNA_DEMO_LOGS", "1"), default=True),
            cors_origins=_parse_origins(os.getenv("CORS_ORIGINS")),
            app_version=os.getenv("ANNA_APP_VERSION", "1.2.0"),
            env=_parse_env(os.getenv("ANNA_ENV")),
            webhook_secret=_env("ANNA_WEBHOOK_SECRET"),
            log_format=_parse_log_format(os.getenv("ANNA_LOG_FORMAT")),
            db_path=_env("ANNA_DB_PATH") or ":memory:",
            events_webhook_url=_env("ANNA_EVENTS_WEBHOOK_URL"),
            events_signing_secret=_env("ANNA_EVENTS_SIGNING_SECRET"),
        )


settings = Settings.from_env()
