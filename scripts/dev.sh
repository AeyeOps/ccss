#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Ensure no lingering textual console processes
pkill -f "textual console" >/dev/null 2>&1 || true

# Centralized log directory alongside ccss.log
LOG_DIR="${LOG_DIR:-$HOME/.cache/ccss/logs}"
mkdir -p "${LOG_DIR}"

# Optional: write Textual internal logs to file
TEXTUAL_LOG="${LOG_DIR}/textual.log"
TEXTUAL_LOG_LEVEL="${TEXTUAL_LOG_LEVEL:-debug}"
export TEXTUAL_LOG TEXTUAL_LOG_LEVEL

echo "Dev mode: running TUI with Textual dev tools (scripts/dev.sh)"
echo "Textual logs: $TEXTUAL_LOG"

# Run with Textual dev mode directly - no Python wrapper needed
PYTHONPATH=src TEXTUAL=dev uv run textual run --dev ccss.app:SessionSearchApp "$@"
