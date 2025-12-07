#!/usr/bin/env python3
"""Build standalone CCSS executable for Ubuntu using PyInstaller."""

import shutil
import subprocess
import sys
from pathlib import Path

# Project root (build.py -> scripts/ -> ccss/ -> src/ -> project_root/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SPEC_FILE = PROJECT_ROOT / "ccss.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
OUTPUT_BINARY = DIST_DIR / "ccss"
INSTALL_PATH = Path("/opt/bin/ccss")


def run_command(cmd: list[str], description: str) -> None:
    """Run a command, fail on error."""
    print(f"\n>>> {description}")
    print(f"    {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"\nFAILED: {description}")
        sys.exit(result.returncode)


def main() -> None:
    """Build CCSS standalone executable."""
    print("=" * 60)
    print("CCSS PyInstaller Build")
    print("=" * 60)

    # Verify spec file exists
    if not SPEC_FILE.exists():
        print(f"ERROR: Spec file not found: {SPEC_FILE}")
        sys.exit(1)

    # Clean previous builds
    if BUILD_DIR.exists():
        print(f"\nCleaning {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        print(f"Cleaning {DIST_DIR}")
        shutil.rmtree(DIST_DIR)

    # Run PyInstaller
    run_command(
        ["pyinstaller", str(SPEC_FILE), "--clean", "--noconfirm"],
        "Running PyInstaller",
    )

    # Verify output
    if not OUTPUT_BINARY.exists():
        print(f"\nERROR: Expected binary not found: {OUTPUT_BINARY}")
        sys.exit(1)

    # Copy to /opt/bin
    print(f"\n>>> Installing to {INSTALL_PATH}")
    shutil.copy2(OUTPUT_BINARY, INSTALL_PATH)
    INSTALL_PATH.chmod(0o755)

    # Summary
    binary_size = OUTPUT_BINARY.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL")
    print("=" * 60)
    print(f"Binary: {OUTPUT_BINARY}")
    print(f"Size:   {binary_size:.1f} MB")
    print(f"Installed: {INSTALL_PATH}")
    print("\nRun with: ccss")


if __name__ == "__main__":
    main()
