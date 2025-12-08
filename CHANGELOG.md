# Changelog

All notable changes to CCSS (Claude Code Session Search) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2025-12-08

### Added
- `make tests` target to run all pytest tests
- TestSearchHighlighting test class with 8 unit tests for term extraction and highlighting

### Changed
- Upgraded 15 weak tests from "didn't crash" assertions to meaningful state verification

## [0.2.1] - 2025-12-07

### Fixed
- Preview pane now shows messages containing search terms (was showing first messages only)
- Message content no longer truncated in preview (full content now visible)

### Added
- Development mode launcher (ccss-dev) with Textual CSS inspector (F12)
- PyInstaller build configuration for standalone binary distribution

## [0.2.0] - 2025-12-07

### Added
- AeyeOps branding with updated title and footer
- About dialog (Ctrl+A) showing version, license, and project info
- MIT License for open source release
- Professional README with installation, usage, and acknowledgments
- CHANGELOG to track version history

### Changed
- Application title now displays "AeyeOps | Claude Code Session Search"

## [0.1.0] - 2025-12-01

### Added
- Initial release
- Full-text search across Claude Code session history using SQLite FTS5
- TUI interface built with Textual
- Real-time preview of session content
- Keyboard-driven navigation (vim-style j/k, arrow keys)
- Session metadata sidebar (Ctrl+K)
- FTS5 syntax reference panel (F1)
- Theme selection (Ctrl+T) with cc-tribute default theme
- Clipboard integration for copying session paths
- Automatic session indexing with incremental updates
- Search term highlighting in preview
