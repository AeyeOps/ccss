.PHONY: help clean validate build tests dev test-syntax console-logs

help:
	@echo "Available targets:"
	@echo "  make validate  - Fix, format, lint, typecheck"
	@echo "  make build     - Validate then build standalone binary"
	@echo "  make tests     - Build then run all pytest tests"
	@echo "  make dev       - Run app with local source"
	@echo "  make clean     - Clean build artifacts and caches"

validate:
	uv run ruff check . --fix
	uv run ruff format .
	uv run ty check src/

clean:
	bash scripts/clean.sh

build: validate
	bash scripts/build_standalone.sh

dev:
	bash scripts/dev.sh

console-logs:
	bash scripts/console_logs.sh

tests: build
	uv run pytest tests/ -v

test-syntax:
	uv run pytest tests/test_fts5_syntax.py -v
