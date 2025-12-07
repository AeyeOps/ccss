# Change: Enrich Session Metadata

**Status: IMPLEMENTED**

## Why

The Session Details panel currently shows minimal information (session ID, project, file path, start time, message count). Claude Code session files contain rich metadata that would help users understand session context at a glance: working directory, git branch, Claude version, duration, and usage statistics.

Since we're adding new columns to the sessions table, this requires a schema version bump and full reindex. We should capture all useful metadata in one pass rather than iterating on the schema.

## What Changes

### Schema Changes (BREAKING - requires reindex)

Add columns to the `sessions` table:

| Column | Type | Source |
|--------|------|--------|
| `cwd` | TEXT | First message `cwd` field |
| `git_branch` | TEXT | First message `gitBranch` field |
| `version` | TEXT | First message `version` field |
| `last_timestamp` | TEXT | Last message timestamp |
| `is_agent` | INTEGER | 1 if any message has `agentId` |
| `user_turns` | INTEGER | Count of `type: "user"` messages |
| `assistant_turns` | INTEGER | Count of `type: "assistant"` messages |
| `tool_use_count` | INTEGER | Count of `tool_use` blocks in assistant content |
| `total_tokens_est` | INTEGER | Sum of word counts * 1.3 |

### Cache Invalidation

- Add `SCHEMA_VERSION` constant to indexer
- Store schema version in manifest
- `is_index_current()` returns `False` when schema version mismatches
- Automatic full reindex on version bump

### UI Enhancement

Update Session Details panel (`HelpPanel`) to display:
- Working directory (cwd)
- Git branch
- Claude Code version
- Duration (calculated from first/last timestamp)
- Turn counts (user/assistant)
- Tool usage count
- Estimated tokens

## Impact

- Affected specs: `session-search`
- Affected code: `indexer.py`, `search.py`, `app.py`
- **BREAKING**: Existing index cache will be invalidated and rebuilt on first run
