#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# podman_start.sh — START the demo on request (Podman container + tunnel + webhooks).
#
#   1. Starts the container `bukowy-dwor-backend` (mock backend, port 8011), env from mock_backend/.env.
#   2. Starts a cloudflared quick tunnel (trycloudflare) to localhost:8011.
#   3. Pins the tunnel host to IPv4 in the hosts file (works around the router's missing A records).
#   4. Points the agent's 7 webhook tools at the new URL (sync_agent_tools.py, matched by name).
#
# Refuses to open the tunnel when ANNA_WEBHOOK_SECRET is empty (see _common.sh).
# Stop with ./podman_stop.sh.
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
CONTAINER="bukowy-dwor-backend"
IMAGE="localhost/bukowy-dwor-backend"
PORT=8011
CLOUDFLARED="$TUNNEL_DIR/cloudflared.exe"

echo "=== 🐳 Podman demo start ($(date '+%H:%M:%S')) ==="

command -v podman >/dev/null 2>&1 || { echo "❌ podman not found in PATH"; exit 1; }
[[ -x "$CLOUDFLARED" || -f "$CLOUDFLARED" ]] || { echo "❌ cloudflared not found: $CLOUDFLARED"; exit 1; }

# 0) the public tunnel must never open without the webhook secret
require_webhook_secret "$BACKEND_ENV_FILE"

# 1) container
if podman ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ℹ️  container already running — skipping start (its env is the one it was created with)"
elif podman ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  podman start "$CONTAINER" >/dev/null
  echo "✅ container started (existing; env from its creation)"
else
  if ! podman image exists "$IMAGE"; then
    echo "🔨 no image — building $IMAGE from $BACKEND_DIR/Dockerfile"
    if ! podman build -t "$CONTAINER" -f "$BACKEND_DIR/Dockerfile" "$BACKEND_DIR"; then
      echo "❌ image build failed — check the Dockerfile and podman output"
      exit 1
    fi
    echo "✅ image built"
  fi
  # --env-file instead of -e KEY=VALUE: values stay out of the process list and the shell history.
  ENV_FILE_ARGS=()
  if [[ -f "$BACKEND_ENV_FILE" ]]; then
    ENV_FILE_ARGS=(--env-file "$BACKEND_ENV_FILE")
  fi
  podman run -d --name "$CONTAINER" -p "$PORT:$PORT" "${ENV_FILE_ARGS[@]}" "$IMAGE" >/dev/null
  echo "✅ container created (port $PORT)"
fi
sleep 2

# 2) tunnel — always a new one (trycloudflare issues a new URL on every start)
stop_our_tunnels "$PORT"
rm -f "$TUNNEL_DIR/tunnel.log"
"$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate >"$TUNNEL_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!

if ! URL="$(wait_for_tunnel_url "$TUNNEL_DIR/tunnel.log" 40)"; then
  echo "❌ could not read the tunnel URL (see $TUNNEL_DIR/tunnel.log)"
  exit 1
fi
echo "✅ tunnel URL: $URL"

# 3) hosts entry (IPv4)
update_hosts_entry "$(echo "$URL" | sed 's|https://||; s|/||')"

# 4) agent webhooks — one shared script, all 7 tools by name
if PYTHON_BIN="$(find_python)" && [[ -f "$FRONTEND_ENV_FILE" ]] && env_get "$FRONTEND_ENV_FILE" ELEVENLABS_API_KEY >/dev/null; then
  if "$PYTHON_BIN" "$TUNNEL_DIR/sync_agent_tools.py" --base-url "$URL"; then
    echo "✅ agent webhooks updated to $URL"
  else
    echo "❌ not all webhooks were updated — see the messages above"
  fi
else
  echo "⚠️  no Python or no ELEVENLABS_API_KEY in frontend/.env.local — webhooks NOT updated"
fi

# 5) state
cat >"$STATE_FILE" <<EOF
{"port": $PORT, "backend": "podman: $CONTAINER", "tunnel_pid": $TUNNEL_PID, "url": "$URL"}
EOF

echo
echo "============================================================"
echo "  🐳 Anna demo READY (Podman)"
echo "  Backend : container $CONTAINER :$PORT"
echo "  URL     : $URL"
echo "  Stop    : ./podman_stop.sh"
echo "============================================================"
