#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SPEC_FILE="$ROOT_DIR/ccss.spec"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build"
OUTPUT_BINARY="$DIST_DIR/ccss"
INSTALL_DIR="/usr/local/bin"
INSTALL_PATH="$INSTALL_DIR/ccss"

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

# Ensure install directory exists
echo ""
echo ">>> Installing to $INSTALL_PATH"
if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "    Creating $INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
fi

# Copy binary (may need sudo for /usr/local/bin)
if [[ -w "$INSTALL_DIR" ]]; then
    cp "$OUTPUT_BINARY" "$INSTALL_PATH"
    chmod 755 "$INSTALL_PATH"
else
    sudo cp "$OUTPUT_BINARY" "$INSTALL_PATH"
    sudo chmod 755 "$INSTALL_PATH"
fi

# Ensure /usr/local/bin is in PATH via shell rc file
PATH_LINE='export PATH="/usr/local/bin:$PATH"'

# Detect shell and set appropriate rc file
case "$(basename "$SHELL")" in
    zsh)
        RC_FILE="$HOME/.zshrc"
        ;;
    bash)
        RC_FILE="$HOME/.bashrc"
        ;;
    *)
        # Fallback: check which rc files exist
        if [[ -f "$HOME/.zshrc" ]]; then
            RC_FILE="$HOME/.zshrc"
        elif [[ -f "$HOME/.bashrc" ]]; then
            RC_FILE="$HOME/.bashrc"
        else
            RC_FILE="$HOME/.profile"
        fi
        ;;
esac

RC_NAME="$(basename "$RC_FILE")"
PATH_ADDED=false

if [[ -f "$RC_FILE" ]]; then
    # Check if /usr/local/bin is already referenced in PATH
    if grep -qF '/usr/local/bin' "$RC_FILE" 2>/dev/null; then
        echo "    /usr/local/bin already in $RC_NAME PATH"
    else
        echo "    Adding /usr/local/bin to $RC_NAME PATH"
        echo "" >> "$RC_FILE"
        echo "# Added by ccss build script" >> "$RC_FILE"
        echo "$PATH_LINE" >> "$RC_FILE"
        PATH_ADDED=true
    fi
else
    echo "    Creating $RC_NAME with PATH"
    echo "# Added by ccss build script" > "$RC_FILE"
    echo "$PATH_LINE" >> "$RC_FILE"
    PATH_ADDED=true
fi

# If we modified the rc file, tell the user to reload
if [[ "$PATH_ADDED" == true ]]; then
    echo ""
    echo "    PATH updated. To use ccss immediately, run:"
    echo "        source ~/$RC_NAME"
    echo "    Or restart your terminal."
fi

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
