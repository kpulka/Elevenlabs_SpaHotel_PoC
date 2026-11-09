#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# podman_start.sh — START demo na żądanie (Podman kontener + tunel + webhooki)
# Uzdrowisko Bukowy Dwór (ElevenLabs PoC)
#
# Odpala całość TYLKO gdy chcesz pokazać projekt:
#   1. Uruchamia kontener `bukowy-dwor-backend` (mock backend, port 8011).
#   2. Uruchamia cloudflared tunnel (trycloudflare) → localhost:8011.
#   3. Wyłapuje publiczny URL, aktualizuje wpis w hosts (IPv4) — omija DNS routera.
#   4. Aktualizuje 7 narzędzi webhook agenta ElevenLabs na nowy URL
#      (wspólny skrypt sync_agent_tools.py — szuka narzędzi po nazwie).
# Zatrzymanie: ./podman_stop.sh
# ─────────────────────────────────────────────────────────────────────────────
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/mock_backend"
TUNNEL_DIR="$BACKEND_DIR/tunnel"
STATE_FILE="$TUNNEL_DIR/state.json"
PORT=8011
CLOUDFLARED="$TUNNEL_DIR/cloudflared.exe"
PYTHON_BIN="$(command -v python || command -v py || command -v python3 || true)"
HOSTS_FILE="/c/Windows/System32/drivers/etc/hosts"
HOSTS_MARK="# ElevenLabs Anna - tunnel"

echo "=== 🐳 Podman demo start ($(date '+%H:%M:%S')) ==="

# 1) kontener
# Wczytaj env z mock_backend/.env (Telegram) jeśli istnieje
ENV_FILE_BACKEND="$BACKEND_DIR/.env"
ENV_ARGS=()
if [[ -f "$ENV_FILE_BACKEND" ]]; then
  while IFS='=' read -r k v; do
    [[ -z "$k" || "$k" == \#* ]] && continue
    ENV_ARGS+=("-e" "$k=$v")
  done <"$ENV_FILE_BACKEND"
  echo "ℹ️  env z .env: ${#ENV_ARGS[@]/#/-e } opcji"
fi
if podman ps --format '{{.Names}}' | grep -q '^bukowy-dwor-backend$'; then
  echo "ℹ️  kontener już działa — pomijam start"
else
  if podman ps -a --format '{{.Names}}' | grep -q '^bukowy-dwor-backend$'; then
    podman start bukowy-dwor-backend
  else
    # obraz musi istnieć — na świeżym klonie nikt go wcześniej nie zbudował
    if ! podman image exists localhost/bukowy-dwor-backend; then
      echo "🔨 brak obrazu — buduję localhost/bukowy-dwor-backend (Dockerfile: tunnel/Dockerfile, kontekst: mock_backend/)"
      if ! podman build -t bukowy-dwor-backend -f "$TUNNEL_DIR/Dockerfile" "$BACKEND_DIR"; then
        echo "❌ build obrazu localhost/bukowy-dwor-backend nie powiódł się — sprawdź Dockerfile/podman i spróbuj: podman build -t bukowy-dwor-backend -f \"$TUNNEL_DIR/Dockerfile\" \"$BACKEND_DIR\""
        exit 1
      fi
      echo "✅ obraz zbudowany"
    fi
    podman run -d --name bukowy-dwor-backend -p $PORT:$PORT "${ENV_ARGS[@]}" localhost/bukowy-dwor-backend
  fi
  echo "✅ kontener wystartowany (port $PORT)"
fi
sleep 2

# 2) tunel (zawsze nowy — trycloudflare zmienia URL)
# Najpierw ubij stare nasze tunel (taskkill po PID, nie pkill — Windows exe)
OUR_PIDS="$(powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name like '%cloudflared%'\" | Where-Object { \$_.CommandLine -match 'localhost:8011' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r')"
for pid in $OUR_PIDS; do taskkill /F /PID "$pid" >/dev/null 2>&1; done
rm -f "$TUNNEL_DIR/tunnel.log"
"$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate >"$TUNNEL_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!

URL=""
for i in $(seq 1 40); do
  URL="$(grep -aoE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_DIR/tunnel.log" 2>/dev/null | head -1 || true)"
  [[ -n "$URL" ]] && break
  sleep 1
done
if [[ -z "$URL" ]]; then
  echo "❌ nie udało się uzyskać URL tunelu (sprawdź tunnel.log)"
  exit 1
fi
echo "✅ URL tunelu: $URL"

# 3) wpis w hosts (IPv4 — omija router bez A-rekordów)
update_hosts() {
  local host="$1" ip=""
  for attempt in 1 2 3 4 5; do
    ip="$(nslookup "$host" 1.1.1.1 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^1\.1\.1\.1$' | tail -1)"
    [[ -n "$ip" ]] && break
    sleep 3
  done
  [[ -z "$ip" ]] && { echo "⚠️  brak IP dla $host — pomijam hosts"; return; }
  cp "$HOSTS_FILE" "$HOSTS_FILE.bak" 2>/dev/null || true
  sed -i "/$HOSTS_MARK/d; /${host}/d" "$HOSTS_FILE" 2>/dev/null || true
  printf "\n%s\n%s  %s\n" "$HOSTS_MARK" "$ip" "$host" >>"$HOSTS_FILE" 2>/dev/null && \
    echo "✅ hosts: $ip $host" || echo "⚠️  brak uprawnień do hosts"
}
update_hosts "$(echo "$URL" | sed 's|https://||; s|/||')"

# 4) webhooki agenta — jeden wspólny skrypt, wszystkie 7 narzędzi po nazwie
ENV_FILE="$PROJECT_ROOT/frontend/.env.local"
if [[ -f "$ENV_FILE" ]] && grep -q 'ELEVENLABS_API_KEY=' "$ENV_FILE"; then
  if [[ -z "$PYTHON_BIN" ]]; then
    echo "⚠️  brak interpretera python — nie zaktualizowano webhooków"
  elif "$PYTHON_BIN" "$TUNNEL_DIR/sync_agent_tools.py" --base-url "$URL"; then
    echo "✅ webhooki agenta zaktualizowane na $URL"
  else
    echo "❌ nie wszystkie webhooki udało się zaktualizować — patrz komunikaty powyżej"
  fi
else
  echo "⚠️  brak klucza — nie zaktualizowano webhooków"
fi

# 5) stan
cat >"$STATE_FILE" <<EOF
{"port": $PORT, "backend": "podman: bukowy-dwor-backend", "tunnel_pid": $TUNNEL_PID, "url": "$URL"}
EOF

echo
echo "============================================================"
echo "  🐳 Anna demo READY (Podman)"
echo "  Backend : kontener bukowy-dwor-backend :$PORT"
echo "  URL     : $URL"
echo "  Stop    : ./podman_stop.sh"
echo "============================================================"
