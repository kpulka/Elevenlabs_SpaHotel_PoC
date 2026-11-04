#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# podman_stop.sh — stop the demo (stops the container and the tunnel)
# Bukowy Dwór health resort (ElevenLabs PoC)
# ─────────────────────────────────────────────────────────────────────────────
set -u

CONTAINER_NAME="bukowy-dwor-backend"

echo "=== Podman demo stop ==="

# 1) Stop the container
if podman ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  podman stop "$CONTAINER_NAME" 2>/dev/null
  echo "[ok] container stopped"
else
  echo "[info] container is not running"
fi

# 2) Stop our tunnel (cloudflared on :8011), matched by PID via taskkill (pkill does not work on Windows executables)
OUR_PIDS="$(powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name like '%cloudflared%'\" | Where-Object { \$_.CommandLine -match 'localhost:8011' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r')"
if [[ -n "$OUR_PIDS" ]]; then
  for pid in $OUR_PIDS; do
    taskkill /F /PID "$pid" >/dev/null 2>&1 && echo "  stopped cloudflared PID $pid"
  done
  echo "[ok] tunnel stopped"
else
  echo "[info] tunnel was not running"
fi

# 3) Agent webhooks are left as they are; they point to the new URL after the next podman_start.sh
echo "[info] agent webhooks unchanged (they will be updated to the new URL by podman_start.sh)"

echo "=== demo stopped ==="
