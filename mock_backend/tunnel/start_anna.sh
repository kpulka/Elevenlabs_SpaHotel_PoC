#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start_anna.sh — start the mock backend and public tunnel for the "Anna" agent
# Bukowy Dwór health resort (ElevenLabs PoC)
#
# What it does:
#  1. Starts the mock backend (uvicorn) on a free port (default 8011).
#  2. Starts a cloudflared quick tunnel (trycloudflare) pointing at the backend.
#  3. Extracts the public tunnel URL from the log.
#  4. Points the agent's 5 ElevenLabs webhook tools at that URL.
#  5. Saves the state (backend_pid, tunnel_pid, url) to tunnel/state.json.
#
# The tunnel URL changes on every restart, so this script re-points the
# webhook tools to the new URL automatically.
#
# Usage:
#   ./start_anna.sh            # default port 8011
#   ./start_anna.sh 8012       # custom port
#
# Optional environment overrides:
#   CLOUDFLARED   path to the cloudflared binary
#   HOSTS_FILE    path to the hosts file (Windows default is used if unset)
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../.."
BACKEND_DIR="$PROJECT_ROOT/mock_backend"
TUNNEL_DIR="$BACKEND_DIR/tunnel"
STATE_FILE="$TUNNEL_DIR/state.json"
PORT="${1:-8011}"
HOSTS_FILE="${HOSTS_FILE:-/c/Windows/System32/drivers/etc/hosts}"
HOSTS_MARK="# ElevenLabs Anna - tunnel"

# ── locate cloudflared ──────────────────────────────────────────────────────
CLOUDFLARED="${CLOUDFLARED:-}"
if [[ -z "$CLOUDFLARED" ]]; then
  for c in "$TUNNEL_DIR/cloudflared.exe" "/c/Program Files (x86)/cloudflared/cloudflared" "$(command -v cloudflared 2>/dev/null)"; do
    if [[ -n "$c" && -f "$c" ]]; then CLOUDFLARED="$c"; break; fi
  done
fi
if [[ -z "$CLOUDFLARED" ]]; then
  echo "[error] cloudflared not found. Place it at $TUNNEL_DIR/cloudflared.exe or set CLOUDFLARED."
  exit 1
fi
echo "cloudflared: $CLOUDFLARED"
mkdir -p "$TUNNEL_DIR"

# ── backend: start only if it is not already running ───────────────────────
if curl -s -m 5 "http://127.0.0.1:$PORT/" | grep -q '"status":"OK"'; then
  echo "[info] backend already running on :$PORT (skipping start)"
  BACKEND_PID="already-running"
else
  echo "[start] backend on :$PORT"
  (cd "$BACKEND_DIR" && python -m uvicorn main:app --host 0.0.0.0 --port "$PORT" >"$TUNNEL_DIR/backend.log" 2>&1) &
  BACKEND_PID=$!
  ok=0
  for i in $(seq 1 15); do
    if curl -s -m 2 "http://127.0.0.1:$PORT/" | grep -q '"status":"OK"'; then ok=1; break; fi
    sleep 1
  done
  if [[ $ok != 1 ]]; then
    echo "[error] backend did not start (is port $PORT in use by another application?). See $TUNNEL_DIR/backend.log"
    exit 1
  fi
  echo "[ok] backend on :$PORT (pid $BACKEND_PID)"
fi

# ── tunnel: always start a new trycloudflare URL (a new address is acceptable) ─
echo "[start] tunnel -> http://localhost:$PORT"
"$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate >"$TUNNEL_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!

URL=""
for i in $(seq 1 30); do
  URL="$(grep -aoE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_DIR/tunnel.log" 2>/dev/null | head -1 || true)"
  [[ -n "$URL" ]] && break
  sleep 1
done
if [[ -z "$URL" ]]; then
  echo "[error] could not read the tunnel URL. Check $TUNNEL_DIR/tunnel.log"
  exit 1
fi
echo "[ok] tunnel URL: $URL"

# ── save state ──────────────────────────────────────────────────────────────
cat >"$STATE_FILE" <<EOF
{"port": $PORT, "backend_pid": "$BACKEND_PID", "tunnel_pid": $TUNNEL_PID, "url": "$URL"}
EOF
echo "[ok] state saved: $STATE_FILE"

# ── update the hosts file entry ─────────────────────────────────────────────
# The local router's DNS returns only IPv6 (AAAA) records for trycloudflare, and
# this machine has no IPv6, so curl/browsers cannot connect. A hosts entry forces IPv4.
update_hosts() {
  local host="$1"
  # Resolve an IPv4 address through a public resolver (1.1.1.1). On Windows the
  # answer appears in the "Addresses:" block; the "Address: 1.1.1.1" header
  # (the resolver's own IP) is skipped.
  # DNS for a new trycloudflare host can take a few seconds to propagate, so retry.
  local ip=""
  for attempt in 1 2 3 4 5; do
    ip="$(nslookup "$host" 1.1.1.1 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^1\.1\.1\.1$' | tail -1)"
    [[ -n "$ip" ]] && break
    sleep 3
  done
  if [[ -z "$ip" ]]; then
    echo "[warn] could not resolve an IP for $host, skipping hosts entry"
    return
  fi
  # Remove the old entry (marker line and host line), then append the new one.
  if [[ -f "$HOSTS_FILE" ]]; then
    cp "$HOSTS_FILE" "$HOSTS_FILE.bak" 2>/dev/null || true
    sed -i "/$HOSTS_MARK/d; /${host}/d" "$HOSTS_FILE" 2>/dev/null || true
    printf "\n%s\n%s  %s\n" "$HOSTS_MARK" "$ip" "$host" >>"$HOSTS_FILE" 2>/dev/null && \
      echo "[ok] hosts updated: $ip $host" || \
      echo "[warn] no permission to write the hosts file (run as administrator)"
  fi
}
update_hosts "$(echo "$URL" | sed 's|https://||; s|/||')"

# ── update the ElevenLabs agent webhooks ────────────────────────────────────
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
    if st!=200: print(f"  [warn] {name}: GET {st}"); continue
    tc=d.get('tool_config',d)
    tc['api_schema']['url']=newurl+"/"+name
    st2,d2=api('PATCH',f'/v1/convai/tools/{tid}',{'tool_config':tc})
    print(f"  [{'ok' if st2 in (200,201) else 'error'}] {name}: {st2}")
PYEOF
  echo "[ok] agent webhooks updated to $URL"
else
  echo "[warn] no ELEVENLABS_API_KEY in $ENV_FILE, agent webhooks NOT updated"
fi

echo
echo "============================================================"
echo "  Anna is ready."
echo "  Backend : http://localhost:$PORT"
echo "  URL     : $URL"
echo "  Restart : run ./start_anna.sh again"
echo "============================================================"
