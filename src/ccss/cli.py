"""CLI entry point using Typer."""

from __future__ import annotations

from typing import Annotated

import typer

from ccss import __version__
from ccss.app import run_app
from ccss.indexer import build_index, get_db_connection, get_index_stats, init_db

app = typer.Typer(
    name="ccss",
    help="Claude Code Session Search - Search your Claude Code session history",
    no_args_is_help=False,
)


@app.command()
def main(
    query: Annotated[
        str | None,
        typer.Argument(help="Initial search query"),
    ] = None,
    reindex: Annotated[
        bool,
        typer.Option("--reindex", "-r", help="Force reindex all sessions"),
    ] = False,
    stats: Annotated[
        bool,
        typer.Option("--stats", "-s", help="Show index statistics and exit"),
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", "-v", help="Show version and exit"),
    ] = False,
    dev: Annotated[
        bool,
        typer.Option("--dev", help="Dev mode: connects to 'textual console' for debugging"),
    ] = False,
) -> None:
    """Search Claude Code sessions with a TUI interface.

    Run without arguments to browse recent sessions.
    Provide a search query to start with results.
    """
    if version:
        typer.echo(f"ccss version {__version__}")
        raise typer.Exit()

    if dev:
        import os
        os.environ["TEXTUAL"] = "devtools"
        typer.echo("Dev mode: connect 'textual console' in another terminal")

    conn = get_db_connection()
    init_db(conn)

    if reindex:
        typer.echo("Reindexing all sessions...")
        indexed, _, removed = build_index(conn, force=True)
        typer.echo(f"Indexed: {indexed}, Removed: {removed}")

    if stats:
        index_stats = get_index_stats(conn)
        typer.echo(f"Sessions: {index_stats['sessions']}")
        typer.echo(f"Messages: {index_stats['messages']}")
        raise typer.Exit()

    conn.close()

    # Run the TUI
    run_app(initial_query=query or "")


if __name__ == "__main__":
    app()
