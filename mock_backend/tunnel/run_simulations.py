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
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_LOCAL = PROJECT_ROOT / "frontend" / ".env.local"
TRANSCRIPTS = PROJECT_ROOT / ".planning" / "transcripts"
API_BASE = "https://api.elevenlabs.io"
DEFAULT_AGENT = "agent_8401m0n03cggfgebhfh0cj96t7aj"
DEFAULT_BRANCH = "agtbrch_9601m0n03dege4yvwseypec1hm81"
DEFAULT_BACKEND = "http://127.0.0.1:8011"
POLL_SECONDS = 15
POLL_TIMEOUT = 900
TEST_PREFIX = "K2-"


def _utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def api_key(cli: Optional[str]) -> str:
    if cli:
        return cli
    env = os.environ.get("ELEVENLABS_API_KEY")
    if env:
        return env.strip()
    if ENV_LOCAL.exists():
        for line in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("ELEVENLABS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("brak klucza: --api-key, $ELEVENLABS_API_KEY albo frontend/.env.local")


class Client:
    def __init__(self, base: str, key: Optional[str] = None) -> None:
        self.base = base.rstrip("/")
        self.key = key

    def call(self, method: str, path: str, body: Optional[dict] = None,
             timeout: int = 120) -> Tuple[int, Any]:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if self.key:
            req.add_header("xi-api-key", self.key)
        if data is not None:
            req.add_header("Content-Type", "application/json; charset=utf-8")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as err:
            raw = err.read().decode("utf-8", "replace")
            try:
                return err.code, json.loads(raw)
            except json.JSONDecodeError:
                return err.code, raw


def whoami(client: Client, hard: bool = True) -> Tuple[bool, str]:
    """Return (credits_available, message); SystemExit(3) when hard and exhausted."""
    status, sub = client.call("GET", "/v1/user/subscription")
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


def find_slot(backend: Client, service: str, day: date,
              within_hours: Optional[float] = None) -> Optional[str]:
    status, resp = backend.call(
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


def seed(backend: Client, days_ahead: int, service: str, slot: Optional[str],
         guest: str) -> Optional[Dict[str, Any]]:
    day = date.today() + timedelta(days=days_ahead)
    when = slot or find_slot(backend, service, day)
    if when is None:
        return None
    status, resp = backend.call(
        "POST", "/book_spa_appointment",
        {"service_name": service, "date": day.isoformat(), "time": when, "guest_name": guest},
    )
    if status != 200 or not isinstance(resp, dict) or not resp.get("success"):
        return None
    return {"id": resp["confirmation_id"], "date": day.isoformat(), "time": when,
            "service": resp.get("service_name", service), "guest": guest}


def scenario_payloads(seeds: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    book_seed = seeds["book"]
    cancel_free = seeds["cancel_free"]
    cancel_fee = seeds["cancel_fee"]
    book_day = date.fromisoformat(book_seed["date"])

    return [
        {
            "slug": "01-rezerwacja-masaz-ambiguous",
            "body": {
                "type": "simulation",
                "name": TEST_PREFIX + "01-rezerwacja-masaz-ambiguous",
                "simulation_scenario": (
                    "Jesteś gościem uzdrowiska Bukowy Dwór w Krynicy-Zdroju i dzwonisz, żeby zarezerwować "
                    f"masaż na {book_day.strftime('%d.%m.%Y')} na godzinę {book_seed['time']}. Na początku "
                    "mówisz tylko, że chcesz zarezerwować 'masaż', i nie precyzujesz rodzaju, dopóki agent "
                    "sam o to nie zapyta. Gdy agent wymieni kandydatów, wybierasz 'masaż leczniczy pleców'. "
                    "Na pytanie o imię i nazwisko podajesz 'Piotr Zieliński'. Na pytanie o numer telefonu "
                    "podajesz '+48 600 100 200'. Mówisz po polsku, krótko i naturalnie, jak osoba w średnim "
                    "wieku. Nie znasz cen ani godzin — pytasz o nie agenta. Na końcu dziękujesz."
                ),
                "simulation_max_turns": 16,
                "success_conditions": [
                    "Agent zapytał gościa, który masaż ma na myśli, zanim podał termin lub cenę.",
                    "Agent podał cenę 120 zł i czas trwania 30 minut z odpowiedzi check_spa_availability.",
                    "Agent zarezerwował zabieg przez book_spa_appointment i podał numer SPA-XXXX.",
                    "Agent nie wymyślił ceny, godziny ani dostępności — wszystkie liczby z narzędzi.",
                ],
                "dynamic_variables": {"user_language": "pl"},
                "tool_mock_config": {"mocking_strategy": "none"},
                "simulation_environment": "production",
            },
            "expect": {
                "tool": "book_spa_appointment",
                "text": ["120", "SPA-"],
                "forbid": ["129", "150 zł"],
            },
        },
        {
            "slug": "02-anulowanie-ponad-2h",
            "body": {
                "type": "simulation",
                "name": TEST_PREFIX + "02-anulowanie-ponad-2h",
                "simulation_scenario": (
                    "Jesteś gościem uzdrowiska Bukowy Dwór. Dzwonisz, żeby odwołać rezerwację zabiegu o "
                    f"numerze {cancel_free['id']} ({cancel_free['service']}). Zabieg jest "
                    f"{date.fromisoformat(cancel_free['date']).strftime('%d.%m.%Y')} o godzinie "
                    f"{cancel_free['time']}. Powód odwołania: zmiana planów wyjazdu, powód NIE jest medyczny. "
                    "Mówisz po polsku, krótko. Numer rezerwacji i termin podajesz, gdy agent o nie zapyta."
                ),
                "simulation_max_turns": 8,
                "success_conditions": [
                    (
                        f"Agent przekazał appointment_datetime {cancel_free['date']}T{cancel_free['time']} "
                        "w wywołaniu cancel_spa_appointment."
                    ),
                    "Agent przekazał medical_release jako false.",
                    "Agent powtórzył gościowi fee_rule: ponad 2 godziny przed zabiegiem — bezpłatnie (0%).",
                    "Agent nie potwierdził anulowania bez wywołania narzędzia.",
                ],
                "dynamic_variables": {"user_language": "pl"},
                "tool_mock_config": {"mocking_strategy": "none"},
                "simulation_environment": "production",
            },
            "expect": {
                "tool": "cancel_spa_appointment",
                "text": ["0%", cancel_free["id"]],
                "forbid": ["50%"],
            },
        },
        {
            "slug": "03-anulowanie-ponizej-2h",
            "body": {
                "type": "simulation",
                "name": TEST_PREFIX + "03-anulowanie-ponizej-2h",
                "simulation_scenario": (
                    "Jesteś gościem uzdrowiska Bukowy Dwór. Dzwonisz, żeby odwołać rezerwację zabiegu o "
                    f"numerze {cancel_fee['id']} ({cancel_fee['service']}). Zabieg jest dzisiaj, "
                    f"{date.fromisoformat(cancel_fee['date']).strftime('%d.%m.%Y')}, o godzinie "
                    f"{cancel_fee['time']} — czyli w ciągu najbliższych dwóch godzin. Powód: zmiana planów, "
                    "NIE medyczny, czujesz się dobrze. Mówisz po polsku, krótko. Numer i godzinę podajesz, "
                    "gdy agent o nie zapyta."
                ),
                "simulation_max_turns": 8,
                "success_conditions": [
                    (
                        f"Agent przekazał appointment_datetime {cancel_fee['date']}T{cancel_fee['time']} "
                        "w wywołaniu cancel_spa_appointment."
                    ),
                    "Agent przekazał medical_release jako false.",
                    "Agent poinformował gościa o opłacie 50% zgodnie z fee_rule z backendu.",
                    "Agent nie wymyślił kwoty — powtórzył regułę i wartość fee z narzędzia.",
                ],
                "dynamic_variables": {"user_language": "pl"},
                "tool_mock_config": {"mocking_strategy": "none"},
                "simulation_environment": "production",
            },
            "expect": {
                "tool": "cancel_spa_appointment",
                "text": ["50%", cancel_fee["id"]],
                "forbid": ["bezpłatn"],
            },
        },
    ]


def cleanup_old_tests(client: Client) -> None:
    status, listing = client.call("GET", "/v1/convai/agent-testing")
    if status != 200 or not isinstance(listing, dict):
        print(f"  nie mogę wylistować testów (HTTP {status}) — pomijam porządki")
        return
    items = listing.get("tests") or listing.get("items") or []
    for item in items:
        if not str(item.get("name", "")).startswith(TEST_PREFIX):
            continue
        code, _ = client.call("DELETE", f"/v1/convai/agent-testing/{item['id']}")
        print(f"  usunięty stary test {item['name']} ({item['id']}): HTTP {code}")


def run_tests(client: Client, agent: str, branch: str,
              payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    created = []
    for p in payloads:
        status, resp = client.call("POST", "/v1/convai/agent-testing/create", p["body"])
        if status != 200 or not isinstance(resp, dict) or "id" not in resp:
            raise SystemExit(f"create test failed for {p['slug']}: HTTP {status} {str(resp)[:300]}")
        print(f"  test {p['slug']} -> {resp['id']}")
        created.append({"slug": p["slug"], "test_id": resp["id"]})

    status, resp = client.call(
        "POST", f"/v1/convai/agents/{agent}/run-tests",
        {"name": f"K2-evidence-{date.today().isoformat()}",
         "tests": [{"test_id": c["test_id"]} for c in created],
         "branch_id": branch, "repeat_count": 1},
    )
    if status != 200:
        raise SystemExit(f"run-tests failed: HTTP {status} {str(resp)[:500]}")
    return resp


def poll(client: Client, invocation: str) -> Dict[str, Any]:
    deadline = time.time() + POLL_TIMEOUT
    last = None
    resp: Dict[str, Any] = {}
    while time.time() < deadline:
        status, resp = client.call("GET", f"/v1/convai/test-invocations/{invocation}")
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


def transcript_text(run: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for item in run.get("agent_responses") or run.get("messages") or []:
        if isinstance(item, dict):
            chunks.append(json.dumps(item, ensure_ascii=False))
        else:
            chunks.append(str(item))
    return "\n".join(chunks)


def save(resp: Dict[str, Any], payloads: List[Dict[str, Any]], seeds: Dict[str, Dict[str, Any]]) -> int:
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    expect = {p["body"]["name"]: p["expect"] for p in payloads}
    rows = []
    failures = 0
    for run in resp.get("test_runs") or []:
        name = run.get("test_name", "unknown")
        slug = next((p["slug"] for p in payloads if p["body"]["name"] == name), name)
        path = TRANSCRIPTS / f"k2-{slug}.json"
        path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")

        text = transcript_text(run)
        checks = expect.get(name, {})
        missing = [m for m in checks.get("text", []) if m not in text]
        forbidden = [f for f in checks.get("forbid", []) if f in text]
        verdict = run.get("status")
        if verdict != "passed" or missing or forbidden:
            failures += 1
        rows.append({
            "name": name, "status": verdict, "file": str(path.relative_to(PROJECT_ROOT)),
            "missing": missing, "forbidden_hits": forbidden,
            "conditions": sum(1 for c in (run.get("success_conditions") or [])
                              if (c.get("result") or c.get("passed")) is True),
        })

    summary = [f"# K2 — dowód symulacji ({date.today().isoformat()})", "",
               f"Inwokacja: `{resp.get('id')}` · seed: `{json.dumps(seeds, ensure_ascii=False)}`", "",
               "| test | status | warunki OK | brak w transkrypcie | zakazane frazy | plik |",
               "|---|---|---|---|---|---|"]
    for r in rows:
        summary.append(f"| {r['name']} | {r['status']} | {r['conditions']} | "
                       f"{', '.join(r['missing']) or '—'} | {', '.join(r['forbidden_hits']) or '—'} | "
                       f"`{r['file']}` |")
    (TRANSCRIPTS / "SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"zapisano {len(rows)} transkryptów + SUMMARY.md w {TRANSCRIPTS}")
    return failures


def main(argv: Optional[List[str]] = None) -> int:
    _utf8_stdout()
    parser = argparse.ArgumentParser(description="K2 evidence: live simulations + transcripts.")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT)
    parser.add_argument("--branch-id", default=DEFAULT_BRANCH)
    parser.add_argument("--backend", default=DEFAULT_BACKEND)
    parser.add_argument("--api-key")
    parser.add_argument("--check", action="store_true", help="tylko odczyt: kredyty, backend, gałąź")
    parser.add_argument("--dry-run", action="store_true", help="zbuduj payloady, nic nie uruchamiaj")
    parser.add_argument("--keep-tests", action="store_true", help="nie usuwaj poprzednich testów K2-*")
    parser.add_argument("--skip-scenario3", action="store_true", help="pomiń scenariusz <2 h")
    args = parser.parse_args(argv)

    key = api_key(args.api_key)
    el = Client(API_BASE, key)
    backend = Client(args.backend)

    ok, credits = whoami(el, hard=not (args.dry_run or args.check))
    print(f"ElevenLabs: {credits}")
    if not ok and args.dry_run:
        print("(dry run: buduję payloady mimo braku kredytów, nic nie uruchamiam)")

    status, health = backend.call("GET", "/health")
    if status != 200:
        print(f"Backend {args.backend} nie odpowiada (HTTP {status}). Uruchom mock_backend.")
        return 2
    print(f"Backend: {json.dumps(health, ensure_ascii=False)}")

    if args.check:
        status, _branch = el.call("GET", f"/v1/convai/agents/{args.agent_id}/branches/{args.branch_id}")
        print(f"Branch {args.branch_id}: HTTP {status}")
        return 0 if ok else 3

    if args.dry_run:
        seeds = {
            "book": {"id": "SPA-0001", "date": (date.today() + timedelta(days=1)).isoformat(),
                     "time": "11:00", "service": "masaż leczniczy pleców", "guest": "Piotr Zieliński"},
            "cancel_free": {"id": "SPA-0002", "date": (date.today() + timedelta(days=2)).isoformat(),
                            "time": "10:00", "service": "masaż leczniczy pleców", "guest": "Jan Kowalski"},
            "cancel_fee": {"id": "SPA-0003", "date": date.today().isoformat(),
                           "time": "16:00", "service": "kąpiel siarczkowa", "guest": "Maria Nowak"},
        }
        payloads = scenario_payloads(seeds)
        if args.skip_scenario3:
            payloads = [p for p in payloads if not p["slug"].startswith("03")]
        print("\n--- dry run: payloady (bez seed, bez POST) ---")
        print(json.dumps([p["body"] for p in payloads], ensure_ascii=False, indent=2))
        print("--- koniec; nic nie utworzono, nic nie uruchomiono ---")
        return 0

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

    if args.dry_run:
        print("\n--- dry run: payloady (bez POST) ---")
        print(json.dumps([p["body"] for p in payloads], ensure_ascii=False, indent=2))
        print("--- koniec; nic nie utworzono, nic nie uruchomiono ---")
        return 0

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


if __name__ == "__main__":
    raise SystemExit(main())
