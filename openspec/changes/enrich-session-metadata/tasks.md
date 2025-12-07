# Tasks: Enrich Session Metadata

## 1. Schema Versioning
- [x] 1.1 Add `SCHEMA_VERSION = 2` constant to `indexer.py`
- [x] 1.2 Update `_save_manifest()` to include `schema_version` in manifest JSON
- [x] 1.3 Update `_load_manifest()` to return `None` on JSON decode errors (already handles missing file)
- [x] 1.4 Update `is_index_current()` to check schema version match, returning `False` if missing or mismatched
- [x] 1.5 Add test: schema version mismatch triggers rebuild
- [x] 1.6 Add test: missing manifest triggers rebuild
- [x] 1.7 Add test: corrupt manifest (invalid JSON) triggers rebuild
- [x] 1.8 Add test: manifest missing `schema_version` field triggers rebuild

## 2. Database Schema Update
- [x] 2.1 Add new columns to `init_db()` sessions table DDL:
  - `cwd TEXT`
  - `git_branch TEXT`
  - `version TEXT`
  - `last_timestamp TEXT`
  - `is_agent INTEGER DEFAULT 0`
  - `user_turns INTEGER DEFAULT 0`
  - `assistant_turns INTEGER DEFAULT 0`
  - `tool_use_count INTEGER DEFAULT 0`
  - `total_tokens_est INTEGER DEFAULT 0`
- [x] 2.2 Update `SessionInfo` dataclass with new fields (all optional/defaulted)
- [x] 2.3 Update `SearchResult` dataclass with new fields (all optional/defaulted)

## 3. Metadata Extraction
- [x] 3.1 Modify `parse_session_file()` to skip meta/system messages when extracting `cwd`, `gitBranch`, `version`
- [x] 3.2 Extract metadata from first non-meta user/assistant message
- [x] 3.3 Store `None` for missing metadata fields (don't use empty string)
- [x] 3.4 Track `last_timestamp` during message iteration
- [x] 3.5 For single-message sessions, set `last_timestamp = first_timestamp`
- [x] 3.6 Detect `is_agent` by checking `agentId` field on user/assistant messages
- [x] 3.7 Count `user_turns` (exclude `isMeta: true` messages)
- [x] 3.8 Count `assistant_turns`
- [x] 3.9 Count `tool_use_count` from assistant content arrays (items with `type: "tool_use"`)
- [x] 3.10 Calculate `total_tokens_est`:
  - Count words from string content
  - Count words from `type: "text"` items in array content
  - Exclude tool_use, tool_result, thinking blocks
  - Multiply by 1.3 and floor

## 4. Index Storage
- [x] 4.1 Update `index_session()` to accept and store all new metadata fields
- [x] 4.2 Update SQL INSERT/REPLACE statement with new columns
- [x] 4.3 Handle NULL values correctly in SQL (don't quote None as string)

## 5. Search Layer
- [x] 5.1 Update `search_sessions()` SQL to SELECT new columns
- [x] 5.2 Populate new fields in `SearchResult` construction
- [x] 5.3 Pass through NULL as `None` in Python (don't convert to empty string)
- [x] 5.4 Add test: `search_sessions()` returns all new fields
- [x] 5.5 Add test: NULL fields returned as `None`

## 6. UI Display
- [x] 6.1 Update `HelpPanel.update_metadata()` to display working directory
- [x] 6.2 Display git branch
- [x] 6.3 Display Claude version
- [x] 6.4 Calculate and display duration from first/last timestamps
  - Handle single-message sessions (duration = 0)
  - Format as human-readable (e.g., "2h 15m", "45m", "30s")
- [x] 6.5 Display "Agent Session" indicator when `is_agent = 1`
- [x] 6.6 Display user turns count
- [x] 6.7 Display assistant turns count
- [x] 6.8 Display tool use count
- [x] 6.9 Display estimated tokens with "~" prefix (e.g., "~1,234 tokens")
- [x] 6.10 Handle NULL metadata: display "Unknown" or omit field (not empty string)
- [x] 6.11 Add test: `HelpPanel` renders all new fields correctly
- [x] 6.12 Add test: `HelpPanel` handles NULL fields gracefully

## 7. Integration Testing
- [x] 7.1 Add test: metadata extraction from sample session file with all fields present
- [x] 7.2 Add test: metadata extraction from session starting with meta messages
- [x] 7.3 Add test: metadata extraction from session with missing cwd/gitBranch/version
- [x] 7.4 Add test: tool_use counting from assistant content arrays
- [x] 7.5 Add test: token estimation excludes non-text content
- [x] 7.6 Add test: single-message session has duration = 0
- [x] 7.7 Add test: agent session detection (agentId present)
- [x] 7.8 Manual verification: delete `~/.cache/ccss/`, run app, verify reindex with new schema
