.PHONY: help clean build dev

help:
	@echo "Available targets:"
	@echo "  make clean  - Clean build artifacts, caches, pyc files (calls scripts/clean.sh; add CACHE=1 to prune uv cache)"
	@echo "  make build  - Build standalone binary (calls scripts/build_standalone.sh -> uv run ccss-build)"
	@echo "  make dev    - Run app with local source, logs to dev-app.log (calls scripts/dev.sh)"
	@echo "  make console-logs - Run textual console for live debugging (separate terminal)"

clean:
	bash scripts/clean.sh

build:
	bash scripts/build_standalone.sh

dev:
	bash scripts/dev.sh

console-logs:
	bash scripts/console_logs.sh
