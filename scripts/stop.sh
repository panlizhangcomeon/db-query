#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-5174}"
LOG_DIR="$ROOT/logs"

kill_port_listeners() {
  local port="$1"
  local label="$2"
  local pids
  pids="$(lsof -ti ":$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    echo "${label} (端口 ${port}): 无监听进程"
    return 0
  fi
  echo "${label} (端口 ${port}): 结束 PID ${pids//$'\n'/ }"
  kill $pids 2>/dev/null || true
  sleep 0.5
  pids="$(lsof -ti ":$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    kill -9 $pids 2>/dev/null || true
  fi
}

kill_port_listeners "$BACKEND_PORT" "后端"
kill_port_listeners "$FRONTEND_PORT" "前端"

rm -f "$LOG_DIR/backend.pid" "$LOG_DIR/frontend.pid" 2>/dev/null || true
echo "已停止。"
