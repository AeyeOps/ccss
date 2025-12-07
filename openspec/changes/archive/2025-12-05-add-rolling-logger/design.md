# Design: Rolling Logger

## Context

CCSS is a TUI application built with Textual. It needs structured logging that:
- Works with async event loops (Textual uses asyncio)
- Doesn't block the UI during log writes
- Provides consistent output format across all modules
- Manages disk space automatically

## Goals / Non-Goals

**Goals:**
- Single-module implementation (~200 lines)
- Line-count based rotation (not size-based)
- Structured format parseable by grep/awk
- Thread-safe for mixed sync/async usage
- Zero external dependencies (stdlib only)

**Non-Goals:**
- Log aggregation/shipping (out of scope)
- Log levels per-module (single global level)
- Async log rotation (blocking is acceptable for rare rotation events)
- Compression of individual log files (only ZIP archive)

## Decisions

### Decision 1: Custom Handler vs stdlib RotatingFileHandler

**Choice**: Custom `LineCountHandler` extending `logging.FileHandler`

**Rationale**: stdlib `RotatingFileHandler` uses byte size, not line count. Subclassing is simpler than wrapping:

```python
class LineCountHandler(logging.FileHandler):
    def __init__(self, filename: Path, max_lines: int = 2000, backup_count: int = 5):
        self.max_lines = max_lines
        self.backup_count = backup_count
        self.line_count = self._count_existing_lines(filename)  # Resume accurate count
        super().__init__(filename, mode='a', encoding='utf-8')

    def _count_existing_lines(self, filename: Path) -> int:
        """Count lines in existing log file for accurate rotation threshold."""
        if not filename.exists():
            return 0
        with open(filename, 'rb') as f:
            return sum(1 for _ in f)

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.line_count += 1
        if self.line_count >= self.max_lines:
            self._rotate()
```

### Decision 2: Log Format Implementation

**Choice**: Custom `logging.Formatter` subclass

**Rationale**: Allows clean separation of format logic:

```python
class CompactFormatter(logging.Formatter):
    LEVEL_MAP = {'ERROR': 'E', 'WARNING': 'W', 'INFO': 'I', 'DEBUG': 'D'}

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime('%y%m%d-%H%M%S') + f'.{int(record.msecs):03d}'
        level = self.LEVEL_MAP.get(record.levelname, '?')
        pid = f'{os.getpid() & 0xFFFF:04X}'  # Zero-padded: 002B, 0FED
        tid = f'{threading.current_thread().ident & 0xFFFF:04X}'  # Zero-padded: BAAD, F00D
        module = record.module[:8].ljust(8)  # Left-aligned, space-padded to 8 chars

        # Base message
        msg = f'{ts} {level} {pid} {tid} {module} {record.getMessage()}'

        # Append extra kwargs (use repr for strings with spaces)
        extras = {k: v for k, v in record.__dict__.items()
                  if k not in RESERVED_ATTRS and not k.startswith('_')}
        if extras:
            formatted = []
            for k, v in extras.items():
                if isinstance(v, str) and ' ' in v:
                    formatted.append(f'{k}={v!r}')
                else:
                    formatted.append(f'{k}={v}')
            msg += ' ' + ' '.join(formatted)
        return msg
```

### Decision 3: Archive Trigger Timing

**Choice**: Archive when 5th backup would be overwritten

**Rationale**: Simpler than async archive, and rotation is rare (every 10,000 lines = 5 rotations):

```
State: ccss.log, ccss.1.log, ccss.2.log, ccss.3.log, ccss.4.log, ccss.5.log
Event: ccss.log hits 2000 lines
Action:
  1. Archive ccss.1-5.log to ZIP
  2. Delete ccss.1-5.log
  3. Rename ccss.log → ccss.1.log
  4. Create fresh ccss.log
```

### Decision 4: Log Directory Location

**Choice**: `~/.cache/ccss/logs/`

**Rationale**: Follows XDG conventions, consistent with existing `CACHE_DIR` in settings.py:

```python
LOG_DIR = Path.home() / ".cache" / "ccss" / "logs"
ARCHIVE_DIR = LOG_DIR / "archive"
```

### Decision 5: Thread ID Representation

**Choice**: Lower 16 bits of thread ident, hex-encoded

**Rationale**: Full thread IDs are large (140XXXXXXXXXXXXXXX on Linux). Lower 16 bits provide sufficient uniqueness for correlation within a session:

```python
tid = threading.current_thread().ident
if tid is None:
    tid = 0
hex_tid = f'{tid & 0xFFFF:04X}'  # e.g., "0F3C"
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Blocking during rotation | Rotation is rare (~1 per 2000 log lines); sub-millisecond for rename ops |
| ZIP creation blocks UI | Archive only when all 5 backups exist (~10,000 lines between archives) |
| ZIP creation fails | Preserve backups, log to stderr, continue without archive |
| Line count drift if crash | Re-count on startup; append mode preserves partial logs |
| Thread safety | `logging` module is thread-safe by design; handler uses inherited lock |

## Module Structure

```
src/ccss/logger.py
├── Constants (LOG_DIR, ARCHIVE_DIR, MAX_LINES, BACKUP_COUNT)
├── CompactFormatter (format method)
├── LineCountHandler (emit, _rotate, _archive)
└── setup_logger() → logging.Logger
```

## API

```python
# In app.py or cli.py
from ccss.logger import setup_logger

logger = setup_logger()  # Returns configured logger
logger.info("Application started", version="0.1.0")
logger.debug("Search query", query=query, results=len(results))
logger.error("Failed to index", path=str(path), error=str(e))
```

## Open Questions

None - design is complete.
