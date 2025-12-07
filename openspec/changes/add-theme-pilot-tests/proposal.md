# Change: Add Theme Modal Pilot Tests

## Why

The theme selection modal (`ThemeScreen`) has minimal test coverage. The existing test only verifies that `Ctrl+T` opens the modal and `Escape` closes it. There's no testing of:
- Navigation within the theme list (scroll up/down)
- Theme selection behavior (current vs different theme)
- Search bar state preservation after theme operations
- A reported bug where selecting a theme causes garbage characters in the search bar

## What Changes

- Add comprehensive Pilot API tests for `ThemeScreen` modal interactions
- Test navigation: open modal, scroll through options, verify highlighting
- Test selection: select current theme (no change expected), select different theme (theme changes)
- Test search bar preservation: text entered before opening theme modal should remain after closing
- Test for character corruption bug: verify search bar doesn't get wacky characters after theme selection
- Test edge cases: escape without selection, rapid open/close cycles

## Impact

- Affected specs: `tui-testing` (new capability)
- Affected code: `tests/test_app_interactions.py`
- No breaking changes
- Increases test coverage for theme functionality
