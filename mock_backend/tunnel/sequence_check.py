"""Sprawdzacz sekwencji wywołań narzędzi i zakazanych twierdzeń w transkrypcie (bez sieci).

Transkrypt to lista wiadomości (``role``, ``message``, opcjonalnie ``tool_calls``), albo słownik
z kluczem ``transcript`` / ``messages`` / ``agent_responses``. Każde wywołanie narzędzia to słownik
z nazwą (``tool_name`` / ``name`` / ``tool``) i argumentami (``params`` / ``params_as_json`` /
``arguments`` / ``args``, jako dict albo tekst JSON).

``check_sequence`` zwraca listę naruszeń; pusta lista = transkrypt spełnia oczekiwania.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

TOOL_NAME_KEYS = ("tool_name", "name", "tool")
ARG_KEYS = ("params", "params_as_json", "arguments", "args")
AGENT_ROLES = ("agent", "assistant")


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


def _messages(transcript: Any) -> List[Dict[str, Any]]:
    if isinstance(transcript, dict):
        for key in ("transcript", "messages", "agent_responses"):
            if isinstance(transcript.get(key), list):
                transcript = transcript[key]
                break
        else:
            return []
    if not isinstance(transcript, list):
        return []
    return [m for m in transcript if isinstance(m, dict)]


def _args(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            return {"_raw": raw}
    return raw if isinstance(raw, dict) else {}


def extract_tool_calls(transcript: Any) -> List[ToolCall]:
    """Wszystkie wywołania narzędzi w kolejności wystąpienia."""
    calls: List[ToolCall] = []
    for message in _messages(transcript):
        for call in message.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            name = next((str(call[k]) for k in TOOL_NAME_KEYS if call.get(k)), "")
            raw_args: Any = next((call[k] for k in ARG_KEYS if k in call), {})
            if name:
                calls.append(ToolCall(name=name, args=_args(raw_args)))
    return calls


def agent_text(transcript: Any) -> str:
    """Tekst wypowiedzi agenta (bez wiadomości gościa), po jednej wiadomości w linii."""
    lines = []
    for message in _messages(transcript):
        if str(message.get("role", "agent")).lower() in AGENT_ROLES or "role" not in message:
            text = message.get("message") or message.get("text") or ""
            if text:
                lines.append(str(text))
    return "\n".join(lines)


def is_subsequence(expected: Sequence[str], actual: Sequence[str]) -> Optional[str]:
    """None gdy ``expected`` występuje w ``actual`` w tej kolejności (z przeplotem); inaczej opis błędu."""
    pos = 0
    for want in expected:
        try:
            pos = list(actual).index(want, pos) + 1
        except ValueError:
            return f"brak wywołania '{want}' w oczekiwanej kolejności {list(expected)} (było: {list(actual)})"
    return None


def check_sequence(
    transcript: Any,
    expected_order: Iterable[str] = (),
    forbidden_tools: Iterable[str] = (),
    forbidden_claims: Iterable[str] = (),
) -> List[str]:
    """Naruszenia: brakujące lub złe wywołania, zakazane narzędzia i zakazane frazy agenta.

    ``forbidden_claims`` to wyrażenia regularne (bez rozróżniania wielkości liter) szukane w wypowiedziach
    agenta. Niepoprawny wzorzec rzuca ``re.error`` (testy go wyłapują).
    """
    violations: List[str] = []
    names = [c.name for c in extract_tool_calls(transcript)]
    expected = list(expected_order)
    if expected:
        problem = is_subsequence(expected, names)
        if problem:
            violations.append(problem)
    banned = set(forbidden_tools)
    for name in names:
        if name in banned:
            violations.append(f"zakazane wywołanie narzędzia '{name}'")
    text = agent_text(transcript)
    for pattern in forbidden_claims:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            violations.append(f"zakazane twierdzenie agenta: /{pattern}/ -> '{match.group(0)}'")
    return violations
