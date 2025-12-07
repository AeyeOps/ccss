# Make Integration for CLI Tools

Patterns for integrating Python CLI applications with Make in mono-repos, enabling convenient command execution from the repository root.

## Use Case

Mono-repos with multiple CLI applications benefit from centralized command access:

**Without Make integration:**
```bash
cd apps/vendor-analysis && uv run vendor-analysis sync --vendors-only
cd ../data-processor && uv run data-processor transform --format csv
cd ../api-client && uv run api-client fetch --limit 100
```

**With Make integration:**
```bash
make vendor-analysis sync --vendors-only
make data-processor transform --format csv
make api-client fetch --limit 100
```

**Benefits:**
- Run from repo root (no cd required)
- Consistent interface across apps
- Shorter commands
- Easy to remember

---

## The Challenge: Flag Handling

Make interprets `--flags` as Make options, not CLI parameters.

### Problem Example

```makefile
# ❌ WRONG - Make consumes --vendors-only
vendor-analysis:
    uv run vendor-analysis $(MAKECMDGOALS)
```

```bash
make vendor-analysis sync --vendors-only
# Error: make: invalid option -- 'v'
# Make tries to interpret --vendors-only as Make option!
```

---

## Solution: ARGS Variable Pattern

Use a Make variable to pass flags to the CLI command.

### Makefile Implementation

```makefile
# Makefile at repo root

.PHONY: vendor-analysis

vendor-analysis:
    @cd apps/vendor-analysis && uv run vendor-analysis $(ARGS) $(filter-out $@,$(MAKECMDGOALS))

# Catch-all rule to prevent Make treating args as targets
%:
    @:
```

**Explanation:**
- `@cd apps/vendor-analysis` - Navigate to app directory
- `uv run vendor-analysis` - Run CLI command
- `$(ARGS)` - Pass ARGS variable (for --flags)
- `$(filter-out $@,$(MAKECMDGOALS))` - Pass positional arguments
- `%: @:` - Catch-all to prevent errors on non-target arguments

### Usage

**With flags (using ARGS variable):**
```bash
make vendor-analysis ARGS="sync --vendors-only"
make vendor-analysis ARGS="analyze --top 25"
make vendor-analysis ARGS="duplicates --threshold 0.90"
```

**Without flags (positional arguments only):**
```bash
make vendor-analysis sync
make vendor-analysis analyze
make vendor-analysis help
```

**Combining both:**
```bash
make vendor-analysis ARGS="--verbose" sync
```

---

## Complete Example

### Makefile (Repo Root)

```makefile
# /opt/ns/Makefile

.PHONY: vendor-analysis data-processor api-client

# Vendor analysis CLI
vendor-analysis:
    @cd apps/vendor-analysis && uv run vendor-analysis $(ARGS) $(filter-out $@,$(MAKECMDGOALS))

# Data processor CLI
data-processor:
    @cd apps/data-processor && uv run data-processor $(ARGS) $(filter-out $@,$(MAKECMDGOALS))

# API client CLI
api-client:
    @cd apps/api-client && uv run api-client $(ARGS) $(filter-out $@,$(MAKECMDGOALS))

# Catch-all rule
%:
    @:
```

### App Structure

```
/opt/ns/
├── Makefile                          # Root Makefile
├── apps/
│   ├── vendor-analysis/
│   │   ├── pyproject.toml
│   │   └── src/vendor_analysis/
│   │       └── cli/main.py           # Typer CLI
│   ├── data-processor/
│   │   └── ...
│   └── api-client/
│       └── ...
```

---

## Advanced Patterns

### Help Target

```makefile
help:
    @echo "Available CLI tools:"
    @echo "  make vendor-analysis [ARGS='flags'] [command]"
    @echo "  make data-processor [ARGS='flags'] [command]"
    @echo ""
    @echo "Examples:"
    @echo "  make vendor-analysis sync"
    @echo "  make vendor-analysis ARGS='--verbose' analyze"
    @echo "  make vendor-analysis ARGS='sync --vendors-only'"
```

### All Apps Target

```makefile
all-sync:
    @make vendor-analysis sync
    @make data-processor sync
    @make api-client sync
```

### Conditional Targets

```makefile
vendor-sync-prod:
    @cd apps/vendor-analysis && ENV=production uv run vendor-analysis sync

vendor-sync-dev:
    @cd apps/vendor-analysis && ENV=development uv run vendor-analysis sync
```

---

## Alternative: Shell Script Wrapper

For more complex logic, use shell scripts instead of Make:

```bash
#!/bin/bash
# bin/vendor-analysis

cd "$(dirname "$0")/../apps/vendor-analysis" || exit 1
uv run vendor-analysis "$@"
```

```bash
# Usage (after chmod +x bin/vendor-analysis)
bin/vendor-analysis sync --vendors-only
```

**Benefits:**
- Simpler flag passing ($@)
- More readable for complex logic
- Easier debugging

**Downsides:**
- Requires chmod +x
- Not as familiar as Make
- Separate file per CLI

---

## Reference Implementation

**Location:** `/opt/ns/Makefile`

```makefile
.PHONY: vendor-analysis

vendor-analysis:
    @cd apps/vendor-analysis && uv run vendor-analysis $(ARGS) $(filter-out $@,$(MAKECMDGOALS))

%:
    @:

# Usage examples in comments
# make vendor-analysis sync
# make vendor-analysis ARGS="sync --vendors-only"
# make vendor-analysis ARGS="analyze --top 25"
```

---

## Related Patterns

**This Skill:**
- [../examples/](../examples/) - CLI application examples

**Reference Implementation:**
- `/opt/ns/Makefile` - Production Make integration
- `/opt/ns/apps/vendor-analysis/` - CLI app integrated with Make

---

## Summary

**Key Points:**

1. **ARGS variable** - Pass flags through Make safely
2. **filter-out pattern** - Pass positional arguments
3. **Catch-all rule** (`%: @:`) - Prevent Make errors on arguments
4. **@cd pattern** - Navigate to app directory
5. **Easy usage** - `make app-name ARGS="--flags" command`

**This pattern solves Make's flag handling limitation, enabling convenient CLI access from mono-repo root.**
