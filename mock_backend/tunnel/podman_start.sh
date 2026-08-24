#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# podman_start.sh — START demo na żądanie (Podman kontener + tunel + webhooki)
# Uzdrowisko Bukowy Dwór (ElevenLabs PoC)
#
# Odpala całość TYLKO gdy chcesz pokazać projekt:
#   1. Uruchamia kontener `bukowy-dwor-backend` (mock backend, port 8011).
#   2. Uruchamia cloudflared tunnel (trycloudflare) → localhost:8011.
#   3. Wyłapuje publiczny URL, aktualizuje wpis w hosts (IPv4) — omija DNS routera.
#   4. Aktualizuje 5 narzędzi webhook agenta ElevenLabs na nowy URL.
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

# 4) webhooki agenta
ENV_FILE="$PROJECT_ROOT/frontend/.env.local"
if [[ -f "$ENV_FILE" ]] && grep -q 'ELEVENLABS_API_KEY=' "$ENV_FILE"; then
  KEY="$(grep -oE 'ELEVENLABS_API_KEY=[^ ]+' "$ENV_FILE" | head -1 | cut -d= -f2 | tr -d '\r\n"')"
  python - "$KEY" "$URL" <<'PYEOF'
import json,sys,urllib.request
key,newurl=sys.argv[1],sys.argv[2]
tools={
 "tool_4801m0ncs38tf8t93f45jfj992dt":"check_spa_availability",
 "tool_6001m0ncs38vf73v1zbaa9p5vdfv":"book_spa_appointment",
 "tool_6301m0ncs38wewt865sh99v1qkm8":"check_room_availability",
 "tool_8101m0ncs38xe6tb29923tjt9045":"send_sms_summary",
 "tool_6001m0ntyt8xefgsx1e8mcqnsw1n":"transfer_to_simulated_handoff",
}
def api(m,path,b=None):
    req=urllib.request.Request("https://api.elevenlabs.io"+path,method=m)
    req.add_header('xi-api-key',key)
    data=json.dumps(b).encode() if b is not None else None
    if b is not None: req.add_header('Content-Type','application/json')
    try:
        with urllib.request.urlopen(req,data=data) as r: return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return e.code,e.read().decode()[:200]
for tid,name in tools.items():
    st,d=api('GET',f'/v1/convai/tools/{tid}')
    if st!=200: print(f"  ⚠️ {name}: GET {st}"); continue
    tc=d.get('tool_config',d)
    tc['api_schema']['url']=newurl+"/"+name
    st2,_=api('PATCH',f'/v1/convai/tools/{tid}',{'tool_config':tc})
    print(f"  {'✅' if st2 in (200,201) else '❌'} {name}: {st2}")
PYEOF
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
