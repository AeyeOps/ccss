# UI Keyboard Controls

## ADDED Requirements

### Requirement: Help Panel Toggle
The application SHALL use Textual's built-in Help Panel to display all available keyboard bindings when toggled.

#### Scenario: Toggle help panel visibility
- **WHEN** user presses Ctrl+K
- **THEN** Textual's built-in Help Panel toggles between visible and hidden states

#### Scenario: Help panel displays all bindings
- **WHEN** Help Panel is visible
- **THEN** it displays all keyboard bindings including those not shown in footer

#### Scenario: Help panel position
- **WHEN** Help Panel is visible
- **THEN** it appears as a sidebar on the right side of the screen

### Requirement: Persistent Footer
The application SHALL display a Footer widget that remains visible at all times showing core navigation commands.

#### Scenario: Footer always visible
- **WHEN** user performs any action including toggling Help Panel
- **THEN** the Footer remains visible

#### Scenario: Footer displays core bindings
- **WHEN** application is running
- **THEN** the Footer displays: Quit (q), Search (/), navigation hints, Keys (Ctrl+K), Theme (Ctrl+T)

### Requirement: Clean Header
The application SHALL display a Header without clickable command palette icons.

#### Scenario: No command palette icon
- **WHEN** application is running
- **THEN** the header does not display a clickable command palette icon in the top-left corner
