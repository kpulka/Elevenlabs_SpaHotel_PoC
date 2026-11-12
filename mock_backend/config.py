"""Konfiguracja mock backendu (zmienne środowiskowe i flagi uruchomieniowe)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _parse_origins(value: str | None) -> list[str]:
    raw = value if value is not None else "*"
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["*"]


@dataclass
class Settings:
    demo_logs: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    app_version: str = "1.1.0"

    @property
    def cors_wildcard(self) -> bool:
        return "*" in self.cors_origins

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            demo_logs=_parse_bool(os.getenv("ANNA_DEMO_LOGS", "1"), default=True),
            cors_origins=_parse_origins(os.getenv("CORS_ORIGINS")),
            app_version=os.getenv("ANNA_APP_VERSION", "1.1.0"),
        )


settings = Settings.from_env()
