#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SPEC_FILE="$ROOT_DIR/ccss.spec"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build"
OUTPUT_BINARY="$DIST_DIR/ccss"
INSTALL_PATH="/opt/bin/ccss"

echo "========================================"
echo "CCSS PyInstaller Build"
echo "========================================"

# Verify spec file exists
if [[ ! -f "$SPEC_FILE" ]]; then
    echo "ERROR: Spec file not found: $SPEC_FILE"
    exit 1
fi

# Clean previous builds
if [[ -d "$BUILD_DIR" ]]; then
    echo "Cleaning $BUILD_DIR"
    rm -rf "$BUILD_DIR"
fi
if [[ -d "$DIST_DIR" ]]; then
    echo "Cleaning $DIST_DIR"
    rm -rf "$DIST_DIR"
fi

# Run PyInstaller via uv
echo ""
echo ">>> Running PyInstaller"
echo "    uv run pyinstaller $SPEC_FILE --clean --noconfirm"
uv run pyinstaller "$SPEC_FILE" --clean --noconfirm

# Verify output
if [[ ! -f "$OUTPUT_BINARY" ]]; then
    echo ""
    echo "ERROR: Expected binary not found: $OUTPUT_BINARY"
    exit 1
fi

# Copy to /opt/bin
echo ""
echo ">>> Installing to $INSTALL_PATH"
cp "$OUTPUT_BINARY" "$INSTALL_PATH"
chmod 755 "$INSTALL_PATH"

# Summary - cross-platform stat for size
if stat --version >/dev/null 2>&1; then
    # GNU stat (Linux)
    BINARY_SIZE=$(stat --printf="%s" "$OUTPUT_BINARY")
else
    # BSD stat (macOS)
    BINARY_SIZE=$(stat -f%z "$OUTPUT_BINARY")
fi
BINARY_SIZE_MB=$(awk "BEGIN {printf \"%.1f\", $BINARY_SIZE / 1048576}")

echo ""
echo "========================================"
echo "BUILD SUCCESSFUL"
echo "========================================"
echo "Binary: $OUTPUT_BINARY"
echo "Size:   ${BINARY_SIZE_MB} MB"
echo "Installed: $INSTALL_PATH"
echo ""
echo "Run with: ccss"
