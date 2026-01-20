.PHONY: help clean build dev tests test-syntax format lint typecheck check

help:
	@echo "Available targets:"
	@echo "  make build       - Format, lint, typecheck, then build standalone binary"
	@echo "  make check       - Run format + lint + typecheck (no build)"
	@echo "  make format      - Format code with ruff"
	@echo "  make lint        - Lint code with ruff"
	@echo "  make typecheck   - Type check with ty"
	@echo "  make tests       - Run all pytest tests"
	@echo "  make test-syntax - Run FTS5 syntax validation tests only"
	@echo "  make dev         - Run app with local source, logs to dev-app.log"
	@echo "  make clean       - Clean build artifacts, caches, pyc files"

format:
	uv run ruff format .

lint:
	uv run ruff check . --fix

typecheck:
	uv run ty check src/

check: format lint typecheck

clean:
	bash scripts/clean.sh

build: check
	bash scripts/build_standalone.sh

dev:
	bash scripts/dev.sh

console-logs:
	bash scripts/console_logs.sh

tests: build
	uv run pytest tests/ -v

test-syntax:
	uv run pytest tests/test_fts5_syntax.py -v
