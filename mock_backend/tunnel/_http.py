"""Wspólny klient HTTP narzędzi tunelu (RF-10): jedna implementacja dla obu skryptów.

Używają go ``sync_agent_tools.py`` i ``run_simulations.py``. Tu jest jedno miejsce na:
transport (urllib), nagłówek ``xi-api-key``, timeout, opcjonalny retry błędów sieci,
oraz odczyt klucza API (``--api-key`` > ``$ELEVENLABS_API_KEY`` > ``frontend/.env.local``).

Dwa style obsługi odpowiedzi, jawnie:
  * ``request()`` / ``request_json()`` nie rzucają na 4xx/5xx -- zwracają ``(status, ...)``;
  * ``request_ok()`` rzuca ``ApiError`` na 4xx/5xx i na nie-JSON.
Błędy sieci (DNS, timeout, reset połączenia) rzucają ``ApiError`` we wszystkich trybach.

Klucz API trafia tylko do nagłówka. Każdy komunikat wyjątku przechodzi przez ``redact()``,
więc klucz nie pojawi się w tekście błędu nawet wtedy, gdy serwer go odbije.

Tylko standard library -- moduł musi działać bez virtualenv backendu.
"""

from __future__ import annotations

import http.client
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_LOCAL = PROJECT_ROOT / "frontend" / ".env.local"
DEFAULT_TIMEOUT = 60.0
ERROR_BODY_LIMIT = 300
RETRY_DELAY_SECONDS = 1.5
REDACTED = "***"


class ApiError(RuntimeError):
    """API nieosiągalne albo odpowiedź, której nie da się użyć."""


def resolve_api_key(cli_value: Optional[str] = None, env_file: Optional[Path] = None) -> Optional[str]:
    """--api-key > $ELEVENLABS_API_KEY > plik .env (domyślnie frontend/.env.local). Nigdy nie drukowany."""
    if cli_value and cli_value.strip():
        return cli_value.strip()
    env_value = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if env_value:
        return env_value
    path = ENV_LOCAL if env_file is None else Path(env_file)
    if path.is_file():
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        for line in content.splitlines():
            if line.lstrip().startswith("#"):
                continue
            match = re.match(r"\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*(.*)$", line)
            if match:
                value = match.group(1).strip().strip('"').strip("'")
                if value:
                    return value
    return None


class ApiClient:
    """Minimalny klient REST (stdlib). ``key=None`` oznacza brak nagłówka ``xi-api-key``."""

    def __init__(
        self,
        base: str,
        key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = 0,
    ) -> None:
        self.base = base.rstrip("/")
        self._key = key or None
        self.timeout = timeout
        self.retries = max(0, retries)  # ponowienia wyłącznie dla błędów transportu

    def redact(self, text: str) -> str:
        """Maskuje klucz API w dowolnym tekście (komunikaty, fragmenty odpowiedzi)."""
        if self._key:
            return text.replace(self._key, REDACTED)
        return text

    def request(
        self, method: str, path: str, body: Optional[Any] = None, timeout: Optional[float] = None
    ) -> Tuple[int, str]:
        """Surowe ``(status, tekst)``. Nie rzuca na 4xx/5xx; rzuca ``ApiError`` przy błędzie sieci."""
        url = f"{self.base}{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        effective_timeout = self.timeout if timeout is None else timeout
        last_error = ""
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Accept", "application/json")
            if self._key:
                req.add_header("xi-api-key", self._key)
            if data is not None:
                req.add_header("Content-Type", "application/json; charset=utf-8")
            try:
                with urllib.request.urlopen(req, timeout=effective_timeout) as resp:
                    return resp.status, resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as exc:  # odpowiedź serwera, nie błąd transportu
                return exc.code, exc.read().decode("utf-8", "replace")
            except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as exc:
                last_error = str(exc)
                if attempt < self.retries:
                    time.sleep(RETRY_DELAY_SECONDS)
        raise ApiError(self.redact(f"{method} {path} nie doszło: {last_error}"))

    def request_json(
        self, method: str, path: str, body: Optional[Any] = None, timeout: Optional[float] = None
    ) -> Tuple[int, Any]:
        """``(status, obiekt JSON)``; pusta treść -> ``{}``; nie-JSON zwracany jako tekst."""
        status, text = self.request(method, path, body, timeout)
        if not text.strip():
            return status, {}
        try:
            return status, json.loads(text)
        except json.JSONDecodeError:
            return status, text

    def request_ok(
        self, method: str, path: str, body: Optional[Any] = None, timeout: Optional[float] = None
    ) -> Any:
        """Zwraca JSON; rzuca ``ApiError`` na HTTP >= 400 albo na nie-JSON."""
        status, text = self.request(method, path, body, timeout)
        if status >= 400:
            snippet = text.strip()[:ERROR_BODY_LIMIT]
            raise ApiError(self.redact(f"{method} {path} -> HTTP {status}: {snippet}"))
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ApiError(self.redact(f"{method} {path} -> nie-JSON: {text[:200]}")) from exc
