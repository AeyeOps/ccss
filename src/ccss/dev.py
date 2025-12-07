"""Run CCSS with Textual dev tools enabled."""

import shutil
import subprocess
import sys


def main() -> None:
    """Launch CCSS with Textual dev mode (F12 for CSS inspector).

    Runs 'textual run --dev ccss.app:SessionSearchApp'.
    """
    # Find the textual command in PATH
    textual_cmd = shutil.which("textual")
    if textual_cmd is None:
        # Fall back to running via Python
        textual_cmd = [sys.executable, "-m", "textual_dev.cli"]
    else:
        textual_cmd = [textual_cmd]

    subprocess.run(
        [*textual_cmd, "run", "--dev", "ccss.app:SessionSearchApp"],
        check=False,
    )


if __name__ == "__main__":
    main()
