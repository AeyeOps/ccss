# Tasks: Add Rolling Logger

## 1. Core Implementation

- [x] 1.1 Create `src/ccss/logger.py` with module constants
- [x] 1.2 Implement `CompactFormatter` class with structured format
- [x] 1.3 Implement `LineCountHandler` with rotation logic
- [x] 1.4 Implement ZIP archival in `_archive()` method
- [x] 1.5 Implement `setup_logger()` factory function

## 2. Integration

- [x] 2.1 Add logger initialization to `app.py` startup
- [x] 2.2 Replace any existing print-based debugging with logger calls

## 3. Verification

- [x] 3.1 Verify log format matches specification
- [x] 3.2 Verify rotation triggers at 2000 lines
- [x] 3.3 Verify archive creates valid ZIP with 5 log files
- [x] 3.4 Verify pyright strict passes
- [x] 3.5 Verify ruff lint passes
