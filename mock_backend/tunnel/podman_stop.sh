#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# podman_stop.sh — STOP demo (gasi kontener + tunel)
# Uzdrowisko Bukowy Dwór (ElevenLabs PoC)
# ─────────────────────────────────────────────────────────────────────────────
set -u

echo "=== 🐳 Podman demo stop ==="

# 1) zatrzymaj kontener
if podman ps --format '{{.Names}}' | grep -q '^bukowy-dwor-backend$'; then
  podman stop bukowy-dwor-backend 2>/dev/null
  echo "✅ kontener zatrzymany"
else
  echo "ℹ️  kontener nie działa"
fi

# 2) ubij tunel (nasze cloudflared na :8011 — taskkill po PID, pkill nie działa na Windows exe)
OUR_PIDS="$(powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name like '%cloudflared%'\" | Where-Object { \$_.CommandLine -match 'localhost:8011' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r')"
if [[ -n "$OUR_PIDS" ]]; then
  for pid in $OUR_PIDS; do
    taskkill /F /PID "$pid" >/dev/null 2>&1 && echo "  ubity cloudflared PID $pid"
  done
  echo "✅ tunel zatrzymany"
else
  echo "ℹ️  tunel nie działał"
fi

# 3) nie ruszamy webhooków — agent zostaje skonfigurowany (wróci po start)
echo "ℹ️  webhooki agenta pozostają (wrócą na nowy URL po ./podman_start.sh)"

echo "=== demo wyłączone ==="
