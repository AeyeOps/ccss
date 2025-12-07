"""Tests for session indexer with enriched metadata."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ccss import indexer
from ccss.indexer import (
    SCHEMA_VERSION,
    _load_manifest,
    _save_manifest,
    ensure_schema_current,
    extract_session_metadata,
    get_db_connection,
    init_db,
    is_index_current,
)


@pytest.fixture
def temp_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setattr("ccss.indexer.CACHE_DIR", cache_dir)
    monkeypatch.setattr("ccss.indexer.DB_PATH", cache_dir / "sessions.db")
    monkeypatch.setattr("ccss.indexer.MANIFEST_PATH", cache_dir / "index_manifest.json")
    return cache_dir


@pytest.fixture
def temp_db(temp_cache_dir: Path) -> sqlite3.Connection:
    """Create a temporary database."""
    conn = get_db_connection()
    init_db(conn)
    return conn


class TestSchemaVersioning:
    """Tests for schema version handling."""

    def test_schema_version_stored_in_manifest(self, temp_cache_dir: Path) -> None:
        """Schema version should be stored in manifest."""
        _save_manifest(10, 12345.0)

        manifest = _load_manifest()
        assert manifest is not None
        assert manifest["schema_version"] == SCHEMA_VERSION

    def test_schema_mismatch_triggers_rebuild(
        self, temp_cache_dir: Path, temp_db: sqlite3.Connection
    ) -> None:
        """Schema version mismatch should trigger rebuild."""
        # Save manifest with old schema version
        manifest_path = temp_cache_dir / "index_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump({"schema_version": 1, "file_count": 0, "max_mtime": 0.0}, f)

        assert is_index_current() is False

    def test_missing_manifest_triggers_rebuild(
        self, temp_cache_dir: Path, temp_db: sqlite3.Connection
    ) -> None:
        """Missing manifest should trigger rebuild."""
        # DB exists but no manifest
        assert is_index_current() is False

    def test_corrupt_manifest_triggers_rebuild(
        self, temp_cache_dir: Path, temp_db: sqlite3.Connection
    ) -> None:
        """Corrupt manifest (invalid JSON) should trigger rebuild."""
        manifest_path = temp_cache_dir / "index_manifest.json"
        with open(manifest_path, "w") as f:
            f.write("not valid json {{{")

        assert is_index_current() is False

    def test_missing_schema_version_triggers_rebuild(
        self, temp_cache_dir: Path, temp_db: sqlite3.Connection
    ) -> None:
        """Manifest missing schema_version field should trigger rebuild."""
        manifest_path = temp_cache_dir / "index_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump({"file_count": 0, "max_mtime": 0.0}, f)  # No schema_version

        assert is_index_current() is False

    def test_ensure_schema_current_deletes_db_on_mismatch(
        self, temp_cache_dir: Path, temp_db: sqlite3.Connection
    ) -> None:
        """ensure_schema_current should delete DB and manifest on version mismatch."""
        # Close the connection first since we're going to delete the file
        temp_db.close()

        # Save manifest with old schema version
        manifest_path = temp_cache_dir / "index_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump({"schema_version": 1, "file_count": 5, "max_mtime": 100.0}, f)

        # DB should exist before migration (use module attr to get patched value)
        assert indexer.DB_PATH.exists()
        assert indexer.MANIFEST_PATH.exists()

        # Run migration check
        force_rebuild = ensure_schema_current()

        # Should return True indicating force rebuild needed
        assert force_rebuild is True

        # DB and manifest should be deleted
        assert not indexer.DB_PATH.exists()
        assert not indexer.MANIFEST_PATH.exists()

    def test_ensure_schema_current_no_op_when_current(
        self, temp_cache_dir: Path, temp_db: sqlite3.Connection
    ) -> None:
        """ensure_schema_current should not delete DB when version matches."""
        # Save manifest with current schema version
        _save_manifest(5, 100.0)

        # Both should exist (use module attr to get patched value)
        assert indexer.DB_PATH.exists()
        assert indexer.MANIFEST_PATH.exists()

        # Run migration check
        force_rebuild = ensure_schema_current()

        # Should return False (no rebuild needed)
        assert force_rebuild is False

        # DB and manifest should still exist
        assert indexer.DB_PATH.exists()
        assert indexer.MANIFEST_PATH.exists()

    def test_ensure_schema_current_no_manifest(self, temp_cache_dir: Path) -> None:
        """ensure_schema_current should return False when no manifest (fresh install)."""
        # No manifest = fresh install (use module attr to get patched value)
        assert not indexer.MANIFEST_PATH.exists()

        force_rebuild = ensure_schema_current()

        # Fresh install doesn't need force rebuild
        assert force_rebuild is False


class TestUpgradePath:
    """Integration tests for schema upgrade path."""

    def test_v1_to_v2_upgrade_reindexes_all_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Upgrading from v1 to v2 should reindex all sessions with new metadata."""
        # Setup temp cache
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setattr("ccss.indexer.CACHE_DIR", cache_dir)
        monkeypatch.setattr("ccss.indexer.DB_PATH", cache_dir / "sessions.db")
        monkeypatch.setattr("ccss.indexer.MANIFEST_PATH", cache_dir / "index_manifest.json")

        # Create a v1 database (schema without new columns)
        db_path = cache_dir / "sessions.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                project_path TEXT,
                file_path TEXT,
                last_modified REAL,
                message_count INTEGER,
                first_timestamp TEXT
            );
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            );
            CREATE VIRTUAL TABLE messages_fts USING fts5(
                content,
                content='messages',
                content_rowid='id'
            );
        """)
        # Insert a session record (v1 style, no new columns)
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
            ("old-session", "-opt-test", "/fake/path.jsonl", 1000.0, 5, "2025-01-01T00:00:00Z"),
        )
        conn.commit()
        conn.close()

        # Create v1 manifest
        manifest_path = cache_dir / "index_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump({"schema_version": 1, "file_count": 1, "max_mtime": 1000.0}, f)

        # Verify v1 setup
        assert db_path.exists()
        assert manifest_path.exists()

        # Run migration
        force_rebuild = ensure_schema_current()

        # Should delete DB and require force rebuild
        assert force_rebuild is True
        assert not db_path.exists()
        assert not manifest_path.exists()

        # Now create new DB with proper schema
        conn = get_db_connection()
        init_db(conn)

        # Verify new schema has all columns
        cursor = conn.execute("PRAGMA table_info(sessions)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_new_columns = {
            "cwd",
            "git_branch",
            "version",
            "last_timestamp",
            "is_agent",
            "user_turns",
            "assistant_turns",
            "tool_use_count",
            "total_tokens_est",
        }
        assert expected_new_columns.issubset(columns)
        conn.close()


class TestMetadataExtraction:
    """Tests for extract_session_metadata function."""

    def test_extract_metadata_all_fields(self, tmp_path: Path) -> None:
        """Should extract all metadata fields from session file."""
        session_file = tmp_path / "test.jsonl"
        messages = [
            {
                "type": "user",
                "cwd": "/opt/project",
                "gitBranch": "main",
                "version": "2.0.58",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {"role": "user", "content": "Hello world"},
            },
            {
                "type": "assistant",
                "cwd": "/opt/project",
                "gitBranch": "main",
                "version": "2.0.58",
                "timestamp": "2025-01-15T10:05:00.000Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Hi there, how can I help?"},
                        {"type": "tool_use", "name": "Read", "input": {}},
                    ],
                },
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        metadata = extract_session_metadata(session_file)

        assert metadata.cwd == "/opt/project"
        assert metadata.git_branch == "main"
        assert metadata.version == "2.0.58"
        assert metadata.first_timestamp == "2025-01-15T10:00:00.000Z"
        assert metadata.last_timestamp == "2025-01-15T10:05:00.000Z"
        assert metadata.is_agent is False
        assert metadata.user_turns == 1
        assert metadata.assistant_turns == 1
        assert metadata.tool_use_count == 1

    def test_skip_meta_messages(self, tmp_path: Path) -> None:
        """Should skip meta messages when extracting context metadata."""
        session_file = tmp_path / "test.jsonl"
        messages = [
            {
                "type": "user",
                "isMeta": True,
                "cwd": "/wrong/path",
                "gitBranch": "wrong-branch",
                "version": "1.0.0",
                "timestamp": "2025-01-15T09:00:00.000Z",
                "message": {"role": "user", "content": "meta message"},
            },
            {
                "type": "user",
                "cwd": "/correct/path",
                "gitBranch": "correct-branch",
                "version": "2.0.58",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {"role": "user", "content": "real message"},
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        metadata = extract_session_metadata(session_file)

        assert metadata.cwd == "/correct/path"
        assert metadata.git_branch == "correct-branch"
        assert metadata.version == "2.0.58"
        # Meta messages don't count as user turns
        assert metadata.user_turns == 1

    def test_missing_metadata_stored_as_none(self, tmp_path: Path) -> None:
        """Should store None for missing metadata fields."""
        session_file = tmp_path / "test.jsonl"
        messages = [
            {
                "type": "user",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {"role": "user", "content": "Hello"},
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        metadata = extract_session_metadata(session_file)

        assert metadata.cwd is None
        assert metadata.git_branch is None
        assert metadata.version is None

    def test_agent_session_detection(self, tmp_path: Path) -> None:
        """Should detect agent sessions via agentId field."""
        session_file = tmp_path / "test.jsonl"
        messages = [
            {
                "type": "user",
                "agentId": "agent-123",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {"role": "user", "content": "Agent task"},
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        metadata = extract_session_metadata(session_file)

        assert metadata.is_agent is True

    def test_tool_use_counting(self, tmp_path: Path) -> None:
        """Should count tool_use items in assistant content arrays."""
        session_file = tmp_path / "test.jsonl"
        messages = [
            {
                "type": "assistant",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Let me check"},
                        {"type": "tool_use", "name": "Read", "input": {}},
                        {"type": "tool_use", "name": "Write", "input": {}},
                        {"type": "tool_use", "name": "Bash", "input": {}},
                    ],
                },
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        metadata = extract_session_metadata(session_file)

        assert metadata.tool_use_count == 3

    def test_token_estimation_text_only(self, tmp_path: Path) -> None:
        """Should estimate tokens from text content only."""
        session_file = tmp_path / "test.jsonl"
        messages = [
            {
                "type": "user",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {"role": "user", "content": "one two three four five"},  # 5 words
            },
            {
                "type": "assistant",
                "timestamp": "2025-01-15T10:01:00.000Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "six seven eight nine ten"},  # 5 words
                        {"type": "tool_use", "name": "Read", "input": {}},
                    ],
                },
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        metadata = extract_session_metadata(session_file)

        # 10 words * 1.3 = 13 tokens
        assert metadata.total_word_count == 10
        assert metadata.total_tokens_est == 13

    def test_single_message_duration_zero(self, tmp_path: Path) -> None:
        """Single-message session should have last_timestamp equal to first."""
        session_file = tmp_path / "test.jsonl"
        messages = [
            {
                "type": "user",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {"role": "user", "content": "Just one message"},
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        metadata = extract_session_metadata(session_file)

        assert metadata.first_timestamp == "2025-01-15T10:00:00.000Z"
        assert metadata.last_timestamp == "2025-01-15T10:00:00.000Z"


class TestDatabaseSchema:
    """Tests for database schema with new columns."""

    def test_new_columns_exist(self, temp_db: sqlite3.Connection) -> None:
        """Database should have all new columns."""
        cursor = temp_db.execute("PRAGMA table_info(sessions)")
        columns = {row[1] for row in cursor.fetchall()}

        expected_columns = {
            "session_id",
            "project_path",
            "file_path",
            "last_modified",
            "message_count",
            "first_timestamp",
            "cwd",
            "git_branch",
            "version",
            "last_timestamp",
            "is_agent",
            "user_turns",
            "assistant_turns",
            "tool_use_count",
            "total_tokens_est",
        }

        assert expected_columns.issubset(columns)
