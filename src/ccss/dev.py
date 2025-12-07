"""Run CCSS with Textual dev tools enabled."""

import subprocess
import sys


def main() -> None:
    """Launch CCSS with Textual dev mode (F12 for CSS inspector)."""
    # Use -c to run the installed ccss command in dev mode
    subprocess.run(
        [
            sys.executable,
            "-m",
            "textual",
            "run",
            "--dev",
            "-c",
            "ccss",
        ],
        check=False,
    )


if __name__ == "__main__":
    main()
