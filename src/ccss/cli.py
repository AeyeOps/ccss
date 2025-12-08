"""CLI entry point using Typer."""

from __future__ import annotations

from typing import Annotated

import typer

from ccss.app import run_app

app = typer.Typer(
    name="ccss",
    help="Claude Code Session Search - TUI for searching session history",
    no_args_is_help=False,
)


@app.command()
def main(
    query: Annotated[
        str | None,
        typer.Argument(help="Initial search query"),
    ] = None,
) -> None:
    """Search Claude Code sessions with a TUI interface."""
    run_app(initial_query=query or "")


if __name__ == "__main__":
    app()
