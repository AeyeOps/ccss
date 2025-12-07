"""Rolling logger with line-count rotation and ZIP archival."""

from __future__ import annotations

import logging
import os
import sys
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

# Directory constants
LOG_DIR = Path.home() / ".cache" / "ccss" / "logs"
ARCHIVE_DIR = LOG_DIR / "archive"

# Rotation constants
MAX_LINES = 2000
BACKUP_COUNT = 5

# Reserved logging attributes (exclude from extra kwargs)
RESERVED_ATTRS = frozenset({
    "name", "msg", "args", "created", "filename", "funcName", "levelname",
    "levelno", "lineno", "module", "msecs", "pathname", "process",
    "processName", "relativeCreated", "stack_info", "exc_info", "exc_text",
    "thread", "threadName", "taskName", "message",
})


class CompactFormatter(logging.Formatter):
    """Format log entries as: yyMMdd-HHMMSS.mmm L PPPP TTTT module__ message [key=value...]"""

    LEVEL_MAP: ClassVar[dict[str, str]] = {
        "ERROR": "E",
        "WARNING": "W",
        "INFO": "I",
        "DEBUG": "D",
    }

    def format(self, record: logging.LogRecord) -> str:
        # Timestamp: yyMMdd-HHMMSS.mmm
        ts = datetime.now().strftime("%y%m%d-%H%M%S") + f".{int(record.msecs):03d}"

        # Level: single char
        level = self.LEVEL_MAP.get(record.levelname, "?")

        # Process ID: 4-char hex, zero-padded
        pid = f"{os.getpid() & 0xFFFF:04X}"

        # Thread ID: 4-char hex, zero-padded
        tid = threading.current_thread().ident
        if tid is None:
            tid = 0
        hex_tid = f"{tid & 0xFFFF:04X}"

        # Module: 8 chars, left-aligned, space-padded
        module = record.module[:8].ljust(8)

        # Base message
        msg = f"{ts} {level} {pid} {hex_tid} {module} {record.getMessage()}"

        # Append extra kwargs
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in RESERVED_ATTRS and not k.startswith("_")
        }
        if extras:
            formatted: list[str] = []
            for k, v in extras.items():
                if isinstance(v, str) and " " in v:
                    formatted.append(f"{k}={v!r}")
                else:
                    formatted.append(f"{k}={v}")
            msg += " " + " ".join(formatted)

        return msg


class LineCountHandler(logging.FileHandler):
    """File handler that rotates based on line count with ZIP archival."""

    def __init__(
        self,
        filename: Path,
        max_lines: int = MAX_LINES,
        backup_count: int = BACKUP_COUNT,
    ) -> None:
        self.base_filename = filename
        self.max_lines = max_lines
        self.backup_count = backup_count

        # Ensure directories exist
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Count existing lines for accurate rotation threshold
        self.line_count = self._count_existing_lines(filename)

        super().__init__(filename, mode="a", encoding="utf-8")

    def _count_existing_lines(self, filename: Path) -> int:
        """Count lines in existing log file."""
        if not filename.exists():
            return 0
        with open(filename, "rb") as f:
            return sum(1 for _ in f)

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()
        self.line_count += 1
        if self.line_count >= self.max_lines:
            self._rotate()

    def _rotate(self) -> None:
        """Rotate log files, archiving if backup window is full."""
        # Close current file
        self.close()

        # Check if we need to archive (5 backups already exist)
        backup_5 = LOG_DIR / f"ccss.{self.backup_count}.log"
        if backup_5.exists():
            self._archive()

        # Shift backups: 4→5, 3→4, 2→3, 1→2
        for i in range(self.backup_count - 1, 0, -1):
            src = LOG_DIR / f"ccss.{i}.log"
            dst = LOG_DIR / f"ccss.{i + 1}.log"
            if src.exists():
                src.rename(dst)

        # Current → backup 1
        if self.base_filename.exists():
            self.base_filename.rename(LOG_DIR / "ccss.1.log")

        # Reset counter and reopen fresh file
        self.line_count = 0
        self._open()

    def _archive(self) -> None:
        """Archive backup files to ZIP."""
        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        zip_path = ARCHIVE_DIR / f"ccss-{timestamp}.zip"

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for i in range(1, self.backup_count + 1):
                    backup = LOG_DIR / f"ccss.{i}.log"
                    if backup.exists():
                        zf.write(backup, backup.name)

            # Delete backups only after successful ZIP
            for i in range(1, self.backup_count + 1):
                backup = LOG_DIR / f"ccss.{i}.log"
                if backup.exists():
                    backup.unlink()

        except OSError as e:
            # Archive failed - preserve backups, log to stderr, continue
            print(f"Archive failed: {e}", file=sys.stderr)


class AppLogger:
    """Wrapper around logging.Logger that supports kwargs for extra context."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._logger.warning(msg, extra=kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._logger.error(msg, extra=kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        self._logger.exception(msg, extra=kwargs)


# Module-level logger instance (for idempotent setup)
_logger: AppLogger | None = None


def setup_logger(level: int = logging.INFO) -> AppLogger:
    """Create and configure the application logger.

    Returns the same logger instance on repeated calls (idempotent).
    """
    global _logger

    if _logger is not None:
        return _logger

    base_logger = logging.getLogger("ccss")
    base_logger.setLevel(level)

    # Prevent duplicate handlers
    if not base_logger.handlers:
        handler = LineCountHandler(LOG_DIR / "ccss.log")
        handler.setFormatter(CompactFormatter())
        base_logger.addHandler(handler)

    _logger = AppLogger(base_logger)
    return _logger


def get_logger() -> AppLogger:
    """Get the configured logger, setting it up if needed."""
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger
