# Design: Fix Keyboard UI

## Context
The CCSS app accidentally implemented Ctrl+K to hide/show the entire Footer widget. The intended behavior is to toggle Textual's built-in Help Panel (a right-side sidebar showing all key bindings), while the Footer remains visible with essential commands.

## Goals / Non-Goals
- **Goals**:
  - Ctrl+K toggles Textual's built-in Help Panel
  - Footer always visible with core commands
  - Clean header without clickable icons
- **Non-Goals**:
  - Command palette functionality (keep disabled)
  - Custom keys panel widget (use built-in)

## Decisions

### Help Panel Implementation
- **Decision**: Use Textual's built-in `action_show_help_panel()` / `action_hide_help_panel()`
- **Why**: Built-in feature, no custom code needed, consistent UX with other Textual apps
- **Alternative**: Custom KeysPanel widget - rejected, reinventing the wheel

### Binding Change
- **Decision**: Change Ctrl+K binding from `action_toggle_keys` to toggle help panel
- **Implementation**: Either bind to a wrapper action or use built-in action name
- **Code**: Remove `action_toggle_keys()` method at `app.py:533-536`

### Footer Bindings
- **Decision**: Show these bindings in footer (show=True):
  - q = Quit
  - / = Search
  - j/k = Down/Up (combined as "Nav")
  - Ctrl+K = Keys
  - Ctrl+T = Theme
- **Why**: User requested "core + navigation + ^Keys + ^Theme"

### Header Cleanup
- **Decision**: Keep ENABLE_COMMAND_PALETTE=False, no additional changes needed
- **Why**: This already disables the command palette icon in header

## Risks / Trade-offs
- Help Panel is Textual's default UI - may look different than expected (acceptable)
- Panel position controlled by Textual framework (right side, as expected)

## Open Questions
- None - using built-in feature simplifies implementation
