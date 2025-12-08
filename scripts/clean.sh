#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Cleaning build artifacts and caches (scripts/clean.sh)..."

# Uninstall any installed copy of ccss to avoid stale packages shadowing local source
echo "Ensuring no installed ccss package is shadowing local sources..."
CCSS_PATH="$(uv run python - <<'PY' 2>/dev/null || true
from importlib.util import find_spec
spec = find_spec('ccss')
print(spec.origin if spec and spec.origin else '')
PY
)"
if [ -z "$CCSS_PATH" ]; then
  echo "ccss not importable; nothing to uninstall."
elif [[ "$CCSS_PATH" == "$ROOT_DIR"/src/ccss/* ]]; then
  echo "ccss resolves to local source ($CCSS_PATH); skipping uninstall."
else
  echo "Found installed ccss at $CCSS_PATH; uninstalling via uv pip uninstall -y ccss..."
  uv pip uninstall -y ccss >/dev/null 2>&1 || true
fi

rm -rf \
  "$ROOT_DIR/build" \
  "$ROOT_DIR/dist" \
  "$ROOT_DIR/.ruff_cache" \
  "$ROOT_DIR/.mypy_cache" \
  "$ROOT_DIR/.pytest_cache" \
  "$ROOT_DIR/.coverage" \
  "$ROOT_DIR/.ccss" \
  "$ROOT_DIR"/*.egg-info

# Remove Python bytecode and __pycache__ directories
find "$ROOT_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$ROOT_DIR" -type f -name "*.pyc" -delete -o -name "*.pyo" -delete
# Optional: prune uv cache to avoid stale wheels (enable with CACHE=1)
if [ "${CACHE:-0}" -eq 1 ]; then
  echo "Pruning uv cache (CACHE=1)..."
  uv cache clean >/dev/null 2>&1 || true
fi

echo "Clean complete."
