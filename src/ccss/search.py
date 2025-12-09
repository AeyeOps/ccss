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


def _extract_search_terms(query: str) -> list[str]:
    """Extract actual search terms from a query, filtering out FTS5 operators."""
    operators = {"and", "or", "not", "near"}
    # Remove NEAR(...) constructs
    query = re.sub(r"NEAR\s*\([^)]*\)", " ", query, flags=re.IGNORECASE)
    # Extract alphanumeric tokens
    tokens = re.findall(r"[a-zA-Z0-9]+", query)
    return [t.lower() for t in tokens if t.lower() not in operators and len(t) >= 2]


def _extract_snippet_context(content: str, terms: list[str], max_len: int = 100) -> str:
    """Return full content without truncation."""
    return content or ""


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
    - Proximity: NEAR(a b, 5) or a NEAR b (converted to function form)
    - Start anchor: ^term
    - Grouping: (a OR b) AND c
    """
    query = query.strip()
    if not query:
        return ""

    query_upper = query.upper()

    # Convert infix NEAR to function form: "a NEAR b" -> "NEAR(a b)"
    # FTS5 only supports function form NEAR(a b), infix is NOT valid
    infix_near_pattern = r"(\S+)\s+NEAR\s+(\S+)"
    if re.search(infix_near_pattern, query, flags=re.IGNORECASE):
        query = re.sub(infix_near_pattern, r"NEAR(\1 \2)", query, flags=re.IGNORECASE)
        query_upper = query.upper()

    # If query contains advanced syntax, pass through with normalized operators
    if (
        '"' in query
        or " AND " in query_upper
        or " OR " in query_upper
        or " NOT " in query_upper
        or "NEAR(" in query_upper
        or query.startswith("^")
        or "(" in query
    ):
        # Normalize operators to uppercase (FTS5 is case-sensitive for most)
        result = re.sub(r"\bAND\b", "AND", query, flags=re.IGNORECASE)
        result = re.sub(r"\bOR\b", "OR", result, flags=re.IGNORECASE)
        result = re.sub(r"\bNOT\b", "NOT", result, flags=re.IGNORECASE)
        result = re.sub(r"\bNEAR\s*\(", "NEAR(", result, flags=re.IGNORECASE)
        return result

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
    # Use subquery to get the first matching message per session
    # Step 1: Find the MIN rowid of matching messages per session
    # Step 2: Join back to messages to get the actual content from that row
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
            m2.content as matched_content
        FROM (
            SELECT m.session_id, MIN(m.id) as first_match_id
            FROM messages_fts
            JOIN messages m ON messages_fts.rowid = m.id
            WHERE messages_fts MATCH ?
            GROUP BY m.session_id
        ) match_ids
        JOIN messages m2 ON m2.id = match_ids.first_match_id
        JOIN sessions s ON match_ids.session_id = s.session_id
        ORDER BY s.last_modified DESC
    """

    # Extract search terms for context extraction
    search_terms = _extract_search_terms(query)

    results: list[SearchResult] = []
    try:
        for row in conn.execute(sql + " LIMIT ?", (fts_query, limit)):
            content = row["matched_content"] or ""
            snippet = _extract_snippet_context(content, search_terms)
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
    query: str = "",
    limit: int = 20,
) -> list[tuple[str, str]]:
    """Get message preview for a session, prioritizing matched messages.

    When a query is provided, returns messages containing search terms.
    Falls back to first messages if no query or no matches.
    """
    messages: list[tuple[str, str]] = []

    # If query provided, try to find messages containing search terms
    if query:
        terms = _extract_search_terms(query)
        if terms:
            # Build LIKE conditions for each term (OR = any term matches)
            like_conditions = " OR ".join(["content LIKE ?" for _ in terms])
            sql = f"""
                SELECT role, content
                FROM messages
                WHERE session_id = ? AND ({like_conditions})
                ORDER BY id
                LIMIT ?
            """
            params: list[str | int] = [session_id] + [f"%{t}%" for t in terms] + [limit]

            for row in conn.execute(sql, params):
                messages.append((row["role"], row["content"]))

            if messages:
                return messages

    # Fallback: first messages if no query or no matches
    sql = """
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY id
        LIMIT ?
    """

    for row in conn.execute(sql, (session_id, limit)):
        messages.append((row["role"], row["content"]))

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
    """

    results: list[SearchResult] = []
    for row in conn.execute(sql + " LIMIT ?", (limit,)):
        # Get first message as snippet
        first_msg = conn.execute(
            "SELECT content FROM messages WHERE session_id = ? LIMIT 1",
            (row["session_id"],),
        ).fetchone()

        snippet = ""
        if first_msg:
            snippet = first_msg["content"] or ""

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
