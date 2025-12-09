"""FTS5 query syntax validation tests.

Validates all syntax features advertised in the F1 help panel.
Uses a controlled test corpus with predictable content.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ccss.indexer import get_db_connection, index_session, init_db
from ccss.search import build_fts_query, search_sessions


# Test corpus with predictable content for each syntax feature
TEST_MESSAGES: list[dict[str, str]] = [
    # Basic terms & prefix matching
    {"content": "The database connection failed"},
    {"content": "Configuration file parsing error"},
    {"content": "connect to the server successfully"},
    # Exact phrase matching
    {"content": "file not found error occurred"},
    {"content": "error occurred in file system"},
    # Boolean operators
    {"content": "authentication successful user logged in"},
    {"content": "authentication failed invalid password"},
    {"content": "server started listening on port"},
    # Proximity search (NEAR)
    {"content": "api key validation completed"},
    {"content": "key for the api was invalid"},
    {"content": "the api uses a key to authenticate"},
    # Start anchor (^)
    {"content": "import os from pathlib"},
    {"content": "from os import path"},
    {"content": "the import statement failed"},
    # Stemming validation (Porter)
    {"content": "running the test suite"},
    {"content": "the runner executed tests"},
    {"content": "we ran all the tests"},
    # Column filter
    {"content": "unique column test marker"},
]


@pytest.fixture
def temp_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create isolated temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setattr("ccss.indexer.CACHE_DIR", cache_dir)
    monkeypatch.setattr("ccss.indexer.DB_PATH", cache_dir / "sessions.db")
    monkeypatch.setattr("ccss.indexer.MANIFEST_PATH", cache_dir / "index_manifest.json")
    return cache_dir


@pytest.fixture
def fts_db(temp_cache_dir: Path) -> sqlite3.Connection:
    """Create database with FTS5 schema."""
    conn = get_db_connection()
    init_db(conn)
    return conn


@pytest.fixture
def indexed_corpus(tmp_path: Path, fts_db: sqlite3.Connection) -> sqlite3.Connection:
    """Index the test corpus for FTS5 validation."""
    project_dir = tmp_path / "projects" / "-opt-fts-test"
    project_dir.mkdir(parents=True)

    # Create one session file per message for better test isolation
    for i, msg_data in enumerate(TEST_MESSAGES):
        session_file = project_dir / f"fts-test-{i}.jsonl"
        message = {
            "type": "user",
            "cwd": "/opt/fts-test",
            "timestamp": f"2025-01-15T10:{i:02d}:00.000Z",
            "message": {"role": "user", "content": msg_data["content"]},
        }
        with open(session_file, "w") as f:
            f.write(json.dumps(message) + "\n")
        index_session(fts_db, session_file, 12345.0 + i)

    fts_db.commit()
    return fts_db


# =============================================================================
# Unit Tests for build_fts_query()
# =============================================================================


class TestBuildFtsQuery:
    """Unit tests for query transformation logic."""

    def test_simple_terms_get_prefix(self) -> None:
        """Simple terms get automatic prefix wildcard."""
        result = build_fts_query("hello world")
        assert result == "hello* AND world*"

    def test_single_term_gets_prefix(self) -> None:
        """Single term gets prefix wildcard."""
        result = build_fts_query("database")
        assert result == "database*"

    def test_explicit_prefix_preserved(self) -> None:
        """Explicit prefix wildcard is preserved."""
        result = build_fts_query("hello*")
        assert result == "hello*"

    def test_quoted_phrase_passthrough(self) -> None:
        """Quoted phrases pass through unchanged."""
        result = build_fts_query('"exact phrase"')
        assert result == '"exact phrase"'

    def test_and_operator_passthrough(self) -> None:
        """AND operator triggers passthrough."""
        result = build_fts_query("a AND b")
        assert result == "a AND b"

    def test_or_operator_passthrough(self) -> None:
        """OR operator triggers passthrough."""
        result = build_fts_query("a OR b")
        assert result == "a OR b"

    def test_not_operator_passthrough(self) -> None:
        """NOT operator triggers passthrough."""
        result = build_fts_query("a NOT b")
        assert result == "a NOT b"

    def test_near_passthrough(self) -> None:
        """NEAR queries pass through unchanged."""
        result = build_fts_query("NEAR(api key, 5)")
        assert result == "NEAR(api key, 5)"

    def test_start_anchor_passthrough(self) -> None:
        """^term queries pass through unchanged."""
        result = build_fts_query("^import")
        assert result == "^import"

    def test_parentheses_passthrough(self) -> None:
        """Grouped queries pass through unchanged."""
        result = build_fts_query("(a OR b) AND c")
        assert result == "(a OR b) AND c"

    def test_empty_returns_empty(self) -> None:
        """Empty input returns empty string."""
        assert build_fts_query("") == ""

    def test_whitespace_returns_empty(self) -> None:
        """Whitespace-only input returns empty string."""
        assert build_fts_query("   ") == ""

    def test_lowercase_near_normalized(self) -> None:
        """Lowercase 'near' is normalized to uppercase."""
        result = build_fts_query("near(api key)")
        assert result == "NEAR(api key)"

    def test_lowercase_and_normalized(self) -> None:
        """Lowercase 'and' is normalized to uppercase."""
        result = build_fts_query("error and database")
        assert result == "error AND database"

    def test_lowercase_or_normalized(self) -> None:
        """Lowercase 'or' is normalized to uppercase."""
        result = build_fts_query("auth or login")
        assert result == "auth OR login"

    def test_lowercase_not_normalized(self) -> None:
        """Lowercase 'not' is normalized to uppercase."""
        result = build_fts_query("config not test")
        assert result == "config NOT test"

    def test_mixed_case_operators_normalized(self) -> None:
        """Mixed case operators are all normalized to uppercase."""
        result = build_fts_query("(error Or warning) And Not debug")
        assert "AND" in result
        assert "OR" in result
        assert "NOT" in result
        assert " and " not in result.lower() or result.count("AND") >= 1

    def test_infix_near_converted_to_function(self) -> None:
        """Infix NEAR syntax converted to function form (FTS5 only supports function form)."""
        result = build_fts_query("api near key")
        assert result == "NEAR(api key)"

    def test_infix_near_uppercase_converted(self) -> None:
        """Infix uppercase NEAR converted to function form."""
        result = build_fts_query("api NEAR key")
        assert result == "NEAR(api key)"


# =============================================================================
# Integration Tests - Basic Terms
# =============================================================================


class TestBasicTerms:
    """Tests for basic term matching."""

    def test_simple_word_matches(self, indexed_corpus: sqlite3.Connection) -> None:
        """Single word finds matching documents."""
        results = search_sessions(indexed_corpus, "database")
        assert len(results) >= 1
        assert any("database" in r.snippet.lower() for r in results)

    def test_prefix_auto_applied(self, indexed_corpus: sqlite3.Connection) -> None:
        """Simple query auto-applies prefix matching."""
        # 'config' should match 'configuration'
        results = search_sessions(indexed_corpus, "config")
        assert len(results) >= 1
        assert any("configuration" in r.snippet.lower() for r in results)

    def test_explicit_prefix_wildcard(self, indexed_corpus: sqlite3.Connection) -> None:
        """Explicit prefix wildcard (word*) works."""
        results = search_sessions(indexed_corpus, "data*")
        assert len(results) >= 1
        assert any("database" in r.snippet.lower() for r in results)

    def test_start_anchor_matches_field_start(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """^word matches content starting with that word."""
        results = search_sessions(indexed_corpus, "^import")
        assert len(results) >= 1
        # Should match "import os from pathlib"
        for r in results:
            assert r.snippet.lower().startswith("import")

    def test_start_anchor_excludes_mid_content(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """^word should NOT match word appearing mid-content."""
        results = search_sessions(indexed_corpus, "^import")
        # Should NOT include "the import statement failed"
        for r in results:
            assert not r.snippet.lower().startswith("the import")


# =============================================================================
# Integration Tests - Exact Phrases
# =============================================================================


class TestExactPhrases:
    """Tests for quoted exact phrase matching."""

    def test_exact_phrase_matches(self, indexed_corpus: sqlite3.Connection) -> None:
        """Quoted phrase matches exact sequence."""
        results = search_sessions(indexed_corpus, '"file not found"')
        assert len(results) >= 1
        assert any("file not found" in r.snippet.lower() for r in results)

    def test_exact_phrase_word_order_matters(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """Phrase requires exact word order."""
        # "not found file" should NOT match "file not found"
        results = search_sessions(indexed_corpus, '"not found file"')
        assert len(results) == 0

    def test_phrase_partial_match(self, indexed_corpus: sqlite3.Connection) -> None:
        """Partial phrase matches."""
        results = search_sessions(indexed_corpus, '"error occurred"')
        # Should match both "file not found error occurred" and "error occurred in file"
        assert len(results) >= 2


# =============================================================================
# Integration Tests - Boolean Operators
# =============================================================================


class TestBooleanOperators:
    """Tests for AND, OR, NOT operators."""

    def test_and_requires_both_terms(self, indexed_corpus: sqlite3.Connection) -> None:
        """AND requires both terms present."""
        results = search_sessions(indexed_corpus, "authentication AND successful")
        assert len(results) >= 1
        for r in results:
            snippet_lower = r.snippet.lower()
            assert "authentication" in snippet_lower
            assert "successful" in snippet_lower

    def test_and_excludes_partial_matches(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """AND excludes documents with only one term."""
        results = search_sessions(indexed_corpus, "authentication AND nonexistent")
        assert len(results) == 0

    def test_or_matches_either_term(self, indexed_corpus: sqlite3.Connection) -> None:
        """OR matches documents with either term."""
        results = search_sessions(indexed_corpus, "successful OR failed")
        assert len(results) >= 2

    def test_not_excludes_term(self, indexed_corpus: sqlite3.Connection) -> None:
        """NOT excludes documents containing the term."""
        results = search_sessions(indexed_corpus, "authentication NOT failed")
        assert len(results) >= 1
        for r in results:
            assert "failed" not in r.snippet.lower()


# =============================================================================
# Integration Tests - Grouping
# =============================================================================


class TestGrouping:
    """Tests for parenthetical grouping."""

    def test_grouped_or_with_and(self, indexed_corpus: sqlite3.Connection) -> None:
        """(a OR b) AND c works correctly."""
        results = search_sessions(
            indexed_corpus, "(successful OR failed) AND authentication"
        )
        assert len(results) >= 1
        for r in results:
            snippet_lower = r.snippet.lower()
            assert "authentication" in snippet_lower
            assert "successful" in snippet_lower or "failed" in snippet_lower

    def test_nested_grouping(self, indexed_corpus: sqlite3.Connection) -> None:
        """Nested grouping works."""
        results = search_sessions(
            indexed_corpus, "(authentication AND (successful OR logged))"
        )
        assert len(results) >= 1


# =============================================================================
# Integration Tests - Proximity (NEAR)
# =============================================================================


class TestProximity:
    """Tests for NEAR proximity operator."""

    def test_near_default_distance(self, indexed_corpus: sqlite3.Connection) -> None:
        """NEAR(a b) matches within default 10 tokens."""
        results = search_sessions(indexed_corpus, "NEAR(api key)")
        assert len(results) >= 1

    def test_near_custom_distance(self, indexed_corpus: sqlite3.Connection) -> None:
        """NEAR(a b, N) matches within N tokens."""
        # "api key validation" has api and key adjacent
        results = search_sessions(indexed_corpus, "NEAR(api key, 3)")
        assert len(results) >= 1

    def test_near_tight_vs_loose(self, indexed_corpus: sqlite3.Connection) -> None:
        """Tighter NEAR distance returns fewer or equal results."""
        results_tight = search_sessions(indexed_corpus, "NEAR(api key, 1)")
        results_loose = search_sessions(indexed_corpus, "NEAR(api key, 10)")
        assert len(results_loose) >= len(results_tight)

    def test_near_lowercase_works(self, indexed_corpus: sqlite3.Connection) -> None:
        """Lowercase 'near' is normalized and works."""
        results = search_sessions(indexed_corpus, "near(api key)")
        assert len(results) >= 1

    def test_near_infix_syntax(self, indexed_corpus: sqlite3.Connection) -> None:
        """Infix NEAR syntax (a NEAR b) converted to function form and works."""
        results = search_sessions(indexed_corpus, "api NEAR key")
        assert len(results) >= 1

    def test_near_infix_lowercase(self, indexed_corpus: sqlite3.Connection) -> None:
        """Infix lowercase 'near' converted to function form and works."""
        results = search_sessions(indexed_corpus, "api near key")
        assert len(results) >= 1


# =============================================================================
# Integration Tests - Column Filter
# =============================================================================


class TestColumnFilter:
    """Tests for column:term filtering."""

    def test_content_column_explicit(self, indexed_corpus: sqlite3.Connection) -> None:
        """content:term works (only indexed column)."""
        results = search_sessions(indexed_corpus, "content:database")
        assert len(results) >= 1

    def test_nonexistent_column_returns_empty(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """Invalid column name returns empty (not error)."""
        results = search_sessions(indexed_corpus, "title:database")
        assert len(results) == 0


# =============================================================================
# Integration Tests - Stemming
# =============================================================================


class TestStemming:
    """Tests for Porter stemmer functionality."""

    @pytest.mark.parametrize(
        "query,expected_in_snippet",
        [
            ("run", "running"),
            ("run", "runner"),
            # Note: "ran" is irregular past tense - Porter stemmer doesn't handle it
        ],
    )
    def test_stemmer_expands_run_variants(
        self, indexed_corpus: sqlite3.Connection, query: str, expected_in_snippet: str
    ) -> None:
        """Porter stemmer matches 'run' word variants (regular forms only)."""
        results = search_sessions(indexed_corpus, query)
        assert len(results) >= 1
        found = any(expected_in_snippet in r.snippet.lower() for r in results)
        assert found, f"Expected '{expected_in_snippet}' in results for query '{query}'"

    def test_stemmer_connect_connection(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """'connect' matches 'connection' via stemming."""
        results = search_sessions(indexed_corpus, "connect")
        assert len(results) >= 1
        found = any("connection" in r.snippet.lower() for r in results)
        assert found, "Expected 'connection' to match query 'connect'"

    def test_stemmer_bidirectional(self, indexed_corpus: sqlite3.Connection) -> None:
        """Stemming works bidirectionally - 'running' finds 'run' content."""
        results = search_sessions(indexed_corpus, "running")
        # Should find the test suite message
        assert len(results) >= 1


# =============================================================================
# Integration Tests - Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for graceful failure on invalid syntax."""

    def test_unbalanced_parens_returns_empty(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """Unbalanced parentheses return empty, not exception."""
        results = search_sessions(indexed_corpus, "(unbalanced")
        assert results == []

    def test_unclosed_quote_returns_empty(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """Unclosed quote returns empty."""
        results = search_sessions(indexed_corpus, '"unclosed')
        assert results == []

    def test_empty_query_returns_empty(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """Empty query returns empty list."""
        results = search_sessions(indexed_corpus, "")
        assert results == []

    def test_whitespace_only_returns_empty(
        self, indexed_corpus: sqlite3.Connection
    ) -> None:
        """Whitespace-only query returns empty."""
        results = search_sessions(indexed_corpus, "   ")
        assert results == []
