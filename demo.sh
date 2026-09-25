#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-5173}"

if [ "$API_PORT" = "$UI_PORT" ]; then
  printf '%s\n' "API_PORT and UI_PORT must differ" >&2
  exit 1
fi

if [ ! -d "$ROOT/ui/node_modules" ]; then
  printf '%s\n' "UI dependencies are missing; run: npm --prefix ui ci" >&2
  exit 1
fi

if curl -fsS --max-time 1 "http://127.0.0.1:$API_PORT/api/health" >/dev/null 2>&1; then
  printf '%s\n' "API port $API_PORT is already serving; stop it or choose another port" >&2
  exit 1
fi
if curl -fsS --max-time 1 "http://127.0.0.1:$UI_PORT/" >/dev/null 2>&1; then
  printf '%s\n' "UI port $UI_PORT is already serving; stop it or choose another port" >&2
  exit 1
fi

API_PID=""
UI_PID=""
cleanup() {
  trap - INT TERM EXIT
  [ -z "$API_PID" ] || kill "$API_PID" 2>/dev/null || true
  [ -z "$UI_PID" ] || kill "$UI_PID" 2>/dev/null || true
  wait "$API_PID" 2>/dev/null || true
  wait "$UI_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

printf '%s\n' "Starting API on http://127.0.0.1:$API_PORT"
(cd "$ROOT" && exec uv run uvicorn api.app:app --host 127.0.0.1 --port "$API_PORT") &
API_PID=$!

printf '%s\n' "Starting dashboard on http://127.0.0.1:$UI_PORT"
(cd "$ROOT/ui" && API_PORT="$API_PORT" exec npm run dev -- --host 127.0.0.1 --strictPort --port "$UI_PORT") &
UI_PID=$!

for attempt in $(seq 1 60); do
  if curl -fsS --max-time 1 "http://127.0.0.1:$API_PORT/api/health" >/dev/null 2>&1 \
    && curl -fsS --max-time 1 "http://127.0.0.1:$UI_PORT/" >/dev/null 2>&1; then
    printf '%s\n' "Demo ready. Press Ctrl+C to stop."
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null || ! kill -0 "$UI_PID" 2>/dev/null; then
    printf '%s\n' "A local service exited before becoming ready" >&2
    exit 1
  fi
  sleep 1
  if [ "$attempt" = "60" ]; then
    printf '%s\n' "Demo did not become ready within 60 seconds" >&2
    exit 1
  fi
done

wait "$API_PID" "$UI_PID"
