#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="${LOG_DIR:-$HOME/.cache/ccss/logs}"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/textual-console.log}"
echo "Running textual console and logging to ${LOG_FILE} (scripts/console_logs.sh)..."

uv run textual console >>"${LOG_FILE}" 2>&1
