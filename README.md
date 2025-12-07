# CCSS - Claude Code Session Search

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Built with Textual](https://img.shields.io/badge/Built%20with-Textual-orange.svg)](https://textual.textualize.io/)

> Fast terminal UI for searching Claude Code conversation history

CCSS provides a keyboard-driven TUI for quickly finding and navigating your Claude Code session history. It indexes all your conversations using SQLite FTS5 full-text search, enabling instant search across thousands of sessions.

## Features

- **Full-text search** across all Claude Code sessions using SQLite FTS5
- **Real-time preview** of conversation content with search term highlighting
- **Keyboard-driven** navigation (vim-style j/k or arrow keys)
- **Session metadata** sidebar showing project, duration, token counts, and more
- **Theme support** with multiple built-in themes including a Claude-inspired dark theme
- **Clipboard integration** for copying session paths
- **Automatic indexing** with incremental updates on subsequent runs

## Installation

### Using pipx (recommended)

```bash
pipx install ccss
```

### Using pip

```bash
pip install ccss
```

### Using uv

```bash
uv tool install ccss
```

### From source

```bash
git clone https://github.com/aeyeops/ccss.git
cd ccss
uv sync
uv run ccss
```

## Usage

```bash
# Launch the TUI
ccss

# Launch with an initial search query
ccss "authentication"

# Force a full reindex
ccss --reindex

# Show index statistics
ccss --stats

# Show version
ccss --version
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search input |
| `j` / `Down` | Move down in results |
| `k` / `Up` | Move up in results |
| `Enter` / `y` | Copy session path to clipboard |
| `Ctrl+Y` | Copy path (works from anywhere) |
| `p` / `Ctrl+P` | Toggle preview pane |
| `Ctrl+K` | Toggle metadata sidebar |
| `F1` | Toggle FTS5 syntax reference |
| `Ctrl+T` | Change theme |
| `Ctrl+A` | Show about dialog |
| `Escape` / `q` | Quit |

## Search Syntax

CCSS uses SQLite FTS5 for powerful full-text search. Press `F1` in the app for the full syntax reference.

```
# Basic search
error

# Phrase search
"file not found"

# Boolean operators
error AND database
config OR settings
auth NOT test

# Prefix matching
config*

# Proximity search
NEAR(api key, 5)
```

## How It Works

CCSS indexes Claude Code session files stored in `~/.claude/projects/`. Each session's JSONL file contains the full conversation history including:

- User and assistant messages
- Tool calls and results
- Session metadata (project path, timestamps, etc.)

The index is stored in `~/.cache/ccss/sessions.db` and is automatically updated when new sessions are detected.

## Configuration

Settings are stored in `~/.cache/ccss/settings.json`:

- **theme**: Selected theme name (default: `cc-tribute`)

Available themes: `cc-tribute`, `textual-dark`, `textual-light`, `nord`, `gruvbox`, `tokyo-night`, `dracula`, `monokai`, `solarized-light`

## Related Projects

The Claude Code community has built several tools for session management:

- [claude-code-history-viewer](https://github.com/jhlee0409/claude-code-history-viewer) - Tauri-based desktop app with visual browsing
- [Claude Code Assist](https://marketplace.visualstudio.com/items?itemName=agsoft.claude-history-viewer) - VS Code extension for history browsing
- [claude-history](https://github.com/thejud/claude-history) - CLI tool for extracting conversation history
- [Claude Code History MCP](https://lobehub.com/mcp/tim0120-claude-code-history-mcp) - MCP server for AI-powered search

CCSS focuses on being a fast, lightweight terminal option for users who prefer keyboard-driven TUI workflows.

## Acknowledgments

CCSS is built with excellent open source tools:

- [Textual](https://textual.textualize.io/) - TUI framework for Python
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [SQLite FTS5](https://www.sqlite.org/fts5.html) - Full-text search engine

Special thanks to the Claude Code community for identifying the need for better session discovery tools (see GitHub issues [#394](https://github.com/anthropics/claude-code/issues/394), [#6912](https://github.com/anthropics/claude-code/issues/6912), [#8648](https://github.com/anthropics/claude-code/issues/8648)).

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with care by [AeyeOps](https://github.com/aeyeops)
