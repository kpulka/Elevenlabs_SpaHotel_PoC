#!/usr/bin/env python3
"""Kontrola spójności kontraktu narzędzi agenta (offline, bez API ElevenLabs).

Źródłem prawdy jest ``mock_backend/tunnel/tool_schemas.py`` (nazwy narzędzi, ścieżki webhooków,
pola body, które wysyła agent). Skrypt sprawdza, czy zgadzają się z nim:

* ``agent/config/anna_v3.json`` — lista narzędzi (nazwa i ścieżka), ``tool_ids``, procedury,
  pierwsza wiadomość (zgodna z ``## First Message`` w prompcie),
* ``agent/system_prompt_v3.md`` — każda wzmianka o narzędziu to znana nazwa, a wywołania w stylu
  ``nazwa(arg, ...)`` mają argumenty z kontraktu (pozycyjne listy — dokładnie komplet),
* ``agent/procedures/procedures_7.md`` — ``[tool name="..."]`` znane, ``[tool id="..."]`` zgodne
  z ``tool_ids`` w configu, a komentarze z ID w nagłówku zgodne z configiem,
* ``agent/_template/tool_schema.example.json`` i ``scenarios.example.json`` — te same nazwy i pola,
* ``mock_backend/tunnel/scenarios.py`` — narzędzia w oczekiwaniach scenariuszy są znane,
* stub ``agent/tools/new_tools.json`` nie istnieje.

Wynik: exit 0 gdy wszystko zgodne; exit 1 z listą rozjazdów. Stdlib only.

Użycie (z katalogu repo)::

    python scripts/check_tool_contract.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
TUNNEL = Path("mock_backend") / "tunnel"
PROMPT = Path("agent") / "system_prompt_v3.md"
PROCEDURES = Path("agent") / "procedures" / "procedures_7.md"
PROCEDURE_IDS = Path("agent") / "procedures" / "procedure_ids.json"
CONFIG = Path("agent") / "config" / "anna_v3.json"
TEMPLATE_TOOLS = Path("agent") / "_template" / "tool_schema.example.json"
TEMPLATE_SCENARIOS = Path("agent") / "_template" / "scenarios.example.json"
STUB = Path("agent") / "tools" / "new_tools.json"

# Nazwa narzędzia = czasownik + rzeczownik z listy: check_in / check_out (argumenty) nie pasują.
TOOL_TOKEN = re.compile(
    r"\b(?:check|book|cancel|reschedule|send|transfer)_[a-z_]*(?:availability|appointment|summary|handoff)\b"
)
CALL = re.compile(r"\b([a-z][a-z_]*)\(([^()\n]*)\)")
# Tylko prawdziwe identyfikatory: znaczniki w komentarzach-przykładach (np. name="...") są pomijane.
TOOL_NAME_TAG = re.compile(r'\[tool name="([a-z_]+)"\]')
TOOL_ID_TAG = re.compile(r'\[tool id="(tool_[0-9a-z]+)"\]')
TOOL_ID_COMMENT = re.compile(r"^#\s*(tool_[0-9a-z]+)\s*=\s*([a-z_]+)\s*$", re.MULTILINE)
SCENARIO_KEYS = {"slug", "procedure", "tags", "seed", "prompt", "max_turns", "success_criteria", "expect"}


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"nie mogę załadować {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prompt_first_message(prompt_text: str) -> Optional[str]:
    """Tekst pod nagłówkiem ``## First Message`` (do końca pliku), bez białych znaków na krańcach."""
    marker = "## First Message"
    if marker not in prompt_text:
        return None
    return prompt_text.split(marker, 1)[1].strip()


def _norm(text: str) -> str:
    return " ".join(text.split())


class Checker:
    def __init__(self, root: Path, contract: ModuleType, scenarios: ModuleType) -> None:
        self.root = root
        self.ts = contract
        self.sc = scenarios
        self.errors: List[str] = []
        self.checks = 0

    # ── pomocnicze ───────────────────────────────────────────────────────
    def fail(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def expect(self, condition: bool, where: str, message: str) -> None:
        self.checks += 1
        if not condition:
            self.fail(where, message)

    def read(self, relative: Path) -> str:
        return (self.root / relative).read_text(encoding="utf-8")

    def read_json(self, relative: Path) -> Any:
        return json.loads(self.read(relative))

    @property
    def tool_names(self) -> Set[str]:
        return set(self.ts.TOOL_PATHS)

    def procedure_names(self) -> Set[str]:
        return {item["name"] for item in self.read_json(PROCEDURE_IDS)}

    # ── kontrakty ────────────────────────────────────────────────────────
    def check_contract_internal(self) -> None:
        where = "tool_schemas.py"
        self.expect(set(self.ts.TOOL_BODY_FIELDS) == self.tool_names, where,
                    "TOOL_BODY_FIELDS i TOOL_PATHS mają różne nazwy narzędzi")
        for tool, path in self.ts.TOOL_PATHS.items():
            self.expect(path == f"/{tool}", where, f"ścieżka {tool} to {path}, oczekiwano /{tool}")

    def check_config(self, config: Any) -> Dict[str, str]:
        where = CONFIG.as_posix()
        names = {tool.get("name") for tool in config.get("tools", [])}
        self.expect(names == self.tool_names, where,
                    f"lista narzędzi różni się od kontraktu: brak {sorted(self.tool_names - names)}, "
                    f"nadmiar {sorted(names - self.tool_names)}")
        for tool in config.get("tools", []):
            name = tool.get("name")
            if name in self.ts.TOOL_PATHS:
                self.expect(tool.get("path") == self.ts.TOOL_PATHS[name], where,
                            f"{name}: ścieżka {tool.get('path')!r}, oczekiwano {self.ts.TOOL_PATHS[name]!r}")

        tool_ids: Dict[str, str] = {k: v for k, v in config.get("tool_ids", {}).items() if not k.startswith("_")}
        self.expect(set(tool_ids) <= self.tool_names, where,
                    f"tool_ids zawiera nieznane narzędzia: {sorted(set(tool_ids) - self.tool_names)}")

        listed = set(config.get("procedures", []))
        self.expect(listed == self.procedure_names(), where,
                    "lista procedur w configu różni się od agent/procedures/procedure_ids.json")

        first = config.get("agent", {}).get("first_message", "")
        prompt_first = prompt_first_message(self.read(PROMPT))
        self.expect(prompt_first is not None and _norm(first) == _norm(prompt_first), where,
                    "agent.first_message różni się od sekcji '## First Message' w prompcie")
        return tool_ids

    def check_prompt(self) -> None:
        where = PROMPT.as_posix()
        text = self.read(PROMPT)
        for token in sorted(set(TOOL_TOKEN.findall(text))):
            self.expect(token in self.tool_names, where, f"wzmianka o nieznanym narzędziu '{token}'")
        for match in CALL.finditer(text):
            name, raw_args = match.group(1), match.group(2)
            if name not in self.tool_names:
                continue
            args = [part.strip() for part in raw_args.split(",") if part.strip()]
            fields = set(self.ts.TOOL_BODY_FIELDS[name])
            keyword = [a.split("=", 1)[0].strip() for a in args if "=" in a]
            if keyword:  # wywołanie z nazwanymi argumentami: każdy musi być polem kontraktu
                unknown = [k for k in keyword if k not in fields]
                self.expect(not unknown, where, f"{name}(...): nieznane argumenty {unknown}")
                continue
            self.expect(set(args) == fields, where,
                        f"{name}({', '.join(args)}): argumenty różne od kontraktu "
                        f"(brak {sorted(fields - set(args))}, nadmiar {sorted(set(args) - fields)})")

    def check_procedures(self, tool_ids: Dict[str, str]) -> None:
        where = PROCEDURES.as_posix()
        text = self.read(PROCEDURES)
        for name in set(TOOL_NAME_TAG.findall(text)):
            self.expect(name in self.tool_names, where, f"[tool name=\"{name}\"] — nieznane narzędzie")
        known_ids = set(tool_ids.values())
        for tool_id in set(TOOL_ID_TAG.findall(text)):
            self.expect(tool_id in known_ids, where, f"[tool id=\"{tool_id}\"] nie ma w tool_ids configu")
        for tool_id, name in TOOL_ID_COMMENT.findall(text):
            self.expect(tool_ids.get(name) == tool_id, where,
                        f"komentarz: {tool_id} = {name}, ale config ma {tool_ids.get(name)!r}")
        for token in sorted(set(TOOL_TOKEN.findall(text))):
            self.expect(token in self.tool_names, where, f"wzmianka o nieznanym narzędziu '{token}'")

    def check_template_tools(self) -> None:
        where = TEMPLATE_TOOLS.as_posix()
        data = self.read_json(TEMPLATE_TOOLS)
        seen: Set[str] = set()
        for tool in data.get("tools", []):
            name = tool.get("name", "")
            self.expect(name in self.tool_names, where, f"nieznane narzędzie w szablonie: '{name}'")
            if name not in self.tool_names:
                continue
            seen.add(name)
            self.expect(tool.get("path") == self.ts.TOOL_PATHS[name], where, f"{name}: zła ścieżka")
            params = tool.get("parameters", {})
            props = set(params.get("properties", {}))
            required = set(params.get("required", []))
            self.expect(props == set(self.ts.TOOL_BODY_FIELDS[name]), where,
                        f"{name}: pola szablonu {sorted(props)} != kontrakt {sorted(self.ts.TOOL_BODY_FIELDS[name])}")
            self.expect(required <= props, where, f"{name}: required poza properties")
        missing = sorted(self.tool_names - seen)
        self.expect(seen == self.tool_names, where, f"szablon nie pokrywa narzędzi: brak {missing}")

    def check_scenario_expectations(self, scenarios: List[Dict[str, Any]], where: str, seeds: Set[str]) -> None:
        for scenario in scenarios:
            slug = scenario.get("slug", "?")
            missing = SCENARIO_KEYS - set(scenario)
            self.expect(not missing, where, f"{slug}: brak kluczy {sorted(missing)}")
            expect = scenario.get("expect", {})
            for key in ("tools", "forbid_tools"):
                for name in expect.get(key, []):
                    self.expect(name in self.tool_names, where, f"{slug}: {key} zawiera nieznane narzędzie '{name}'")
            seed = scenario.get("seed")
            self.expect(seed is None or seed in seeds, where, f"{slug}: nieznany seed {seed!r}")

    def check_template_scenarios(self) -> None:
        self.check_scenario_expectations(self.read_json(TEMPLATE_SCENARIOS), TEMPLATE_SCENARIOS.as_posix(),
                                         set(self.sc.SEED_SPECS))

    def check_poc_scenarios(self) -> None:
        self.check_scenario_expectations(list(self.sc.SCENARIOS), f"{TUNNEL.as_posix()}/scenarios.py",
                                         set(self.sc.SEED_SPECS))

    def check_stub_removed(self) -> None:
        self.expect(not (self.root / STUB).exists(), STUB.as_posix(),
                    "plik-stub z wartością null nadal istnieje (usuń albo wypełnij)")

    def run(self) -> List[str]:
        self.check_contract_internal()
        config = self.read_json(CONFIG)
        tool_ids = self.check_config(config)
        self.check_prompt()
        self.check_procedures(tool_ids)
        self.check_template_tools()
        self.check_template_scenarios()
        self.check_poc_scenarios()
        self.check_stub_removed()
        return self.errors


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sprawdza spójność kontraktu narzędzi agenta (offline).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="katalog repo (domyślnie: nadrzędny do scripts/)")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    try:
        contract = _load_module("anna_tool_schemas", root / TUNNEL / "tool_schemas.py")
        scenarios = _load_module("anna_scenarios", root / TUNNEL / "scenarios.py")
        checker = Checker(root, contract, scenarios)
        errors = checker.run()
    except (OSError, ImportError, json.JSONDecodeError, KeyError, AttributeError) as err:
        print(f"BŁĄD: nie mogę wczytać danych kontraktu: {err}")
        return 1

    for error in errors:
        print(f"ROZJAZD  {error}")
    if errors:
        print(f"\nFAIL: {len(errors)} rozjazd(ów) kontraktu narzędzi (sprawdzeń: {checker.checks}).")
        return 1
    print(f"OK: kontrakt narzędzi zgodny ({checker.checks} sprawdzeń, {len(contract.TOOL_PATHS)} narzędzi).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
