"""Testy wspólnego klienta narzędzi tunelu (`tunnel/_http.py`) i obu skryptów na nim opartych.

Offline: lokalny `http.server` w wątku na 127.0.0.1, zero wywołań ElevenLabs, zero kredytów.
Klucz API w testach to atrapa; test regresyjny pilnuje, że nigdy nie trafia do wyjątku ani logu.
"""

from __future__ import annotations

import re
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from tunnel import _http, run_simulations as rs, sync_agent_tools as sync
from tunnel._http import ApiClient, ApiError, resolve_api_key

SECRET = "sk_test_CANARY_do_not_leak_0123456789"
TUNNEL_DIR = Path(__file__).resolve().parents[1] / "tunnel"


# ── lokalny serwer HTTP w wątku ────────────────────────────────────────────
@pytest.fixture()
def server():
    routes: dict[str, dict] = {}
    seen: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def _respond(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            seen.append({"method": self.command, "path": self.path,
                         "key": self.headers.get("xi-api-key")})
            spec = routes.get(self.path, {"status": 404, "type": "text/plain", "body": "brak trasy"})
            if spec.get("delay"):
                time.sleep(spec["delay"])
            payload = spec["body"].encode("utf-8")
            try:
                self.send_response(spec["status"])
                self.send_header("Content-Type", spec["type"])
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except OSError:  # klient mógł już zamknąć gniazdo (timeout)
                pass

        def do_GET(self) -> None:
            self._respond()

        def do_POST(self) -> None:
            self._respond()

        def do_PATCH(self) -> None:
            self._respond()

        def do_DELETE(self) -> None:
            self._respond()

        def log_message(self, format, *args) -> None:  # noqa: A002 - cisza w konsoli
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield SimpleNamespace(
            base=f"http://127.0.0.1:{httpd.server_address[1]}", routes=routes, seen=seen
        )
    finally:
        httpd.shutdown()
        httpd.server_close()


def route(srv, path: str, status: int, body: str, kind: str = "application/json",
          delay: float = 0.0) -> None:
    srv.routes[path] = {"status": status, "type": kind, "body": body, "delay": delay}


def closed_port_base() -> str:
    """Adres, na którym na pewno nikt nie słucha (błąd transportu)."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return f"http://127.0.0.1:{port}"


# ── 200 ────────────────────────────────────────────────────────────────────
def test_200_json_parsed_and_key_sent_in_header(server):
    route(server, "/v1/ok", 200, '{"tools": []}')
    client = ApiClient(server.base, key=SECRET)

    status, text = client.request("GET", "/v1/ok")
    assert status == 200 and text == '{"tools": []}'
    assert client.request_json("GET", "/v1/ok") == (200, {"tools": []})
    assert client.request_ok("GET", "/v1/ok") == {"tools": []}
    assert server.seen[-1]["key"] == SECRET  # klucz idzie do nagłówka, nie do URL


def test_no_key_means_no_header(server):
    route(server, "/v1/ok", 200, "{}")
    ApiClient(server.base).request("GET", "/v1/ok")
    assert server.seen[-1]["key"] is None


def test_empty_2xx_body_is_empty_dict(server):
    route(server, "/v1/empty", 200, "")
    assert ApiClient(server.base).request_ok("DELETE", "/v1/empty") == {}
    assert ApiClient(server.base).request_json("DELETE", "/v1/empty") == (200, {})


# ── 4xx z JSON ─────────────────────────────────────────────────────────────
def test_4xx_json_request_returns_status_and_request_json_parses(server):
    route(server, "/v1/bad", 422, '{"detail": "zły payload"}')
    client = ApiClient(server.base, key=SECRET)

    status, text = client.request("POST", "/v1/bad", {"a": 1})
    assert status == 422 and "zły payload" in text
    assert client.request_json("POST", "/v1/bad", {"a": 1}) == (422, {"detail": "zły payload"})


def test_4xx_json_request_ok_raises_api_error(server):
    route(server, "/v1/bad", 422, '{"detail": "zły payload"}')
    with pytest.raises(ApiError) as exc:
        ApiClient(server.base).request_ok("POST", "/v1/bad", {"a": 1})
    assert "HTTP 422" in str(exc.value) and "zły payload" in str(exc.value)


# ── 4xx z tekstem ──────────────────────────────────────────────────────────
def test_4xx_plain_text_request_json_returns_text(server):
    route(server, "/v1/missing", 404, "brak zasobu", kind="text/plain")
    client = ApiClient(server.base)
    assert client.request_json("GET", "/v1/missing") == (404, "brak zasobu")


def test_4xx_plain_text_request_ok_raises_with_text(server):
    route(server, "/v1/missing", 404, "brak zasobu", kind="text/plain")
    with pytest.raises(ApiError) as exc:
        ApiClient(server.base).request_ok("GET", "/v1/missing")
    assert "HTTP 404" in str(exc.value) and "brak zasobu" in str(exc.value)


def test_2xx_non_json_request_ok_raises(server):
    route(server, "/v1/html", 200, "<html>nie json</html>", kind="text/html")
    client = ApiClient(server.base)
    assert client.request_json("GET", "/v1/html") == (200, "<html>nie json</html>")
    with pytest.raises(ApiError, match="nie-JSON"):
        client.request_ok("GET", "/v1/html")


# ── timeout i błędy transportu ─────────────────────────────────────────────
def test_timeout_raises_api_error_in_every_mode(server):
    route(server, "/v1/slow", 200, "{}", delay=1.0)
    client = ApiClient(server.base, key=SECRET, timeout=0.2)
    with pytest.raises(ApiError, match="nie doszło"):
        client.request("GET", "/v1/slow")
    with pytest.raises(ApiError, match="nie doszło"):
        client.request_json("GET", "/v1/slow")
    with pytest.raises(ApiError, match="nie doszło"):
        client.request_ok("GET", "/v1/slow")


def test_per_call_timeout_overrides_default(server):
    route(server, "/v1/slow", 200, "{}", delay=1.0)
    client = ApiClient(server.base, timeout=60.0)
    with pytest.raises(ApiError):
        client.request("GET", "/v1/slow", timeout=0.2)


def test_transport_error_retried_only_when_asked(monkeypatch):
    monkeypatch.setattr(_http, "RETRY_DELAY_SECONDS", 0)
    base = closed_port_base()
    with pytest.raises(ApiError, match="nie doszło"):
        ApiClient(base, timeout=0.5).request("GET", "/v1/x")
    with pytest.raises(ApiError, match="nie doszło"):
        ApiClient(base, timeout=0.5, retries=1).request("GET", "/v1/x")


def test_http_error_is_never_retried(server, monkeypatch):
    monkeypatch.setattr(_http, "RETRY_DELAY_SECONDS", 0)
    route(server, "/v1/bad", 500, "boom", kind="text/plain")
    assert ApiClient(server.base, retries=3).request("GET", "/v1/bad") == (500, "boom")
    assert len([s for s in server.seen if s["path"] == "/v1/bad"]) == 1


# ── klucz API nigdy w wyjątku ani w logu ───────────────────────────────────
def test_key_echoed_by_server_is_masked_in_api_error(server):
    route(server, "/v1/auth", 401, f'{{"detail": "zły klucz {SECRET}"}}')
    client = ApiClient(server.base, key=SECRET)
    with pytest.raises(ApiError) as exc:
        client.request_ok("GET", "/v1/auth")
    message = str(exc.value)
    assert SECRET not in message and "***" in message


def test_key_not_in_transport_error_message():
    client = ApiClient(closed_port_base(), key=SECRET, timeout=0.5)
    with pytest.raises(ApiError) as exc:
        client.request("GET", "/v1/x")
    assert SECRET not in str(exc.value) and SECRET not in repr(exc.value)


def test_sync_cli_error_output_has_no_key(server, capsys):
    route(server, "/v1/convai/tools", 401, f'{{"detail": "invalid {SECRET}"}}')
    code = sync.main(["--list", "--api-key", SECRET, "--api-base", server.base])
    captured = capsys.readouterr()
    assert code == 1
    assert "HTTP 401" in captured.err
    assert SECRET not in captured.out and SECRET not in captured.err


def test_sync_patch_detail_is_redacted(server):
    route(server, "/v1/convai/tools/t1", 403, f"forbidden for {SECRET}")
    client = ApiClient(server.base, key=SECRET)
    status, detail = sync.patch_tool(client, "t1", {"api_schema": {}})
    assert status == 403 and SECRET not in detail and "***" in detail


def test_run_simulations_whoami_error_has_no_key(server):
    route(server, "/v1/user/subscription", 401, f'{{"detail": "bad {SECRET}"}}')
    client = ApiClient(server.base, key=SECRET, timeout=5)
    with pytest.raises(SystemExit) as exc:
        rs.whoami(client)
    assert SECRET not in str(exc.value)


# ── odczyt klucza API ──────────────────────────────────────────────────────
def test_resolve_api_key_precedence(tmp_path, monkeypatch):
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "# komentarz ELEVENLABS_API_KEY=ignorowany\n"
        'export ELEVENLABS_API_KEY="z-pliku"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert resolve_api_key(None, env_file=env_file) == "z-pliku"

    monkeypatch.setenv("ELEVENLABS_API_KEY", "z-env")
    assert resolve_api_key(None, env_file=env_file) == "z-env"

    assert resolve_api_key("z-cli", env_file=env_file) == "z-cli"


def test_resolve_api_key_none_when_nothing_set(tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert resolve_api_key(None, env_file=tmp_path / "brak.env") is None


# ── struktura: jeden klient, zero zduplikowanych klas ─────────────────────
@pytest.mark.parametrize("script", ["sync_agent_tools.py", "run_simulations.py"])
def test_no_duplicate_client_class(script):
    source = (TUNNEL_DIR / script).read_text(encoding="utf-8")
    assert not re.search(r"^class Client\b", source, re.MULTILINE)


@pytest.mark.parametrize("script", ["sync_agent_tools.py", "run_simulations.py"])
def test_cli_help_runs_as_plain_script(script):
    # uruchomienie jako skrypt (sys.path[0] = tunnel/) musi znaleźć _http bez pakietu
    result = subprocess.run(
        [sys.executable, str(TUNNEL_DIR / script), "--help"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "usage" in result.stdout.lower()


# ── list_tools: paginacja na lokalnym serwerze ─────────────────────────────
def test_list_tools_follows_cursor(server):
    route(server, "/v1/convai/tools",
          200, '{"tools": [{"id": "a"}], "has_more": true, "next_cursor": "c2"}')
    route(server, "/v1/convai/tools?cursor=c2",
          200, '{"tools": [{"id": "b"}], "has_more": false}')
    tools = sync.list_tools(ApiClient(server.base, key=SECRET))
    assert [t["id"] for t in tools] == ["a", "b"]
