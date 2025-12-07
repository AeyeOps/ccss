# Tasks: Fix Keyboard UI

## 1. Fix Ctrl+K to Toggle Keys Panel
- [x] 1.1 Created custom `HelpPanel` widget showing key bindings reference
- [x] 1.2 Update Ctrl+K binding to `toggle_keys_panel` action
- [x] 1.3 Implemented `action_toggle_keys_panel()` to show/hide panel via CSS class

## 2. Add F1 Syntax Help Panel
- [x] 2.1 Created `SyntaxPanel` widget showing FTS5 syntax reference
- [x] 2.2 Added F1 binding to `toggle_syntax_panel` action
- [x] 2.3 Panels are mutually exclusive (only one visible at a time)

## 3. Footer and Header
- [x] 3.1 Footer is always visible (no hide logic)
- [x] 3.2 ENABLE_COMMAND_PALETTE=False removes command palette icon

## 4. Testing
- [x] 4.1 Verify Ctrl+K toggles keys panel on right side
- [x] 4.2 Verify Footer remains visible when panel is toggled
- [x] 4.3 Updated demo.py to use `action_toggle_keys_panel()`
- [x] 4.4 Updated test to check `.visible` CSS class correctly
- [x] 4.5 All 39 tests passing
