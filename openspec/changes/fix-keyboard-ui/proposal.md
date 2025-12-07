# Change: Fix Keyboard UI Behavior

## Why
The current Ctrl+K binding incorrectly hides the entire Footer widget instead of toggling Textual's built-in Help Panel. The Footer should remain visible at all times showing core navigation hints, while Ctrl+K should toggle the Help Panel (a right-side sidebar displaying all available key bindings).

## What Changes
- **BREAKING**: Change Ctrl+K to use Textual's built-in `action_show_help_panel()` / `action_hide_help_panel()` instead of hiding Footer
- Remove custom `action_toggle_keys()` that hides Footer
- Keep Footer always visible with core navigation commands
- Remove clickable command palette icon from header (already disabled, ensure no visual remnant)

## Impact
- Affected specs: ui (new capability spec)
- Affected code: `src/ccss/app.py:533-536` (remove custom action_toggle_keys, update binding)
