#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start_anna.sh — start the mock backend (uvicorn, no container) and a public tunnel for "Anna".
#
#   1. Starts the mock backend with uvicorn on a free port (default 8011), env from mock_backend/.env.
#   2. Starts a cloudflared quick tunnel (trycloudflare) to that backend.
#   3. Reads the public URL from the tunnel log and writes state to tunnel/state.json.
#   4. Pins the tunnel host to IPv4 in the hosts file.
#   5. Points the agent's 7 webhook tools at the new URL (sync_agent_tools.py, matched by name).
#
# Refuses to open the tunnel when ANNA_WEBHOOK_SECRET is empty (see _common.sh).
# Trycloudflare issues a new URL on every start; the webhook sync repairs the agent after each restart.
#
# Usage:
#   ./start_anna.sh            # default port 8011
#   ./start_anna.sh 8012       # another port
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/mock_backend"
TUNNEL_DIR="$BACKEND_DIR/tunnel"
STATE_FILE="$TUNNEL_DIR/state.json"
BACKEND_ENV_FILE="$BACKEND_DIR/.env"
FRONTEND_ENV_FILE="$PROJECT_ROOT/frontend/.env.local"
PORT="${1:-8011}"

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "❌ no Python interpreter on PATH (python/py/python3). Install Python 3.12 or add it to PATH."
  exit 1
fi

# ── cloudflared ─────────────────────────────────────────────────────────────
CLOUDFLARED=""
for candidate in "$TUNNEL_DIR/cloudflared.exe" "/c/Program Files (x86)/cloudflared/cloudflared" "$(command -v cloudflared 2>/dev/null || true)"; do
  if [[ -n "$candidate" && -f "$candidate" ]]; then
    CLOUDFLARED="$candidate"
    break
  fi
done
if [[ -z "$CLOUDFLARED" ]]; then
  echo "❌ cloudflared not found. Put it at $TUNNEL_DIR/cloudflared.exe"
  exit 1
fi
echo "cloudflared: $CLOUDFLARED"

# ── the public tunnel must never open without the webhook secret ────────────
require_webhook_secret "$BACKEND_ENV_FILE"

# ── backend: start only when it is not already answering ────────────────────
# Variables from mock_backend/.env are exported here, because uvicorn inherits this shell's environment.
load_env_file "$BACKEND_ENV_FILE"
mkdir -p "$TUNNEL_DIR"
if curl -s -m 5 "http://127.0.0.1:$PORT/" | grep -q '"status":"OK"'; then
  echo "ℹ️  backend already running on :$PORT — skipping start (it keeps the env it was started with)"
  BACKEND_PID="already-running"
else
  echo "🚀 starting backend on :$PORT"
  (cd "$BACKEND_DIR" && "$PYTHON_BIN" -m uvicorn main:app --host 0.0.0.0 --port "$PORT" >"$TUNNEL_DIR/backend.log" 2>&1) &
  BACKEND_PID=$!
  ok=0
  for _ in $(seq 1 15); do
    if curl -s -m 2 "http://127.0.0.1:$PORT/" | grep -q '"status":"OK"'; then
      ok=1
      break
    fi
    sleep 1
  done
  if [[ $ok != 1 ]]; then
    echo "❌ backend did not start (is port $PORT taken by another application?). See $TUNNEL_DIR/backend.log"
    exit 1
  fi
  echo "✅ backend on :$PORT (pid $BACKEND_PID)"
fi

# ── tunnel: always a new trycloudflare URL ──────────────────────────────────
echo "🚀 starting tunnel -> http://localhost:$PORT"
"$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate >"$TUNNEL_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!

if ! URL="$(wait_for_tunnel_url "$TUNNEL_DIR/tunnel.log" 30)"; then
  echo "❌ could not read the tunnel URL — see $TUNNEL_DIR/tunnel.log"
  exit 1
fi
echo "✅ tunnel URL: $URL"

cat >"$STATE_FILE" <<EOF
{"port": $PORT, "backend_pid": "$BACKEND_PID", "tunnel_pid": $TUNNEL_PID, "url": "$URL"}
EOF
echo "📄 state saved: $STATE_FILE"

# ── hosts entry (IPv4) — the router returns AAAA only for trycloudflare hosts ─
update_hosts_entry "$(echo "$URL" | sed 's|https://||; s|/||')"

# ── agent webhooks (one shared script) ──────────────────────────────────────
if [[ -f "$FRONTEND_ENV_FILE" ]] && env_get "$FRONTEND_ENV_FILE" ELEVENLABS_API_KEY >/dev/null; then
  if "$PYTHON_BIN" "$TUNNEL_DIR/sync_agent_tools.py" --base-url "$URL"; then
    echo "✅ agent webhooks updated to $URL"
  else
    echo "❌ not all webhooks were updated — see the messages above"
  fi
else
  echo "⚠️  no ELEVENLABS_API_KEY in $FRONTEND_ENV_FILE — webhooks NOT updated"
fi

echo
echo "============================================================"
echo "  Anna ready."
echo "  Backend : http://localhost:$PORT"
echo "  URL     : $URL"
echo "  Restart : ./start_anna.sh"
echo "============================================================"
