# Change: Add Rolling Logger with Archive Support

## Why

CCSS needs structured logging for debugging and operational visibility. Current print-based output offers no persistence, rotation, or archival. A production-grade rolling logger enables:
- Post-mortem debugging without reproducing issues
- Operational monitoring with structured, parseable output
- Bounded disk usage via automatic rotation and archival

## What Changes

- **ADDED**: `src/ccss/logger.py` - Rolling logger with line-count rotation
- **ADDED**: Structured log format: `yyMMdd-HHMMSS.999 L PPPP TTTT module message key=value...`
- **ADDED**: Automatic rotation at 2000 lines with 5-file window
- **ADDED**: ZIP archival when rotation window fills
- **ADDED**: Logger integration in app lifecycle

## Format Specification

```
250605-143022.847 I 1A2B 0F3C search query="test" results=42
│      │          │ │    │    │      └─ key=value pairs (extra args)
│      │          │ │    │    └─ module name
│      │          │ │    └─ thread ID (hex, 4-char padded)
│      │          │ └─ process ID (hex, 4-char padded)
│      │          └─ level: E=ERROR, W=WARNING, I=INFO, D=DEBUG
│      └─ timestamp: HHMMSS.mmm (milliseconds)
└─ date: yyMMdd
```

## Rotation Behavior

1. Log to `ccss.log` until 2000 lines reached
2. Rotate: `ccss.log` → `ccss.1.log`, `ccss.1.log` → `ccss.2.log`, etc.
3. When `ccss.5.log` would overflow, archive all 5 to ZIP
4. ZIP naming: `ccss-{yyMMdd-HHMMSS}.zip`
5. Delete archived `.log` files after successful ZIP creation

## Impact

- Affected specs: None (new capability)
- Affected code: `src/ccss/app.py` (logger initialization)
- New files: `src/ccss/logger.py`
- Disk impact: ~5MB max before archival (5 × 2000 lines × ~500 bytes)
