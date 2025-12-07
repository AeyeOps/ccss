# Change: Enhance UX Polish

## Why

The initial session search implementation works but has UX friction points that interrupt workflow. Load time is slow with no visual feedback, search term highlighting is missing in the preview pane, and the command palette approach adds unnecessary complexity when direct keybindings would be faster.

## What Changes

### 1. Loading UX with Progress Feedback

**Problem**: The app blocks during index build with no visual feedback—users see a blank screen for several seconds.

**Solution**: Display a skeleton UI immediately on launch with a loading indicator showing indexing progress. Refresh the full UI once indexing completes.

### 2. Search Term Highlighting in Preview

**Problem**: When viewing a session preview, the user cannot quickly locate where search terms appear in the conversation.

**Solution**: Highlight all occurrences of the search term in the preview pane, making matches visually distinct as the user scrolls.

### 3. Direct Keybindings Replace Palette

**Problem**: The command palette requires mouse interaction or multiple keystrokes to access simple toggles.

**Solution**:
- **Ctrl+K**: Toggle key hints display on/off
- **Ctrl+T**: Open theme selection menu
- Remove the palette button from the header

### 4. Theme Persistence

**Problem**: Theme selection is lost between sessions.

**Solution**: Save the selected theme to a cache file (`~/.cache/ccss/settings.json`) and restore on next launch.

### 5. Research: Search Performance Improvements

**Problem**: Search could be faster, especially for large session histories.

**Solution**: Document a research plan to investigate:
- Query optimization strategies
- Index structure improvements
- Caching frequently accessed results
- Background indexing options

## Impact

### Affected Specs
- **session-search**: Modified requirements for TUI Layout, Keyboard-Driven Interface; Added requirements for Loading UX, Search Highlighting, Theme Persistence

### Affected Code
- `src/ccss/app.py`: Loading screen, theme persistence, keybindings, highlight rendering
- `src/ccss/indexer.py`: Progress reporting callbacks
- New: Theme/settings cache management

### User Experience Change

Before:
- Blank screen during load
- No visual cue where search matches appear in preview
- Must use palette for theme/key toggles
- Theme resets each launch

After:
- Skeleton UI with progress bar during load
- Search terms highlighted in preview pane
- Ctrl+K toggles key hints, Ctrl+T opens theme menu
- Theme persists across sessions

## Open Questions

1. **Theme menu style**: Modal dialog vs inline dropdown? (Recommend: Modal for simplicity)
2. **Highlight style**: Bold + background color vs underline? (Recommend: Background highlight matching theme accent)
