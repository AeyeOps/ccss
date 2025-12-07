## Implementation Tasks

### 1. Loading UX
- [x] 1.1 Create LoadingOverlay widget with progress bar and status text
- [x] 1.2 Modify `compose()` to yield both LoadingOverlay and MainContent
- [x] 1.3 Add async indexing with progress callback to `on_mount()`
- [x] 1.4 Implement overlay-to-main transition on index completion
- [x] 1.5 Add minimum 200ms display time to prevent flicker

### 2. Search Term Highlighting
- [x] 2.1 Store current search query in app state
- [x] 2.2 Create `highlight_matches()` function using Rich markup
- [x] 2.3 Apply highlighting in `_update_preview()` method
- [x] 2.4 Test with single terms, multiple terms, and case variations

### 3. Theme Persistence
- [x] 3.1 Create settings module with load/save functions
- [x] 3.2 Define settings schema (JSON with `theme` field)
- [x] 3.3 Load settings on app init, apply theme before mounting
- [x] 3.4 Save settings on theme change

### 4. Keyboard Shortcuts
- [x] 4.1 Add Ctrl+K binding for `action_toggle_keys()`
- [x] 4.2 Implement `action_toggle_keys()` to show/hide Footer
- [x] 4.3 Add Ctrl+T binding for `action_show_theme_menu()`
- [x] 4.4 Implement theme selection modal using OptionList
- [x] 4.5 Wire theme selection to persistence and app.theme

### 5. Header Cleanup
- [x] 5.1 Configure Header to disable command palette button
- [x] 5.2 Verify no palette-related bindings remain
- [x] 5.3 Test that Ctrl+P and other palette shortcuts are inactive

### 6. Research Document
- [x] 6.1 Profile current search performance with cProfile
- [x] 6.2 Benchmark FTS5 query times for various query types
- [x] 6.3 Document findings in `docs/performance-research.md`
- [x] 6.4 Propose 2-3 optimization strategies with trade-offs

### 7. Verification
- [x] 7.1 Test loading UX with empty index (first run)
- [x] 7.2 Test loading UX with large index (300+ sessions)
- [x] 7.3 Test search highlighting with various query patterns
- [x] 7.4 Test theme persistence across app restarts
- [x] 7.5 Verify all keybindings work correctly
- [x] 7.6 Run Pyright and Ruff checks

---

*Implementation complete.*
