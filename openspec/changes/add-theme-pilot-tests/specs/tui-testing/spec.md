# TUI Testing

Pilot API test coverage for the TUI application.

## ADDED Requirements

### Requirement: Theme Modal Navigation Testing

The test suite SHALL verify theme modal navigation behavior including opening, scrolling, and highlighting.

#### Scenario: Open theme modal and verify focus

- **WHEN** user presses Ctrl+T to open theme modal
- **THEN** ThemeScreen modal is pushed to screen stack
- **AND** OptionList widget has focus
- **AND** current theme is highlighted with marker

#### Scenario: Scroll down through theme list

- **WHEN** theme modal is open
- **AND** user presses down arrow or j key
- **THEN** highlighted index increases
- **AND** app does not crash

#### Scenario: Scroll up through theme list

- **WHEN** theme modal is open
- **AND** user presses up arrow or k key
- **THEN** highlighted index decreases
- **AND** app does not crash

#### Scenario: Scroll past list boundaries

- **WHEN** user scrolls past top or bottom of theme list
- **THEN** app does not crash
- **AND** highlighted index stays at boundary

### Requirement: Theme Selection Testing

The test suite SHALL verify theme selection behavior for both current and different themes.

#### Scenario: Select current theme

- **WHEN** theme modal is open
- **AND** current theme is highlighted
- **AND** user presses Enter to select
- **THEN** modal closes
- **AND** theme property remains unchanged
- **AND** no notification or state change occurs

#### Scenario: Select different theme

- **WHEN** theme modal is open
- **AND** user navigates to different theme
- **AND** user presses Enter to select
- **THEN** modal closes
- **AND** app.theme property changes to selected theme
- **AND** settings are persisted

#### Scenario: Cancel theme selection

- **WHEN** theme modal is open
- **AND** user presses Escape
- **THEN** modal closes
- **AND** theme property remains unchanged

### Requirement: Search Bar State Preservation Testing

The test suite SHALL verify that search bar content is preserved across theme modal operations.

#### Scenario: Empty search bar preserved after escape

- **GIVEN** search bar is empty
- **WHEN** user opens theme modal with Ctrl+T
- **AND** user closes modal with Escape
- **THEN** search bar remains empty
- **AND** no garbage characters appear

#### Scenario: Text preserved after escape

- **GIVEN** search bar contains text "test query"
- **WHEN** user opens theme modal with Ctrl+T
- **AND** user closes modal with Escape
- **THEN** search bar still contains "test query"
- **AND** no characters added or removed

#### Scenario: Text preserved after selecting same theme

- **GIVEN** search bar contains text
- **WHEN** user opens theme modal
- **AND** selects the current theme
- **THEN** search bar content is unchanged

#### Scenario: Text preserved after selecting different theme

- **GIVEN** search bar contains text "my search"
- **WHEN** user opens theme modal
- **AND** selects a different theme
- **THEN** search bar still contains "my search"
- **AND** no wacky or garbage characters appear in search bar

### Requirement: Theme Modal Edge Case Testing

The test suite SHALL verify theme modal handles edge cases gracefully.

#### Scenario: Rapid open/close cycles

- **WHEN** user rapidly opens and closes theme modal multiple times
- **THEN** app does not crash
- **AND** theme state remains consistent

#### Scenario: Theme change with search results displayed

- **GIVEN** search results are displayed in results list
- **WHEN** user opens theme modal
- **AND** selects a different theme
- **THEN** search results remain displayed
- **AND** results list content is unchanged
