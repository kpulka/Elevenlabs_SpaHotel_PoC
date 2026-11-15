#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# _common.sh — helpers shared by podman_start.sh, start_anna.sh and podman_stop.sh.
#
# SOURCED, never executed:   source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
# The caller is responsible for `set -euo pipefail`. Every function here is written
# so that a "nothing found" result is a return code the caller handles, not a crash.
# ─────────────────────────────────────────────────────────────────────────────

ANNA_HOSTS_FILE="/c/Windows/System32/drivers/etc/hosts"
ANNA_HOSTS_MARK="# ElevenLabs Anna - tunnel"

# env_get FILE KEY — prints the value of KEY from a dotenv-style file.
# The file is parsed, never sourced: values are taken literally, the same way
# `podman run --env-file` takes them. Returns 1 when the key is absent.
env_get() {
  local file="$1" key="$2" line k v
  [[ -f "$file" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
    k="${line%%=*}"
    v="${line#*=}"
    k="${k#export }"
    k="${k// /}"
    if [[ "$k" == "$key" ]]; then
      printf '%s' "$v"
      return 0
    fi
  done <"$file"
  return 1
}

# load_env_file FILE — exports every valid KEY=VALUE pair of FILE into the current shell.
# Used by start_anna.sh, which runs uvicorn directly and therefore needs the backend's
# variables (ANNA_WEBHOOK_SECRET, TELEGRAM_*, ...) in its own environment.
load_env_file() {
  local file="$1" line k v
  [[ -f "$file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
    k="${line%%=*}"
    v="${line#*=}"
    k="${k#export }"
    k="${k// /}"
    [[ "$k" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    export "$k=$v"
  done <"$file"
}

# require_webhook_secret ENV_FILE — refuses to continue unless ANNA_WEBHOOK_SECRET is set.
# Without the secret the tool endpoints accept any caller, and the public tunnel would
# expose them to the whole internet. Exits the script with status 1.
require_webhook_secret() {
  local env_file="$1" secret=""
  secret="${ANNA_WEBHOOK_SECRET:-}"
  if [[ -z "$secret" ]]; then
    secret="$(env_get "$env_file" ANNA_WEBHOOK_SECRET || true)"
  fi
  if [[ -z "$secret" ]]; then
    echo "❌ ANNA_WEBHOOK_SECRET is empty — NOT starting the public tunnel." >&2
    echo "   Without it the tool webhooks accept any request. Set a value in $env_file" >&2
    echo "   (for example: openssl rand -hex 32) and run the script again." >&2
    exit 1
  fi
}

# wait_for_tunnel_url LOG_FILE [TRIES] — polls the cloudflared log for the trycloudflare URL.
# Prints the URL and returns 0, or returns 1 after TRIES seconds.
wait_for_tunnel_url() {
  local log="$1" tries="${2:-40}" url="" i
  for ((i = 0; i < tries; i++)); do
    url="$(grep -aoE 'https://[a-z0-9-]+\.trycloudflare\.com' "$log" 2>/dev/null | head -1 || true)"
    if [[ -n "$url" ]]; then
      printf '%s' "$url"
      return 0
    fi
    sleep 1
  done
  return 1
}

# update_hosts_entry HOST — pins HOST to an IPv4 address in the Windows hosts file.
# The local router returns only AAAA records for trycloudflare hosts and this machine has
# no IPv6, so curl and browsers cannot connect without this entry. The address is taken from
# a public resolver (1.1.1.1), and the 1.1.1.1 line in nslookup's header is ignored.
# A failure here is a warning, not an error: the tunnel still works for anyone with DNS.
update_hosts_entry() {
  local host="$1" ip="" attempt
  for attempt in 1 2 3 4 5; do
    ip="$(nslookup "$host" 1.1.1.1 2>/dev/null | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^1\.1\.1\.1$' | tail -1 || true)"
    [[ -n "$ip" ]] && break
    sleep 3
  done
  if [[ -z "$ip" ]]; then
    echo "⚠️  no IP for $host — hosts entry skipped"
    return 0
  fi
  if [[ ! -f "$ANNA_HOSTS_FILE" ]]; then
    echo "⚠️  hosts file not found: $ANNA_HOSTS_FILE — hosts entry skipped"
    return 0
  fi
  cp "$ANNA_HOSTS_FILE" "$ANNA_HOSTS_FILE.bak" 2>/dev/null || true
  sed -i "/$ANNA_HOSTS_MARK/d; /${host}/d" "$ANNA_HOSTS_FILE" 2>/dev/null || true
  if printf "\n%s\n%s  %s\n" "$ANNA_HOSTS_MARK" "$ip" "$host" >>"$ANNA_HOSTS_FILE" 2>/dev/null; then
    echo "✅ hosts: $ip $host"
  else
    echo "⚠️  no permission to write the hosts file (run the terminal as administrator)"
  fi
}

# find_python — prints the first Python interpreter on PATH (python, py, python3); returns 1 if none.
find_python() {
  local candidate
  for candidate in python py python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

# stop_our_tunnels PORT — kills cloudflared processes that point at localhost:PORT.
# Only those: other tunnels on the machine are left alone. Windows-only (taskkill, CIM).
stop_our_tunnels() {
  local port="$1" pids="" pid
  pids="$(powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name like '%cloudflared%'\" | Where-Object { \$_.CommandLine -match 'localhost:$port' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r' || true)"
  for pid in $pids; do
    taskkill /F /PID "$pid" >/dev/null 2>&1 || true
    echo "  stopped cloudflared PID $pid"
  done
}
