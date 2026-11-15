#!/usr/bin/env python3
"""Porównanie konfiguracji agenta „Anna" na żywo z repo (config-as-code + prompt).

Źródło prawdy w repo:
  - ``agent/config/anna_v3.json`` (first_message, język, LLM, TTS, turn, RAG, lista KB),
  - prompt: pierwszy blok ``` po nagłówku „## PEŁNY TEKST SYSTEM PROMPTU" w pliku z
    ``llm.system_prompt_file`` (domyślnie ``agent/system_prompt_v3.md``).

Tryby:
  python scripts/diff_agent_config.py --from-file zapis.json   # offline: zapisana odpowiedź GET
  python scripts/diff_agent_config.py                          # live: GET /v1/convai/agents/{id}

Tryb live wymaga ELEVENLABS_API_KEY i ELEVENLABS_AGENT_ID (brak = błąd, bez domyślnego agenta)
i wykonuje WYŁĄCZNIE żądanie GET (odczyt). Używa samego urllib, więc nie wymaga ``requests``.

Ścieżki pól w odpowiedzi GET (``LIVE_PATHS``) odpowiadają miejscom, do których zapisuje
``scripts/deploy_kb_and_tools.py`` (agent.prompt.knowledge_base / rag / timezone, turn, tts.speed).
Pozostałe ścieżki (tts.model_id, turn.turn_timeout, agent.language) są ustalone na podstawie
konwencji API ElevenLabs i NIE zostały zweryfikowane na żywym agencie w tym repo. Brak pola
w odpowiedzi jest raportowany jako dryf (MISSING), a nie jako zgodność.

Wynik:
  exit 0 - wszystkie sprawdzone pola zgodne z repo,
  exit 1 - dryf (różna wartość albo brak pola w odpowiedzi),
  exit 2 - wejście nieczytelne (brak pliku, zły JSON, brak bloku promptu, brak zmiennych, błąd HTTP).
Skrypt nie wypisuje klucza API ani ID agenta.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "agent" / "config" / "anna_v3.json"
BASE = "https://api.elevenlabs.io/v1"
AGENT_ID_PATTERN = re.compile(r"^agent_[A-Za-z0-9]+$")
PROMPT_HEADING = "## PEŁNY TEKST SYSTEM PROMPTU"
MAX_DIFF_LINES = 20

MISSING = object()

# Etykieta pola -> ścieżka w odpowiedzi GET /v1/convai/agents/{id}.
LIVE_PATHS: Dict[str, Tuple[str, ...]] = {
    "first_message": ("conversation_config", "agent", "first_message"),
    "language": ("conversation_config", "agent", "language"),
    "timezone": ("conversation_config", "agent", "prompt", "timezone"),
    "llm.model": ("conversation_config", "agent", "prompt", "llm"),
    "tts.model_id": ("conversation_config", "tts", "model_id"),
    "tts.voice_id": ("conversation_config", "tts", "voice_id"),
    "tts.speed": ("conversation_config", "tts", "speed"),
    "turn.turn_eagerness": ("conversation_config", "turn", "turn_eagerness"),
    "turn.turn_timeout": ("conversation_config", "turn", "turn_timeout"),
    "rag.enabled": ("conversation_config", "agent", "prompt", "rag", "enabled"),
    "knowledge_base": ("conversation_config", "agent", "prompt", "knowledge_base"),
    "prompt": ("conversation_config", "agent", "prompt", "prompt"),
}


class InputError(RuntimeError):
    """Wejście nieczytelne: skrypt kończy się kodem 2."""


@dataclass
class Finding:
    label: str
    status: str  # "ok" | "drift" | "missing"
    expected: Any = None
    live: Any = None
    detail: str = ""


def normalise_prompt(text: str) -> str:
    """CRLF -> LF, bez końcowych spacji w liniach i na brzegach."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).strip()


def extract_prompt(markdown: str) -> str:
    """Zwraca treść pierwszego bloku ``` po nagłówku PROMPT_HEADING."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == PROMPT_HEADING)
    except StopIteration:
        raise InputError(f"Brak nagłówka „{PROMPT_HEADING}”") from None
    try:
        open_at = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("```"))
    except StopIteration:
        raise InputError("Brak bloku ``` pod nagłówkiem promptu") from None
    try:
        close_at = next(i for i in range(open_at + 1, len(lines)) if lines[i].strip() == "```")
    except StopIteration:
        raise InputError("Blok promptu nie jest zamknięty") from None
    return normalise_prompt("\n".join(lines[open_at + 1:close_at]))


def load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InputError(f"Brak pliku: {path}") from None
    except (OSError, json.JSONDecodeError) as err:
        raise InputError(f"Nie udało się wczytać {path.name}: {type(err).__name__}") from None
    if not isinstance(data, dict):
        raise InputError(f"{path.name}: oczekiwany obiekt JSON")
    return data


def expected_from_repo(config: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """Wartości, jakie agent powinien mieć według repo."""
    try:
        kb = config["knowledge_base"]
        return {
            "first_message": config["agent"]["first_message"].strip(),
            "language": config["agent"]["default_language"],
            "timezone": config["agent"]["timezone"],
            "llm.model": config["llm"]["model"],
            "tts.model_id": config["tts"]["model"],
            "tts.voice_id": config["tts"]["voice_id"],
            "tts.speed": config["tts"]["speed"],
            "turn.turn_eagerness": config["turn"]["turn_eagerness"],
            "turn.turn_timeout": config["turn"]["turn_timeout_seconds"],
            "rag.enabled": kb["rag_enabled"],
            "knowledge_base": [(d["name"], d["usage_mode"]) for d in kb["documents"]],
            "prompt": normalise_prompt(prompt),
        }
    except (KeyError, TypeError) as err:
        raise InputError(f"Konfiguracja repo jest niekompletna: brak {err}") from None


def get_path(data: Any, path: Sequence[str]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return MISSING
        current = current[key]
    return current


def normalise_live(label: str, value: Any) -> Any:
    if value is MISSING:
        return MISSING
    if label == "prompt":
        return normalise_prompt(value) if isinstance(value, str) else value
    if label == "first_message":
        return value.strip() if isinstance(value, str) else value
    if label == "knowledge_base":
        if not isinstance(value, list):
            return value
        return [(item.get("name"), item.get("usage_mode")) if isinstance(item, dict) else item
                for item in value]
    return value


def compare(expected: Dict[str, Any], live_response: Dict[str, Any]) -> List[Finding]:
    findings: List[Finding] = []
    for label, path in LIVE_PATHS.items():
        want = expected[label]
        got = normalise_live(label, get_path(live_response, path))
        if got is MISSING:
            findings.append(Finding(label, "missing", want, None, "brak pola w odpowiedzi"))
        elif got == want:
            findings.append(Finding(label, "ok", want, got))
        else:
            findings.append(Finding(label, "drift", want, got, _describe(label, want, got)))
    return findings


def _describe(label: str, want: Any, got: Any) -> str:
    if label == "prompt":
        want_lines, got_lines = want.split("\n"), got.split("\n")
        changed = sum(1 for line in difflib.unified_diff(want_lines, got_lines, lineterm="", n=0)
                      if line[:1] in "+-" and line[:3] not in ("+++", "---"))
        return f"treść różni się w {changed} liniach (diff poniżej)"
    if label == "knowledge_base":
        return f"repo: {want}; live: {got}"
    return f"repo={want!r}; live={got!r}"


def prompt_diff_lines(expected: str, live: str) -> List[str]:
    diff = difflib.unified_diff(expected.split("\n"), live.split("\n"),
                                fromfile="repo", tofile="live", lineterm="", n=0)
    return list(diff)[:MAX_DIFF_LINES]


def fetch_live() -> Dict[str, Any]:
    agent_id = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not agent_id:
        raise InputError("Ustaw ELEVENLABS_AGENT_ID (brak domyślnego agenta).")
    if not AGENT_ID_PATTERN.match(agent_id):
        raise InputError("ELEVENLABS_AGENT_ID ma nieprawidłowy format.")
    if not api_key:
        raise InputError("Ustaw ELEVENLABS_API_KEY.")
    request = urllib.request.Request(f"{BASE}/convai/agents/{agent_id}",
                                     headers={"xi-api-key": api_key}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raise InputError(f"GET agenta zwrócił HTTP {err.code}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        raise InputError(f"Nie udało się pobrać agenta: {type(err).__name__}") from None
    if not isinstance(body, dict):
        raise InputError("Odpowiedź GET agenta nie jest obiektem JSON")
    return body


def report(findings: List[Finding], expected: Dict[str, Any], live_response: Dict[str, Any]) -> int:
    for item in findings:
        if item.status == "ok":
            print(f"  OK       {item.label}")
        elif item.status == "missing":
            print(f"  MISSING  {item.label}: {item.detail}")
        else:
            print(f"  DRYF     {item.label}: {item.detail}")
    drift = [item for item in findings if item.status != "ok"]
    if any(item.label == "prompt" and item.status == "drift" for item in findings):
        live_prompt = normalise_live("prompt", get_path(live_response, LIVE_PATHS["prompt"]))
        print("\nRóżnice w prompcie (pierwsze linie):")
        for line in prompt_diff_lines(expected["prompt"], live_prompt):
            print(f"    {line}")
    if drift:
        print(f"\nDRYF: {len(drift)} pól różni się od repo. Wdrożenie z repo nadpisze live, "
              "albo repo trzeba zaktualizować do stanu agenta.")
        return 1
    print(f"\nOK: konfiguracja agenta zgodna z repo ({len(findings)} pól).")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Porównuje agenta Anna na żywo z repo (tylko odczyt).")
    parser.add_argument("--from-file", type=Path, default=None,
                        help="zapisana odpowiedź GET agenta (JSON); tryb offline, bez sieci")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH,
                        help="plik konfiguracji repo (domyślnie agent/config/anna_v3.json)")
    args = parser.parse_args(argv)

    try:
        config = load_json(args.config)
        try:
            prompt_path = ROOT / config["llm"]["system_prompt_file"]
        except (KeyError, TypeError):
            raise InputError("W konfiguracji brak llm.system_prompt_file") from None
        try:
            prompt_markdown = prompt_path.read_text(encoding="utf-8")
        except OSError:
            raise InputError(f"Nie można odczytać promptu: {prompt_path}") from None
        expected = expected_from_repo(config, extract_prompt(prompt_markdown))
        live_response = load_json(args.from_file) if args.from_file else fetch_live()
    except InputError as err:
        print(f"BŁĄD: {err}")
        return 2

    findings = compare(expected, live_response)
    return report(findings, expected, live_response)


if __name__ == "__main__":
    sys.exit(main())
