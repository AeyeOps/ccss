## ADDED Requirements

### Requirement: Loading UX

The system SHALL display a loading screen with progress feedback during index initialization.

On launch, the app displays a skeleton UI structure immediately, with a visible progress indicator showing indexing status. Once indexing completes, the loading overlay is hidden and the main interface becomes interactive.

#### Scenario: First launch with large history
- **WHEN** the user launches ccss with 300+ session files
- **THEN** a loading screen appears within 100ms
- **AND** progress text shows current indexing status (e.g., "Indexing sessions...")
- **AND** the main UI appears when indexing completes

#### Scenario: Incremental update on subsequent launch
- **WHEN** the user launches ccss after previous use
- **THEN** the loading screen appears briefly during incremental index check
- **AND** transitions to main UI within 2 seconds for typical incremental updates

#### Scenario: Already indexed
- **WHEN** no files need indexing
- **THEN** the loading screen is shown for minimum 200ms to prevent flicker
- **AND** then transitions smoothly to main UI

---

### Requirement: Search Term Highlighting

The system SHALL highlight search term matches in the preview pane.

When viewing a session preview, all occurrences of the current search query are visually highlighted, making it easy to locate matches while scrolling through conversation content.

#### Scenario: Single term highlighting
- **WHEN** the user searches for "typescript"
- **AND** selects a result to preview
- **THEN** all occurrences of "typescript" in the preview are highlighted
- **AND** highlighting is case-insensitive

#### Scenario: Multiple term highlighting
- **WHEN** the user searches for "react hooks"
- **AND** selects a result to preview
- **THEN** both "react" and "hooks" are highlighted wherever they appear

#### Scenario: No search query
- **WHEN** viewing recent sessions (no search query)
- **THEN** no highlighting is applied to the preview

---

### Requirement: Theme Persistence

The system SHALL persist the user's theme selection across sessions.

Theme preference is stored in a cache file and restored on subsequent launches. The default theme is `textual-dark` if no preference is saved.

#### Scenario: Theme selection saved
- **WHEN** the user selects a theme via Ctrl+T
- **THEN** the selection is saved to `~/.cache/ccss/settings.json`
- **AND** the theme is applied immediately

#### Scenario: Theme restored on launch
- **WHEN** the user launches ccss after previously selecting a theme
- **THEN** the saved theme is applied before the UI is displayed

#### Scenario: Settings file missing
- **WHEN** the settings file does not exist
- **THEN** the default theme (`textual-dark`) is used
- **AND** a new settings file is created on first theme change

#### Scenario: Settings file corrupted
- **WHEN** the settings file cannot be parsed
- **THEN** the default theme is used
- **AND** the corrupted file is overwritten on next save

---

### Requirement: Research Search Performance

The system SHALL document a performance analysis plan for search optimization.

A research document SHALL be created identifying:
- Current performance bottlenecks
- Query optimization strategies
- Index structure improvements
- Caching opportunities
- Background indexing feasibility

#### Scenario: Research deliverable
- **WHEN** this change is implemented
- **THEN** a performance research document exists in the project
- **AND** it includes benchmark data for current search performance
- **AND** it proposes specific optimization strategies with trade-offs

---

## MODIFIED Requirements

### Requirement: Keyboard-Driven Interface

The system SHALL be fully operable via keyboard.

All primary actions are accessible through single-key bindings:
- Search input: `/` or start typing
- Navigation: `j`/`k` or arrows
- Select/Copy: `Enter` or `y`
- Toggle preview: `p`
- Toggle key hints: `Ctrl+K`
- Theme selection: `Ctrl+T`
- Quit: `q` or `Esc`

#### Scenario: Keyboard-only workflow
- **WHEN** the user operates ccss
- **THEN** all actions (search, navigate, preview, copy, theme, quit) are achievable via keyboard
- **AND** no mouse interaction is required

#### Scenario: Search on launch
- **WHEN** ccss is launched with a search argument (`ccss typescript`)
- **THEN** the search is pre-populated and results are shown immediately

#### Scenario: Toggle key hints
- **WHEN** the user presses Ctrl+K
- **THEN** the footer key hints are hidden or shown
- **AND** the toggle persists for the session

#### Scenario: Theme selection menu
- **WHEN** the user presses Ctrl+T
- **THEN** a theme selection menu appears
- **AND** the user can navigate and select a theme with keyboard

---

### Requirement: TUI Layout

The system SHALL present a terminal user interface with defined zones.

Layout zones:
1. **Loading overlay** (startup): Progress indicator during initialization
2. **Header** (top): Application title (no palette button)
3. **Search bar**: Text input for search query
4. **Results list** (middle): Scrollable list of matching sessions
5. **Preview pane** (bottom): Conversation excerpt from selected session
6. **Footer** (bottom): Keyboard shortcuts and result count (toggleable)

#### Scenario: Responsive layout
- **WHEN** the terminal is resized
- **THEN** the TUI adjusts to fit the new dimensions
- **AND** content remains readable

#### Scenario: Minimal terminal size
- **WHEN** the terminal is very small (< 80x24)
- **THEN** the TUI displays a warning or gracefully degrades

#### Scenario: Loading to main transition
- **WHEN** indexing completes
- **THEN** the loading overlay fades or hides
- **AND** the main content becomes visible and interactive
- **AND** focus moves to the search input
