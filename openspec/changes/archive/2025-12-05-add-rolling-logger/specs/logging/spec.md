# Logging

Structured rolling logger with automatic archival.

## ADDED Requirements

### Requirement: Structured Log Format

The logger SHALL produce log entries in the format:
`yyMMdd-HHMMSS.mmm L PPPP TTTT module__ message [key=value...]`

Where:
- `yyMMdd-HHMMSS.mmm` - Timestamp with milliseconds
- `L` - Single-char level (E/W/I/D for ERROR/WARNING/INFO/DEBUG)
- `PPPP` - Process ID as 4-char uppercase hex, zero-padded (e.g., `0FED`, `002B`)
- `TTTT` - Thread ID as 4-char uppercase hex, zero-padded (e.g., `BAAD`, `F00D`)
- `module__` - Source module name, left-aligned, space-padded to 8 chars
- `message` - Log message text
- `key=value` - Optional extra arguments

#### Scenario: Standard log entry format

- **WHEN** a log entry is written with level INFO, message "query executed", and extra args query="test" results=42
- **THEN** the output line SHALL match pattern `\d{6}-\d{6}\.\d{3} I [0-9A-F]{4} [0-9A-F]{4} .{8} query executed query=test results=42`

#### Scenario: Hex ID zero-padding

- **WHEN** the process ID is 43 (0x002B) and thread ID is 4013 (0x0FAD)
- **THEN** the log entry SHALL contain `002B 0FAD`

#### Scenario: Module name formatting

- **WHEN** a log entry is written from module "search"
- **THEN** the module field SHALL be left-aligned as "search  " (space-padded to 8 chars)

#### Scenario: Module name truncation

- **WHEN** a log entry is written from module "longmodulename"
- **THEN** the module field SHALL be truncated to 8 characters as "longmodu"

#### Scenario: Level character mapping

- **WHEN** log entries are written at each level
- **THEN** ERROR maps to "E", WARNING maps to "W", INFO maps to "I", DEBUG maps to "D"

### Requirement: Extra Arguments Formatting

The logger SHALL format extra key-value pairs using Python repr() for non-primitive values.

#### Scenario: Simple values unquoted

- **WHEN** extra args are `count=5` and `active=True`
- **THEN** the suffix SHALL be `count=5 active=True`

#### Scenario: String values with spaces quoted

- **WHEN** extra arg is `query="hello world"`
- **THEN** the suffix SHALL be `query='hello world'` (repr-escaped)

#### Scenario: Reserved attributes excluded

- **WHEN** extra arguments include Python logging reserved names (name, msg, args, etc.)
- **THEN** those attributes SHALL NOT appear in the key=value suffix

### Requirement: Line-Count Rotation

The logger SHALL rotate log files when a file reaches 2000 lines.

#### Scenario: Rotation at line threshold

- **WHEN** the active log file reaches 2000 lines
- **THEN** the logger SHALL close the current file
- **AND** rename `ccss.log` to `ccss.1.log`, shifting existing backups (`ccss.1.log` → `ccss.2.log`, etc.)
- **AND** create a fresh `ccss.log` for new entries

#### Scenario: Backup count limit

- **WHEN** rotation occurs and 5 backup files already exist
- **THEN** the logger SHALL archive the 5 backups before rotating

### Requirement: Startup Line Count Recovery

The logger SHALL count existing lines on initialization to maintain accurate rotation thresholds.

#### Scenario: Resume after restart

- **WHEN** the logger initializes and `ccss.log` exists with 1500 lines
- **THEN** the line counter SHALL start at 1500
- **AND** rotation SHALL trigger after 500 more lines (reaching 2000)

#### Scenario: Fresh start

- **WHEN** the logger initializes and `ccss.log` does not exist
- **THEN** the line counter SHALL start at 0

### Requirement: ZIP Archival

The logger SHALL archive rotated log files to ZIP when the backup window fills.

#### Scenario: Archive creation

- **WHEN** 5 backup files exist and rotation is triggered
- **THEN** the logger SHALL create a ZIP file named `ccss-{yyMMdd-HHMMSS}.zip` in the archive directory
- **AND** the ZIP SHALL contain `ccss.1.log` through `ccss.5.log`
- **AND** the original backup files SHALL be deleted after successful ZIP creation

#### Scenario: Archive failure handling

- **WHEN** ZIP creation fails (disk full, permission error, etc.)
- **THEN** the backup files SHALL NOT be deleted
- **AND** an error SHALL be logged to stderr
- **AND** the logger SHALL continue operating (skip archive, proceed with rotation)

#### Scenario: Archive directory structure

- **WHEN** the logger initializes
- **THEN** the archive directory SHALL be created at `~/.cache/ccss/logs/archive/` if it does not exist

### Requirement: Log Directory Location

The logger SHALL write logs to the user's cache directory.

#### Scenario: Default log path

- **WHEN** the logger initializes
- **THEN** logs SHALL be written to `~/.cache/ccss/logs/ccss.log`

#### Scenario: Directory creation

- **WHEN** the log directory does not exist
- **THEN** the logger SHALL create `~/.cache/ccss/logs/` with parent directories

### Requirement: Thread Safety

The logger SHALL be safe for concurrent use from multiple threads.

#### Scenario: Concurrent logging

- **WHEN** multiple threads write log entries simultaneously
- **THEN** entries SHALL NOT be interleaved or corrupted
- **AND** the line count SHALL remain accurate

### Requirement: Logger Factory

The module SHALL provide a `setup_logger()` function that returns a configured logger.

#### Scenario: Logger initialization

- **WHEN** `setup_logger()` is called
- **THEN** it SHALL return a `logging.Logger` instance configured with `CompactFormatter` and `LineCountHandler`
- **AND** the default level SHALL be INFO

#### Scenario: Idempotent setup

- **WHEN** `setup_logger()` is called multiple times
- **THEN** it SHALL return the same logger instance without adding duplicate handlers
