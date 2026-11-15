#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# podman_stop.sh — STOP the demo (stops the container and the tunnel).
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"

CONTAINER="bukowy-dwor-backend"
PORT=8011

echo "=== 🐳 Podman demo stop ==="

# 1) stop the container
if command -v podman >/dev/null 2>&1 && podman ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  podman stop "$CONTAINER" >/dev/null 2>&1 || true
  echo "✅ container stopped"
else
  echo "ℹ️  container is not running"
fi

# 2) stop our tunnel (only cloudflared processes pointing at localhost:$PORT)
stop_our_tunnels "$PORT"
echo "✅ tunnel stopped (if it was running)"

# 3) webhooks are left as they are: the agent stays configured and is re-pointed by the next start
echo "ℹ️  agent webhooks stay as they are (the next ./podman_start.sh points them at the new URL)"

echo "=== demo off ==="
