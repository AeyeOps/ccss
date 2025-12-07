"""Search engine using SQLite FTS5."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class SearchResult:
    """A search result with session info and snippet."""

    session_id: str
    project_path: str
    file_path: str
    first_timestamp: str
    message_count: int
    snippet: str
    rank: float
    # v2 fields
    cwd: str | None = None
    git_branch: str | None = None
    version: str | None = None
    last_timestamp: str | None = None
    is_agent: bool = False
    user_turns: int = 0
    assistant_turns: int = 0
    tool_use_count: int = 0
    total_tokens_est: int = 0

    @property
    def display_date(self) -> str:
        """Format the timestamp for display."""
        if not self.first_timestamp:
            return "Unknown"
        try:
            dt = datetime.fromisoformat(self.first_timestamp.replace("Z", "+00:00"))
            return dt.strftime("%b %d")
        except (ValueError, AttributeError):
            return "Unknown"

    @property
    def display_project(self) -> str:
        """Format the project path for display."""
        # Convert -opt-foo-bar to /opt/foo/bar
        if self.project_path.startswith("-"):
            return "/" + self.project_path[1:].replace("-", "/")
        return self.project_path

    @property
    def duration_seconds(self) -> int | None:
        """Calculate duration in seconds from timestamps."""
        if not self.first_timestamp or not self.last_timestamp:
            return None
        try:
            start = datetime.fromisoformat(self.first_timestamp.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.last_timestamp.replace("Z", "+00:00"))
            return max(0, int((end - start).total_seconds()))
        except (ValueError, AttributeError):
            return None

    @property
    def display_duration(self) -> str:
        """Format duration for display."""
        seconds = self.duration_seconds
        if seconds is None:
            return "Unknown"
        if seconds == 0:
            return "0s"
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes else f"{hours}h"
        if minutes > 0:
            return f"{minutes}m {secs}s" if secs else f"{minutes}m"
        return f"{secs}s"


def escape_fts_query(query: str) -> str:
    """Escape special FTS5 characters in a query."""
    # FTS5 special chars that need escaping: " * - ^
    # Keep quotes for phrase search, escape others
    escaped = re.sub(r'([*\-^])', r'"\1"', query)
    return escaped


def build_fts_query(query: str) -> str:
    """Build an FTS5 query from user input.

    Supports:
    - Simple terms: foo bar -> foo* AND bar* (both required)
    - Phrases: "foo bar" -> "foo bar" (exact)
    - Prefix: foo* -> foo*
    - Boolean: AND, OR, NOT operators
    - Proximity: NEAR(a b, 5)
    - Start anchor: ^term
    - Grouping: (a OR b) AND c
    """
    query = query.strip()
    if not query:
        return ""

    query_upper = query.upper()

    # If query contains advanced syntax, pass through as-is
    # User knows what they're doing
    if (
        '"' in query
        or " AND " in query_upper
        or " OR " in query_upper
        or " NOT " in query_upper
        or "NEAR(" in query_upper
        or query.startswith("^")
        or "(" in query
    ):
        return query

    # Simple query: split into terms, add prefix wildcard, join with AND
    terms = query.split()
    processed: list[str] = []
    for term in terms:
        if term.endswith("*") or term.startswith("^"):
            processed.append(term)
        else:
            # Add prefix matching for better results
            processed.append(f"{term}*")

    return " AND ".join(processed)


def search_sessions(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 50,
) -> list[SearchResult]:
    """Search for sessions matching the query."""
    fts_query = build_fts_query(query)
    if not fts_query:
        return []

    # Search using FTS5 with external content table
    # Note: bm25() doesn't work with external content, so we sort by recency
    sql = """
        SELECT
            s.session_id,
            s.project_path,
            s.file_path,
            s.first_timestamp,
            s.message_count,
            s.last_modified,
            s.cwd,
            s.git_branch,
            s.version,
            s.last_timestamp,
            s.is_agent,
            s.user_turns,
            s.assistant_turns,
            s.tool_use_count,
            s.total_tokens_est,
            m.content as matched_content
        FROM messages_fts
        JOIN messages m ON messages_fts.rowid = m.id
        JOIN sessions s ON m.session_id = s.session_id
        WHERE messages_fts MATCH ?
        GROUP BY s.session_id
        ORDER BY s.last_modified DESC
        LIMIT ?
    """

    results: list[SearchResult] = []
    try:
        for row in conn.execute(sql, (fts_query, limit)):
            # Truncate content for snippet
            content = row["matched_content"] or ""
            snippet = content[:100] + "..." if len(content) > 100 else content
            results.append(
                SearchResult(
                    session_id=row["session_id"],
                    project_path=row["project_path"],
                    file_path=row["file_path"],
                    first_timestamp=row["first_timestamp"],
                    message_count=row["message_count"],
                    snippet=snippet,
                    rank=row["last_modified"],
                    cwd=row["cwd"],
                    git_branch=row["git_branch"],
                    version=row["version"],
                    last_timestamp=row["last_timestamp"],
                    is_agent=bool(row["is_agent"]),
                    user_turns=row["user_turns"] or 0,
                    assistant_turns=row["assistant_turns"] or 0,
                    tool_use_count=row["tool_use_count"] or 0,
                    total_tokens_est=row["total_tokens_est"] or 0,
                )
            )
    except sqlite3.OperationalError:
        # Invalid query syntax - return empty results
        pass

    return results


def get_session_preview(
    conn: sqlite3.Connection,
    session_id: str,
    limit: int = 20,
) -> list[tuple[str, str]]:
    """Get message preview for a session. Returns list of (role, content) tuples."""
    sql = """
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY id
        LIMIT ?
    """

    messages: list[tuple[str, str]] = []
    for row in conn.execute(sql, (session_id, limit)):
        content = row["content"]
        # Truncate long messages for preview
        if len(content) > 500:
            content = content[:500] + "..."
        messages.append((row["role"], content))

    return messages


def get_recent_sessions(
    conn: sqlite3.Connection,
    limit: int = 20,
) -> list[SearchResult]:
    """Get most recent sessions without search query."""
    sql = """
        SELECT
            session_id,
            project_path,
            file_path,
            first_timestamp,
            message_count,
            cwd,
            git_branch,
            version,
            last_timestamp,
            is_agent,
            user_turns,
            assistant_turns,
            tool_use_count,
            total_tokens_est
        FROM sessions
        ORDER BY last_modified DESC
        LIMIT ?
    """

    results: list[SearchResult] = []
    for row in conn.execute(sql, (limit,)):
        # Get first message as snippet
        first_msg = conn.execute(
            "SELECT content FROM messages WHERE session_id = ? LIMIT 1",
            (row["session_id"],),
        ).fetchone()

        snippet = ""
        if first_msg:
            content = first_msg["content"]
            snippet = content[:100] + "..." if len(content) > 100 else content

        results.append(
            SearchResult(
                session_id=row["session_id"],
                project_path=row["project_path"],
                file_path=row["file_path"],
                first_timestamp=row["first_timestamp"],
                message_count=row["message_count"],
                snippet=snippet,
                rank=0.0,
                cwd=row["cwd"],
                git_branch=row["git_branch"],
                version=row["version"],
                last_timestamp=row["last_timestamp"],
                is_agent=bool(row["is_agent"]),
                user_turns=row["user_turns"] or 0,
                assistant_turns=row["assistant_turns"] or 0,
                tool_use_count=row["tool_use_count"] or 0,
                total_tokens_est=row["total_tokens_est"] or 0,
            )
        )

    return results
