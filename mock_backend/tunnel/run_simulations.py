#!/usr/bin/env python3
"""Produce the K2 evidence: seed the mock PMS, run three live simulations, save transcripts.

Why this exists
---------------
The K2 proof is not "the prompt looks right" -- it is three recorded conversations in
which the agent asks before booking an ambiguous treatment, quotes the backend's 0%/50%
cancellation fee instead of inventing one, and passes ``appointment_datetime`` to the
tool. Simulations are created through the current API (``POST /v1/convai/agent-testing/
create`` + ``POST /v1/convai/agents/{id}/run-tests``); the old ``simulate-conversation``
endpoint was removed on 31 Oct 2026 and returns 410.

Dates are computed at run time, never hardcoded: the mock backend computes the fee from
``appointment_datetime`` versus *now*, so a scenario written for a fixed day silently
turns into a 0% case a week later. Test scenarios therefore embed the booking id and
datetime that this script has just created in the in-memory store.

The scenario texts and their assertions are data in ``tunnel/scenarios.py``; this module
only seeds the PMS, talks to the APIs and writes the results.

Modes
-----
  (default)          full run: credits check, seed, create tests, run, poll, save
  --check            read-only: subscription credits + backend health + branch
  --dry-run          build every payload and print it, spend nothing, write nothing
  --keep-tests       do not delete previous ``K2-*`` tests first
  --skip-scenario3   run scenarios 1-2 only (when no slot is within the 2 h window)

Exit codes: 0 = all simulations passed, 1 = at least one failed, 2 = config/backend,
3 = credits exhausted, 4 = timeout, 5 = partial (scenario 3 skipped).

The key is read from ``--api-key``, else ``$ELEVENLABS_API_KEY``, else ``frontend/.env.local``.
It is never printed. Standard library only (urllib), like ``sync_agent_tools.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:  # uruchomienie jako skrypt: sys.path[0] == katalog tunnel/
    from _http import ApiClient, resolve_api_key
    from scenarios import TEST_PREFIX, dry_run_seeds, scenario_payloads
    from tool_schemas import TOOL_PATHS, api_schema_of, tool_name
    from transcripts import save, transcript_text  # noqa: F401 - transcript_text: re-eksport dla testów
except ImportError:  # import jako pakiet: `from tunnel import run_simulations`
    from tunnel._http import ApiClient, resolve_api_key
    from tunnel.scenarios import TEST_PREFIX, dry_run_seeds, scenario_payloads
    from tunnel.tool_schemas import TOOL_PATHS, api_schema_of, tool_name
    from tunnel.transcripts import save, transcript_text  # noqa: F401

API_BASE = "https://api.elevenlabs.io"
CALL_TIMEOUT = 120  # sekundy na jedno wywołanie HTTP (symulacje bywają wolne)
DEFAULT_AGENT = "agent_8401m0n03cggfgebhfh0cj96t7aj"
DEFAULT_BRANCH = "agtbrch_9601m0n03dege4yvwseypec1hm81"
DEFAULT_BACKEND = "http://127.0.0.1:8011"
POLL_SECONDS = 15
POLL_TIMEOUT = 900


def _utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def api_key(cli: Optional[str]) -> str:
    key = resolve_api_key(cli)
    if not key:
        raise SystemExit("brak klucza: --api-key, $ELEVENLABS_API_KEY albo frontend/.env.local")
    return key


def whoami(client: ApiClient, hard: bool = True) -> Tuple[bool, str]:
    """Return (credits_available, message); SystemExit(3) when hard and exhausted."""
    status, sub = client.request_json("GET", "/v1/user/subscription")
    if status != 200 or not isinstance(sub, dict):
        raise SystemExit(f"nie mogę odczytać subskrypcji (HTTP {status}); sprawdź klucz")
    used = sub.get("character_count")
    limit = sub.get("character_limit")
    tier = sub.get("tier", "?")
    reset_ts = sub.get("next_character_count_reset_unix")
    reset = datetime.fromtimestamp(reset_ts).strftime("%Y-%m-%d %H:%M") if reset_ts else "?"
    text = f"tier={tier} credits={used}/{limit} reset={reset}"
    exhausted = isinstance(used, int) and isinstance(limit, int) and used >= limit >= 0
    if exhausted and hard:
        print(f"KREDYTY WYCZERPANE — {text}")
        print("Symulacje skończą się 'Insufficient credits'. Nic nie uruchamiam.")
        raise SystemExit(3)
    return (not exhausted), text


def find_slot(backend: ApiClient, service: str, day: date,
              within_hours: Optional[float] = None) -> Optional[str]:
    status, resp = backend.request_json(
        "POST", "/check_spa_availability", {"service_name": service, "date": day.isoformat()}
    )
    if status != 200 or not isinstance(resp, dict) or not resp.get("available"):
        return None
    slots = resp.get("slots") or []
    if within_hours is None:
        return slots[0] if slots else None
    now = datetime.now()
    for slot in slots:
        when = datetime.combine(day, datetime.strptime(slot, "%H:%M").time())
        delta = (when - now).total_seconds() / 3600
        if 0 < delta <= within_hours:
            return slot
    return None


def _sync_module() -> Any:
    """Import sync_agent_tools whether we run as a module or as a plain script."""
    try:
        from tunnel import sync_agent_tools as sync
        return sync
    except ImportError:
        import importlib.util

        path = Path(__file__).with_name("sync_agent_tools.py")
        spec = importlib.util.spec_from_file_location("anna_sync_agent_tools", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module


def tool_health(key: str, timeout: int = 20) -> List[Dict[str, Any]]:
    """Resolve every webhook tool URL and report whether its host answers /health.

    A stale quick-tunnel URL is the classic reason a simulation fails mid-call:
    the agent reaches the tool, the webhook host is dead, the procedure stops.
    """
    sync = _sync_module()

    client = ApiClient(sync.DEFAULT_API_BASE, key, timeout=CALL_TIMEOUT)
    bases: Dict[str, List[str]] = {}
    seen: set = set()
    for tool in sync.list_tools(client):
        name = tool_name(tool)
        if name not in TOOL_PATHS or name in seen:
            continue  # the workspace also holds unrelated tools (other projects)
        seen.add(name)
        config = tool.get("tool_config") or {}
        url = str(api_schema_of(config).get("url") or "")
        if not url:
            raise SystemExit(f"narzędzie {name} nie ma URL-a webhooka")
        parts = urllib.parse.urlsplit(url)
        bases.setdefault(f"{parts.scheme}://{parts.netloc}", []).append(name)
    missing = sorted(set(TOOL_PATHS) - seen)
    if missing:
        raise SystemExit("brakujące narzędzia agenta: " + ", ".join(missing))
    report = []
    for base, names in bases.items():
        try:
            status, _ = ApiClient(base, timeout=timeout).request_json("GET", "/health")
        except Exception as err:  # noqa: BLE001 - DNS/timeout means a dead host
            status = f"ERR {err}"
        report.append({"base": base, "tools": names, "status": status})
    return report


def seed(backend: ApiClient, days_ahead: int, service: str, slot: Optional[str],
         guest: str) -> Optional[Dict[str, Any]]:
    day = date.today() + timedelta(days=days_ahead)
    when = slot or find_slot(backend, service, day)
    if when is None:
        return None
    status, resp = backend.request_json(
        "POST", "/book_spa_appointment",
        {"service_name": service, "date": day.isoformat(), "time": when, "guest_name": guest},
    )
    if status != 200 or not isinstance(resp, dict) or not resp.get("success"):
        return None
    return {"id": resp["confirmation_id"], "date": day.isoformat(), "time": when,
            "service": resp.get("service_name", service), "guest": guest}


def cleanup_old_tests(client: ApiClient) -> None:
    status, listing = client.request_json("GET", "/v1/convai/agent-testing")
    if status != 200 or not isinstance(listing, dict):
        print(f"  nie mogę wylistować testów (HTTP {status}) — pomijam porządki")
        return
    items = listing.get("tests") or listing.get("items") or []
    for item in items:
        if not str(item.get("name", "")).startswith(TEST_PREFIX):
            continue
        code, _ = client.request_json("DELETE", f"/v1/convai/agent-testing/{item['id']}")
        print(f"  usunięty stary test {item['name']} ({item['id']}): HTTP {code}")


def run_tests(client: ApiClient, agent: str, branch: str,
              payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    created = []
    for p in payloads:
        status, resp = client.request_json("POST", "/v1/convai/agent-testing/create", p["body"])
        if status != 200 or not isinstance(resp, dict) or "id" not in resp:
            raise SystemExit(f"create test failed for {p['slug']}: HTTP {status} {str(resp)[:300]}")
        print(f"  test {p['slug']} -> {resp['id']}")
        created.append({"slug": p["slug"], "test_id": resp["id"]})

    status, resp = client.request_json(
        "POST", f"/v1/convai/agents/{agent}/run-tests",
        {"name": f"K2-evidence-{date.today().isoformat()}",
         "tests": [{"test_id": c["test_id"]} for c in created],
         "branch_id": branch, "repeat_count": 1},
    )
    if status != 200:
        raise SystemExit(f"run-tests failed: HTTP {status} {str(resp)[:500]}")
    return resp


def poll(client: ApiClient, invocation: str) -> Dict[str, Any]:
    deadline = time.time() + POLL_TIMEOUT
    last = None
    resp: Dict[str, Any] = {}
    while time.time() < deadline:
        status, resp = client.request_json("GET", f"/v1/convai/test-invocations/{invocation}")
        if status != 200 or not isinstance(resp, dict):
            raise SystemExit(f"poll failed: HTTP {status} {str(resp)[:300]}")
        runs = resp.get("test_runs") or []
        line = ", ".join(f"{r.get('test_name')}={r.get('status')}" for r in runs)
        if line != last:
            print(f"  {time.strftime('%H:%M:%S')} {line}", flush=True)
            last = line
        if runs and all(r.get("status") in {"passed", "failed", "cancelled"} for r in runs):
            return resp
        time.sleep(POLL_SECONDS)
    raise SystemExit(4)


# ── CLI: parsowanie, sprawdzenia wstępne, tryby ───────────────────────────
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="K2 evidence: live simulations + transcripts.")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT)
    parser.add_argument("--branch-id", default=DEFAULT_BRANCH)
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--api-key")
    parser.add_argument("--check", action="store_true", help="tylko odczyt: kredyty, backend, gałąź")
    parser.add_argument("--dry-run", action="store_true", help="zbuduj payloady, nic nie uruchamiaj")
    parser.add_argument("--keep-tests", action="store_true", help="nie usuwaj poprzednich testów K2-*")
    parser.add_argument("--skip-scenario3", action="store_true", help="pomiń scenariusz <2 h")
    parser.add_argument("--skip-tools-check", action="store_true",
                        help="nie sprawdzaj, czy hosty webhooków agenta odpowiadają")
    return parser.parse_args(argv)


def _check_tools(key: str) -> Optional[int]:
    """Kod wyjścia 2 gdy narzędzi brak albo hosty webhooków nie odpowiadają; None gdy OK."""
    try:
        report = tool_health(key)
    except Exception as err:  # noqa: BLE001 - surface any API/network failure as config error
        print(f"nie mogę sprawdzić narzędzi agenta: {err}")
        return 2
    if not report:
        print("agent nie ma narzędzi z URL-em webhooka — uruchom sync_agent_tools.py")
        return 2
    dead = []
    for entry in report:
        host_status = entry["status"]
        host_ok = isinstance(host_status, int) and 200 <= host_status < 300
        print(f"  webhooki @ {entry['base']}: {host_status} "
              f"({len(entry['tools'])} narzędzi: {', '.join(entry['tools'])})")
        if not host_ok:
            dead.append(entry["base"])
    if dead:
        print("Martwy host webhooków: " + ", ".join(dead))
        print("Uruchom tunel i przepnij narzędzia: "
              "python mock_backend/tunnel/sync_agent_tools.py --base-url https://<tunel>")
        return 2
    return None


def _print_dry_run(args: argparse.Namespace) -> int:
    payloads = scenario_payloads(dry_run_seeds(date.today()))
    if args.skip_scenario3:
        payloads = [p for p in payloads if not p["slug"].startswith("03")]
    print("\n--- dry run: payloady (bez seed, bez POST) ---")
    print(json.dumps([p["body"] for p in payloads], ensure_ascii=False, indent=2))
    print("--- koniec; nic nie utworzono, nic nie uruchomiono ---")
    return 0


def _run_simulations(el: ApiClient, backend: ApiClient, args: argparse.Namespace) -> int:
    if args.skip_scenario3:
        fee_slot = None
    else:
        fee_slot = find_slot(backend, "kąpiel siarczkowa", date.today(), within_hours=2)
        if fee_slot is None:
            print("Scenariusz <2 h: brak wolnego slotu w najbliższych 2 h.")
            print("Uruchom ponownie między 08:00 a 16:00 (albo z --skip-scenario3).")
            return 2
        print(f"Scenariusz <2 h: dzisiejszy slot {fee_slot}")

    seeds = {
        "book": seed(backend, 1, "masaż leczniczy pleców", None, "Piotr Zieliński"),
        "cancel_free": seed(backend, 2, "masaż leczniczy pleców", None, "Jan Kowalski"),
        "cancel_fee": seed(backend, 0, "kąpiel siarczkowa", fee_slot, "Maria Nowak") if fee_slot else None,
    }
    for name, value in seeds.items():
        if value is None:
            print(f"seed '{name}' nie wyszedł — sprawdź dostępność w backendzie")
            return 2
        print(f"seed {name}: {value['id']} {value['date']} {value['time']}")

    payloads = scenario_payloads(seeds)
    if args.skip_scenario3:
        payloads = [p for p in payloads if not p["slug"].startswith("03")]

    if not args.keep_tests:
        cleanup_old_tests(el)

    invocation = run_tests(el, args.agent_id, args.branch_id, payloads)
    print(f"inwokacja {invocation.get('id')} — czekam na wynik")
    final = poll(el, invocation["id"])
    failures = save(final, payloads, seeds)
    if failures:
        print(f"{failures} test(ów) nie przeszło — patrz SUMMARY.md")
        return 1
    print("wszystkie symulacje przeszły")
    return 0


def dispatch(args: argparse.Namespace) -> int:
    key = api_key(args.api_key)
    el = ApiClient(API_BASE, key, timeout=CALL_TIMEOUT)
    backend = ApiClient(args.backend, timeout=CALL_TIMEOUT)

    ok, credits = whoami(el, hard=not (args.dry_run or args.check))
    print(f"ElevenLabs: {credits}")
    if not ok and args.dry_run:
        print("(dry run: buduję payloady mimo braku kredytów, nic nie uruchamiam)")

    status, health = backend.request_json("GET", "/health")
    if status != 200:
        print(f"Backend {args.backend} nie odpowiada (HTTP {status}). Uruchom mock_backend.")
        return 2
    print(f"Backend: {json.dumps(health, ensure_ascii=False)}")

    if not args.skip_tools_check:
        code = _check_tools(key)
        if code is not None:
            return code

    if args.check:
        status, _branch = el.request_json("GET", f"/v1/convai/agents/{args.agent_id}/branches/{args.branch_id}")
        print(f"Branch {args.branch_id}: HTTP {status}")
        return 0 if ok else 3

    if args.dry_run:
        return _print_dry_run(args)
    return _run_simulations(el, backend, args)


def main(argv: Optional[List[str]] = None) -> int:
    _utf8_stdout()
    return dispatch(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
