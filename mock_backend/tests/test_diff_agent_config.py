"""Testy scripts/diff_agent_config.py - wyłącznie offline.

Nic tu nie otwiera sieci: tryb live jest sprawdzany tylko pod kątem fail-closed (brak zmiennych),
a urlopen jest podmieniany na atrapę, która przerywa test, gdyby została wywołana.
Odpowiedź GET agenta jest składana z konfiguracji repo, więc test „zgodne" sprawdza spójność repo,
a modyfikacje tej odpowiedzi symulują dryf.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "diff_agent_config.py"
_SPEC = importlib.util.spec_from_file_location("diff_agent_config", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
diff = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = diff
_SPEC.loader.exec_module(diff)

REPO_CONFIG = json.loads((REPO_ROOT / "agent" / "config" / "anna_v3.json").read_text(encoding="utf-8"))
REPO_PROMPT = diff.extract_prompt((REPO_ROOT / "agent" / "system_prompt_v3.md").read_text(encoding="utf-8"))


def live_from_repo() -> Dict[str, Any]:
    """Odpowiedź GET udająca agenta zgodnego z repo (kształt ścieżek z LIVE_PATHS)."""
    expected = diff.expected_from_repo(REPO_CONFIG, REPO_PROMPT)
    kb = [{"name": name, "usage_mode": mode, "type": "file", "id": f"doc{i}"}
          for i, (name, mode) in enumerate(expected["knowledge_base"])]
    return {
        "name": "fixture",
        "conversation_config": {
            "agent": {
                "first_message": expected["first_message"],
                "language": expected["language"],
                "prompt": {
                    "prompt": REPO_PROMPT,
                    "llm": expected["llm.model"],
                    "knowledge_base": kb,
                    "rag": {"enabled": expected["rag.enabled"]},
                    "timezone": expected["timezone"],
                },
            },
            "tts": {
                "model_id": expected["tts.model_id"],
                "voice_id": expected["tts.voice_id"],
                "speed": expected["tts.speed"],
            },
            "turn": {
                "turn_eagerness": expected["turn.turn_eagerness"],
                "turn_timeout": expected["turn.turn_timeout"],
            },
        },
    }


def write_json(path: Path, data: Dict[str, Any]) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def run(live: Dict[str, Any], tmp_path: Path, capsys) -> tuple:
    live_path = write_json(tmp_path / "live.json", live)
    code = diff.main(["--from-file", str(live_path)])
    return code, capsys.readouterr().out


# ── zgodność z repo ──────────────────────────────────────────────────────
def test_repo_mirror_is_reported_as_in_sync(tmp_path, capsys):
    code, out = run(live_from_repo(), tmp_path, capsys)
    assert code == 0, out
    assert "DRYF" not in out and "MISSING" not in out
    assert "OK: konfiguracja agenta zgodna z repo" in out


def test_repo_prompt_block_is_extracted_and_contains_emergency_rule():
    assert REPO_PROMPT.startswith("Jesteś")
    assert "112" in REPO_PROMPT
    assert "\r" not in REPO_PROMPT


def test_prompt_normalisation_ignores_line_endings_and_trailing_spaces():
    assert diff.normalise_prompt("a  \r\nb\r\n") == diff.normalise_prompt("a\nb")


# ── dryf ─────────────────────────────────────────────────────────────────
def test_changed_first_message_is_drift(tmp_path, capsys):
    live = live_from_repo()
    live["conversation_config"]["agent"]["first_message"] = "Dzień dobry, inny tekst."
    code, out = run(live, tmp_path, capsys)
    assert code == 1
    assert "DRYF     first_message" in out


def test_changed_prompt_line_is_drift_with_diff(tmp_path, capsys):
    live = live_from_repo()
    live["conversation_config"]["agent"]["prompt"]["prompt"] = REPO_PROMPT.replace(
        "112", "999", 1)
    code, out = run(live, tmp_path, capsys)
    assert code == 1
    assert "DRYF     prompt" in out
    assert "999" in out and "112" in out


def test_changed_kb_usage_mode_is_drift(tmp_path, capsys):
    live = live_from_repo()
    live["conversation_config"]["agent"]["prompt"]["knowledge_base"][0]["usage_mode"] = "prompt"
    code, out = run(live, tmp_path, capsys)
    assert code == 1
    assert "DRYF     knowledge_base" in out


def test_missing_kb_document_is_drift(tmp_path, capsys):
    live = live_from_repo()
    live["conversation_config"]["agent"]["prompt"]["knowledge_base"].pop()
    code, out = run(live, tmp_path, capsys)
    assert code == 1
    assert "DRYF     knowledge_base" in out


def test_changed_tts_speed_and_turn_are_drift(tmp_path, capsys):
    live = live_from_repo()
    live["conversation_config"]["tts"]["speed"] = 1.0
    live["conversation_config"]["turn"]["turn_eagerness"] = "eager"
    code, out = run(live, tmp_path, capsys)
    assert code == 1
    assert "DRYF     tts.speed" in out and "DRYF     turn.turn_eagerness" in out


def test_missing_field_is_reported_as_missing_not_ok(tmp_path, capsys):
    live = live_from_repo()
    del live["conversation_config"]["turn"]["turn_timeout"]
    code, out = run(live, tmp_path, capsys)
    assert code == 1
    assert "MISSING  turn.turn_timeout" in out


def test_compare_flags_every_difference_once():
    expected = diff.expected_from_repo(REPO_CONFIG, REPO_PROMPT)
    findings = diff.compare(expected, live_from_repo())
    assert all(item.status == "ok" for item in findings)
    assert {item.label for item in findings} == set(diff.LIVE_PATHS)


def test_changed_rag_flag_is_drift(tmp_path, capsys):
    live = live_from_repo()
    live["conversation_config"]["agent"]["prompt"]["rag"]["enabled"] = False
    code, out = run(live, tmp_path, capsys)
    assert code == 1
    assert "DRYF     rag.enabled" in out


# ── wejście nieczytelne: kod 2 ───────────────────────────────────────────
def test_missing_from_file_is_input_error(tmp_path, capsys):
    code = diff.main(["--from-file", str(tmp_path / "nie-ma.json")])
    assert code == 2
    assert "Brak pliku" in capsys.readouterr().out


def test_invalid_json_from_file_is_input_error(tmp_path, capsys):
    broken = tmp_path / "broken.json"
    broken.write_text("{nie json", encoding="utf-8")
    assert diff.main(["--from-file", str(broken)]) == 2


def test_non_object_json_is_input_error(tmp_path, capsys):
    arr = tmp_path / "arr.json"
    arr.write_text("[1, 2]", encoding="utf-8")
    assert diff.main(["--from-file", str(arr)]) == 2


def test_prompt_block_missing_is_input_error(tmp_path, capsys):
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("## Inna sekcja\n\n```\ntekst\n```\n", encoding="utf-8")
    config = copy.deepcopy(REPO_CONFIG)
    config["llm"]["system_prompt_file"] = str(prompt_file)
    config_path = write_json(tmp_path / "config.json", config)
    code = diff.main(["--config", str(config_path), "--from-file", str(tmp_path / "live.json")])
    assert code == 2
    assert "nagłówka" in capsys.readouterr().out


def test_unclosed_prompt_block_is_input_error():
    with pytest.raises(diff.InputError):
        diff.extract_prompt("## PEŁNY TEKST SYSTEM PROMPTU\n\n```\ntekst bez zamknięcia\n")


def test_incomplete_repo_config_is_input_error(tmp_path, capsys):
    config = copy.deepcopy(REPO_CONFIG)
    del config["tts"]["voice_id"]
    config_path = write_json(tmp_path / "config.json", config)
    code = diff.main(["--config", str(config_path), "--from-file", str(tmp_path / "live.json")])
    assert code == 2


# ── tryb live: tylko fail-closed, bez sieci ──────────────────────────────
def _no_network(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("test nie może otwierać połączeń sieciowych")


def test_live_mode_requires_agent_id_and_never_calls_network(monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "klucz-testowy")
    monkeypatch.setattr(diff.urllib.request, "urlopen", _no_network)
    assert diff.main([]) == 2
    assert "ELEVENLABS_AGENT_ID" in capsys.readouterr().out


def test_live_mode_requires_api_key(monkeypatch, capsys):
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_test12345")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(diff.urllib.request, "urlopen", _no_network)
    assert diff.main([]) == 2
    assert "ELEVENLABS_API_KEY" in capsys.readouterr().out


@pytest.mark.parametrize("bad", ["agent_bad&x=1", "../agent_x", "nie-agent"])
def test_live_mode_rejects_malformed_agent_id(monkeypatch, capsys, bad):
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", bad)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "klucz-testowy")
    monkeypatch.setattr(diff.urllib.request, "urlopen", _no_network)
    assert diff.main([]) == 2


def test_script_has_no_hardcoded_agent_id_or_api_key():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "agent_8401" not in text
    assert "xi-api-key" in text  # nagłówek bierze klucz z env, nie z pliku


def test_live_fetch_uses_get_only(monkeypatch):
    seen: Dict[str, Any] = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def read(self):
            return json.dumps(live_from_repo()).encode("utf-8")

    def fake_urlopen(request, timeout=None):
        seen["method"] = request.get_method()
        seen["url"] = request.full_url
        return _Resp()

    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "agent_test12345")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "klucz-testowy")
    monkeypatch.setattr(diff.urllib.request, "urlopen", fake_urlopen)
    body = diff.fetch_live()
    assert seen["method"] == "GET"
    assert seen["url"].endswith("/convai/agents/agent_test12345")
    assert "conversation_config" in body
