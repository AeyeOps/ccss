## Implementation Tasks

### 1. Project Setup
- [x] 1.1 Initialize UV project structure
- [x] 1.2 Configure pyproject.toml with dependencies (textual, etc.)
- [x] 1.3 Set up Ruff and Pyright configuration
- [x] 1.4 Create basic CLI entry point with Typer

### 2. Session Indexing
- [x] 2.1 Implement JSONL parser for session files
- [x] 2.2 Create SQLite FTS5 schema
- [x] 2.3 Build initial index from all session files
- [x] 2.4 Implement incremental indexing (mtime comparison)
- [x] 2.5 Handle deleted session cleanup

### 3. Search Engine
- [x] 3.1 Implement FTS5 query interface
- [x] 3.2 Add result ranking and sorting (by recency)
- [x] 3.3 Support phrase and prefix search
- [x] 3.4 Extract result snippets with context

### 4. TUI Components
- [x] 4.1 Create main App class (Textual)
- [x] 4.2 Implement SearchInput widget
- [x] 4.3 Implement ResultsList widget
- [x] 4.4 Implement PreviewPane widget
- [x] 4.5 Add StatusBar with key hints
- [x] 4.6 Wire up keyboard bindings

### 5. Path Output
- [x] 5.1 Extract file path from selection
- [x] 5.2 Copy to system clipboard (pyperclip)
- [x] 5.3 Display confirmation in status bar

### 6. Polish
- [x] 6.1 Add CLI argument for initial search query
- [x] 6.2 Test with large session histories (332 sessions, 4603 messages)
- [x] 6.3 Validate keyboard-only workflow
- [x] 6.4 Document installation and usage (via --help)

---

*Implementation complete.*
