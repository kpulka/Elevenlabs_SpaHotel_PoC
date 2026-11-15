"""Offline tests for the Anna outbound events contract (receiver + n8n workflow artifacts).

What is verified here:
* the reference receiver (receiver_example.py) against a fixed HMAC test vector,
* tamper detection, replay window, header and payload checks, HTTP round-trip,
* the n8n workflow JSON structure and the Code node source (verify_signature.js),
  executed with Node.js when it is available (skipped otherwise).

What is NOT verified here: the workflow is never imported or executed in a live n8n instance.

Run from the repository root:  python -m pytest -q integrations/n8n/test_receiver.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import receiver_example as rx

HERE = Path(__file__).resolve().parent
WORKFLOW = HERE / "anna_events_workflow.example.json"
CODE_JS = HERE / "verify_signature.js"

SECRET = "test-secret"
TIMESTAMP = "1700000000"
BODY = b'{"event_id":"e1"}'
# Vector computed with Python's hmac module (see the scratch note in the README):
# HMAC-SHA256(key="test-secret", msg="1700000000." + '{"event_id":"e1"}')
VECTOR_SIGNATURE = "sha256=18a2df74eba88d0ed4b4033fc9f3860558e826c9e5d1b77dc702b5da0d0cefe6"


def _headers(event_id: str = "e1", timestamp: str = TIMESTAMP, signature: str = VECTOR_SIGNATURE) -> dict:
    return {"X-Anna-Event-Id": event_id, "X-Anna-Timestamp": timestamp, "X-Anna-Signature": signature}


def _signed(event: dict, timestamp: str = TIMESTAMP, secret: str = SECRET) -> tuple[dict, bytes]:
    body = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    headers = {
        "X-Anna-Event-Id": event["event_id"],
        "X-Anna-Timestamp": timestamp,
        "X-Anna-Signature": rx.sign(secret, timestamp, body),
    }
    return headers, body


EVENT = {
    "event_id": "evt_0001",
    "event_type": "booking.created",
    "occurred_at": "2026-11-15T10:00:00Z",
    "request_id": "req_0001",
    "conversation_id": None,
    "data": {"confirmation_id": "SPA-1001", "guest_name": "J*** K*******"},
}


# ── 1. test vector and verification ──────────────────────────────────────────

def test_vector_signature_matches_independent_hmac():
    expected = "sha256=" + hmac.new(SECRET.encode(), f"{TIMESTAMP}.".encode() + BODY, hashlib.sha256).hexdigest()
    assert expected == VECTOR_SIGNATURE
    assert rx.sign(SECRET, TIMESTAMP, BODY) == VECTOR_SIGNATURE


def test_valid_signature_is_accepted_at_signing_time():
    assert rx.verify(SECRET, TIMESTAMP, VECTOR_SIGNATURE, BODY, now=1700000000) == "ok"


def test_tampered_body_is_rejected():
    tampered = b'{"event_id":"e2"}'
    assert rx.verify(SECRET, TIMESTAMP, VECTOR_SIGNATURE, tampered, now=1700000000) == "bad_signature"


def test_tampered_timestamp_is_rejected_even_with_same_signature():
    assert rx.verify(SECRET, "1700000001", VECTOR_SIGNATURE, BODY, now=1700000001) == "bad_signature"


def test_wrong_secret_is_rejected():
    assert rx.verify("other-secret", TIMESTAMP, VECTOR_SIGNATURE, BODY, now=1700000000) == "bad_signature"


def test_signature_without_prefix_is_rejected():
    bare = VECTOR_SIGNATURE.removeprefix("sha256=")
    assert rx.verify(SECRET, TIMESTAMP, bare, BODY, now=1700000000) == "bad_signature"


# ── 2. replay window (300 s) ─────────────────────────────────────────────────

@pytest.mark.parametrize("now", [1700000000 + 300, 1700000000 - 300])
def test_timestamp_on_the_300s_boundary_is_accepted(now):
    assert rx.verify(SECRET, TIMESTAMP, VECTOR_SIGNATURE, BODY, now=now) == "ok"


@pytest.mark.parametrize("now", [1700000000 + 301, 1700000000 - 301, 1700000000 + 3600])
def test_stale_or_future_timestamp_is_rejected(now):
    assert rx.verify(SECRET, TIMESTAMP, VECTOR_SIGNATURE, BODY, now=now) == "stale_timestamp"


def test_replay_check_runs_before_signature_check():
    # Old but correctly signed request: rejected as stale, not as a signature problem.
    assert rx.verify(SECRET, TIMESTAMP, VECTOR_SIGNATURE, BODY, now=1800000000) == "stale_timestamp"


# ── 3. malformed input ───────────────────────────────────────────────────────

@pytest.mark.parametrize("timestamp,signature", [(None, VECTOR_SIGNATURE), (TIMESTAMP, None), ("", "")])
def test_missing_headers_are_rejected(timestamp, signature):
    assert rx.verify(SECRET, timestamp, signature, BODY, now=1700000000) == "missing_headers"


@pytest.mark.parametrize("timestamp", ["1700000000.5", "-1", "17e8", " 1700000000", "١٧٠٠٠٠٠٠٠٠"])
def test_non_integer_timestamp_is_rejected(timestamp):
    assert rx.verify(SECRET, timestamp, VECTOR_SIGNATURE, BODY, now=1700000000) == "bad_timestamp"


def test_empty_secret_fails_closed():
    assert rx.verify("", TIMESTAMP, VECTOR_SIGNATURE, BODY, now=1700000000) == "missing_secret"


# ── 4. receiver core (headers + raw bytes -> status) ─────────────────────────

def _receiver(now: int = 1700000000) -> rx.AnnaEventsReceiver:
    return rx.AnnaEventsReceiver(SECRET, clock=lambda: now)


def test_handle_accepts_signed_event_once_then_acks_duplicate():
    headers, body = _signed(EVENT)
    receiver = _receiver()
    assert receiver.handle(headers, body) == (200, {"accepted": True, "duplicate": False, "event_id": "evt_0001"})
    assert receiver.handle(headers, body) == (200, {"accepted": True, "duplicate": True, "event_id": "evt_0001"})


def test_handle_returns_generic_401_without_revealing_the_failed_check():
    headers, body = _signed(EVENT)
    headers["X-Anna-Signature"] = "sha256=" + "0" * 64
    assert _receiver().handle(headers, body) == (401, {"error": "unauthorized"})


def test_handle_rejects_header_body_event_id_mismatch():
    headers, body = _signed(EVENT)
    headers["X-Anna-Event-Id"] = "evt_other"
    assert _receiver().handle(headers, body) == (400, {"error": "event_id_mismatch"})


def test_handle_rejects_unknown_event_type():
    event = {**EVENT, "event_type": "handoff"}  # old, never-emitted name from the previous workflow
    headers, body = _signed(event)
    assert _receiver().handle(headers, body) == (400, {"error": "unknown_event_type"})


def test_handle_rejects_signed_but_invalid_json():
    body = b"{not json"
    headers = {
        "X-Anna-Event-Id": "evt_x",
        "X-Anna-Timestamp": TIMESTAMP,
        "X-Anna-Signature": rx.sign(SECRET, TIMESTAMP, body),
    }
    assert _receiver().handle(headers, body) == (400, {"error": "invalid_json"})


def test_handle_rejects_oversized_body_before_verifying():
    body = b"x" * (rx.MAX_BODY_BYTES + 1)
    assert _receiver().handle({}, body) == (413, {"error": "payload_too_large"})


def test_signature_covers_raw_bytes_not_reserialized_json():
    # Same logical event, different whitespace: the signature over the original bytes must not verify
    # after re-serialization. This is why the n8n workflow reads the raw body.
    headers, body = _signed(EVENT)
    spaced = json.dumps(json.loads(body), indent=2).encode("utf-8")
    assert _receiver().handle(headers, spaced)[0] == 401


# ── 5. HTTP round-trip (stdlib server on an ephemeral port) ──────────────────

@pytest.fixture()
def running_server():
    server = rx.make_server(rx.AnnaEventsReceiver(SECRET), "127.0.0.1", 0)  # real clock
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    yield f"http://{host}:{port}{rx.ENDPOINT_PATH}"
    server.shutdown()
    server.server_close()


def _post(url: str, headers: dict, body: bytes) -> tuple[int, dict]:
    all_headers = {**headers, "Content-Type": "application/json"}
    request = urllib.request.Request(url, data=body, method="POST", headers=all_headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_http_round_trip_status_codes(running_server):
    now = str(int(time.time()))
    headers, body = _signed(EVENT, timestamp=now)
    assert _post(running_server, headers, body)[0] == 200
    assert _post(running_server, headers, body) == (200, {"accepted": True, "duplicate": True, "event_id": "evt_0001"})

    bad_headers = {**headers, "X-Anna-Signature": "sha256=" + "f" * 64}
    assert _post(running_server, bad_headers, body) == (401, {"error": "unauthorized"})


def test_http_unknown_path_is_404(running_server):
    request = urllib.request.Request(running_server.replace(rx.ENDPOINT_PATH, "/nope"), data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as info:
        urllib.request.urlopen(request, timeout=5)
    assert info.value.code == 404


# ── 6. n8n workflow artifact ─────────────────────────────────────────────────

@pytest.fixture(scope="module")
def workflow() -> dict:
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_is_inactive_and_marked_as_example(workflow):
    assert workflow["active"] is False
    assert "EXAMPLE" in workflow["name"]
    assert "NOT DEPLOYED" in workflow["name"]


def test_workflow_connections_reference_existing_nodes(workflow):
    names = {node["name"] for node in workflow["nodes"]}
    assert len(names) == len(workflow["nodes"]), "node names must be unique"
    for source, outputs in workflow["connections"].items():
        assert source in names, f"connection from unknown node {source!r}"
        for branch in outputs["main"]:
            for target in branch:
                assert target["node"] in names, f"connection to unknown node {target['node']!r}"


def test_workflow_has_required_pipeline_nodes(workflow):
    types = {node["type"] for node in workflow["nodes"]}
    for required in (
        "n8n-nodes-base.webhook",
        "n8n-nodes-base.code",
        "n8n-nodes-base.if",
        "n8n-nodes-base.switch",
        "n8n-nodes-base.httpRequest",
        "n8n-nodes-base.respondToWebhook",
    ):
        assert required in types, required


def test_workflow_webhook_keeps_raw_body_and_waits_for_response_node(workflow):
    webhook = next(n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.webhook")
    assert webhook["parameters"]["options"]["rawBody"] is True
    assert webhook["parameters"]["responseMode"] == "responseNode"


def test_workflow_responds_200_and_401(workflow):
    codes = {
        node["parameters"]["options"]["responseCode"]
        for node in workflow["nodes"]
        if node["type"] == "n8n-nodes-base.respondToWebhook"
    }
    assert codes == {200, 401}


def test_workflow_switch_routes_every_contract_event_type(workflow):
    switch = next(n for n in workflow["nodes"] if n["name"] == "Switch - event_type")
    routed = {rule["outputKey"] for rule in switch["parameters"]["rules"]["values"]}
    assert routed == {"booking.created", "booking.rescheduled", "booking.cancelled", "handoff.requested"}
    assert switch["parameters"]["options"]["fallbackOutput"] == "extra"


def test_workflow_embeds_the_same_code_as_the_source_file(workflow):
    code = next(n for n in workflow["nodes"] if n["type"] == "n8n-nodes-base.code")
    assert code["parameters"]["jsCode"] == CODE_JS.read_text(encoding="utf-8")


def test_workflow_contains_no_secrets_or_real_hosts(workflow):
    text = WORKFLOW.read_text(encoding="utf-8")
    assert SECRET not in text
    assert VECTOR_SIGNATURE not in text
    assert "ANNA_EVENTS_SIGNING_SECRET=" not in text
    urls = re.findall(r"https?://[^\s\"'\\)]+", text)
    assert all(url.rstrip("/").endswith(".invalid") for url in urls), urls
    # Credentials are referenced by placeholder id only.
    for node in workflow["nodes"]:
        for cred in (node.get("credentials") or {}).values():
            assert cred["id"].startswith("REPLACE_") or cred["id"].startswith("PLACEHOLDER"), cred


def test_code_source_uses_the_contract_tolerance():
    source = CODE_JS.read_text(encoding="utf-8")
    assert re.search(r"TOLERANCE_S\s*=\s*300\b", source)
    assert rx.TOLERANCE_S == 300


# ── 7. Code node executed with Node.js (cross-check against Python) ──────────

NODE = shutil.which("node")
NODE_RUNNER = """
const fs = require('fs');
globalThis.require = require;
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
Date.now = () => input.now * 1000;
const code = fs.readFileSync(input.file, 'utf8');
const $env = { ANNA_EVENTS_SIGNING_SECRET: input.secret };
const item = { json: { headers: input.headers, rawBody: input.useBinary ? undefined : input.body } };
if (input.useBinary) {
  item.binary = { data: { data: Buffer.from(input.body, 'utf8').toString('base64') } };
}
const $input = { first: () => item };
const out = new Function('$input', '$env', code)($input, $env);
process.stdout.write(JSON.stringify(out));
"""


def _run_code_node(headers: dict, body: bytes, now: int, *, secret: str = SECRET, binary: bool = False) -> dict:
    payload = {
        "file": str(CODE_JS),
        "now": now,
        "secret": secret,
        "headers": {key.lower(): value for key, value in headers.items()},
        "body": body.decode("utf-8"),
        "useBinary": binary,
    }
    completed = subprocess.run(
        [NODE, "-e", NODE_RUNNER],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return json.loads(completed.stdout)[0]["json"]


needs_node = pytest.mark.skipif(NODE is None, reason="Node.js not available; Code node cross-check skipped")


@needs_node
@pytest.mark.parametrize("binary", [False, True], ids=["rawBody-string", "binary-data-base64"])
def test_code_node_accepts_the_test_vector(binary):
    result = _run_code_node(_headers(), BODY, now=1700000000, binary=binary)
    assert result["authorized"] is True
    assert result["reason"] == "ok"
    assert result["eventId"] == "e1"


@needs_node
@pytest.mark.parametrize(
    "case",
    [
        {"name": "tampered_body", "body": b'{"event_id":"e2"}', "headers": _headers(event_id="e2")},
        {"name": "bad_signature", "body": BODY, "headers": _headers(signature="sha256=" + "0" * 64)},
        {"name": "stale", "body": BODY, "headers": _headers(), "now": 1700000000 + 301},
        {"name": "missing_headers", "body": BODY, "headers": {"X-Anna-Event-Id": "e1"}},
        {"name": "non_integer_timestamp", "body": BODY, "headers": _headers(timestamp="17.5")},
    ],
    ids=lambda c: c["name"],
)
def test_code_node_rejects_what_the_receiver_rejects(case):
    now = case.get("now", 1700000000)
    js = _run_code_node(case["headers"], case["body"], now=now)
    assert js["authorized"] is False
    python_reason = rx.verify(
        SECRET,
        case["headers"].get("X-Anna-Timestamp"),
        case["headers"].get("X-Anna-Signature"),
        case["body"],
        now=now,
    )
    assert js["reason"] == python_reason


@needs_node
def test_code_node_rejects_when_secret_is_not_configured():
    js = _run_code_node(_headers(), BODY, now=1700000000, secret="")
    assert js == {"authorized": False, "reason": "missing_secret", "eventId": "e1", "eventType": None, "event": None}


@needs_node
def test_code_node_returns_event_type_for_a_signed_event():
    headers, body = _signed(EVENT)
    js = _run_code_node(headers, body, now=int(headers["X-Anna-Timestamp"]))
    assert js["authorized"] is True
    assert js["eventType"] == "booking.created"
    assert js["event"]["data"]["confirmation_id"] == "SPA-1001"
