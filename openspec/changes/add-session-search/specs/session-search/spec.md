## ADDED Requirements

### Requirement: Session Indexing

The system SHALL index Claude Code session files for full-text search.

Session files are JSONL files located in `~/.claude/projects/*/`. The indexer extracts user and assistant message content, storing it in a searchable format with associated metadata (session ID, project path, timestamp).

The index SHALL support incremental updates—only modified files are re-indexed on subsequent runs.

#### Scenario: Initial index build
- **WHEN** the user runs ccss for the first time
- **THEN** all session files in `~/.claude/projects/` are indexed
- **AND** the index is stored in a persistent location

#### Scenario: Incremental index update
- **WHEN** the user runs ccss after previous use
- **THEN** only session files modified since last index are re-indexed
- **AND** deleted sessions are removed from the index

#### Scenario: Large history performance
- **WHEN** the user has 1000+ session files
- **THEN** initial indexing completes within 60 seconds
- **AND** incremental updates complete within 5 seconds

---

### Requirement: Full-Text Search

The system SHALL provide full-text search across indexed session content.

Search uses SQLite FTS5 with porter stemming, enabling:
- Single word search ("typescript")
- Phrase search ("strict mode")
- Prefix search ("migrat*")
- Boolean operators (implicit AND between terms)

Results SHALL be ranked by relevance and sorted by recency as secondary criterion.

#### Scenario: Single word search
- **WHEN** the user searches "migration"
- **THEN** sessions containing "migration", "migrate", "migrating" are returned
- **AND** results are ranked by relevance

#### Scenario: Phrase search
- **WHEN** the user searches "typescript strict mode" (quoted or unquoted)
- **THEN** sessions containing that phrase or those terms in proximity are prioritized

#### Scenario: No results
- **WHEN** the user searches for a term not in any session
- **THEN** an empty result set is returned
- **AND** the UI indicates no matches found

---

### Requirement: Search Results Display

The system SHALL display search results in a navigable list.

Each result shows:
- Project identifier (derived from project path)
- Session date
- Matching excerpt with search terms highlighted

Results SHALL be keyboard-navigable using vim-style keys (j/k) or arrow keys.

#### Scenario: Results list navigation
- **WHEN** search returns multiple results
- **THEN** the user can navigate with j/k or arrow keys
- **AND** the selected result is visually highlighted

#### Scenario: Result metadata display
- **WHEN** a result is displayed
- **THEN** it shows the project name and date
- **AND** it shows a snippet of matching content

---

### Requirement: Session Preview

The system SHALL display a preview of the selected session's conversation.

The preview pane shows message exchanges (user and assistant) surrounding the matched content, providing context for the search result.

#### Scenario: Preview pane content
- **WHEN** a search result is selected
- **THEN** the preview pane shows conversation excerpts from that session
- **AND** the matched search terms are visible in context

#### Scenario: Preview toggle
- **WHEN** the user presses the preview toggle key
- **THEN** the preview pane expands or collapses
- **AND** the results list adjusts accordingly

---

### Requirement: Path Output

The system SHALL copy the selected session's file path to the clipboard.

When the user confirms selection (Enter or `y` key), the full path to the session JSONL file is copied to the system clipboard for external use.

#### Scenario: Copy path to clipboard
- **WHEN** the user presses Enter or `y` on a selected result
- **THEN** the session file path is copied to the system clipboard
- **AND** a confirmation message appears in the status bar

#### Scenario: Path format
- **WHEN** the path is copied
- **THEN** it is the full absolute path (e.g., `/home/user/.claude/projects/-opt-ns/abc123.jsonl`)
- **AND** the TUI remains open for additional searches

---

### Requirement: Keyboard-Driven Interface

The system SHALL be fully operable via keyboard.

All primary actions are accessible through single-key bindings:
- Search input: `/` or start typing
- Navigation: `j`/`k` or arrows
- Select/Resume: `Enter`
- Quit: `q` or `Esc`

#### Scenario: Keyboard-only workflow
- **WHEN** the user operates ccss
- **THEN** all actions (search, navigate, preview, resume, quit) are achievable via keyboard
- **AND** no mouse interaction is required

#### Scenario: Search on launch
- **WHEN** ccss is launched with a search argument (`ccss typescript`)
- **THEN** the search is pre-populated and results are shown immediately

---

### Requirement: TUI Layout

The system SHALL present a terminal user interface with defined zones.

Layout zones:
1. **Search bar** (top): Text input for search query
2. **Results list** (middle): Scrollable list of matching sessions
3. **Preview pane** (bottom): Conversation excerpt from selected session
4. **Status bar** (footer): Keyboard shortcuts and result count

#### Scenario: Responsive layout
- **WHEN** the terminal is resized
- **THEN** the TUI adjusts to fit the new dimensions
- **AND** content remains readable

#### Scenario: Minimal terminal size
- **WHEN** the terminal is very small (< 80x24)
- **THEN** the TUI displays a warning or gracefully degrades
