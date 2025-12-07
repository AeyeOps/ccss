# Design: UX Polish Enhancements

## Context

The ccss TUI application is functional but has UX gaps that create friction. This design addresses loading feedback, search highlighting, keyboard-first interactions, and theme persistence.

## Goals / Non-Goals

### Goals
- Immediate visual feedback during app startup
- Quick identification of search matches in preview
- Single-keystroke access to common toggles
- Persistent user preferences

### Non-Goals
- Comprehensive settings management
- Complex theming system
- Background/daemon indexing mode

## Decisions

### 1. Loading Screen Architecture

**Decision**: Use Textual's reactive mounting pattern with a loading overlay.

**Approach**:
```
compose() creates:
├── LoadingOverlay (visible initially)
│   ├── ProgressBar
│   └── StatusText ("Indexing 45 of 332 sessions...")
└── MainContent (hidden initially)
    ├── Header
    ├── SearchInput
    ├── ResultsList
    ├── PreviewPane
    └── Footer
```

**Flow**:
1. `compose()` yields both LoadingOverlay and MainContent
2. MainContent is hidden via CSS (`display: none`)
3. `on_mount()` starts async indexing with progress callback
4. Progress callback updates LoadingOverlay
5. On completion, hide LoadingOverlay, show MainContent, focus search

**Alternatives considered**:
- **Screen switching**: More complex, loses state during transition
- **Single-phase blocking**: Current approach, poor UX
- **Worker thread + polling**: Unnecessary complexity for SQLite operations

### 2. Search Term Highlighting

**Decision**: Use Rich markup to highlight matches in preview text.

**Approach**:
- Store current search query in app state
- When rendering preview, wrap search term matches with Rich markup: `[reverse]{term}[/reverse]`
- Use case-insensitive matching
- Highlight all occurrences, not just first

**Implementation**:
```python
def highlight_matches(text: str, query: str) -> str:
    if not query:
        return text
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(lambda m: f"[reverse]{m.group(0)}[/reverse]", text)
```

**Alternatives considered**:
- **Custom widget with styled spans**: More flexible but overkill for text highlighting
- **FTS5 snippet with markers**: Only returns small excerpt, not full message

### 3. Theme Persistence

**Decision**: Simple JSON file in cache directory.

**Location**: `~/.cache/ccss/settings.json`

**Schema**:
```json
{
  "theme": "textual-dark"
}
```

**Flow**:
1. On app init, load settings (create with defaults if missing)
2. Apply saved theme before mounting
3. On theme change, write to settings file immediately
4. No validation beyond JSON parsing (fail-fast if corrupted)

**Alternatives considered**:
- **YAML config**: Extra dependency, overkill for one setting
- **Environment variable**: Awkward for interactive selection
- **Database storage**: Already have DB, but mixing concerns

### 4. Keybindings

**Decision**: Direct bindings without command palette.

**New bindings**:
| Key | Action | Implementation |
|-----|--------|----------------|
| `Ctrl+K` | Toggle footer key hints | `action_toggle_keys()` sets `Footer.show = not Footer.show` |
| `Ctrl+T` | Open theme menu | `action_show_theme_menu()` pushes theme selection screen |

**Theme menu**:
- Use Textual's `OptionList` in a modal
- List available themes: `textual-dark`, `textual-light`, `nord`, `gruvbox`, `tokyo-night`
- On selection, apply theme and save to settings

**Header changes**:
- Set `Header(show_clock=False)` or use custom header without command palette button
- Remove any palette-related bindings

### 5. Research: Search Performance

**Investigation areas**:

1. **Query optimization**:
   - Profile current FTS5 query execution time
   - Test `bm25()` ranking function (currently disabled due to external content table)
   - Consider denormalizing session metadata into FTS table

2. **Index structure**:
   - Benchmark contentless FTS vs stored content
   - Evaluate trigram tokenizer for partial matching
   - Test column-based vs single-content indexing

3. **Caching**:
   - Cache recent session previews in memory
   - Consider SQLite WAL mode for concurrent reads
   - Profile hot paths with cProfile

4. **Background indexing**:
   - Evaluate file watcher (watchdog) for live updates
   - Consider subprocess index building
   - Benchmark incremental vs full rebuild thresholds

**Deliverable**: Performance analysis document with benchmark data and recommendations.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Loading overlay flickers on fast systems | Add minimum 200ms display time |
| Regex highlighting slow on large text | Limit preview text length (already capped at 500 chars) |
| Settings file corruption | Delete and recreate with defaults on parse error |
| Theme not found | Fall back to `textual-dark` |

## Migration Plan

No migration needed—all changes are additive:
- New settings file created on first run
- Existing index unchanged
- No breaking API changes

## Open Questions

1. Should we show index statistics in the loading screen (e.g., "332 sessions, 4603 messages")?
2. Should Ctrl+T cycle themes directly or show a menu? (Recommend: menu for discoverability)
