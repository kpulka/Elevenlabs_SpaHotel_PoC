"""sync_agent_tools sets the webhook auth header so tool calls pass the backend's shared-secret check.

Offline: a fake ApiClient records the PATCHes; nothing touches the network and the secret is never printed.
"""

from __future__ import annotations

import pytest

from tunnel import sync_agent_tools as sync, tool_schemas as ts

SECRET = "s3cr3t-value-for-test"
BASE = "https://demo.example"


class FakeClient:
    def __init__(self, headers: dict | None = None, url_fn=lambda name: f"{BASE}{ts.TOOL_PATHS[name]}"):
        self.patches: list[tuple[str, dict]] = []
        self._tools = []
        for i, name in enumerate(ts.TOOL_PATHS):
            api_schema: dict = {"url": url_fn(name)}
            if headers is not None:
                api_schema["request_headers"] = dict(headers)
            self._tools.append({"id": f"tool_{i}", "tool_config": {"name": name, "api_schema": api_schema}})

    def request_ok(self, method, path, body=None):
        assert method == "GET"
        return {"tools": self._tools, "has_more": False}

    def request(self, method, path, body=None):
        assert method == "PATCH"
        self.patches.append((path, body))
        return 200, "{}"

    def redact(self, text):
        return text


def test_auth_header_helpers():
    assert sync.auth_header_ok({}, "") is True  # nothing configured -> nothing to manage
    assert sync.auth_header_ok({}, SECRET) is False
    assert sync.auth_header_ok({"request_headers": {sync.AUTH_HEADER: SECRET}}, SECRET) is True
    assert sync.auth_header_ok({"request_headers": {sync.AUTH_HEADER: "old"}}, SECRET) is False
    merged = sync.with_auth_header({"url": "u", "request_headers": {"X-Other": "1"}}, SECRET)
    assert merged["request_headers"] == {"X-Other": "1", sync.AUTH_HEADER: SECRET}
    assert merged["url"] == "u"


def test_sync_sets_header_on_every_tool_even_when_url_is_current(monkeypatch, capsys):
    monkeypatch.setenv("ANNA_WEBHOOK_SECRET", SECRET)
    client = FakeClient()  # URLs already correct, but no auth header
    assert sync.run_sync(client, BASE, dry_run=False) == 0
    assert len(client.patches) == len(ts.TOOL_PATHS)
    for _, body in client.patches:
        schema = body["tool_config"]["api_schema"]
        assert schema["request_headers"][sync.AUTH_HEADER] == SECRET
    assert SECRET not in capsys.readouterr().out


def test_sync_is_idempotent_when_header_and_url_match(monkeypatch):
    monkeypatch.setenv("ANNA_WEBHOOK_SECRET", SECRET)
    client = FakeClient(headers={sync.AUTH_HEADER: SECRET})
    assert sync.run_sync(client, BASE, dry_run=False) == 0
    assert client.patches == []


def test_sync_without_secret_does_not_touch_headers(monkeypatch):
    monkeypatch.delenv("ANNA_WEBHOOK_SECRET", raising=False)
    client = FakeClient(url_fn=lambda name: f"https://old.example{ts.TOOL_PATHS[name]}")
    assert sync.run_sync(client, BASE, dry_run=False) == 0
    assert len(client.patches) == len(ts.TOOL_PATHS)
    for _, body in client.patches:
        assert "request_headers" not in body["tool_config"]["api_schema"]


@pytest.mark.parametrize("dry_run", [True])
def test_dry_run_writes_nothing(monkeypatch, dry_run):
    monkeypatch.setenv("ANNA_WEBHOOK_SECRET", SECRET)
    client = FakeClient()
    assert sync.run_sync(client, BASE, dry_run=dry_run) == 0
    assert client.patches == []
