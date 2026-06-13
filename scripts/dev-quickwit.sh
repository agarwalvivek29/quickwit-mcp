#!/usr/bin/env bash
#
# dev-quickwit.sh — one-command local Quickwit for developing quickwit-mcp.
#
# Spins up a throwaway Quickwit in Docker, creates a `logs-demo` index and seeds
# it with sample logs, so the MCP server (and the REST client) can be exercised
# against real data. Everything is self-contained — no extra fixture files.
#
# Usage:
#   scripts/dev-quickwit.sh up       # start Quickwit + create index + seed logs
#   scripts/dev-quickwit.sh down     # stop and remove the container
#   scripts/dev-quickwit.sh reset    # down + up (clean slate)
#   scripts/dev-quickwit.sh status   # is it reachable? how many docs?
#
# Override via env:
#   QW_VERSION   Quickwit image tag        (default: 0.8.2)
#   QW_PORT      host port for the REST API (default: 7280)
#   QW_INDEX     demo index id             (default: logs-demo)
#   QW_CONTAINER docker container name      (default: quickwit-mcp-dev)
#
set -euo pipefail

QW_VERSION="${QW_VERSION:-0.8.2}"
QW_PORT="${QW_PORT:-7280}"
QW_INDEX="${QW_INDEX:-logs-demo}"
QW_CONTAINER="${QW_CONTAINER:-quickwit-mcp-dev}"
QW_IMAGE="quickwit/quickwit:${QW_VERSION}"
BASE_URL="http://localhost:${QW_PORT}"

info() { printf '\033[0;36m==>\033[0m %s\n' "$*"; }
err() { printf '\033[0;31merror:\033[0m %s\n' "$*" >&2; }

require_docker() {
  command -v docker >/dev/null 2>&1 || { err "docker is required but not found"; exit 1; }
  docker info >/dev/null 2>&1 || { err "docker daemon is not running"; exit 1; }
}

wait_for_ready() {
  info "waiting for Quickwit on ${BASE_URL} ..."
  for _ in $(seq 1 60); do
    if curl -fsS -m 2 "${BASE_URL}/api/v1/version" >/dev/null 2>&1; then
      info "Quickwit is up."
      return 0
    fi
    sleep 1
  done
  err "Quickwit did not become ready in time. Check: docker logs ${QW_CONTAINER}"
  exit 1
}

index_exists() {
  curl -fsS -m 5 "${BASE_URL}/api/v1/indexes/${QW_INDEX}" >/dev/null 2>&1
}

create_index() {
  info "creating index '${QW_INDEX}' ..."
  curl -fsS -X POST "${BASE_URL}/api/v1/indexes" \
    -H 'Content-Type: application/json' \
    --data-binary @- >/dev/null <<JSON
{
  "version": "0.8",
  "index_id": "${QW_INDEX}",
  "doc_mapping": {
    "field_mappings": [
      {"name": "timestamp", "type": "datetime", "input_formats": ["unix_timestamp"], "fast": true, "fast_precision": "seconds"},
      {"name": "level", "type": "text", "tokenizer": "raw", "fast": true},
      {"name": "service", "type": "text", "tokenizer": "raw", "fast": true},
      {"name": "message", "type": "text", "tokenizer": "default", "record": "position"}
    ],
    "timestamp_field": "timestamp"
  }
}
JSON
  info "index created."
}

seed_logs() {
  info "ingesting sample logs ..."
  curl -fsS -X POST "${BASE_URL}/api/v1/${QW_INDEX}/ingest?commit=force" \
    -H 'Content-Type: application/x-ndjson' \
    --data-binary @- >/dev/null <<'NDJSON'
{"timestamp": 1718200000, "level": "INFO", "service": "payment", "message": "charge succeeded for user 42"}
{"timestamp": 1718200060, "level": "ERROR", "service": "payment", "message": "charge failed: card declined for user 99"}
{"timestamp": 1718200120, "level": "WARN", "service": "auth", "message": "token nearing expiry for session abc"}
{"timestamp": 1718200180, "level": "ERROR", "service": "auth", "message": "login failed: invalid password"}
{"timestamp": 1718200240, "level": "INFO", "service": "gateway", "message": "request routed to payment upstream"}
{"timestamp": 1718200300, "level": "ERROR", "service": "gateway", "message": "upstream timeout calling payment service"}
NDJSON
  info "seeded 6 sample log lines."
}

cmd_up() {
  require_docker
  if docker ps -a --format '{{.Names}}' | grep -qx "${QW_CONTAINER}"; then
    info "container '${QW_CONTAINER}' exists — (re)starting it."
    docker start "${QW_CONTAINER}" >/dev/null
  else
    info "starting ${QW_IMAGE} as '${QW_CONTAINER}' on :${QW_PORT} ..."
    docker run -d --name "${QW_CONTAINER}" -p "${QW_PORT}:7280" "${QW_IMAGE}" run >/dev/null
  fi
  wait_for_ready
  if index_exists; then
    info "index '${QW_INDEX}' already exists — leaving data as-is (use 'reset' for a clean slate)."
  else
    create_index
    seed_logs
  fi
  cat <<EOF

Quickwit is ready with index '${QW_INDEX}'.

  export QW_BASE_URL=${BASE_URL}

Try it:
  curl -s -X POST ${BASE_URL}/api/v1/${QW_INDEX}/search \\
    -H 'Content-Type: application/json' -d '{"query":"level:ERROR","max_hits":5}'

Tear down with: scripts/dev-quickwit.sh down
EOF
}

cmd_down() {
  require_docker
  info "removing container '${QW_CONTAINER}' ..."
  docker rm -f "${QW_CONTAINER}" >/dev/null 2>&1 || info "nothing to remove."
  info "done."
}

cmd_reset() {
  cmd_down
  cmd_up
}

cmd_status() {
  if ! curl -fsS -m 2 "${BASE_URL}/api/v1/version" >/dev/null 2>&1; then
    err "Quickwit is not reachable at ${BASE_URL}"
    exit 1
  fi
  info "Quickwit is reachable at ${BASE_URL}"
  if index_exists; then
    docs=$(curl -fsS "${BASE_URL}/api/v1/indexes/${QW_INDEX}/describe" \
      | sed -n 's/.*"num_published_docs"[: ]*\([0-9]*\).*/\1/p')
    info "index '${QW_INDEX}' present (num_published_docs=${docs:-unknown})"
  else
    info "index '${QW_INDEX}' does not exist yet — run 'up'."
  fi
}

usage() {
  sed -n '3,20p' "$0"
}

case "${1:-}" in
  up) cmd_up ;;
  down) cmd_down ;;
  reset) cmd_reset ;;
  status) cmd_status ;;
  *) usage; exit 1 ;;
esac
