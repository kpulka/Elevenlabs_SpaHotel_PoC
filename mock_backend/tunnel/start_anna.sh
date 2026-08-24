#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start_anna.sh — stały startowy mock backend + tunnel dla agenta "Anna"
# Uzdrowisko Bukowy Dwór (ElevenLabs PoC)
#
# Co robi:
#  1. Uruchamia mock backend (uvicorn) na wolnym porcie (domyślnie 8011).
#  2. Uruchamia cloudflared tunnel (trycloudflare) wskazujący na backend.
#  3. Wyłapuje publiczny URL tunelu z logu.
#  4. Aktualizuje 5 narzędzi webhook agenta ElevenLabs na ten URL.
#  5. Zapisuje stan (backend_pid, tunnel_pid, url) do tunnel/state.json.
#
# Rozwiązuje awarię webhooków po restarcie (trycloudflare zmienia URL):
#  po odpaleniu skrypt narzędzia same wracają na żywy URL.
#
# Użycie:
#   ./start_anna.sh            # domyślny port 8011
#   ./start_anna.sh 8012       # inny port
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../.."
BACKEND_DIR="$PROJECT_ROOT/mock_backend"
TUNNEL_DIR="$BACKEND_DIR/tunnel"
STATE_FILE="$TUNNEL_DIR/state.json"
PORT="${1:-8011}"

# ── znajdź cloudflared ──────────────────────────────────────────────────────
CLOUDFLARED=""
for c in "$TUNNEL_DIR/cloudflared.exe" "/c/Program Files (x86)/cloudflared/cloudflared" "$(command -v cloudflared 2>/dev/null)"; do
  if [[ -n "$c" && -f "$c" ]]; then CLOUDFLARED="$c"; break; fi
done
if [[ -z "$CLOUDFLARED" ]]; then
  echo "❌ cloudflared nie znaleziony. Umieść go w $TUNNEL_DIR/cloudflared.exe"
  exit 1
fi
echo "cloudflared: $CLOUDFLARED"
mkdir -p "$TUNNEL_DIR"

# ── backend: start tylko jeśli nie działa ───────────────────────────────────
if curl -s -m 5 "http://127.0.0.1:$PORT/" | grep -q '"status":"OK"'; then
  echo "ℹ️  backend już działa na :$PORT (pomijam start)"
  BACKEND_PID="already-running"
else
  echo "🚀 startuję backend na :$PORT"
  (cd "$BACKEND_DIR" && python -m uvicorn main:app --host 0.0.0.0 --port "$PORT" >"$TUNNEL_DIR/backend.log" 2>&1) &
  BACKEND_PID=$!
  ok=0
  for i in $(seq 1 15); do
    if curl -s -m 2 "http://127.0.0.1:$PORT/" | grep -q '"status":"OK"'; then ok=1; break; fi
    sleep 1
  done
  if [[ $ok != 1 ]]; then
    echo "❌ backend nie wystartował (port $PORT zajęty przez aplikację?). Zobacz $TUNNEL_DIR/backend.log"
    exit 1
  fi
  echo "✅ backend na :$PORT (pid $BACKEND_PID)"
fi

# ── tunel: start (zawsze nowy trycloudflare URL; nowy adres akceptowalny) ──
echo "🚀 startuję tunel -> http://localhost:$PORT"
"$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate >"$TUNNEL_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!

URL=""
for i in $(seq 1 30); do
  URL="$(grep -aoE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_DIR/tunnel.log" 2>/dev/null | head -1 || true)"
  [[ -n "$URL" ]] && break
  sleep 1
done
if [[ -z "$URL" ]]; then
  echo "❌ nie udało się wyłapać URL tunelu — sprawdź $TUNNEL_DIR/tunnel.log"
  exit 1
fi
echo "✅ URL tunelu: $URL"

# ── zapisz stan ─────────────────────────────────────────────────────────────
cat >"$STATE_FILE" <<EOF
{"port": $PORT, "backend_pid": "$BACKEND_PID", "tunnel_pid": $TUNNEL_PID, "url": "$URL"}
EOF
echo "📄 stan zapisany: $STATE_FILE"

# ── aktualizacja wpisu w hosts (omija problem z routerem DNS: brak A/IPv4) ──
# Lokalny resolver (router) zwraca dla trycloudflare tylko IPv6 (AAAA), a maszyna
# nie ma IPv6 → curl/przeglądarka nie mogą się połączyć. Wpis w hosts wymusza IPv4.
HOSTS_FILE="/c/Windows/System32/drivers/etc/hosts"
HOSTS_MARK="# ElevenLabs Anna - tunnel"
update_hosts() {
  local host="$1"
  # wyciągnij IPv4 z publicznego resolwera (nslookup 1.1.1.1).
  # Windows: adresy odpowiedzi w bloku "Addresses:" (linie z tabulacją);
  # pomijamy nagłówek "Address: 1.1.1.1" (IP samego resolwera).
  # DNS trycloudflare propaguje się kilka sekund — próbuj z retry.
  local ip=""
  for attempt in 1 2 3 4 5; do
    ip="$(nslookup "$host" 1.1.1.1 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^1\.1\.1\.1$' | tail -1)"
    [[ -n "$ip" ]] && break
    sleep 3
  done
  if [[ -z "$ip" ]]; then
    echo "⚠️  nie udało się wyciągnąć IP dla $host — pomijam wpis w hosts"
    return
  fi
  # usuń stary wpis (marker + poprzednia linia), dopisz nowy
  if [[ -f "$HOSTS_FILE" ]]; then
    cp "$HOSTS_FILE" "$HOSTS_FILE.bak" 2>/dev/null || true
    sed -i "/$HOSTS_MARK/d; /${host}/d" "$HOSTS_FILE" 2>/dev/null || true
    printf "\n%s\n%s  %s\n" "$HOSTS_MARK" "$ip" "$host" >>"$HOSTS_FILE" 2>/dev/null && \
      echo "✅ hosts zaktualizowany: $ip $host" || \
      echo "⚠️  brak uprawnień do zapisu hosts (uruchom jako admin)"
  fi
}
update_hosts "$(echo "$URL" | sed 's|https://||; s|/||')"

# ── aktualizacja webhooków agenta ElevenLabs ───────────────────────────────
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
    st2,d2=api('PATCH',f'/v1/convai/tools/{tid}',{'tool_config':tc})
    print(f"  {'✅' if st2 in (200,201) else '❌'} {name}: {st2}")
PYEOF
  echo "✅ webhooki agenta zaktualizowane na $URL"
else
  echo "⚠️  brak klucza w $ENV_FILE — NIE zaktualizowano webhooków."
fi

echo
echo "============================================================"
echo "  Anna ready."
echo "  Backend : http://localhost:$PORT"
echo "  URL     : $URL"
echo "  Restart : ponownie ./start_anna.sh"
echo "============================================================"