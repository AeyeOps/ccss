.PHONY: help clean build dev tests test-syntax

help:
	@echo "Available targets:"
	@echo "  make clean  - Clean build artifacts, caches, pyc files (calls scripts/clean.sh; add CACHE=1 to prune uv cache)"
	@echo "  make build  - Build standalone binary (calls scripts/build_standalone.sh -> uv run ccss-build)"
	@echo "  make dev    - Run app with local source, logs to dev-app.log (calls scripts/dev.sh)"
	@echo "  make console-logs - Run textual console for live debugging (separate terminal)"
	@echo "  make tests  - Run all pytest tests (search, indexer, app interactions)"
	@echo "  make test-syntax - Run FTS5 syntax validation tests only"

clean:
	bash scripts/clean.sh

build:
	bash scripts/build_standalone.sh

dev:
	bash scripts/dev.sh

console-logs:
	bash scripts/console_logs.sh

tests:
	uv run pytest tests/ -v

test-syntax:
	uv run pytest tests/test_fts5_syntax.py -v
