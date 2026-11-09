#!/usr/bin/env python3
"""Point every ElevenLabs webhook tool of the "Anna" agent at the current tunnel.

Why this exists
---------------
The demo backend is exposed through a *quick tunnel* (cloudflared / trycloudflare),
whose public URL changes on every restart. The ElevenLabs Conversational AI tools
that call the backend are plain webhooks with an absolute URL baked into their
``tool_config.api_schema.url``, so after a restart they keep pointing at a dead
host and the affected procedures fail silently mid-call.

This script rewrites those URLs. It resolves tools **by name** (never by a
hardcoded tool id, so re-created tools keep working) and covers *all* seven spa
tools, not just the five the old inline heredocs knew about.

Modes
-----
  (default)          sync every tool URL to ``--base-url`` + the canonical path
  --list             read-only: name / id / current URL / body fields table
  --ensure-schema    add missing *optional* request-body properties to the live
                     tools (additive only, idempotent, prints each change)

``--dry-run`` works in every mode: it prints the intended PATCHes and writes
nothing.

The API key is read from ``--api-key``, else ``$ELEVENLABS_API_KEY``, else
``ELEVENLABS_API_KEY=...`` in ``frontend/.env.local``. The key is never printed
and never written anywhere.

Exit codes: 0 = everything fine, 1 = at least one tool failed, 2 = usage/config.

Only the Python standard library is used (urllib) so this runs even where the
backend's virtualenv / third-party packages are not available -- it is executed
from the autostart-on-logon script.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_API_BASE = "https://api.elevenlabs.io"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_LOCAL = PROJECT_ROOT / "frontend" / ".env.local"
HTTP_TIMEOUT = 60.0

# Canonical tool name -> path on the mock backend (see mock_backend/main.py).
# This map is the single source of truth for the demo: add a tool here once and
# both tunnel scripts pick it up.
TOOL_PATHS: Dict[str, str] = {
    "check_spa_availability": "/check_spa_availability",
    "book_spa_appointment": "/book_spa_appointment",
    "check_room_availability": "/check_room_availability",
    "send_sms_summary": "/send_sms_summary",
    "transfer_to_simulated_handoff": "/transfer_to_simulated_handoff",
    "cancel_spa_appointment": "/cancel_spa_appointment",
    "reschedule_spa_appointment": "/reschedule_spa_appointment",
}


def _string_property(description: str, enum: Optional[List[str]] = None) -> Dict[str, Any]:
    """Build a request-body property in the exact shape the API returns."""
    return {
        "type": "string",
        "description": description,
        "enum": enum,
        "is_system_provided": False,
        "dynamic_variable": "",
        "allowed_values": None,
        "allowed_values_dynamic_variable": "",
        "constant_value": "",
        "is_omitted": False,
    }


# Optional body properties the agent should send but currently does not.
# Strictly additive: --ensure-schema only ever *adds* these keys and never
# touches ``required``, never renames and never removes an existing property.
SCHEMA_ADDITIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "cancel_spa_appointment": {
        "appointment_datetime": _string_property(
            "Scheduled treatment date and time, ISO 8601 with time "
            "(e.g. 2026-11-09T18:30). Needed to apply the cancellation fee "
            "rule: more than 2 hours before the appointment is free.",
        ),
    },
    "send_sms_summary": {
        "language": _string_property(
            "Guest's language code (pl/en) so the SMS/Telegram summary uses the right language.",
            enum=["pl", "en"],
        ),
    },
    "transfer_to_simulated_handoff": {
        "language": _string_property(
            "Guest's language code (pl/en) so the handoff message uses the right language.",
            enum=["pl", "en"],
        ),
    },
}


class ApiError(RuntimeError):
    """Raised when the API cannot be reached or returns an unusable payload."""


class Client:
    """Minimal ElevenLabs REST client (stdlib only)."""

    def __init__(self, api_key: str, api_base: str = DEFAULT_API_BASE) -> None:
        self._api_key = api_key
        self.api_base = api_base.rstrip("/")

    # -- transport ---------------------------------------------------------
    def _raw(self, method: str, path: str, body: Optional[dict] = None) -> Tuple[int, str]:
        url = f"{self.api_base}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("xi-api-key", self._api_key)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        last_error = ""
        for attempt in range(2):  # one retry, transient network only
            try:
                with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                    return resp.status, resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as exc:  # real API answer -- no retry
                return exc.code, exc.read().decode("utf-8", "replace")[:400]
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = str(exc)
                if attempt == 0:
                    time.sleep(1.5)
        raise ApiError(f"{method} {path} nie doszło: {last_error}")

    def _json(self, method: str, path: str, body: Optional[dict] = None) -> Any:
        status, text = self._raw(method, path, body)
        if status >= 400:
            raise ApiError(f"{method} {path} -> HTTP {status}: {text.strip()[:300]}")
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ApiError(f"{method} {path} -> nie-JSON: {text[:200]}") from exc

    # -- endpoints ---------------------------------------------------------
    def list_tools(self) -> List[dict]:
        """All tools of the workspace, following pagination cursors."""
        tools: List[dict] = []
        cursor: Optional[str] = None
        for _ in range(50):  # hard stop, never loop forever
            path = "/v1/convai/tools"
            if cursor:
                path += "?cursor=" + urllib.parse.quote(cursor)
            payload = self._json("GET", path)
            if isinstance(payload, list):  # defensive: bare list
                tools.extend(payload)
                break
            if not isinstance(payload, dict):
                raise ApiError("GET /v1/convai/tools -> nieoczekiwany format odpowiedzi")
            tools.extend(payload.get("tools") or [])
            if not payload.get("has_more"):
                break
            cursor = payload.get("next_cursor")
            if not cursor:
                break
        return tools

    def get_tool(self, tool_id: str) -> dict:
        payload = self._json("GET", f"/v1/convai/tools/{tool_id}")
        if not isinstance(payload, dict):
            raise ApiError(f"GET tool {tool_id} -> nieoczekiwany format")
        return payload

    def patch_tool(self, tool_id: str, tool_config: dict) -> Tuple[int, str]:
        status, text = self._raw(
            "PATCH", f"/v1/convai/tools/{tool_id}", {"tool_config": tool_config}
        )
        return status, text.strip()[:300]


# ── helpers ────────────────────────────────────────────────────────────────
def load_api_key(cli_value: Optional[str]) -> Optional[str]:
    """--api-key > $ELEVENLABS_API_KEY > frontend/.env.local. Never echoed."""
    if cli_value and cli_value.strip():
        return cli_value.strip()
    env_value = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if env_value:
        return env_value
    if ENV_LOCAL.is_file():
        try:
            content = ENV_LOCAL.read_text(encoding="utf-8", errors="replace")
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


def tool_name(tool: dict) -> str:
    return str((tool.get("tool_config") or {}).get("name") or "")


def tool_config_of(tool: dict) -> dict:
    return tool.get("tool_config") or {}


def api_schema_of(tool_config: dict) -> dict:
    schema = tool_config.get("api_schema")
    return schema if isinstance(schema, dict) else {}


def body_schema_of(tool_config: dict) -> Optional[dict]:
    body = api_schema_of(tool_config).get("request_body_schema")
    return body if isinstance(body, dict) else None


def body_fields(tool_config: dict) -> List[str]:
    body = body_schema_of(tool_config) or {}
    return list((body.get("properties") or {}).keys())


def index_by_name(tools: List[dict]) -> Dict[str, dict]:
    """name -> tool (first occurrence wins)."""
    index: Dict[str, dict] = {}
    for tool in tools:
        name = tool_name(tool)
        if name and name not in index:
            index[name] = tool
    return index


def normalize_base_url(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    if not cleaned:
        raise ValueError("--base-url jest pusty")
    if not re.match(r"^https?://", cleaned, re.IGNORECASE):
        raise ValueError("--base-url musi zaczynać się od http:// lub https://")
    return cleaned


def _print_table(rows: List[Tuple[str, ...]], headers: Tuple[str, ...]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line)
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def _assert_additive(before: Dict[str, Any], after: Dict[str, Any], label: str) -> None:
    """Guard: refuse to send a schema that drops or rewrites anything."""
    for key, value in before.items():
        if key not in after:
            raise ApiError(f"{label}: wewnętrzny błąd — pole '{key}' zostałoby usunięte")
        if after[key] != value:
            raise ApiError(f"{label}: wewnętrzny błąd — pole '{key}' zostałoby zmienione")


# ── modes ──────────────────────────────────────────────────────────────────
def run_list(client: Client) -> int:
    tools = client.list_tools()
    index = index_by_name(tools)

    rows: List[Tuple[str, ...]] = []
    for name in TOOL_PATHS:
        tool = index.get(name)
        if tool is None:
            rows.append((name, "-", "(brak narzędzia w workspace)", "-"))
            continue
        config = tool_config_of(tool)
        rows.append(
            (
                name,
                str(tool.get("id") or "?"),
                str(api_schema_of(config).get("url") or "(brak URL)"),
                ",".join(body_fields(config)) or "(brak body)",
            )
        )
    _print_table(rows, ("NARZĘDZIE", "ID", "URL", "POLA BODY"))

    missing = [name for name in TOOL_PATHS if name not in index]
    extra_schema: List[str] = []
    for name, additions in SCHEMA_ADDITIONS.items():
        tool = index.get(name)
        if tool is None:
            continue
        fields = set(body_fields(tool_config_of(tool)))
        gaps = [prop for prop in additions if prop not in fields]
        if gaps:
            extra_schema.append(f"{name}: {', '.join(gaps)}")

    print()
    print(f"Narzędzi w workspace: {len(tools)}; oczekiwanych spa: {len(TOOL_PATHS)}")
    if missing:
        print("BRAKUJE: " + ", ".join(missing))
    else:
        print("Wszystkie 7 narzędzi spa obecne.")
    if extra_schema:
        print("Brakujące opcjonalne pola body (--ensure-schema): " + "; ".join(extra_schema))
    else:
        print("Schematy body kompletne.")
    return 1 if missing else 0


def run_sync(client: Client, base_url: str, dry_run: bool) -> int:
    base = normalize_base_url(base_url)
    index = index_by_name(client.list_tools())

    print(f"Synchronizacja webhooków -> {base}" + (" [DRY-RUN: bez zapisu]" if dry_run else ""))
    failures = 0
    changed = 0

    for name in TOOL_PATHS:
        target = f"{base}{TOOL_PATHS[name]}"
        tool = index.get(name)
        if tool is None:
            print(f"  [FAIL] {name}: nie znaleziono narzędzia o tej nazwie")
            failures += 1
            continue

        tool_id = str(tool.get("id") or "")
        config = tool_config_of(tool)
        schema = api_schema_of(config)
        current = str(schema.get("url") or "")

        if current == target:
            print(f"  [OK]   {name}: już wskazuje na nowy URL (bez zmian)")
            continue

        print(f"  [{'DRY' if dry_run else 'PATCH'}] {name} ({tool_id})")
        print(f"         było: {current or '(brak)'}")
        print(f"         będzie: {target}")
        if dry_run:
            changed += 1
            continue

        schema["url"] = target
        config["api_schema"] = schema
        try:
            status, detail = client.patch_tool(tool_id, config)
        except ApiError as exc:
            print(f"         [FAIL] {exc}")
            failures += 1
            continue
        if status in (200, 201):
            print(f"         [OK]   HTTP {status}")
            changed += 1
        else:
            print(f"         [FAIL] HTTP {status}: {detail[:200]}")
            failures += 1

    print()
    print(f"Zmieniono: {changed}; błędów: {failures}")
    return 1 if failures else 0


def run_ensure_schema(client: Client, dry_run: bool) -> int:
    index = index_by_name(client.list_tools())
    print(
        "Uzupełnianie brakujących opcjonalnych pól body"
        + (" [DRY-RUN: bez zapisu]" if dry_run else "")
    )
    failures = 0
    changed = 0

    for name, additions in SCHEMA_ADDITIONS.items():
        tool = index.get(name)
        if tool is None:
            print(f"  [SKIP] {name}: brak narzędzia w workspace")
            continue
        tool_id = str(tool.get("id") or "")

        # Fresh read right before writing -- the list payload can be stale.
        try:
            tool = client.get_tool(tool_id)
        except ApiError as exc:
            print(f"  [FAIL] {name}: {exc}")
            failures += 1
            continue

        config = tool_config_of(tool)
        body = body_schema_of(config)
        if body is None:
            print(f"  [SKIP] {name}: brak request_body_schema (nie dotykam)")
            continue

        properties = body.get("properties")
        if not isinstance(properties, dict):
            print(f"  [SKIP] {name}: request_body_schema bez 'properties' (nie dotykam)")
            continue

        present = [prop for prop in additions if prop in properties]
        missing = {prop: spec for prop, spec in additions.items() if prop not in properties}

        for prop in present:
            print(f"  [=]    {name}.{prop}: już jest — bez zmian")

        if not missing:
            continue

        before = dict(properties)
        after = dict(properties)
        after.update(missing)
        _assert_additive(before, after, name)  # never remove/rename anything

        print(f"  [{'DRY' if dry_run else 'PATCH'}] {name} ({tool_id}) dodaje:")
        for prop, spec in missing.items():
            print(f"         + {prop}: {json.dumps(spec, ensure_ascii=False)}")
        print(f"         required pozostaje: {json.dumps(body.get('required') or [])}")

        if dry_run:
            changed += 1
            continue

        body["properties"] = after
        api_schema_of(config)["request_body_schema"] = body
        try:
            status, detail = client.patch_tool(tool_id, config)
        except ApiError as exc:
            print(f"         [FAIL] {exc}")
            failures += 1
            continue
        if status in (200, 201):
            print(f"         [OK]   HTTP {status} — dodano: {', '.join(missing)}")
            changed += 1
        else:
            print(f"         [FAIL] HTTP {status}: {detail[:200]}")
            failures += 1

    print()
    print(f"Zmienionych narzędzi: {changed}; błędów: {failures}")
    return 1 if failures else 0


# ── entry point ────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sync_agent_tools.py",
        description=(
            "Przepina webhooki agenta ElevenLabs na aktualny URL tunelu "
            "(trycloudflare zmienia URL przy każdym starcie) i opcjonalnie "
            "uzupełnia brakujące opcjonalne pola schematu."
        ),
        epilog=(
            "Przykłady:\n"
            "  python sync_agent_tools.py --base-url https://xxx.trycloudflare.com\n"
            "  python sync_agent_tools.py --list\n"
            "  python sync_agent_tools.py --ensure-schema --dry-run\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base-url",
        metavar="URL",
        help="publiczny URL tunelu; wymagany w trybie synchronizacji (domyślnym)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="tylko odczyt: tabela nazwa/id/URL/pola body i wyjście",
    )
    parser.add_argument(
        "--ensure-schema",
        action="store_true",
        help="dodaj brakujące OPCJONALNE pola body (appointment_datetime, language)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="pokaż zamierzone PATCH-e, nic nie zapisuj",
    )
    parser.add_argument(
        "--api-key",
        metavar="KEY",
        help="klucz API (domyślnie $ELEVENLABS_API_KEY lub frontend/.env.local)",
    )
    parser.add_argument(
        "--api-base",
        default=DEFAULT_API_BASE,
        metavar="URL",
        help=f"baza API (domyślnie {DEFAULT_API_BASE})",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    try:  # emoji/diacritics must never crash a logon script
        sys.stdout.reconfigure(errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

    args = build_parser().parse_args(argv)

    api_key = load_api_key(args.api_key)
    if not api_key:
        print(
            "BŁĄD: brak klucza API — ustaw ELEVENLABS_API_KEY w środowisku, "
            f"podaj --api-key albo wpisz go do {ENV_LOCAL}",
            file=sys.stderr,
        )
        return 2

    client = Client(api_key, args.api_base)

    try:
        if args.list:
            return run_list(client)
        if args.ensure_schema:
            return run_ensure_schema(client, args.dry_run)
        if not args.base_url:
            print(
                "BŁĄD: tryb synchronizacji wymaga --base-url "
                "(albo użyj --list / --ensure-schema)",
                file=sys.stderr,
            )
            return 2
        try:
            base_url = normalize_base_url(args.base_url)
        except ValueError as exc:
            print(f"BŁĄD: {exc}", file=sys.stderr)
            return 2
        return run_sync(client, base_url, args.dry_run)
    except ApiError as exc:
        print(f"BŁĄD API: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
