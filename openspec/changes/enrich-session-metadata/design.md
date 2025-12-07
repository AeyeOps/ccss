# Design: Enrich Session Metadata

## Context

The indexer currently extracts minimal metadata from session files during indexing. Session JSONL files contain additional context that's cheap to extract during the same parsing pass.

## Goals / Non-Goals

**Goals:**
- Extract all useful session metadata in a single indexing pass
- Provide schema versioning for clean cache invalidation
- Display enriched metadata in the Session Details panel
- Handle edge cases gracefully (missing data, corrupt manifests, unusual sessions)

**Non-Goals:**
- Per-tool breakdown (future feature)
- Thinking block analysis (marginal value)
- Real-time metadata updates (only at index time)
- Precise token counting (approximation is sufficient)

## Decisions

### Decision: Schema version in manifest

**Chosen**: Store `schema_version` in the manifest JSON file.

**Alternatives considered**:
- SQLite `PRAGMA user_version`: Requires DB connection to check; manifest check is faster
- Delete DB on startup always: Wasteful; we want incremental updates when schema unchanged
- ALTER TABLE migrations: Complex for a dev tool; clean rebuild is simpler

**Rationale**: The manifest already exists for cache validation. Adding schema version there keeps the fast-path check (no DB open) while enabling automatic invalidation on schema changes.

**Recovery behavior**: If manifest is missing, corrupt (invalid JSON), or lacks `schema_version`, treat as version mismatch and trigger rebuild. This ensures users never get stuck.

### Decision: Compute stats during indexing

**Chosen**: Calculate turn counts, tool use, and token estimates during `parse_session_file()`.

**Alternatives considered**:
- On-demand calculation: Slower UI response when selecting sessions
- Separate stats table: Over-engineered for this use case
- Store raw counts only, compute tokens in UI: Adds UI complexity

**Rationale**: The indexer already iterates every message. Adding counters is O(1) per message, negligible overhead. Pre-computed stats enable instant display.

### Decision: Token estimation via word count

**Chosen**: `total_tokens_est = floor(sum(word_count) * 1.3)`

**Scope**: Only count words from actual text content:
- String `content` fields: count words directly
- Array `content` fields: only count words from items where `type == "text"`
- Exclude: `tool_use` payloads, `tool_result` content, `thinking` blocks, binary data

**Rationale**: Approximate but useful. Real tokenization would require model-specific tokenizers (tiktoken, etc.) and add dependencies. Word count * 1.3 is within 20% for most English text. Excluding non-text content prevents inflated counts from large tool payloads.

### Decision: Skip meta/system messages for metadata extraction

**Chosen**: When extracting `cwd`, `gitBranch`, `version`, iterate until finding the first message where:
- `type` is `"user"` or `"assistant"`
- `isMeta` is not `true`
- `type` is not `"system"`

**Rationale**: Many sessions begin with meta messages (file-history-snapshot, system prompts, command messages). These may lack context fields or have incorrect values. The first "real" conversational message reliably contains the session context.

### Decision: ISO-8601 timestamps

**Chosen**: Store and compare timestamps in ISO-8601 format with timezone (e.g., `2025-01-15T10:30:00.000Z`).

**Rationale**: Claude Code already uses this format. No conversion needed. String comparison works for ordering. Duration calculation parses with `datetime.fromisoformat()`.

### Decision: Agent detection scope

**Chosen**: Check `agentId` field on user and assistant messages only.

**Rationale**: The `agentId` field appears on messages within agent sessions. Checking user/assistant messages (which we already iterate) is sufficient. Nested tool call metadata is not a reliable indicator and would require deeper parsing.

## Schema v2 Layout

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    project_path TEXT,
    file_path TEXT,
    last_modified REAL,
    message_count INTEGER,
    first_timestamp TEXT,
    -- v2 additions
    cwd TEXT,                    -- NULL if not found
    git_branch TEXT,             -- NULL if not found
    version TEXT,                -- NULL if not found
    last_timestamp TEXT,         -- Same as first if single message
    is_agent INTEGER DEFAULT 0,  -- 1 if agentId found
    user_turns INTEGER DEFAULT 0,
    assistant_turns INTEGER DEFAULT 0,
    tool_use_count INTEGER DEFAULT 0,
    total_tokens_est INTEGER DEFAULT 0
);
```

## Data Extraction Logic

### Metadata Extraction (cwd, git_branch, version)

```python
def extract_session_metadata(file_path: Path) -> dict:
    """Extract metadata from first real message."""
    with open(file_path) as f:
        for line in f:
            data = json.loads(line)
            # Skip non-conversational messages
            if data.get("type") not in ("user", "assistant"):
                continue
            if data.get("isMeta"):
                continue
            # Found first real message
            return {
                "cwd": data.get("cwd"),  # May be None
                "git_branch": data.get("gitBranch"),  # May be None
                "version": data.get("version"),  # May be None
            }
    return {"cwd": None, "git_branch": None, "version": None}
```

### Turn and Stats Counting

```python
def count_session_stats(messages: list[SessionMessage], raw_data: list[dict]) -> dict:
    """Count turns, tool use, and estimate tokens."""
    user_turns = 0
    assistant_turns = 0
    tool_use_count = 0
    word_count = 0
    is_agent = False
    last_timestamp = None

    for data in raw_data:
        msg_type = data.get("type")

        # Check for agent
        if data.get("agentId"):
            is_agent = True

        # Track last timestamp
        if msg_type in ("user", "assistant"):
            ts = data.get("timestamp")
            if ts:
                last_timestamp = ts

        # Count turns (exclude meta)
        if msg_type == "user" and not data.get("isMeta"):
            user_turns += 1
        elif msg_type == "assistant":
            assistant_turns += 1

        # Count tool use and tokens from assistant content
        if msg_type == "assistant":
            content = data.get("message", {}).get("content", "")
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "tool_use":
                        tool_use_count += 1
                    elif item.get("type") == "text":
                        text = item.get("text", "")
                        if isinstance(text, str):
                            word_count += len(text.split())
            elif isinstance(content, str):
                word_count += len(content.split())

        # Count tokens from user content
        if msg_type == "user" and not data.get("isMeta"):
            content = data.get("message", {}).get("content", "")
            if isinstance(content, str):
                word_count += len(content.split())

    return {
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "tool_use_count": tool_use_count,
        "total_tokens_est": int(word_count * 1.3),
        "is_agent": 1 if is_agent else 0,
        "last_timestamp": last_timestamp,
    }
```

### Schema Version Check

```python
SCHEMA_VERSION = 2

def is_index_current() -> bool:
    """Check if index is up-to-date."""
    if not DB_PATH.exists():
        return False

    manifest = _load_manifest()

    # Missing or corrupt manifest = rebuild
    if manifest is None:
        return False

    # Missing or mismatched schema version = rebuild
    if manifest.get("schema_version") != SCHEMA_VERSION:
        return False

    # Check file signature as before
    current_count, current_max_mtime = _get_filesystem_signature()
    return (
        manifest.get("file_count") == current_count
        and manifest.get("max_mtime") == current_max_mtime
    )

def _load_manifest() -> dict | None:
    """Load manifest, returning None if missing or corrupt."""
    if not MANIFEST_PATH.exists():
        return None
    try:
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None  # Corrupt = trigger rebuild
```

## Edge Cases

| Case | Behavior |
|------|----------|
| Session starts with meta/system messages | Skip until first user/assistant message |
| No cwd/gitBranch/version in any message | Store NULL, UI shows "Unknown" |
| Single-message session | `last_timestamp = first_timestamp`, duration = 0 |
| Session with only user messages | `assistant_turns = 0`, valid state |
| Empty session file | Skip entirely, don't index |
| Manifest missing | Trigger rebuild |
| Manifest corrupt (invalid JSON) | Trigger rebuild |
| Manifest missing schema_version | Trigger rebuild |
| Content is dict/object (not string/array) | Skip for token counting |
| Very large content strings | Still count words (no truncation during indexing) |

## Migration Plan

1. Bump `SCHEMA_VERSION` from 1 to 2
2. On startup, `is_index_current()` detects version mismatch
3. Returns `False`, triggering full rebuild with progress UI
4. User sees "Indexing X of Y sessions..." (existing UX)
5. New schema populated, manifest updated with version 2

No explicit migration needed - clean rebuild is the migration.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| First run after upgrade is slow | Progress UI already exists; typically < 30s for 1000 sessions |
| Token estimate inaccuracy | Label as "~tokens" to indicate approximation |
| Large sessions slow indexing | Content already parsed; stats are cheap additions |
| Missing metadata common | UI designed to handle NULL gracefully |

## Open Questions

None - all edge cases addressed.
