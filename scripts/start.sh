#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-5174}"

port_in_use() {
  lsof -i ":$1" -sTCP:LISTEN -t >/dev/null 2>&1
}

if port_in_use "$BACKEND_PORT"; then
  echo "端口 ${BACKEND_PORT} 已被占用，请先执行 ./scripts/stop.sh 或更换 BACKEND_PORT。"
  exit 1
fi
if port_in_use "$FRONTEND_PORT"; then
  echo "端口 ${FRONTEND_PORT} 已被占用，请先执行 ./scripts/stop.sh 或更换 FRONTEND_PORT。"
  exit 1
fi

BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

if [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  PY="$BACKEND_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "未找到 Python，请在 backend 目录创建 .venv 或安装 python3。"
  exit 1
fi

echo "启动后端 (uvicorn) http://127.0.0.1:${BACKEND_PORT} ..."
(
  cd "$BACKEND_DIR"
  exec "$PY" -m uvicorn src.main:app --host 127.0.0.1 --port "$BACKEND_PORT"
) >"$LOG_DIR/backend.log" 2>&1 &
echo $! >"$LOG_DIR/backend.pid"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "正在安装前端依赖 (npm install) ..."
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "启动前端 (Vite) http://127.0.0.1:${FRONTEND_PORT} ..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
) >"$LOG_DIR/frontend.log" 2>&1 &
echo $! >"$LOG_DIR/frontend.pid"

echo "已启动。日志: $LOG_DIR/backend.log 与 $LOG_DIR/frontend.log"
echo "停止服务: $ROOT/scripts/stop.sh"
