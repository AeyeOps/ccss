# Change: Add Claude Code Session Search (ccss)

## Why

Claude Code sessions accumulate across projects. Finding a specific session to resume—by topic, keyword, or code snippet—requires manually browsing through `/resume` output or grepping JSONL files. This friction interrupts workflow and discourages session reuse.

A dedicated search tool eliminates this friction by providing hyperfast full-text search across all session history with a keyboard-driven TUI for browsing results and resuming sessions.

## Problem Analysis

### Current State
- Sessions stored as JSONL in `~/.claude/projects/<project-hash>/`
- ~1000 files, ~400MB typical accumulation
- `/resume` shows recent sessions by timestamp, no content search
- Manual grep works but lacks context preview and is slow for large histories

### User Pain Points
1. **Lost context**: "I discussed X last week but can't find that session"
2. **Slow discovery**: Scrolling through recent sessions hoping to recognize one
3. **No content search**: Cannot search by what was discussed, only by recency
4. **Cross-project blindness**: Sessions organized by project path, not by topic

### Opportunity
Build a TUI tool that indexes all sessions and provides instant full-text search with session preview and one-key resume.

## What Changes

### New Capability: Session Search TUI

A standalone CLI/TUI application (`ccss`) that:

1. **Indexes session content** - Extracts searchable text from JSONL conversation history (including subagent sessions)
2. **Provides instant search** - SQLite FTS5 for sub-second results across all sessions
3. **Shows context preview** - Display matching excerpts with surrounding context
4. **Outputs session path** - Copy or display the full path to the session file for external use

### User Interface Concept

```
┌─ Claude Code Session Search ─────────────────────────────────────────────────┐
│ Search: typescript migration█                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ ▶ [Dec 01] -opt-ns: "help me migrate the typescript config..."               │
│   [Nov 28] -opt-ai-toolkit: "...typescript strict mode..."                   │
│   [Nov 25] -opt-christina: "...migration from javascript to typescript..."   │
│   [Nov 22] -opt-ns: "update tsconfig for the new typescript version..."      │
├──────────────────────────────────────────────────────────────────────────────┤
│ Preview:                                                                      │
│ User: help me migrate the typescript config to use strict mode               │
│ Assistant: I'll update your tsconfig.json to enable strict mode. First,      │
│ let me read the current configuration...                                     │
│                                                                               │
│ User: also update the eslint rules to match                                  │
│ Assistant: I'll align the ESLint TypeScript rules with the new strict...     │
└──────────────────────────────────────────────────────────────────────────────┘
│ [Enter] Copy Path  [j/k] Navigate  [/] Search  [q] Quit                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Interaction Model

| Key | Action |
|-----|--------|
| `/` or typing | Focus search input |
| `j` / `↓` | Next result |
| `k` / `↑` | Previous result |
| `Enter` or `y` | Copy session file path to clipboard |
| `p` | Toggle preview pane |
| `q` / `Esc` | Quit |

## Technical Approach

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ccss TUI (Textual)                       │
├─────────────────────────────────────────────────────────────────┤
│  Search Input → FTS Query → Results List → Preview → Resume    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                      Search Engine Layer                        │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  SQLite FTS5    │  │  Index Manager   │  │  JSONL Parser  │ │
│  │  (full-text)    │  │  (incremental)   │  │  (extraction)  │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                     ~/.claude/projects/                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  session-1.jsonl│  │  session-2.jsonl│  │  agent-*.jsonl  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Index Strategy: SQLite FTS5

Why SQLite FTS5:
- Fast full-text search (sub-second for millions of tokens)
- No external dependencies (Python stdlib sqlite3)
- Incremental updates (index new/modified files only)
- Porter stemming built-in (finds "migrate" when searching "migration")
- Phrase search support ("typescript strict mode")

Schema concept:
```sql
-- Sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    project_path TEXT,
    file_path TEXT,
    last_modified REAL,
    message_count INTEGER
);

-- FTS index for searchable content
CREATE VIRTUAL TABLE session_content USING fts5(
    session_id,
    role,           -- 'user' or 'assistant'
    content,        -- message text
    timestamp,
    content='',     -- contentless for smaller index
    tokenize='porter unicode61'
);
```

### JSONL Parsing

Extract from session files:
- `type: "user"` and `type: "assistant"` messages
- `message.content` (string or tool-use array)
- `sessionId`, `timestamp`, `cwd`
- Skip: `file-history-snapshot`, tool results, metadata

### Incremental Indexing

On startup:
1. Scan `~/.claude/projects/` for session files
2. Compare `mtime` against last indexed timestamp
3. Re-index only modified files
4. Prune deleted sessions from index

Index location: `~/.cache/ccss/sessions.db` (or XDG-compliant path)

### TUI Implementation

Framework: **Textual**
- Modern Python TUI framework
- Built-in widgets (Input, ListView, Static)
- CSS-like styling
- Async-native (non-blocking search)

Components:
- `SearchInput` - Text input with debounced search
- `ResultsList` - Scrollable list of matching sessions
- `PreviewPane` - Shows conversation excerpt
- `StatusBar` - Keyboard shortcuts, result count

### Path Output

When user presses Enter or `y`:
1. Extract file path from selected result
2. Copy full path to system clipboard (e.g., `/home/user/.claude/projects/-opt-ns/abc123.jsonl`)
3. Display confirmation in status bar
4. TUI remains open for additional searches

## Design Decisions

### Decision: SQLite FTS5 over alternatives

**Chosen**: SQLite FTS5

**Alternatives considered**:
- **Real-time grep**: Simple but slow for large histories (seconds, not milliseconds)
- **Tantivy (Rust)**: Faster but adds dependency complexity
- **In-memory index**: Fast but memory-heavy, requires rebuild each launch
- **Whoosh (Python)**: Pure Python but slower than FTS5, unmaintained

**Rationale**: FTS5 provides excellent performance with zero external dependencies. The Python sqlite3 module is stdlib. Incremental updates keep the index fresh without full rebuilds.

### Decision: Textual for TUI

**Chosen**: Textual

**Alternatives considered**:
- **prompt_toolkit**: Better for REPL/line input, less suited for full-screen apps
- **curses**: Low-level, no built-in widgets, platform quirks
- **Rich + manual layout**: Possible but reinvents widget management
- **blessed (Node)**: Wrong language

**Rationale**: Textual provides the widget library (Input, ListView) and layout system needed for this UI with minimal code. The loaded skill expertise supports this choice.

### Decision: Separate CLI tool (not Claude Code extension)

**Chosen**: Standalone `ccss` command

**Alternatives considered**:
- **MCP server**: Would require Claude Code running, adds complexity
- **Hook integration**: Limited to session events, not search
- **Plugin**: Harder to distribute, version-coupled

**Rationale**: A standalone tool can be invoked from any terminal, works without Claude Code running, and can be installed/updated independently.

## Scope

### In Scope (MVP)
- Full-text search across session content (user/assistant messages only)
- Index includes subagent session files
- Results list with project path and date
- Preview pane showing conversation excerpt
- Copy session file path to clipboard
- Vim-style keyboard navigation
- Incremental indexing

### Out of Scope (Future)
- Filtering by project, date range, or model
- Session tagging/bookmarking
- Session deletion from TUI
- Cross-machine sync
- Search result export
- Direct Claude Code resume integration
- Tool output indexing

## Impact

### Affected Specs
- New capability: `session-search` (new spec to be created)

### Affected Code
- New application: `src/ccss/` or similar structure
- Dependencies: textual, sqlite3 (stdlib)

### User Workflow Change
Before: `/resume` → scroll → hope to recognize session → guess
After: `ccss` → type keywords → instant results → copy path → use externally

## Success Criteria

1. **Search speed**: Results appear within 200ms of typing
2. **Index freshness**: New sessions searchable within 5 seconds of indexing
3. **Path copy works**: Clipboard contains valid session file path
4. **Keyboard-driven**: All actions achievable without mouse

---

*This proposal establishes the high-level design for ccss. Implementation details will be refined in design.md after approval.*
