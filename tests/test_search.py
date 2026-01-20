"""Tests for search layer with enriched metadata."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ccss.indexer import get_db_connection, index_session, init_db
from ccss.search import SearchResult, get_recent_sessions, search_sessions


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


@pytest.fixture
def session_with_metadata(tmp_path: Path, temp_db: sqlite3.Connection) -> str:
    """Create a session file with full metadata and index it."""
    project_dir = tmp_path / "projects" / "-opt-test"
    project_dir.mkdir(parents=True)
    session_file = project_dir / "test-session.jsonl"

    messages = [
        {
            "type": "user",
            "cwd": "/opt/test",
            "gitBranch": "feature-branch",
            "version": "2.0.58",
            "timestamp": "2025-01-15T10:00:00.000Z",
            "message": {"role": "user", "content": "searchable keyword here"},
        },
        {
            "type": "assistant",
            "cwd": "/opt/test",
            "gitBranch": "feature-branch",
            "version": "2.0.58",
            "timestamp": "2025-01-15T10:05:00.000Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Here is the response"},
                    {"type": "tool_use", "name": "Read", "input": {}},
                ],
            },
        },
    ]
    with open(session_file, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")

    index_session(temp_db, session_file, 12345.0)
    temp_db.commit()

    return "test-session"


class TestSearchResultsIncludeNewFields:
    """Tests for search results including new metadata fields."""

    def test_search_returns_all_new_fields(
        self, temp_db: sqlite3.Connection, session_with_metadata: str
    ) -> None:
        """search_sessions should return all new metadata fields."""
        results = search_sessions(temp_db, "searchable")

        assert len(results) == 1
        result = results[0]

        assert result.cwd == "/opt/test"
        assert result.git_branch == "feature-branch"
        assert result.version == "2.0.58"
        assert result.last_timestamp == "2025-01-15T10:05:00.000Z"
        assert result.is_agent is False
        assert result.user_turns == 1
        assert result.assistant_turns == 1
        assert result.tool_use_count == 1
        assert result.total_tokens_est > 0

    def test_get_recent_returns_all_new_fields(
        self, temp_db: sqlite3.Connection, session_with_metadata: str
    ) -> None:
        """get_recent_sessions should return all new metadata fields."""
        results = get_recent_sessions(temp_db)

        assert len(results) == 1
        result = results[0]

        assert result.cwd == "/opt/test"
        assert result.git_branch == "feature-branch"
        assert result.version == "2.0.58"


class TestNullFieldHandling:
    """Tests for NULL field handling."""

    @pytest.fixture
    def session_without_metadata(self, tmp_path: Path, temp_db: sqlite3.Connection) -> str:
        """Create a session file without metadata fields."""
        project_dir = tmp_path / "projects" / "-opt-empty"
        project_dir.mkdir(parents=True)
        session_file = project_dir / "empty-session.jsonl"

        messages = [
            {
                "type": "user",
                "timestamp": "2025-01-15T10:00:00.000Z",
                "message": {"role": "user", "content": "unique searchterm"},
            },
        ]
        with open(session_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        index_session(temp_db, session_file, 12345.0)
        temp_db.commit()

        return "empty-session"

    def test_null_fields_returned_as_none(
        self, temp_db: sqlite3.Connection, session_without_metadata: str
    ) -> None:
        """NULL fields should be returned as None, not empty string."""
        results = search_sessions(temp_db, "searchterm")

        assert len(results) == 1
        result = results[0]

        assert result.cwd is None
        assert result.git_branch is None
        assert result.version is None


class TestSearchResultProperties:
    """Tests for SearchResult computed properties."""

    def test_duration_calculation(self) -> None:
        """Should calculate duration from timestamps."""
        result = SearchResult(
            session_id="test",
            project_path="-opt-test",
            file_path="/test.jsonl",
            first_timestamp="2025-01-15T10:00:00.000Z",
            message_count=10,
            snippet="test",
            rank=0.0,
            last_timestamp="2025-01-15T11:30:45.000Z",
        )

        assert result.duration_seconds == 5445  # 1h 30m 45s
        assert result.display_duration == "1h 30m"

    def test_duration_zero_for_same_timestamps(self) -> None:
        """Duration should be 0s when timestamps are equal."""
        result = SearchResult(
            session_id="test",
            project_path="-opt-test",
            file_path="/test.jsonl",
            first_timestamp="2025-01-15T10:00:00.000Z",
            message_count=1,
            snippet="test",
            rank=0.0,
            last_timestamp="2025-01-15T10:00:00.000Z",
        )

        assert result.duration_seconds == 0
        assert result.display_duration == "0s"

    def test_duration_unknown_for_missing_timestamps(self) -> None:
        """Duration should be Unknown when timestamps are missing."""
        result = SearchResult(
            session_id="test",
            project_path="-opt-test",
            file_path="/test.jsonl",
            first_timestamp="",
            message_count=1,
            snippet="test",
            rank=0.0,
            last_timestamp=None,
        )

        assert result.duration_seconds is None
        assert result.display_duration == "Unknown"

    def test_display_duration_minutes_only(self) -> None:
        """Should display minutes and seconds for short durations."""
        result = SearchResult(
            session_id="test",
            project_path="-opt-test",
            file_path="/test.jsonl",
            first_timestamp="2025-01-15T10:00:00.000Z",
            message_count=10,
            snippet="test",
            rank=0.0,
            last_timestamp="2025-01-15T10:15:30.000Z",
        )

        assert result.display_duration == "15m 30s"

    def test_display_duration_seconds_only(self) -> None:
        """Should display seconds only for very short durations."""
        result = SearchResult(
            session_id="test",
            project_path="-opt-test",
            file_path="/test.jsonl",
            first_timestamp="2025-01-15T10:00:00.000Z",
            message_count=10,
            snippet="test",
            rank=0.0,
            last_timestamp="2025-01-15T10:00:45.000Z",
        )

        assert result.display_duration == "45s"
