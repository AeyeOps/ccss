## ADDED Requirements

### Requirement: Schema Versioning
The indexer SHALL track schema version to enable automatic cache invalidation when the database structure changes.

#### Scenario: Schema version stored in manifest
- **WHEN** the index is built or updated
- **THEN** the manifest file SHALL contain a `schema_version` field with an integer value

#### Scenario: Schema mismatch triggers rebuild
- **WHEN** the stored schema version differs from the current `SCHEMA_VERSION` constant
- **THEN** `is_index_current()` SHALL return `False`
- **AND** a full index rebuild SHALL occur on next app launch

#### Scenario: Missing manifest triggers rebuild
- **WHEN** the manifest file does not exist or cannot be parsed as valid JSON
- **THEN** `is_index_current()` SHALL return `False`
- **AND** a full index rebuild SHALL occur

#### Scenario: Missing schema version in manifest triggers rebuild
- **WHEN** the manifest exists but lacks a `schema_version` field
- **THEN** `is_index_current()` SHALL return `False`

### Requirement: Session Context Metadata
The indexer SHALL extract session context metadata from session files, skipping meta and system messages.

#### Scenario: Working directory extraction
- **WHEN** a session file is indexed
- **THEN** the `cwd` field from the first user or assistant message (not meta/system) SHALL be stored

#### Scenario: Git branch extraction
- **WHEN** a session file is indexed
- **THEN** the `gitBranch` field from the first user or assistant message (not meta/system) SHALL be stored

#### Scenario: Claude version extraction
- **WHEN** a session file is indexed
- **THEN** the `version` field from the first user or assistant message (not meta/system) SHALL be stored

#### Scenario: Missing metadata stored as NULL
- **WHEN** a session file lacks `cwd`, `gitBranch`, or `version` fields in any message
- **THEN** the corresponding column SHALL be stored as NULL

#### Scenario: Skip meta messages for metadata extraction
- **WHEN** a session file begins with meta (`isMeta: true`) or system messages
- **THEN** the indexer SHALL skip these and extract metadata from the first actual user or assistant message

### Requirement: Session Timestamp Tracking
The indexer SHALL store timestamps in ISO-8601 format and track both first and last message times.

#### Scenario: Timestamp format
- **WHEN** timestamps are stored in the database
- **THEN** they SHALL be in ISO-8601 format with timezone (e.g., `2025-01-15T10:30:00.000Z`)

#### Scenario: Last timestamp stored
- **WHEN** a session file is indexed
- **THEN** the timestamp of the last user or assistant message SHALL be stored as `last_timestamp`

#### Scenario: Single-message session duration
- **WHEN** a session contains only one message (no last timestamp distinct from first)
- **THEN** `last_timestamp` SHALL equal `first_timestamp`
- **AND** duration SHALL display as "0s" or equivalent

#### Scenario: Duration calculation
- **WHEN** a session is selected in the UI
- **THEN** duration SHALL be calculated as `last_timestamp - first_timestamp`
- **AND** displayed in human-readable format (e.g., "2h 15m", "45m", "30s")

### Requirement: Agent Session Detection
The indexer SHALL identify sessions that were created by or involve sub-agents.

#### Scenario: Agent session flagged from message field
- **WHEN** any user or assistant message in a session file contains an `agentId` field
- **THEN** the session SHALL be marked with `is_agent = 1`

#### Scenario: Non-agent session
- **WHEN** no message in a session file contains an `agentId` field
- **THEN** the session SHALL be marked with `is_agent = 0`

### Requirement: Turn Statistics
The indexer SHALL count user and assistant turns during indexing.

#### Scenario: User turn counting
- **WHEN** a session file is indexed
- **THEN** the count of user messages where `isMeta` is not true SHALL be stored as `user_turns`

#### Scenario: Assistant turn counting
- **WHEN** a session file is indexed
- **THEN** the count of assistant messages SHALL be stored as `assistant_turns`

#### Scenario: Zero turns handled
- **WHEN** a session contains no user or assistant messages
- **THEN** `user_turns` and `assistant_turns` SHALL be 0

### Requirement: Tool Usage Statistics
The indexer SHALL count tool invocations from assistant message content.

#### Scenario: Tool use counting from content arrays
- **WHEN** an assistant message contains a content array
- **THEN** each item with `type: "tool_use"` SHALL increment `tool_use_count`

#### Scenario: String content has no tool use
- **WHEN** an assistant message content is a plain string (not an array)
- **THEN** it SHALL contribute 0 to `tool_use_count`

#### Scenario: Zero tool use
- **WHEN** no assistant messages contain tool_use items
- **THEN** `tool_use_count` SHALL be 0

### Requirement: Token Estimation
The indexer SHALL estimate total tokens based on text content word count.

#### Scenario: Token estimation from text content only
- **WHEN** a session file is indexed
- **THEN** `total_tokens_est` SHALL be calculated from text content only:
  - For string content: word count of the string
  - For array content: sum of word counts from `type: "text"` items only
  - Tool payloads, thinking blocks, and binary content SHALL be excluded

#### Scenario: Token multiplier
- **WHEN** total word count is calculated
- **THEN** `total_tokens_est` SHALL be `floor(word_count * 1.3)`

#### Scenario: Empty session tokens
- **WHEN** a session contains no text content
- **THEN** `total_tokens_est` SHALL be 0

### Requirement: Search Layer Metadata Exposure
The search layer SHALL expose all indexed metadata fields to the UI.

#### Scenario: Search results include new fields
- **WHEN** `search_sessions()` returns results
- **THEN** each `SearchResult` SHALL include: `cwd`, `git_branch`, `version`, `last_timestamp`, `is_agent`, `user_turns`, `assistant_turns`, `tool_use_count`, `total_tokens_est`

#### Scenario: NULL fields passed through
- **WHEN** a metadata field is NULL in the database
- **THEN** the corresponding `SearchResult` field SHALL be `None`

### Requirement: Enriched Session Details Display
The Session Details panel SHALL display all extracted session metadata with graceful handling of missing values.

#### Scenario: Full metadata display
- **WHEN** a session is selected in the UI
- **THEN** the Session Details panel SHALL display:
  - Session ID
  - Project path
  - Working directory (cwd)
  - Git branch
  - Claude version
  - Start time
  - Duration
  - Agent indicator (if is_agent = 1)
  - User turns
  - Assistant turns
  - Tool use count
  - Estimated tokens (labeled as approximate, e.g., "~1,234 tokens")

#### Scenario: Missing metadata display
- **WHEN** a metadata field is NULL (cwd, git_branch, version)
- **THEN** the UI SHALL display "Unknown" or omit the field
- **AND** SHALL NOT display empty strings or "null"

#### Scenario: Agent session indicator
- **WHEN** `is_agent = 1`
- **THEN** the Session Details panel SHALL display an indicator (e.g., "Agent Session" label or icon)
