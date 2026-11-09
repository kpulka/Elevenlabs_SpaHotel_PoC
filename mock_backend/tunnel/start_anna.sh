#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start_anna.sh — stały startowy mock backend + tunnel dla agenta "Anna"
# Uzdrowisko Bukowy Dwór (ElevenLabs PoC)
#
# Co robi:
#  1. Uruchamia mock backend (uvicorn) na wolnym porcie (domyślnie 8011).
#  2. Uruchamia cloudflared tunnel (trycloudflare) wskazujący na backend.
#  3. Wyłapuje publiczny URL tunelu z logu.
#  4. Aktualizuje 7 narzędzi webhook agenta ElevenLabs na ten URL
#     (wspólny skrypt sync_agent_tools.py — szuka narzędzi po nazwie).
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
PYTHON_BIN="$(command -v python || command -v py || command -v python3 || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "❌ brak interpretera Python w PATH (python/py/python3). Zainstaluj Python albo dodaj go do PATH."
  exit 1
fi

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
  # PYTHON_BIN, nie literalne "python" — autostart o logowaniu bywa bez Pythona w PATH.
  (cd "$BACKEND_DIR" && "$PYTHON_BIN" -m uvicorn main:app --host 0.0.0.0 --port "$PORT" >"$TUNNEL_DIR/backend.log" 2>&1) &
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

# ── aktualizacja webhooków agenta ElevenLabs (jeden wspólny skrypt) ───────
ENV_FILE="$PROJECT_ROOT/frontend/.env.local"
if [[ -f "$ENV_FILE" ]] && grep -q 'ELEVENLABS_API_KEY=' "$ENV_FILE"; then
  if [[ -z "$PYTHON_BIN" ]]; then
    echo "⚠️  brak interpretera python — NIE zaktualizowano webhooków."
  elif "$PYTHON_BIN" "$TUNNEL_DIR/sync_agent_tools.py" --base-url "$URL"; then
    echo "✅ webhooki agenta zaktualizowane na $URL"
  else
    echo "❌ nie wszystkie webhooki udało się zaktualizować — patrz komunikaty powyżej"
  fi
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