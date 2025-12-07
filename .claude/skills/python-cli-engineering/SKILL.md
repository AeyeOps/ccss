---
name: python-cli-engineering
description: Modern Python CLI application development using UV package manager, Ruff linting/formatting, Pyright strict type checking, Typer framework, and Rich console output. Use when building command-line tools, data processing applications, admin utilities, or developer tooling. Covers fail-fast error handling, dual configuration (YAML + .env with pydantic-settings), modular architecture with size constraints, SQLAlchemy patterns, and professional CLI UX design.
---

# Python CLI Engineering

Modern patterns for building production-grade Python command-line applications.

## When to Use This Skill

Use this skill when building:
- Command-line tools and utilities
- Data processing applications
- Admin/operations tooling
- Developer utilities
- ETL/sync scripts with user interaction
- Analysis tools with formatted output
- Database management CLIs

## Technology Stack

### Package Management: UV
**Why UV over pip/poetry:**
- 10-100x faster dependency resolution
- Built in Rust (blazing fast)
- Compatible with standard pyproject.toml
- Automatic virtual environment management
- Lock files for reproducible builds

**Installation:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Basic Commands:**
```bash
uv init              # Initialize new project
uv add package       # Add dependency
uv sync              # Install/update dependencies
uv run script.py     # Run script in venv
uv build             # Build wheel/sdist
```

→ **See**: [reference/uv-guide.md](reference/uv-guide.md)

### Linting & Formatting: Ruff
**Why Ruff:**
- Written in Rust (10-100x faster than flake8/black)
- Replaces 6+ tools (flake8, black, isort, pyupgrade, etc.)
- Compatible with existing configs
- Auto-fix support

**Configuration:**
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "C4", "UP", "SIM", "TCH"]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

→ **See**: [reference/ruff-guide.md](reference/ruff-guide.md)

### Type Checking: Pyright (Strict Mode)
**Why Pyright over mypy:**
- 3-5x faster (written in TypeScript)
- Stricter default checking
- Powers VS Code Pylance
- Real-time IDE feedback
- Better error messages

**Strict Configuration:**
```toml
[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.12"
reportMissingTypeStubs = true
reportUnknownMemberType = true
reportUnknownArgumentType = true
reportUnknownVariableType = true
strictListInference = true
strictDictionaryInference = true
strictSetInference = true
```

→ **See**: [reference/pyright-strict.md](reference/pyright-strict.md)

### CLI Framework: Typer
**Features:**
- Built on Click
- Automatic help generation
- Type hints for argument parsing
- Rich output integration
- Subcommand support

**Basic Pattern:**
```python
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def sync(
    verbose: bool = typer.Option(False, "--verbose", "-v")
) -> None:
    """Sync data from source."""
    if verbose:
        console.print("[yellow]Starting sync...[/yellow]")
    # Implementation

if __name__ == "__main__":
    app()
```

→ **See**: [reference/typer-patterns.md](reference/typer-patterns.md)

### Console Output: Rich
**Features:**
- Colored output
- Tables, progress bars, panels
- Markdown rendering
- Syntax highlighting
- Logging integration

→ **See**: [reference/rich-output.md](reference/rich-output.md)

## Fail-Fast Discipline

### Core Principles

1. **No default values** (except in explicit config files)
2. **No try/catch swallowing** (let exceptions propagate)
3. **No fallback mechanisms** (fail immediately on errors)
4. **Explicit configuration** (missing config = app stops)
5. **Type everything** (strict Pyright mode)

### Exception Handling Pattern

```python
# Custom exceptions (core/exceptions.py)
class AppError(Exception):
    """Base exception - let it bubble up."""
    pass

class ConfigurationError(AppError):
    """Configuration missing/invalid - STOP IMMEDIATELY."""
    pass

class ConnectionError(AppError):
    """External service connection failed."""
    pass

# CLI main entry (cli/main.py)
def main() -> None:
    """Main entry point - ONLY catch at top level."""
    try:
        app()
    except AppError as e:
        console.print(f"[red]ERROR: {e}[/red]")
        raise typer.Exit(code=1) from e
    except KeyboardInterrupt as e:
        console.print("\n[yellow]Interrupted[/yellow]")
        raise typer.Exit(code=130) from e
    except Exception as e:
        console.print(f"[red]UNEXPECTED: {e}[/red]")
        raise  # Re-raise for full traceback
```

**CRITICAL**: No try/catch around:
- Static imports
- Business logic
- Database operations
- API calls (except for retry logic)

Only catch at:
- Top-level CLI entry point (for user-friendly messages)
- Retry mechanisms (re-raise after max attempts)

→ **See**: [patterns/fail-fast.md](patterns/fail-fast.md)

## Configuration Management

### Dual-Source Pattern

**YAML**: Application settings, tunable parameters
**.env**: Secrets and credentials only

```yaml
# config.yaml
database:
  host: localhost
  port: 5432
  name: myapp

application:
  log_level: INFO
  page_size: 100
```

```bash
# .env (never commit)
DB_USER=admin
DB_PASSWORD=secret123
API_KEY=abc123
```

### Pydantic Settings Implementation

```python
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseConfig(BaseModel):
    host: str
    port: int
    name: str

class YAMLConfig(BaseModel):
    database: DatabaseConfig
    # ... other sections

def load_yaml_config(path: Path) -> YAMLConfig:
    """Load YAML config - FAIL if missing."""
    if not path.exists():
        raise ConfigurationError(f"Config not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return YAMLConfig(**data)  # Pydantic validates

class Settings(BaseSettings):
    """Credentials from .env, settings from YAML."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,  # Allow NS_ACCOUNT_ID → ns_account_id
        extra="ignore"
    )

    # Credentials from .env (REQUIRED)
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")
    api_key: str = Field(..., description="API key")

    _yaml_config: YAMLConfig | None = None

    @property
    def yaml_config(self) -> YAMLConfig:
        if self._yaml_config is None:
            self._yaml_config = load_yaml_config(Path("config.yaml"))
        return self._yaml_config

    @property
    def database_url(self) -> str:
        """Build connection URL from both sources."""
        db = self.yaml_config.database
        return f"postgresql://{self.db_user}:{self.db_password}@{db.host}:{db.port}/{db.name}"
```

→ **See**: [patterns/configuration.md](patterns/configuration.md)

## Modular Architecture

### Size Discipline

**Rule**: No module exceeds 300 lines (preferably <200)

**Directory Structure:**
```
src/myapp/
├── core/           # Foundation (<150 lines each)
│   ├── config.py
│   ├── exceptions.py
│   └── constants.py
├── api/            # External APIs (<250 lines each)
│   ├── client.py
│   └── models.py
├── db/             # Database layer (<200 lines each)
│   ├── models.py
│   ├── session.py
│   └── queries.py
├── analysis/       # Business logic (<250 lines each)
│   ├── module1.py
│   ├── module2.py
│   └── module3.py
└── cli/            # CLI commands (<200 lines each)
    ├── main.py
    ├── command1.py
    └── command2.py
```

### Module Responsibilities

**core/**: Configuration, exceptions, constants only
**{domain}/**: Single-domain logic (vendors, customers, etc.)
**db/**: Database models and queries only
**cli/**: CLI command handlers only (thin layer)

**Anti-pattern**: `utils.py` or `helpers.py` with unrelated functions

→ **See**: [patterns/modular-architecture.md](patterns/modular-architecture.md)

## CLI Design Patterns

### Command Structure

```python
import typer

app = typer.Typer(
    name="myapp",
    help="Description of application",
    add_completion=False  # Unless you need shell completion
)

# Group related commands
@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Force re-initialization")
) -> None:
    """Initialize application (idempotent)."""
    # Implementation

@app.command()
def sync(
    full: bool = typer.Option(False, "--full", help="Full sync (not incremental)")
) -> None:
    """Sync data from source."""
    # Implementation

@app.callback()
def callback() -> None:
    """Called before every command."""
    # Global setup if needed
```

### Rich Output Patterns

**Progress Bars:**
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("[cyan]Processing...", total=len(items))
    for item in items:
        process(item)
        progress.advance(task)
```

**Tables:**
```python
from rich.table import Table

table = Table(title="Vendor Spend")
table.add_column("Vendor", style="magenta")
table.add_column("Amount", justify="right", style="green")

for vendor, amount in data:
    table.add_row(vendor, f"${amount:,.2f}")

console.print(table)
```

**Panels:**
```python
from rich.panel import Panel

console.print(Panel.fit(
    "[green]✓ Success![/green]\nOperation completed",
    border_style="green"
))
```

→ **See**: [reference/rich-output.md](reference/rich-output.md)

## Project Template

### pyproject.toml
```toml
[project]
name = "myapp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.7.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.4.0",
    "pyright>=1.1.0",
]

[project.scripts]
myapp = "myapp.cli.main:main"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "C4", "UP", "SIM", "TCH"]

[tool.pyright]
typeCheckingMode = "strict"
pythonVersion = "3.12"
```

### Makefile
```makefile
.PHONY: help install typecheck lint format clean

help:
	@echo "Available commands:"
	@echo "  make install     Install dependencies"
	@echo "  make typecheck   Run Pyright"
	@echo "  make lint        Run Ruff linter"
	@echo "  make format      Format with Ruff"
	@echo "  make clean       Remove artifacts"

install:
	uv sync

typecheck:
	uv run pyright

lint:
	uv run ruff check .

format:
	uv run ruff format .

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

## SQLAlchemy Patterns

### Model Definition
```python
from datetime import datetime
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Record(Base):
    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(datetime.UTC if hasattr(datetime, 'UTC') else None),  # type: ignore[arg-type]
        nullable=False
    )
```

### Session Management
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

def create_db_engine(database_url: str):
    """Create SQLAlchemy engine."""
    return create_engine(database_url, echo=False, future=True)

def get_session(database_url: str) -> Session:
    """Get database session."""
    engine = create_db_engine(database_url)
    session_factory = sessionmaker(bind=engine)
    return session_factory()

def init_database(database_url: str) -> None:
    """Initialize schema (idempotent)."""
    engine = create_db_engine(database_url)
    Base.metadata.create_all(engine)
```

→ **See**: [reference/sqlalchemy-patterns.md](reference/sqlalchemy-patterns.md)

## Read-Only API Client Pattern

### Enforcement Strategy
```python
from typing import Final

class ReadOnlyClient:
    """Enforce read-only operations."""

    ALLOWED_METHODS: Final[frozenset[str]] = frozenset(["GET"])

    def _enforce_read_only(self, method: str) -> None:
        if method.upper() not in self.ALLOWED_METHODS:
            raise ReadOnlyViolationError(
                f"CRITICAL: Attempted {method} operation. "
                f"Only {self.ALLOWED_METHODS} allowed."
            )

    def _request(self, method: str, url: str, **kwargs):
        self._enforce_read_only(method)
        return self.session.request(method, url, **kwargs)
```

→ **See**: [patterns/read-only-clients.md](patterns/read-only-clients.md)

## Bootstrap Script Pattern

### Idempotent Setup
```python
#!/usr/bin/env python3
"""Idempotent bootstrap script."""

from rich.console import Console
from rich.panel import Panel

console = Console()

def check_dependencies() -> None:
    """Check Python version, UV installation."""
    # Fail fast if requirements not met

def install_dependencies() -> None:
    """Run uv sync (idempotent)."""
    # Safe to run multiple times

def initialize_database() -> None:
    """Create schema (idempotent)."""
    # SQLAlchemy create_all is idempotent

def main() -> None:
    console.print(Panel("Bootstrap Starting..."))

    check_dependencies()
    install_dependencies()
    initialize_database()

    console.print(Panel("[green]✓ Complete[/green]"))

if __name__ == "__main__":
    main()
```

→ **See**: [patterns/bootstrap-scripts.md](patterns/bootstrap-scripts.md)

## Complete Examples

### Data Processing CLI
→ **See**: [examples/data-processor.md](examples/data-processor.md)

Full application:
- UV + Ruff + Pyright setup
- Typer commands with subcommands
- Rich progress bars and tables
- SQLAlchemy database operations
- Configuration management

### Vendor Analysis CLI
→ **See**: [examples/vendor-analysis.md](examples/vendor-analysis.md)

Production application:
- NetSuite API integration (read-only)
- PostgreSQL storage
- Pandas analysis
- Duplicate detection
- Executive reporting

## Best Practices

### 1. Project Structure
```
myapp/
├── src/myapp/
│   ├── __init__.py
│   ├── core/          # Config, exceptions, constants
│   ├── cli/           # CLI commands
│   ├── {domain}/      # Business logic
│   └── py.typed       # PEP 561 marker
├── tests/
├── scripts/
│   └── bootstrap.py
├── pyproject.toml
├── config.yaml
├── .env.example
├── Makefile
└── README.md
```

### 2. Type Hints Everywhere
```python
# Good
def process_items(items: list[Item], threshold: float) -> list[Result]:
    """Process items above threshold."""
    results: list[Result] = []
    for item in items:
        if item.value > threshold:
            results.append(Result(item))
    return results

# Bad (no type hints)
def process_items(items, threshold):
    results = []
    for item in items:
        if item.value > threshold:
            results.append(Result(item))
    return results
```

### 3. Validation at Boundaries
- API responses → Pydantic models
- Database queries → SQLAlchemy models
- User input → Typer type validation
- Config files → Pydantic Settings

### 4. Module Organization
- One responsibility per module
- Clear dependency flow (core → domain → cli)
- No circular dependencies
- Keep modules small (<300 lines)

### 5. Error Messages
```python
# Good: Specific, actionable
raise ConfigurationError(
    f"Database config not found in config.yaml\n"
    f"Add 'database' section with host, port, name"
)

# Bad: Generic, unhelpful
raise Exception("Config error")
```

## Development Workflow

```bash
# Initial setup
uv init myapp
cd myapp
uv add typer rich pydantic pydantic-settings
uv add --dev ruff pyright

# Development cycle
uv run myapp command       # Test functionality
uv run pyright            # Type check
uv run ruff check .       # Lint
uv run ruff format .      # Format

# Build and distribute
uv build                  # Creates wheel in dist/
```

## Testing Strategy

**For production applications where testing is not required:**
- Manual testing with real data
- Bootstrap script verifies setup
- Type checking catches type errors
- Linting catches code smells
- Fail-fast catches runtime errors immediately

**If tests needed later:**
- pytest for unit tests
- pytest-cov for coverage
- Integration tests with test database

## Common Patterns

### Idempotent Operations
→ **See**: [patterns/idempotency.md](patterns/idempotency.md)

- Database initialization (create_all)
- File creation (overwrite if exists)
- Bootstrap scripts
- Sync operations (upsert pattern)

### Progress Reporting
→ **See**: [patterns/progress-reporting.md](patterns/progress-reporting.md)

- Long-running operations
- Batch processing
- Multi-step workflows

### Subprocess Management
→ **See**: [patterns/subprocess.md](patterns/subprocess.md)

- Live output streaming
- Error handling
- Logging stdout/stderr

### Data Persistence

**PostgreSQL JSONB:**
→ **See**: [patterns/postgresql-jsonb.md](patterns/postgresql-jsonb.md)

- Schema-flexible storage (hybrid typed + JSONB columns)
- GIN indexes for JSONB query performance
- Lifecycle metadata tracking (first_seen, last_seen, deprecated)
- Complete audit trail with raw_data storage
- Reference implementation: vendor-analysis app

**Schema Resilience:**
→ **See**: [patterns/schema-resilience.md](patterns/schema-resilience.md)

- 3-layer architecture (Source → Storage → Application)
- Field classification (known vs unknown fields)
- Merge strategies for preserving historical data
- Never destroy data (additive migrations only)
- Graceful degradation when fields removed

**Database Migrations:**
→ **See**: [reference/database-migrations.md](reference/database-migrations.md)

- Idempotent migration patterns (IF NOT EXISTS)
- Verification steps for migration success
- Python migration runners
- Never DROP columns rule
- Safe rollback strategies

### API Integration

**Flexible Data Models:**
→ **See**: [patterns/pydantic-flexible.md](patterns/pydantic-flexible.md)

- Pydantic for inconsistent APIs (extra="allow")
- Handle empty strings, missing fields, type variations
- Field validators for common API quirks
- Reference field extraction patterns
- Model validators for nested objects

**Multi-Method Authentication:**
→ **See**: [patterns/multi-method-auth.md](patterns/multi-method-auth.md)

- Factory pattern for multiple auth methods
- Abstract base class for auth providers
- Configuration-driven auth selection
- Gradual migration support (OAuth 1.0 → OAuth 2.0)
- Environment-specific authentication

### Build Integration

**Make Commands:**
→ **See**: [patterns/make-integration.md](patterns/make-integration.md)

- ARGS pattern for passing CLI flags through Make
- Mono-repo CLI access from root
- Catch-all rule pattern
- Simple command proxying

## Anti-Patterns

❌ **Monolithic main.py**: Split into modular commands
❌ **Print statements**: Use Rich console
❌ **Silent failures**: Fail fast with clear errors
❌ **Mutable defaults**: Use None, create in function
❌ **String concatenation**: Use f-strings
❌ **Global state**: Pass dependencies explicitly
❌ **Ignoring type errors**: Fix them, don't suppress

## Tools Comparison

| Tool | Replaces | Speed | Notes |
|------|----------|-------|-------|
| UV | pip, poetry, pipenv | 10-100x | Rust-based |
| Ruff | flake8, black, isort, pyupgrade | 10-100x | Rust-based |
| Pyright | mypy | 3-5x | TypeScript, strict |
| Typer | argparse, click | Similar | Better DX |
| Rich | print, logging | Similar | Better UX |

## Deployment

### Package Distribution
```bash
# Build wheel
uv build

# Distribute
# Option 1: Internal PyPI
twine upload dist/* --repository internal

# Option 2: S3 bucket
aws s3 cp dist/*.whl s3://packages/

# Option 3: Direct install
pip install dist/myapp-0.1.0-py3-none-any.whl
```

### Standalone Binary (Optional)
Use PyInstaller or Nuitka for single-file executables.

---

*Use this skill when building modern Python CLI applications with professional UX, strict typing, and fail-fast reliability.*
