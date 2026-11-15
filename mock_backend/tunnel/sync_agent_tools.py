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
tools, not just the five the old inline heredocs knew about. The tool names, paths
and body fields are data in ``tunnel/tool_schemas.py``.

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
import io
import json
import os
import re
import sys
import urllib.parse
from typing import List, Optional, Tuple

try:  # uruchomienie jako skrypt: sys.path[0] == katalog tunnel/
    import tool_schemas as ts
    from _http import ENV_LOCAL, ApiClient, ApiError, resolve_api_key
except ImportError:  # import jako pakiet: `from tunnel import sync_agent_tools`
    from tunnel import tool_schemas as ts
    from tunnel._http import ENV_LOCAL, ApiClient, ApiError, resolve_api_key

DEFAULT_API_BASE = "https://api.elevenlabs.io"
HTTP_TIMEOUT = 60.0
HTTP_RETRIES = 1  # ponowienie tylko przy błędzie sieci (patrz _http.ApiClient)

# Header the backend expects on every tool call (routers/security.py). The sync sets it on each
# tool when $ANNA_WEBHOOK_SECRET is configured; without it every call would be rejected with 401.
# NOTE: `api_schema.request_headers` follows the ElevenLabs tool schema as documented; it has not
# been verified against the live workspace from this repository (the value is never printed).
AUTH_HEADER = "X-Webhook-Secret"


def webhook_secret_from_env() -> str:
    return os.environ.get("ANNA_WEBHOOK_SECRET", "").strip()


def auth_header_ok(schema: dict, secret: str) -> bool:
    """True when no secret is configured, or the tool already carries the exact header value."""
    if not secret:
        return True
    headers = schema.get("request_headers")
    return isinstance(headers, dict) and headers.get(AUTH_HEADER) == secret


def with_auth_header(schema: dict, secret: str) -> dict:
    """Return the schema with the auth header merged in (existing headers are kept)."""
    headers = dict(schema.get("request_headers") or {})
    headers[AUTH_HEADER] = secret
    return {**schema, "request_headers": headers}


# ── endpoints (ApiClient z _http.py) ───────────────────────────────────────
def list_tools(client: ApiClient) -> List[dict]:
    """All tools of the workspace, following pagination cursors."""
    tools: List[dict] = []
    cursor: Optional[str] = None
    for _ in range(50):  # hard stop, never loop forever
        path = "/v1/convai/tools"
        if cursor:
            path += "?cursor=" + urllib.parse.quote(cursor)
        payload = client.request_ok("GET", path)
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


def get_tool(client: ApiClient, tool_id: str) -> dict:
    payload = client.request_ok("GET", f"/v1/convai/tools/{tool_id}")
    if not isinstance(payload, dict):
        raise ApiError(f"GET tool {tool_id} -> nieoczekiwany format")
    return payload


def patch_tool(client: ApiClient, tool_id: str, tool_config: dict) -> Tuple[int, str]:
    """Zwraca (status, skrócona treść); HTTP-owe błędy są po stronie wywołującego."""
    status, text = client.request(
        "PATCH", f"/v1/convai/tools/{tool_id}", {"tool_config": tool_config}
    )
    return status, client.redact(text.strip()[:300])


# ── helpers ────────────────────────────────────────────────────────────────
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


def _assert_additive(before: dict, after: dict, label: str) -> None:
    """Guard: refuse to send a schema that drops or rewrites anything."""
    for key, value in before.items():
        if key not in after:
            raise ApiError(f"{label}: wewnętrzny błąd — pole '{key}' zostałoby usunięte")
        if after[key] != value:
            raise ApiError(f"{label}: wewnętrzny błąd — pole '{key}' zostałoby zmienione")


# ── modes ──────────────────────────────────────────────────────────────────
def run_list(client: ApiClient) -> int:
    tools = list_tools(client)
    index = ts.index_by_name(tools)

    rows: List[Tuple[str, ...]] = []
    for name in ts.TOOL_PATHS:
        tool = index.get(name)
        if tool is None:
            rows.append((name, "-", "(brak narzędzia w workspace)", "-"))
            continue
        config = ts.tool_config_of(tool)
        rows.append(
            (
                name,
                str(tool.get("id") or "?"),
                str(ts.api_schema_of(config).get("url") or "(brak URL)"),
                ",".join(ts.body_fields(config)) or "(brak body)",
            )
        )
    _print_table(rows, ("NARZĘDZIE", "ID", "URL", "POLA BODY"))

    missing = [name for name in ts.TOOL_PATHS if name not in index]
    extra_schema = ts.additions_gaps(index)

    print()
    print(f"Narzędzi w workspace: {len(tools)}; oczekiwanych spa: {len(ts.TOOL_PATHS)}")
    if missing:
        print("BRAKUJE: " + ", ".join(missing))
    else:
        print("Wszystkie 7 narzędzi spa obecne.")
    if extra_schema:
        print("Brakujące opcjonalne pola body (--ensure-schema): " + "; ".join(extra_schema))
    else:
        print("Schematy body kompletne.")
    return 1 if missing else 0


def run_sync(client: ApiClient, base_url: str, dry_run: bool) -> int:
    base = normalize_base_url(base_url)
    index = ts.index_by_name(list_tools(client))

    print(f"Synchronizacja webhooków -> {base}" + (" [DRY-RUN: bez zapisu]" if dry_run else ""))
    secret = webhook_secret_from_env()
    if secret:
        print(f"  Nagłówek {AUTH_HEADER} zostanie ustawiony na każdym narzędziu (wartość nie jest wypisywana).")
    else:
        print(f"  UWAGA: ANNA_WEBHOOK_SECRET nie jest ustawiony — nagłówek {AUTH_HEADER} nie jest zarządzany.")
    failures = 0
    changed = 0

    for name in ts.TOOL_PATHS:
        target = f"{base}{ts.TOOL_PATHS[name]}"
        tool = index.get(name)
        if tool is None:
            print(f"  [FAIL] {name}: nie znaleziono narzędzia o tej nazwie")
            failures += 1
            continue

        tool_id = str(tool.get("id") or "")
        config = ts.tool_config_of(tool)
        schema = ts.api_schema_of(config)
        current = str(schema.get("url") or "")

        header_ok = auth_header_ok(schema, secret)
        if current == target and header_ok:
            print(f"  [OK]   {name}: już wskazuje na nowy URL (bez zmian)")
            continue

        print(f"  [{'DRY' if dry_run else 'PATCH'}] {name} ({tool_id})")
        print(f"         było: {current or '(brak)'}")
        print(f"         będzie: {target}")
        if not header_ok:
            print(f"         + ustawia nagłówek {AUTH_HEADER}")
        if dry_run:
            changed += 1
            continue

        schema["url"] = target
        if not header_ok:
            schema = with_auth_header(schema, secret)
        config["api_schema"] = schema
        try:
            status, detail = patch_tool(client, tool_id, config)
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


def run_ensure_schema(client: ApiClient, dry_run: bool) -> int:
    index = ts.index_by_name(list_tools(client))
    print(
        "Uzupełnianie brakujących opcjonalnych pól body"
        + (" [DRY-RUN: bez zapisu]" if dry_run else "")
    )
    failures = 0
    changed = 0

    for name, additions in ts.SCHEMA_ADDITIONS.items():
        tool = index.get(name)
        if tool is None:
            print(f"  [SKIP] {name}: brak narzędzia w workspace")
            continue
        tool_id = str(tool.get("id") or "")

        # Fresh read right before writing -- the list payload can be stale.
        try:
            tool = get_tool(client, tool_id)
        except ApiError as exc:
            print(f"  [FAIL] {name}: {exc}")
            failures += 1
            continue

        config = ts.tool_config_of(tool)
        body = ts.body_schema_of(config)
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
        ts.api_schema_of(config)["request_body_schema"] = body
        try:
            status, detail = patch_tool(client, tool_id, config)
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


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def dispatch(args: argparse.Namespace) -> int:
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print(
            "BŁĄD: brak klucza API — ustaw ELEVENLABS_API_KEY w środowisku, "
            f"podaj --api-key albo wpisz go do {ENV_LOCAL}",
            file=sys.stderr,
        )
        return 2

    client = ApiClient(args.api_base, api_key, timeout=HTTP_TIMEOUT, retries=HTTP_RETRIES)

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


def main(argv: Optional[List[str]] = None) -> int:
    try:  # emoji/diacritics must never crash a logon script
        # isinstance zamiast `type: ignore`: typeshed daje sys.stdout typ TextIO, a reconfigure jest
        # tylko na TextIOWrapper (to CPython daje w konsoli i w pipe).
        for stream in (sys.stdout, sys.stderr):
            if isinstance(stream, io.TextIOWrapper):
                stream.reconfigure(errors="replace")
    except ValueError:
        pass
    return dispatch(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
