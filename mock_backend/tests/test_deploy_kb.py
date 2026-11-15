"""Testy wdrożenia KB do ElevenLabs (deploy_kb_and_tools.py) — offline, z atrapą sesji HTTP.

Żadne żądanie nie wychodzi do sieci: ``FakeSession`` zapisuje kolejność wywołań, a testy sprawdzają:
brak agenta w env = błąd (bez domyślnego ID), dry-run bez połączeń, kolejność POST -> PATCH -> DELETE,
zero kasowania przy błędzie PATCH, zapis manifestu po każdym kroku i sprzątanie duplikatów.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "deploy_kb_and_tools.py"
_SPEC = importlib.util.spec_from_file_location("deploy_kb_and_tools", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
deploy = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = deploy
_SPEC.loader.exec_module(deploy)

AGENT = "agent_test12345"


class FakeResponse:
    def __init__(self, payload: Any = None) -> None:
        self._payload = payload if payload is not None else {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._payload


class FakeSession:
    """Atrapa ``requests.Session``: pamięta wywołania i potrafi rzucić błąd w wybranym miejscu."""

    def __init__(self, remote: Optional[List[Dict[str, str]]] = None, *, fail_post_at: Optional[int] = None,
                 fail_patch: bool = False, fail_delete_ids: tuple = ()) -> None:
        self.remote: List[Dict[str, str]] = [dict(doc) for doc in (remote or [])]
        self.calls: List[tuple] = []
        self.fail_post_at = fail_post_at
        self.fail_patch = fail_patch
        self.fail_delete_ids = set(fail_delete_ids)
        self._posts = 0

    def get(self, url: str, params: Any = None, timeout: Any = None) -> FakeResponse:
        self.calls.append(("GET", url))
        return FakeResponse({"documents": list(self.remote), "has_more": False, "next_cursor": None})

    def post(self, url: str, files: Any = None, data: Any = None, timeout: Any = None) -> FakeResponse:
        self._posts += 1
        if self.fail_post_at == self._posts:
            raise RuntimeError("POST padł (symulacja)")
        name = data["name"]
        new_id = f"new{self._posts}"
        self.remote.append({"id": new_id, "name": name})
        self.calls.append(("POST", name))
        return FakeResponse({"id": new_id})

    def patch(self, url: str, json: Any = None, timeout: Any = None) -> FakeResponse:
        self.calls.append(("PATCH", url))
        if self.fail_patch:
            raise RuntimeError("PATCH padł (symulacja)")
        return FakeResponse({})

    def delete(self, url: str, timeout: Any = None) -> FakeResponse:
        doc_id = url.rsplit("/", 1)[-1]
        self.calls.append(("DELETE", doc_id))
        if doc_id in self.fail_delete_ids:
            raise RuntimeError("DELETE padł (symulacja)")
        self.remote = [doc for doc in self.remote if doc["id"] != doc_id]
        return FakeResponse({})

    def ops(self) -> List[str]:
        return [call[0] for call in self.calls]


@pytest.fixture()
def docs():
    found = deploy.local_documents()
    assert len(found) == 5
    return found


def _no_network(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("dry-run nie może otwierać sesji HTTP")


# ── konfiguracja i brak domyślnego agenta (7.5) ──────────────────────────
def test_script_contains_no_hardcoded_agent_id():
    assert "agent_8401" not in SCRIPT.read_text(encoding="utf-8")
    assert not hasattr(deploy, "DEFAULT_AGENT_ID")


def test_agent_id_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", AGENT)
    assert deploy.resolve_agent_id(required=True) == AGENT


def test_missing_agent_id_fails_closed_when_required(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    with pytest.raises(SystemExit) as err:
        deploy.resolve_agent_id(required=True)
    assert "ELEVENLABS_AGENT_ID" in str(err.value)


def test_missing_agent_id_is_allowed_only_for_dry_run(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    assert deploy.resolve_agent_id(required=False) is None


@pytest.mark.parametrize("bad", ["agent_bad&evil=1", "../agent_x", "nie-agent"])
def test_malformed_agent_id_is_rejected(monkeypatch, bad):
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", bad)
    with pytest.raises(SystemExit):
        deploy.resolve_agent_id(required=True)


def test_main_refuses_to_deploy_without_agent_id(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "klucz-testowy")
    monkeypatch.setattr(deploy, "make_session", _no_network)
    with pytest.raises(SystemExit) as err:
        deploy.main([])
    assert "ELEVENLABS_AGENT_ID" in str(err.value)


def test_main_checks_agent_before_api_key(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(SystemExit) as err:
        deploy.main([])
    assert "ELEVENLABS_AGENT_ID" in str(err.value)


def test_main_requires_api_key_when_agent_is_set(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", AGENT)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(SystemExit) as err:
        deploy.main([])
    assert "ELEVENLABS_API_KEY" in str(err.value)


# ── dry-run bez sieci ────────────────────────────────────────────────────
def test_dry_run_makes_no_network_calls(monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_AGENT_ID", raising=False)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(deploy, "make_session", _no_network)
    assert deploy.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "Dry-run: brak połączeń sieciowych" in out
    assert "NIE ustawione" in out


def test_dry_run_reports_agent_id_presence_without_printing_it(monkeypatch, capsys):
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", AGENT)
    monkeypatch.setattr(deploy, "make_session", _no_network)
    assert deploy.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "ustawione" in out and AGENT not in out


# ── kolejność i bezpieczeństwo wdrożenia (7.2) ───────────────────────────
def test_fresh_deploy_creates_all_then_patches_without_deleting(docs, tmp_path):
    session = FakeSession()
    manifest_path = tmp_path / "manifest.json"
    result = deploy.deploy(AGENT, docs, {}, session, manifest_path)
    ops = session.ops()
    assert ops.count("POST") == 5 and ops.count("PATCH") == 1 and "DELETE" not in ops
    assert ops.index("PATCH") > max(i for i, op in enumerate(ops) if op == "POST")
    assert len(result.doc_ids) == 5 and result.leftover_ids == []
    patch_sends_new_ids = session.calls[-1]
    assert patch_sends_new_ids[0] == "PATCH"


def test_replaced_document_is_deleted_only_after_patch(docs, tmp_path):
    old = docs[0]
    session = FakeSession(remote=[{"id": "old1", "name": old.name}])
    manifest = {old.name: {"id": "old1", "sha256": "0" * 64, "stale_ids": []}}
    deploy.deploy(AGENT, docs, manifest, session, tmp_path / "m.json")
    ops = session.calls
    patch_at = ops.index(next(c for c in ops if c[0] == "PATCH"))
    delete_at = ops.index(("DELETE", "old1"))
    post_at = ops.index(("POST", old.name))
    assert post_at < patch_at < delete_at


def test_patch_failure_deletes_nothing_and_keeps_stale_ids(docs, tmp_path):
    old = docs[0]
    session = FakeSession(remote=[{"id": "old1", "name": old.name}], fail_patch=True)
    manifest_path = tmp_path / "m.json"
    manifest = {old.name: {"id": "old1", "sha256": "0" * 64, "stale_ids": []}}
    with pytest.raises(deploy.DeployError):
        deploy.deploy(AGENT, docs, manifest, session, manifest_path)
    assert "DELETE" not in session.ops()
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved[old.name]["stale_ids"] == ["old1"]


def test_manifest_is_saved_after_each_created_document(docs, tmp_path):
    session = FakeSession(fail_post_at=3)
    manifest_path = tmp_path / "m.json"
    with pytest.raises(RuntimeError):
        deploy.deploy(AGENT, docs, {}, session, manifest_path)
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(saved) == {docs[0].name, docs[1].name}
    assert saved[docs[0].name]["id"] == "new1"
    assert not list(tmp_path.glob("*.tmp"))


def test_unchanged_document_is_kept_without_upload(docs, tmp_path):
    current = docs[2]
    session = FakeSession(remote=[{"id": "keep1", "name": current.name}])
    manifest = {current.name: {"id": "keep1", "sha256": current.sha256, "stale_ids": []}}
    result = deploy.deploy(AGENT, docs, manifest, session, tmp_path / "m.json")
    assert ("POST", current.name) not in session.calls
    assert "keep1" in result.doc_ids
    assert "DELETE" not in session.ops()


def test_duplicate_remote_names_are_cleaned_after_patch(docs, tmp_path):
    kept = docs[1]
    session = FakeSession(remote=[{"id": "d1", "name": kept.name}, {"id": "d2", "name": kept.name}])
    manifest = {kept.name: {"id": "d2", "sha256": kept.sha256, "stale_ids": []}}
    deploy.deploy(AGENT, docs, manifest, session, tmp_path / "m.json")
    assert ("DELETE", "d1") in session.calls
    assert ("DELETE", "d2") not in session.calls
    assert session.ops().index("PATCH") < session.ops().index("DELETE")


def test_failed_delete_is_reported_and_stays_in_manifest(docs, tmp_path):
    old = docs[0]
    session = FakeSession(remote=[{"id": "old1", "name": old.name}], fail_delete_ids=("old1",))
    manifest_path = tmp_path / "m.json"
    result = deploy.deploy(AGENT, docs, {old.name: {"id": "old1", "sha256": "0" * 64}}, session, manifest_path)
    assert result.leftover_ids == ["old1"]
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved[old.name]["stale_ids"] == ["old1"]


def test_retry_after_failed_delete_cleans_up_pending_ids(docs, tmp_path):
    old = docs[0]
    manifest_path = tmp_path / "m.json"
    first = FakeSession(remote=[{"id": "old1", "name": old.name}], fail_delete_ids=("old1",))
    deploy.deploy(AGENT, docs, {old.name: {"id": "old1", "sha256": "0" * 64}}, first, manifest_path)
    second = FakeSession(remote=first.remote)
    manifest = deploy.load_manifest(manifest_path)
    result = deploy.deploy(AGENT, docs, manifest, second, manifest_path)
    assert result.leftover_ids == []
    assert ("DELETE", "old1") in second.calls


# ── pomocnicze ───────────────────────────────────────────────────────────
def test_build_kb_entries_rejects_mismatched_lengths(docs):
    with pytest.raises(ValueError):
        deploy.build_kb_entries(docs, ["only-one"])


def test_usage_modes_match_the_documented_policy(docs):
    entries = deploy.build_kb_entries(docs, [f"id{i}" for i in range(len(docs))])
    by_name = {entry["name"]: entry["usage_mode"] for entry in entries}
    assert by_name["Bukowy_Dwor_03_pokoje"] == "prompt"
    assert by_name["Bukowy_Dwor_05_procedury"] == "prompt"
    assert by_name["Bukowy_Dwor_02_zabiegi"] == "auto"


def test_unreadable_manifest_is_treated_as_empty(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{nie json", encoding="utf-8")
    assert deploy.load_manifest(path) == {}
    assert "nieczytelny" in capsys.readouterr().out


def test_save_manifest_round_trips_without_leaving_tmp_file(tmp_path):
    path = tmp_path / "m.json"
    deploy.save_manifest({"x": {"id": "1", "sha256": "ab"}}, path)
    assert json.loads(path.read_text(encoding="utf-8")) == {"x": {"id": "1", "sha256": "ab"}}
    assert not list(tmp_path.glob("*.tmp"))
