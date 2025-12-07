"""Session indexing using SQLite FTS5."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Iterator

# Schema version - bump when database structure changes to trigger rebuild
SCHEMA_VERSION = 2

# Type alias for progress callback: (current, total, message) -> None
ProgressCallback = Callable[[int, int, str], None]

CLAUDE_DIR = Path.home() / ".claude" / "projects"
CACHE_DIR = Path.home() / ".cache" / "ccss"
DB_PATH = CACHE_DIR / "sessions.db"
MANIFEST_PATH = CACHE_DIR / "index_manifest.json"


@dataclass
class SessionMessage:
    """A single message from a session."""

    session_id: str
    role: str
    content: str
    timestamp: str
    file_path: str
    project_path: str


@dataclass
class SessionInfo:
    """Metadata about a session."""

    session_id: str
    project_path: str
    file_path: str
    last_modified: float
    message_count: int
    first_timestamp: str
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


@dataclass
class SessionMetadata:
    """Extracted metadata from a session file."""

    cwd: str | None = None
    git_branch: str | None = None
    version: str | None = None
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    is_agent: bool = False
    user_turns: int = 0
    assistant_turns: int = 0
    tool_use_count: int = 0
    total_word_count: int = 0

    @property
    def total_tokens_est(self) -> int:
        """Estimate tokens as word_count * 1.3."""
        return int(self.total_word_count * 1.3)


def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the index database."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_filesystem_signature() -> tuple[int, float]:
    """Get a quick signature of session files: (file_count, max_mtime).

    This is O(n) file stats but no file reads. Used for cache validation.
    """
    if not CLAUDE_DIR.exists():
        return 0, 0.0

    file_count = 0
    max_mtime = 0.0

    for project_dir in CLAUDE_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for file_path in project_dir.glob("*.jsonl"):
            file_count += 1
            mtime = file_path.stat().st_mtime
            if mtime > max_mtime:
                max_mtime = mtime

    return file_count, max_mtime


def _load_manifest() -> dict[str, Any] | None:
    """Load the index manifest if it exists."""
    if not MANIFEST_PATH.exists():
        return None
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_manifest(file_count: int, max_mtime: float) -> None:
    """Save the index manifest with schema version."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "file_count": file_count,
        "max_mtime": max_mtime,
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f)


def is_index_current() -> bool:
    """Check if the index is up-to-date without a full scan.

    Compares stored manifest (schema_version, file_count, max_mtime) with current state.
    Returns True if unchanged, False if index needs updating.
    """
    if not DB_PATH.exists():
        return False

    manifest = _load_manifest()
    # Missing or corrupt manifest = rebuild
    if manifest is None:
        return False

    # Missing or mismatched schema version = rebuild
    if manifest.get("schema_version") != SCHEMA_VERSION:
        return False

    current_count, current_max_mtime = _get_filesystem_signature()

    return (
        manifest.get("file_count") == current_count
        and manifest.get("max_mtime") == current_max_mtime
    )


def ensure_schema_current() -> bool:
    """Ensure database schema matches current version, migrating if needed.

    If schema version mismatches, deletes the database and manifest to force
    a complete rebuild with the new schema.

    Returns True if a force rebuild is required (schema was migrated).
    """
    manifest = _load_manifest()

    # No manifest = fresh install, no migration needed
    if manifest is None:
        return False

    stored_version = manifest.get("schema_version")

    # Schema matches = no migration needed
    if stored_version == SCHEMA_VERSION:
        return False

    # Schema mismatch = delete DB and manifest to force full rebuild
    if DB_PATH.exists():
        DB_PATH.unlink()
    if MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()

    return True


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            project_path TEXT,
            file_path TEXT,
            last_modified REAL,
            message_count INTEGER,
            first_timestamp TEXT,
            cwd TEXT,
            git_branch TEXT,
            version TEXT,
            last_timestamp TEXT,
            is_agent INTEGER DEFAULT 0,
            user_turns INTEGER DEFAULT 0,
            assistant_turns INTEGER DEFAULT 0,
            tool_use_count INTEGER DEFAULT 0,
            total_tokens_est INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            content,
            content='messages',
            content_rowid='id',
            tokenize='porter unicode61'
        );

        CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
            INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
        END;

        CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, content)
                VALUES('delete', old.id, old.content);
        END;

        CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, content)
                VALUES('delete', old.id, old.content);
            INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
        END;

        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
    """)
    conn.commit()


def parse_session_file(file_path: Path) -> Iterator[SessionMessage]:
    """Parse a JSONL session file and yield messages."""
    project_path = file_path.parent.name
    session_id: str | None = None

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            if msg_type not in ("user", "assistant"):
                continue

            if session_id is None:
                session_id = data.get("sessionId", file_path.stem)

            message = data.get("message", {})
            role = message.get("role", msg_type)
            content = message.get("content", "")
            timestamp = data.get("timestamp", "")

            # Handle assistant messages with list content
            if isinstance(content, list):
                text_parts: list[str] = []
                content_list = cast(list[dict[str, Any]], content)
                for item in content_list:
                    item_type = item.get("type")
                    if item_type == "text":
                        text_val = item.get("text", "")
                        if isinstance(text_val, str):
                            text_parts.append(text_val)
                    elif item_type == "thinking":
                        # Optionally include thinking for search
                        think_val = item.get("thinking", "")
                        if isinstance(think_val, str):
                            text_parts.append(think_val)
                content = "\n".join(text_parts)

            if not isinstance(content, str) or not content.strip():
                continue

            # Skip meta/command messages for cleaner results
            if data.get("isMeta"):
                continue

            yield SessionMessage(
                session_id=session_id or file_path.stem,
                role=role,
                content=content,
                timestamp=timestamp,
                file_path=str(file_path),
                project_path=project_path,
            )


def extract_session_metadata(file_path: Path) -> SessionMetadata:
    """Extract metadata from a session file.

    Reads through the file to extract context metadata from the first
    non-meta message and compute statistics across all messages.
    """
    metadata = SessionMetadata()
    context_extracted = False

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            # Skip non-conversational messages for most extraction
            if msg_type not in ("user", "assistant"):
                continue

            # Check for agent session
            if data.get("agentId"):
                metadata.is_agent = True

            # Extract context from first non-meta user/assistant message
            if not context_extracted and not data.get("isMeta"):
                metadata.cwd = data.get("cwd")
                metadata.git_branch = data.get("gitBranch")
                metadata.version = data.get("version")
                metadata.first_timestamp = data.get("timestamp")
                context_extracted = True

            # Track last timestamp for all user/assistant messages
            timestamp = data.get("timestamp")
            if timestamp:
                metadata.last_timestamp = timestamp

            # Count turns
            is_meta = data.get("isMeta", False)
            if msg_type == "user" and not is_meta:
                metadata.user_turns += 1
            elif msg_type == "assistant":
                metadata.assistant_turns += 1

            # Process content for tool_use count and word count
            message = data.get("message", {})
            content = message.get("content", "")

            if msg_type == "assistant":
                if isinstance(content, list):
                    content_list = cast(list[dict[str, Any]], content)
                    for item in content_list:
                        item_type = item.get("type")
                        if item_type == "tool_use":
                            metadata.tool_use_count += 1
                        elif item_type == "text":
                            text = item.get("text", "")
                            if isinstance(text, str):
                                metadata.total_word_count += len(text.split())
                elif isinstance(content, str):
                    metadata.total_word_count += len(content.split())

            elif msg_type == "user" and not is_meta and isinstance(content, str):
                metadata.total_word_count += len(content.split())

    # For single-message sessions, ensure last_timestamp equals first
    if metadata.last_timestamp is None and metadata.first_timestamp:
        metadata.last_timestamp = metadata.first_timestamp

    return metadata


def find_session_files() -> Iterator[tuple[Path, float]]:
    """Find all session JSONL files and their modification times."""
    if not CLAUDE_DIR.exists():
        return

    for project_dir in CLAUDE_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        for file_path in project_dir.glob("*.jsonl"):
            mtime = file_path.stat().st_mtime
            yield file_path, mtime


def index_session(conn: sqlite3.Connection, file_path: Path, mtime: float) -> int:
    """Index a single session file. Returns message count."""
    messages = list(parse_session_file(file_path))
    if not messages:
        return 0

    # Extract metadata from raw file
    metadata = extract_session_metadata(file_path)

    # Use file stem as canonical session_id to avoid collisions
    # (agent sessions share parent's sessionId in content)
    session_id = file_path.stem
    project_path = messages[0].project_path
    first_timestamp = metadata.first_timestamp or (messages[0].timestamp if messages else "")

    # Delete existing messages for this session
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

    # Insert new messages
    for msg in messages:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, msg.role, msg.content, msg.timestamp),
        )

    # Update session metadata with all v2 fields
    conn.execute(
        """INSERT OR REPLACE INTO sessions
           (session_id, project_path, file_path, last_modified, message_count, first_timestamp,
            cwd, git_branch, version, last_timestamp, is_agent,
            user_turns, assistant_turns, tool_use_count, total_tokens_est)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            project_path,
            str(file_path),
            mtime,
            len(messages),
            first_timestamp,
            metadata.cwd,
            metadata.git_branch,
            metadata.version,
            metadata.last_timestamp,
            1 if metadata.is_agent else 0,
            metadata.user_turns,
            metadata.assistant_turns,
            metadata.tool_use_count,
            metadata.total_tokens_est,
        ),
    )

    return len(messages)


def build_index(
    conn: sqlite3.Connection,
    force: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> tuple[int, int, int]:
    """Build or update the index. Returns (indexed, skipped, removed) counts."""
    init_db(conn)

    # Get currently indexed sessions
    indexed_sessions: dict[str, tuple[str, float]] = {}
    for row in conn.execute("SELECT session_id, file_path, last_modified FROM sessions"):
        indexed_sessions[row["session_id"]] = (row["file_path"], row["last_modified"])

    # Collect all files first for progress tracking
    all_files = list(find_session_files())
    total_files = len(all_files)

    indexed_count = 0
    skipped_count = 0
    seen_files: set[str] = set()

    # Compute filesystem signature for manifest
    max_mtime = 0.0

    # Process all session files
    for i, (file_path, mtime) in enumerate(all_files):
        file_str = str(file_path)
        seen_files.add(file_str)
        if mtime > max_mtime:
            max_mtime = mtime

        # Report progress
        if progress_callback:
            progress_callback(i + 1, total_files, f"Processing {file_path.name}...")

        # Check if we need to reindex
        session_id = file_path.stem
        if not force and session_id in indexed_sessions:
            _, last_mtime = indexed_sessions[session_id]
            if mtime <= last_mtime:
                skipped_count += 1
                continue

        msg_count = index_session(conn, file_path, mtime)
        if msg_count > 0:
            indexed_count += 1

    # Remove deleted sessions
    removed_count = 0
    for session_id, (file_path, _) in indexed_sessions.items():
        if file_path not in seen_files:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            removed_count += 1

    conn.commit()

    # Save manifest for cache validation
    _save_manifest(total_files, max_mtime)

    return indexed_count, skipped_count, removed_count


def get_index_stats(conn: sqlite3.Connection) -> dict[str, int]:
    """Get statistics about the index."""
    stats: dict[str, int] = {}

    row = conn.execute("SELECT COUNT(*) as count FROM sessions").fetchone()
    stats["sessions"] = row["count"] if row else 0

    row = conn.execute("SELECT COUNT(*) as count FROM messages").fetchone()
    stats["messages"] = row["count"] if row else 0

    return stats
