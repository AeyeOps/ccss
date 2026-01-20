"""Textual TUI application for session search."""

from __future__ import annotations

import atexit
import contextlib
import shutil
import signal
import sqlite3
import sys
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar

import pyperclip
from rich.text import Text
from textual import events, on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Horizontal, Middle, ScrollableContainer, Vertical
from textual.content import Content
from textual.geometry import Size
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    OptionList,
    ProgressBar,
    Static,
)
from textual.widgets.input import Selection
from textual.widgets.option_list import Option

from ccss import __version__
from ccss.indexer import (
    build_index,
    ensure_schema_current,
    get_db_connection,
    get_index_stats,
    init_db,
    is_index_current,
)
from ccss.logger import AppLogger, get_logger
from ccss.search import SearchResult, get_session_preview, search_sessions
from ccss.settings import AVAILABLE_THEMES, load_settings, save_settings
from ccss.themes import CUSTOM_THEMES

if TYPE_CHECKING:
    from textual.events import Key


class SearchInput(Input):
    """Custom Input that rejects slash character when focused via slash shortcut."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._reject_slash = False
        self._expected_value: str | None = None  # Value to restore if "/" leaks through
        self._in_cleanup = False  # Prevent recursion

    def focus_via_slash(self, expected_value: str) -> None:
        """Mark to reject "/" and store expected value for cleanup."""
        self._reject_slash = True
        self._expected_value = expected_value
        # Clear the flag after 100ms in case no "/" ever comes
        self.set_timer(0.1, self._clear_reject_flag)

    def _clear_reject_flag(self) -> None:
        """Clear the reject flag after timeout."""
        self._reject_slash = False
        self._expected_value = None

    def watch_value(self, value: str) -> None:
        """React to value changes - cleanup any leaked "/" immediately."""
        if self._in_cleanup:
            return  # Skip during cleanup

        # Check if "/" was appended when rejection flag is set
        if (
            self._reject_slash
            and self._expected_value is not None
            and value == self._expected_value + "/"
        ):
            # Cleanup synchronously
            expected = self._expected_value
            self._in_cleanup = True
            self._reject_slash = False
            self._expected_value = None
            # Set value directly (triggers watch_value again but _in_cleanup is True)
            self.value = expected
            self.selection = Selection.cursor(len(expected))
            self._in_cleanup = False

    def insert_text_at_cursor(self, text: str) -> None:
        """Reject "/" if we were just focused via slash key."""
        if self._reject_slash and text == "/":
            return  # Silently reject
        super().insert_text_at_cursor(text)

    def replace(self, text: str, start: int, end: int) -> None:
        """Reject "/" replacement if we were just focused via slash key."""
        if self._reject_slash and text == "/":
            return  # Silently reject
        super().replace(text, start, end)

    async def _on_key(self, event: Key) -> None:
        """Intercept "/" key at event level when rejection flag is set."""
        if self._reject_slash and event.key == "slash":
            event.stop()
            event.prevent_default()
            return
        await super()._on_key(event)

    def handle_key(self, event: Key) -> bool:
        """Handle key input - reject "/" when flag is set."""
        if self._reject_slash and event.key == "slash":
            return True  # Consumed, don't process
        return super().handle_key(event)


class ThemeScreen(ModalScreen[str | None]):
    """Modal screen for theme selection."""

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "cancel", "Cancel"),
    ]

    CSS = """
    ThemeScreen {
        align: center middle;
    }

    #theme-dialog {
        width: 40;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #theme-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #theme-list {
        height: auto;
        max-height: 15;
    }
    """

    def __init__(self, current_theme: str) -> None:
        super().__init__()
        self.current_theme = current_theme

    def compose(self) -> ComposeResult:
        with Container(id="theme-dialog"):
            yield Label("Select Theme", id="theme-title")
            option_list = OptionList(id="theme-list")
            for theme in AVAILABLE_THEMES:
                marker = " *" if theme == self.current_theme else ""
                option_list.add_option(Option(f"{theme}{marker}", id=theme))
            yield option_list

    def on_mount(self) -> None:
        option_list = self.query_one("#theme-list", OptionList)
        # Focus the current theme
        for i, theme in enumerate(AVAILABLE_THEMES):
            if theme == self.current_theme:
                option_list.highlighted = i
                break
        option_list.focus()

    @on(OptionList.OptionSelected)
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            self.dismiss(str(event.option.id))

    def on_key(self, event: Key) -> None:
        """Block all key events from bubbling to parent app."""
        # Only allow escape (handled by binding) and navigation keys for OptionList
        if event.key not in ("escape", "up", "down", "enter", "j", "k"):
            event.stop()
            event.prevent_default()

    def action_cancel(self) -> None:
        self.dismiss(None)


class AboutScreen(ModalScreen[None]):
    """Modal screen showing application information."""

    BINDINGS = [  # noqa: RUF012
        Binding("escape", "dismiss_about", "Close"),
        Binding("enter", "dismiss_about", "Close"),
    ]

    CSS = """
    AboutScreen {
        align: center middle;
    }

    #about-dialog {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #about-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #about-content {
        text-align: center;
    }

    #about-footer {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="about-dialog"):
            yield Label("About", id="about-title")
            content = Text()
            content.append("AeyeOps | Claude Code Session Search\n", style="bold")
            content.append(f"Version {__version__}\n\n", style="dim")
            content.append("Fast TUI for finding past\n")
            content.append("Claude Code conversations\n\n")
            content.append("Author: ", style="dim")
            content.append("Steve Antonakakis\n")
            content.append("License: ", style="dim")
            content.append("MIT\n\n")
            content.append(
                "https://github.com/AeyeOps/ccss",
                style="underline link https://github.com/AeyeOps/ccss",
            )
            yield Static(content, id="about-content")
            yield Label("[Press Escape to close]", id="about-footer")

    def action_dismiss_about(self) -> None:
        self.dismiss(None)


class ReindexConfirmScreen(ModalScreen[bool]):
    """Modal screen for reindex confirmation."""

    BINDINGS = [  # noqa: RUF012
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    CSS = """
    ReindexConfirmScreen {
        align: center middle;
    }

    #reindex-dialog {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #reindex-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #reindex-message {
        text-align: center;
        margin-bottom: 1;
    }

    #reindex-footer {
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self, session_count: int) -> None:
        super().__init__()
        self.session_count = session_count

    def compose(self) -> ComposeResult:
        with Container(id="reindex-dialog"):
            yield Label("Rebuild Index", id="reindex-title")
            yield Label(
                f"Reindex all {self.session_count} sessions?\nThis may take a moment.",
                id="reindex-message",
            )
            yield Static("[bold green]Y[/] Yes  [bold red]N[/] No", id="reindex-footer")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class ResultItem(ListItem):
    """A list item for a search result."""

    def __init__(self, result: SearchResult) -> None:
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        # Use Text object to avoid markup parsing issues
        text = Text()
        text.append(f"[{self.result.display_date}] ", style="dim")
        text.append(f"{self.result.display_project}: ", style="bold")
        # Truncate snippet to 200 chars for display
        snippet = self.result.snippet
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."
        text.append(snippet)
        yield Static(text)


# Comprehensive FTS5 syntax reference
SYNTAX_REFERENCE = """[b]SEARCH SYNTAX[/b]
[dim]SQLite FTS5 Full-Text Search[/dim]

[b cyan]BASIC TERMS[/b cyan]
  [green]word[/green]        Match word (prefix auto)
  [green]word*[/green]       Explicit prefix match
  [green]^word[/green]       Must start field

[b cyan]EXACT PHRASES[/b cyan]
  [green]"exact phrase"[/green]   Match exact sequence
  [green]"two words"*[/green]     Phrase with prefix

[b cyan]BOOLEAN OPERATORS[/b cyan]
  [green]a AND b[/green]     Both terms required
  [green]a OR b[/green]      Either term matches
  [green]a NOT b[/green]     Has a, excludes b

[b cyan]GROUPING[/b cyan]
  [green](a OR b) AND c[/green]
  [green](error OR warn) AND config[/green]

[b cyan]PROXIMITY (NEAR)[/b cyan]
  [green]NEAR(a b)[/green]       Within 10 tokens
  [green]NEAR(a b, 5)[/green]    Within 5 tokens
  [green]NEAR(a b c, 3)[/green]  All within 3

[b cyan]COLUMN FILTER[/b cyan]
  [green]content:term[/green]    Search specific column

[b cyan]STEMMING (Automatic)[/b cyan]
  Porter stemmer active:
  [dim]run[/dim] -> run, runs, running
  [dim]connect[/dim] -> connected, connection
  [dim]search[/dim] -> searches, searching

[b cyan]ESCAPING SPECIAL CHARS[/b cyan]
  [green]"*"[/green]  [green]"^"[/green]  Wrap in quotes
  Special: [dim]* ^ ( )[/dim]

[b cyan]EXAMPLES[/b cyan]
  [green]error AND database[/green]
  [green]"file not found"[/green]
  [green]config* NOT test[/green]
  [green](auth OR login) AND fail[/green]
  [green]NEAR(api key, 5)[/green]
  [green]^import AND python[/green]

[dim]Press F1 to close[/dim]
"""


class HelpPanel(ScrollableContainer):
    """Right-side panel showing session metadata."""

    DEFAULT_CSS = """
    HelpPanel {
        width: 40;
        height: 100%;
        border-left: solid $primary;
        background: $surface;
        padding: 1;
        display: none;
        scrollbar-color: #e07a3c;
        scrollbar-size-vertical: 1;
    }

    HelpPanel.visible {
        display: block;
    }

    HelpPanel Static {
        width: 100%;
    }

    HelpPanel .metadata-label {
        color: $text-muted;
    }

    HelpPanel .metadata-value {
        color: $text;
    }

    HelpPanel .metadata-copyable:hover {
        background: $primary 20%;
    }
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._current_result: SearchResult | None = None

    def compose(self) -> ComposeResult:
        yield Static("Select a session to see details", id="help-content")

    def update_metadata(self, result: SearchResult | None) -> None:
        """Update panel with session metadata."""
        self._current_result = result
        content = self.query_one("#help-content", Static)

        if result is None:
            content.update("Select a session to see details")
            return

        # Parse timestamp
        datetime_str = "Unknown"
        if result.first_timestamp:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(result.first_timestamp.replace("Z", "+00:00"))
                datetime_str = dt.strftime("%b %d, %Y at %I:%M %p")
            except (ValueError, AttributeError):
                pass

        # Build metadata display
        text = Text()
        text.append("Session Details\n", style="bold")
        text.append("=" * 20 + "\n\n", style="dim")

        # Agent indicator
        if result.is_agent:
            text.append("  [Agent Session]\n\n", style="bold magenta")

        text.append("Session ID\n", style="dim")
        text.append(f"  {result.session_id}\n\n", style="bold")

        text.append("Project\n", style="dim")
        text.append(f"  {result.display_project}\n\n", style="bold")

        # Working directory
        text.append("Working Dir\n", style="dim")
        cwd_display = result.cwd or "Unknown"
        text.append(f"  {cwd_display}\n\n", style="")

        # Git branch
        text.append("Git Branch\n", style="dim")
        branch_display = result.git_branch or "Unknown"
        text.append(f"  {branch_display}\n\n", style="")

        # Claude version
        text.append("Claude Version\n", style="dim")
        version_display = result.version or "Unknown"
        text.append(f"  {version_display}\n\n", style="")

        text.append("Started\n", style="dim")
        text.append(f"  {datetime_str}\n\n", style="")

        # Duration
        text.append("Duration\n", style="dim")
        text.append(f"  {result.display_duration}\n\n", style="")

        text.append("Messages\n", style="dim")
        text.append(f"  {result.message_count}\n\n", style="")

        # Turn counts
        text.append("Turns\n", style="dim")
        turns_str = f"  User: {result.user_turns}  Assistant: {result.assistant_turns}\n\n"
        text.append(turns_str, style="")

        # Tool use
        text.append("Tool Calls\n", style="dim")
        text.append(f"  {result.tool_use_count}\n\n", style="")

        # Token estimate
        text.append("Tokens\n", style="dim")
        text.append(f"  ~{result.total_tokens_est:,}\n", style="")

        content.update(text)


class SyntaxPanel(ScrollableContainer):
    """Right-side panel showing FTS5 syntax reference."""

    DEFAULT_CSS = """
    SyntaxPanel {
        width: 40;
        height: 100%;
        border-left: solid $primary;
        background: $surface;
        padding: 1;
        display: none;
        scrollbar-color: #e07a3c;
        scrollbar-size-vertical: 1;
    }

    SyntaxPanel.visible {
        display: block;
    }

    SyntaxPanel Static {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(SYNTAX_REFERENCE, markup=True)


class BrandedHeader(Header):
    """Custom header with accent-colored AeyeOps branding."""

    def format_title(self) -> Content:
        """Format the title with AeyeOps in accent color."""
        # Get accent color from current theme
        accent_color = self.app.current_theme.accent
        accent_style = f"bold {accent_color}"
        return Content.styled("AeyeOps", accent_style) + Content(" | Claude Code Session Search")


class BrandedFooter(Footer):
    """Custom footer with AeyeOps branding."""

    DEFAULT_CSS = """
    BrandedFooter {
        dock: bottom;
    }

    BrandedFooter #brand-label {
        dock: right;
        padding: 0 1;
        color: $accent;
        text-style: italic;
    }
    """

    def compose(self) -> ComposeResult:
        yield from super().compose()
        yield Label(f"AeyeOps {datetime.now().year} | CCSS v{__version__}", id="brand-label")


class SessionSearchApp(App[str | None]):
    """TUI application for searching Claude Code sessions."""

    TITLE = "AeyeOps | Claude Code Session Search"
    ENABLE_COMMAND_PALETTE = False  # Disable command palette icon in header
    LOGGING = "debug"
    HORIZONTAL_BREAKPOINTS: ClassVar[list[tuple[int, str]]] = [(0, "-narrow"), (120, "-wide")]
    CSS_PATH = None  # Disable external CSS files; use inlined CSS only

    CSS = """
    /* Root screen should stretch and use vertical layout */
    Screen {
        width: 100%;
        height: 100%;
        layout: vertical;
    }

    /* Root view inside screen should also stretch */
    .view {
        width: 100%;
        height: 100%;
        layout: vertical;
    }

    /* Loading overlay - floats above everything */
    #loading-overlay {
        layer: overlay;
    }

    #loading-container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 4;
    }

    #loading-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #loading-status {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    #loading-brand {
        text-align: center;
        color: $accent;
        margin-top: 1;
    }

    #loading-progress {
        width: 100%;
        margin: 1 0;
    }

    /* Main content - hidden until loading complete */
    #main-content {
        width: 1fr;
        min-width: 0;
        height: 1fr;
        display: none;
    }

    #main-content.visible {
        display: block;
    }

    #main-layout {
        width: 1fr;
        height: 1fr;
    }

    #left-content {
        width: 1fr;
        height: 100%;
    }

    #right-sidebar {
        width: 40;
        height: 100%;
        display: none;
    }

    #right-sidebar.visible {
        display: block;
    }

    #search-container {
        width: 100%;
        height: auto;
        padding: 1 2;
        min-width: 0;
    }

    #search-input {
        width: 100%;
    }

    #results-container {
        width: 100%;
        border: solid $primary;
        height: 1fr;
        overflow: hidden;
        min-width: 0;
    }

    #results-list {
        width: 100%;
        height: 100%;
        scrollbar-color: #e07a3c;
        scrollbar-size-vertical: 1;
    }

    #preview-container {
        width: 100%;
        border: solid $secondary;
        height: 1fr;
        overflow-y: auto;
        scrollbar-color: #e07a3c;
        scrollbar-size-vertical: 1;
        min-width: 0;
    }

    #preview-content {
        width: 100%;
        padding: 1 2;
    }

    #path-display {
        width: 100%;
        height: auto;
        padding: 0 2;
        background: $surface-darken-1;
        color: $text-muted;
        min-width: 0;
    }

    #path-display.has-path {
        color: $success;
    }

    .result-item {
        padding: 0 1;
    }

    /* Header cleanup - remove icon and disable focus expansion */
    HeaderIcon {
        display: none;
    }

    Header {
        width: 100%;
        height: 1;
    }

    Footer {
        width: 100%;
    }
    """

    BINDINGS = [  # noqa: RUF012
        # Quit: q when not in input, escape always
        Binding("q", "quit", "Quit", show=False),
        Binding("escape", "quit", "Quit"),
        # Search focus: "/" with priority to ensure it's always handled
        Binding("slash", "handle_slash", "Search", priority=True, show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        # Copy: enter/y when on results, ctrl+y always
        Binding("enter", "copy_path", "Copy", show=False),
        Binding("y", "copy_path", "Copy", show=False),
        Binding("ctrl+y", "copy_path", "Copy", priority=True),
        # Preview: p when not in input, ctrl+p always
        Binding("p", "toggle_preview", "Preview", show=False),
        Binding("ctrl+p", "toggle_preview", "Preview", priority=True),
        # Panels
        Binding("ctrl+k", "toggle_keys_panel", "Sidebar", priority=True),
        Binding("f1", "toggle_syntax_panel", "Syntax", priority=True),
        Binding("ctrl+t", "show_theme_menu", "Theme", priority=True),
        # About
        Binding("ctrl+a", "show_about", "About", priority=True),
        # Reindex
        Binding("ctrl+r", "reindex", "Reindex", priority=True),
    ]

    def __init__(self, initial_query: str = "") -> None:
        super().__init__()
        self.initial_query = initial_query
        self.conn: sqlite3.Connection | None = None
        self.results: list[SearchResult] = []
        self.show_preview = True
        self.current_query = ""
        self._load_start_time: float = 0.0
        self._app_logger: AppLogger | None = None
        self._search_timer: Timer | None = None
        self._active_panel: str | None = None  # "keys" or "syntax" or None
        self._last_polled_size: tuple[int, int] | None = None
        self._size_poll_timer: Timer | None = None
        # Track whether sidebar is visible to adjust grid columns
        self._sidebar_visible: bool = False
        # Track whether reindex is in progress (disables search)
        self._reindex_in_progress: bool = False

        # Register custom themes
        for custom_theme in CUSTOM_THEMES:
            self.register_theme(custom_theme)

        # Load settings and apply theme
        settings = load_settings()
        self.theme = settings["theme"]

    def compose(self) -> ComposeResult:
        # Loading overlay (visible initially)
        with Center(id="loading-overlay"), Middle(), Container(id="loading-container"):
            yield Label(f"Claude Code Session Search v{__version__}", id="loading-title")
            yield ProgressBar(id="loading-progress", show_eta=False)
            yield Label("Initializing...", id="loading-status")
            yield Label(f"AeyeOps {datetime.now().year}", id="loading-brand")

        # Main content (hidden initially)
        with Vertical(id="main-content"):
            yield BrandedHeader(show_clock=False)
            with Horizontal(id="main-layout"):
                with Vertical(id="left-content"):
                    with Vertical(id="search-container"):
                        yield SearchInput(
                            placeholder="Search sessions... (F1 for syntax help)",
                            id="search-input",
                        )
                    with Vertical(id="results-container"):
                        yield ListView(id="results-list")
                    with Vertical(id="preview-container"):
                        yield Static("Select a session to preview", id="preview-content")
                    yield Static("Select a session to see path (Enter to copy)", id="path-display")
                with Vertical(id="right-sidebar"):
                    yield HelpPanel(id="help-panel")
                    yield SyntaxPanel(id="syntax-panel")
            yield BrandedFooter()

    def on_mount(self) -> None:
        """Initialize the app on mount."""
        # Initialize logger after Textual's setup is complete
        self._app_logger = get_logger()
        self._app_logger.info("Application started", theme=self.theme)
        self._load_start_time = time.monotonic()
        self._start_indexing()
        # Poll terminal size as a fallback if driver misses horizontal resize
        self._size_poll_timer = self.set_interval(0.5, self._poll_terminal_size, pause=False)
        # Log an initial poll immediately
        self._poll_terminal_size()

    def on_resize(self, event: events.Resize) -> None:
        """Force a full layout recalculation on resize.

        Per Textual GitHub #3527: Resize events fire BEFORE layout is redrawn.
        We must use call_after_refresh to defer cache invalidation.
        """
        self.log(
            f"on_resize reported size={event.size.width}x{event.size.height} "
            f"app_size={self.size.width}x{self.size.height}"
        )
        # Defer to after the layout pass so we don't fight Textual's own sizing
        self.call_after_refresh(self._post_resize_refresh)

    def _post_resize_refresh(self) -> None:
        """Force all widgets to recalculate dimensions on resize."""
        # Log screen size for debugging
        self.log(f"[resize] screen.size={self.screen.size.width}x{self.screen.size.height}")

        # Force style invalidation on all widgets by walking the tree
        def force_recalc(widget: object) -> None:
            try:
                # Dirty the styles to force recalculation
                if hasattr(widget, "styles") and hasattr(widget.styles, "_updates"):
                    widget.styles._updates += 1
                # Clear any cached content size
                if hasattr(widget, "_content_width"):
                    widget._content_width = None
                if hasattr(widget, "_content_height"):
                    widget._content_height = None
                # Request layout refresh
                widget.refresh(layout=True, repaint=True)
            except Exception:
                pass

        # Walk all widgets and force recalc
        try:
            for widget in self.query("*"):
                force_recalc(widget)
        except Exception:
            pass

        # Force screen-level layout
        try:
            self.screen._layout_required = True
            self.screen.refresh(layout=True)
        except Exception:
            pass

        self._apply_sidebar_grid()

        # Log sizes after next refresh cycle when layout is complete
        self.call_after_refresh(self._log_widget_sizes_deferred)

    def _log_widget_sizes_deferred(self) -> None:
        """Log widget sizes after layout pass completes."""
        try:
            main = self.query_one("#main-content")
            layout = self.query_one("#main-layout")
            left = self.query_one("#left-content")
            self.log(
                f"[resize-final] main={main.size.width}x{main.size.height} "
                f"layout={layout.size.width}x{layout.size.height} "
                f"left={left.size.width}x{left.size.height}"
            )
        except Exception as e:
            self.log(f"[resize-final] widget size logging failed: {e}")

    def _poll_terminal_size(self) -> None:
        """Poll terminal size and synthesize a resize if driver missed it.

        Note: WSL2 has a known bug where horizontal-only resize doesn't
        propagate SIGWINCH (Microsoft/WSL#1001). We use ioctl TIOCGWINSZ
        which directly queries the terminal driver.
        """
        import fcntl
        import struct
        import termios

        cols, rows = 0, 0

        # Method 1: ioctl TIOCGWINSZ - most reliable, direct kernel query
        # Build fd list first - fileno() may fail in test environments (pytest captures)
        fds = []
        for stream in (sys.stdin, sys.stdout, sys.stderr):
            try:
                fds.append(stream.fileno())
            except Exception:
                continue
        for fd in fds:
            try:
                result = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\x00" * 8)
                rows, cols = struct.unpack("HHHH", result)[:2]
                if cols > 0 and rows > 0:
                    break
            except Exception:
                continue

        # Method 2: Fallback to shutil
        if cols <= 0 or rows <= 0:
            try:
                cols, rows = shutil.get_terminal_size(fallback=(0, 0))
            except Exception:
                return
        if cols <= 0 or rows <= 0:
            return
        current = (self.size.width, self.size.height)
        polled = (cols, rows)
        if self._last_polled_size != polled:
            self._last_polled_size = polled
            self.log(f"[size-poll] tty={cols}x{rows} app={current[0]}x{current[1]}")
            if polled != current:
                # Force update internal size state before posting event
                new_size = Size(cols, rows)
                self._size = new_size
                if hasattr(self, "_driver") and self._driver:
                    self._driver._size = new_size
                self.screen._size = new_size
                # Now post the resize event
                self.post_message(
                    events.Resize(
                        size=new_size,
                        virtual_size=new_size,
                        container_size=new_size,
                    )
                )
                # Force a full layout refresh
                self.screen.refresh(layout=True)
                self.call_after_refresh(self._log_widget_sizes_deferred)

    def _apply_sidebar_grid(self) -> None:
        """Refresh layout after sidebar visibility changes."""
        try:
            sidebar = self.query_one("#right-sidebar")
        except Exception:
            return

        visible = sidebar.has_class("visible")
        self._sidebar_visible = visible
        sidebar.styles.display = "block" if visible else "none"
        sidebar.refresh(layout=True)

    def _log_layout_sizes(self) -> None:
        """Log key widget widths/heights to debug resize behavior."""

        def q(selector: object) -> object | None:
            try:
                return self.query_one(selector)
            except Exception:
                return None

        widgets = {
            "screen": self.screen,
            "view": getattr(self.screen, "view", None),
            "main-content": q("#main-content"),
            "main-layout": q("#main-layout"),
            "left-content": q("#left-content"),
            "right-sidebar": q("#right-sidebar"),
            "header": q(Header),
            "footer": q(Footer),
            "brand-label": q("#brand-label"),
        }

        def size_tuple(widget: object) -> str:
            if widget is None:
                return "n/a"
            try:
                box = getattr(widget, "render_box", None)
                box_str = f"{box.width}x{box.height}" if box else "render-box:n/a"
                size = getattr(widget, "size", None)
                size_str = f"{size.width}x{size.height}" if size else "size:n/a"
                return f"{size_str} ({box_str})"
            except Exception:
                return "err"

        log_parts = [f"app-size={self.size.width}x{self.size.height}"]
        for name, widget in widgets.items():
            log_parts.append(f"{name}={size_tuple(widget)}")

        line = " | ".join(log_parts)
        self.log(f"[sizes] {line}")
        if self._app_logger:
            with contextlib.suppress(Exception):
                self._app_logger.info(f"[sizes] {line}")
        with contextlib.suppress(Exception):
            sys.stderr.write(f"[sizes] {line}\n")
            sys.stderr.flush()

    @work(thread=True)
    def _start_indexing(self) -> None:
        """Run indexing in background thread."""
        # Handle schema migrations first (deletes DB if version mismatch)
        force_rebuild = ensure_schema_current()

        # Check if index is already up-to-date (fast path)
        if not force_rebuild and is_index_current():
            conn = get_db_connection()
            init_db(conn)
            stats = get_index_stats(conn)
            conn.close()
            self.call_from_thread(self._on_indexing_complete, stats)
            return

        # Use a separate connection for background indexing
        # SQLite connections must be used in the thread that created them
        conn = get_db_connection()
        init_db(conn)

        def progress_callback(current: int, total: int, message: str) -> None:
            # Schedule UI update on main thread
            self.call_from_thread(self._update_loading_progress, current, total, message)

        # Build/update index with progress (force=True after schema migration)
        build_index(conn, force=force_rebuild, progress_callback=progress_callback)
        stats = get_index_stats(conn)
        conn.close()

        # Schedule completion on main thread
        self.call_from_thread(self._on_indexing_complete, stats)

    def _update_loading_progress(self, current: int, total: int, message: str) -> None:
        """Update loading progress UI (safe if overlay already removed)."""
        try:
            progress_bar = self.query_one("#loading-progress", ProgressBar)
            status_label = self.query_one("#loading-status", Label)
            progress_bar.update(total=total, progress=current)
            status_label.update(f"Indexing {current} of {total} sessions...")
        except Exception:
            # Overlay already removed - ignore stale callbacks
            pass

    def _on_indexing_complete(self, stats: dict[str, int]) -> None:
        """Handle indexing completion - transition to main UI."""
        # Ensure minimum display time to prevent flicker
        elapsed = time.monotonic() - self._load_start_time
        min_display_time = 0.2  # 200ms
        if elapsed < min_display_time:
            # Schedule the transition after remaining time
            remaining = min_display_time - elapsed
            self.set_timer(remaining, lambda: self._show_main_ui(stats))
        else:
            self._show_main_ui(stats)

    def _show_main_ui(self, stats: dict[str, int]) -> None:
        """Show main UI after loading completes."""
        # Check if already transitioned (idempotent)
        try:
            loading_overlay = self.query_one("#loading-overlay")
        except Exception:
            return  # Already transitioned

        # Create query connection in main thread
        if not self.conn:
            self.conn = get_db_connection()

        # Remove loading overlay entirely for clean layout
        loading_overlay.remove()

        # Show main content
        main_content = self.query_one("#main-content")
        main_content.add_class("visible")
        # Ensure grid columns reflect current sidebar visibility
        self._apply_sidebar_grid()

        # Force screen refresh to recalculate layout after overlay removal
        self.refresh(layout=True)

        # Notify user
        self.notify(
            f"Indexed {stats['sessions']} sessions ({stats['messages']} messages)",
            timeout=2,
        )
        if self._app_logger:
            self._app_logger.info(
                "Indexing complete", sessions=stats["sessions"], messages=stats["messages"]
            )

        # Load initial results
        if self.initial_query:
            search_input = self.query_one("#search-input", Input)
            search_input.value = self.initial_query
            self.current_query = self.initial_query
            self._do_search(self.initial_query)
        else:
            self._clear_results()

        # Focus search input
        self.query_one("#search-input", Input).focus()

    def _clear_results(self) -> None:
        """Clear results list."""
        self.results = []
        results_list = self.query_one("#results-list", ListView)
        results_list.clear()
        preview = self.query_one("#preview-content", Static)
        preview.update("Enter a search query")
        path_display = self.query_one("#path-display", Static)
        path_display.update("")
        path_display.remove_class("has-path")

    def _do_search(self, query: str) -> None:
        """Perform a search."""
        if not self.conn or self._reindex_in_progress:
            return

        self.current_query = query.strip()

        if not self.current_query:
            self._clear_results()
            return

        self.results = search_sessions(self.conn, query, limit=50)
        self._update_results_list()

    def _update_results_list(self) -> None:
        """Update the results list widget."""
        results_list = self.query_one("#results-list", ListView)
        results_list.clear()

        # Clear metadata panel when results change
        self._update_metadata(None)

        for result in self.results:
            results_list.append(ResultItem(result))

        preview = self.query_one("#preview-content", Static)
        path_display = self.query_one("#path-display", Static)

        if self.results:
            # Don't auto-select first item - let user navigate to select
            preview.update("Select a session to see preview")
            path_display.update("")
            path_display.remove_class("has-path")
        else:
            preview.update("No results found")
            path_display.update("No results")
            path_display.remove_class("has-path")

    def _extract_highlight_terms(self, query: str) -> list[str]:
        """Extract actual search terms from FTS5 query, filtering out operators and syntax."""
        import re

        # FTS5 operators to ignore (case-insensitive)
        operators = {"and", "or", "not", "near"}

        # Remove NEAR(...) constructs entirely
        query = re.sub(r"NEAR\s*\([^)]*\)", " ", query, flags=re.IGNORECASE)

        # Split on whitespace and punctuation, keeping alphanumeric sequences
        tokens = re.findall(r"[a-zA-Z0-9]+", query)

        # Filter out operators and very short terms
        terms = []
        for token in tokens:
            lower_token = token.lower()
            if lower_token not in operators and len(token) >= 2:
                terms.append(lower_token)

        return terms

    def _build_highlighted_text(self, content: str, base_style: str = "") -> Text:
        """Build a Text object with search term highlighting at word boundaries."""
        import re

        if not self.current_query:
            return Text(content, style=base_style)

        terms = self._extract_highlight_terms(self.current_query)
        if not terms:
            return Text(content, style=base_style)

        # Build regex pattern for word-boundary matching
        # Match terms at word start (allows prefix matching like FTS5)
        escaped_terms = [re.escape(term) for term in terms]
        pattern = r"\b(" + "|".join(escaped_terms) + r")\w*"

        text = Text(style=base_style)
        last_end = 0

        for match in re.finditer(pattern, content, re.IGNORECASE):
            # Add text before match
            if match.start() > last_end:
                text.append(content[last_end : match.start()])
            # Add highlighted match
            text.append(match.group(), style="reverse")
            last_end = match.end()

        # Add remaining text
        if last_end < len(content):
            text.append(content[last_end:])

        return text

    def _update_preview(self, result: SearchResult) -> None:
        """Update the preview pane for a result."""
        if not self.conn or not self.show_preview:
            return

        preview = self.query_one("#preview-content", Static)
        messages = get_session_preview(
            self.conn, result.session_id, query=self.current_query, limit=10
        )

        if not messages:
            preview.update("No messages to preview")
            return

        # Build Text object directly - no markup parsing needed
        text = Text()
        for role, content in messages:
            role_style = "green" if role == "user" else "cyan"
            role_label = "User" if role == "user" else "Assistant"

            # Flatten newlines for display
            content_preview = content.replace("\n", " ")

            # Add role label with style
            text.append(f"{role_label}: ", style=role_style)
            # Add content with highlighting
            text.append_text(self._build_highlighted_text(content_preview))
            text.append("\n\n")

        preview.update(text)

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes with debounce."""
        # Cancel any pending search
        if self._search_timer:
            self._search_timer.stop()

        # Schedule new search after 1 second debounce
        query = event.value
        self._search_timer = self.set_timer(1.0, lambda: self._do_search(query))

    @on(ListView.Highlighted, "#results-list")
    def on_result_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle result highlight - update preview only."""
        if event.item and isinstance(event.item, ResultItem):
            self._update_preview(event.item.result)
            self._update_path_display(event.item.result)

    @on(ListView.Selected, "#results-list")
    def on_result_selected(self, event: ListView.Selected) -> None:
        """Handle explicit result selection - show metadata details."""
        if event.item and isinstance(event.item, ResultItem):
            self._update_metadata(event.item.result)

    def _update_metadata(self, result: SearchResult | None) -> None:
        """Update the metadata panel with session details."""
        help_panel = self.query_one("#help-panel", HelpPanel)
        help_panel.update_metadata(result)

    def _update_path_display(self, result: SearchResult) -> None:
        """Update the path display bar with the selected session path."""
        path_display = self.query_one("#path-display", Static)
        path_display.update(f"Path: {result.file_path}  [Enter to copy]")
        path_display.add_class("has-path")

    def action_focus_search(self) -> None:
        """Focus the search input and move cursor to end without selecting."""
        search_input = self.query_one("#search-input", SearchInput)
        search_input.focus()
        # Clear selection and move cursor to end (use current value, cleanup handles restoration)
        end_pos = len(search_input.value)
        search_input.selection = Selection.cursor(end_pos)

    def _focus_search_after_slash(self) -> None:
        """Focus search input, marking it to reject the "/" key."""
        search_input = self.query_one("#search-input", SearchInput)
        # Mark to reject "/" with expected value for cleanup
        search_input.focus_via_slash(search_input.value)
        search_input.focus()
        # Move cursor to end
        end_pos = len(search_input.value)
        search_input.selection = Selection.cursor(end_pos)

    def action_cursor_down(self) -> None:
        """Move cursor down in results."""
        results_list = self.query_one("#results-list", ListView)
        results_list.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in results."""
        results_list = self.query_one("#results-list", ListView)
        results_list.action_cursor_up()

    def action_copy_path(self) -> None:
        """Copy the selected session path to clipboard."""
        results_list = self.query_one("#results-list", ListView)
        if results_list.highlighted_child and isinstance(
            results_list.highlighted_child, ResultItem
        ):
            path = results_list.highlighted_child.result.file_path
            path_display = self.query_one("#path-display", Static)
            try:
                pyperclip.copy(path)
                path_display.update(f"Copied to clipboard: {path}")
                self.notify("Path copied!", timeout=1)
            except pyperclip.PyperclipException:
                # Fallback: just show the path prominently
                path_display.update(f"Copy manually: {path}")
                self.notify("Clipboard unavailable - copy path manually", timeout=3)

    def action_toggle_preview(self) -> None:
        """Toggle the preview pane."""
        self.show_preview = not self.show_preview
        preview_container = self.query_one("#preview-container")
        preview_container.display = self.show_preview

        if self.show_preview:
            results_list = self.query_one("#results-list", ListView)
            if results_list.highlighted_child and isinstance(
                results_list.highlighted_child, ResultItem
            ):
                self._update_preview(results_list.highlighted_child.result)

    def action_toggle_keys_panel(self) -> None:
        """Toggle the keys panel on the right side."""
        help_panel = self.query_one("#help-panel", HelpPanel)
        syntax_panel = self.query_one("#syntax-panel", SyntaxPanel)
        sidebar = self.query_one("#right-sidebar")

        if self._active_panel == "keys":
            # Hide keys panel and sidebar
            help_panel.remove_class("visible")
            sidebar.remove_class("visible")
            self._active_panel = None
        else:
            # Show keys panel, hide syntax if visible
            syntax_panel.remove_class("visible")
            help_panel.add_class("visible")
            sidebar.add_class("visible")
            self._active_panel = "keys"
        self._apply_sidebar_grid()

    def action_toggle_syntax_panel(self) -> None:
        """Toggle the syntax help panel on the right side."""
        help_panel = self.query_one("#help-panel", HelpPanel)
        syntax_panel = self.query_one("#syntax-panel", SyntaxPanel)
        sidebar = self.query_one("#right-sidebar")

        if self._active_panel == "syntax":
            # Hide syntax panel and sidebar
            syntax_panel.remove_class("visible")
            sidebar.remove_class("visible")
            self._active_panel = None
        else:
            # Show syntax panel, hide keys if visible
            help_panel.remove_class("visible")
            syntax_panel.add_class("visible")
            sidebar.add_class("visible")
            self._active_panel = "syntax"
        self._apply_sidebar_grid()

    def action_show_theme_menu(self) -> None:
        """Show theme selection menu."""
        # Don't open if already showing
        if any(isinstance(s, ThemeScreen) for s in self.screen_stack):
            return

        def handle_theme_result(result: str | None) -> None:
            if result:
                self.theme = result
                save_settings({"theme": result})
                self.notify(f"Theme changed to {result}", timeout=1)

        self.push_screen(ThemeScreen(self.theme), handle_theme_result)

    def action_show_about(self) -> None:
        """Show about dialog."""
        # Don't open if already showing
        if any(isinstance(s, AboutScreen) for s in self.screen_stack):
            return
        self.push_screen(AboutScreen())

    def action_reindex(self) -> None:
        """Show reindex confirmation dialog."""
        # Don't open if already showing or reindex in progress
        if any(isinstance(s, ReindexConfirmScreen) for s in self.screen_stack):
            return
        if self._reindex_in_progress:
            self.notify("Reindex already in progress", timeout=2)
            return

        # Get current session count for confirmation message
        session_count = 0
        if self.conn:
            stats = get_index_stats(self.conn)
            session_count = stats.get("sessions", 0)

        def handle_reindex_result(confirmed: bool) -> None:
            if confirmed:
                self._start_reindex()

        self.push_screen(ReindexConfirmScreen(session_count), handle_reindex_result)

    def _start_reindex(self) -> None:
        """Start the reindex process."""
        # Close existing connection before reindex
        if self.conn:
            self.conn.close()
            self.conn = None

        # Set flag to block search during reindex
        self._reindex_in_progress = True

        # Show reindex overlay
        self._show_reindex_overlay()

        # Start background reindex
        self._do_reindex()

    def _show_reindex_overlay(self) -> None:
        """Show the reindex progress overlay."""
        # Build overlay structure similar to loading overlay
        overlay_content = Container(
            Label("Rebuilding Index", id="reindex-title"),
            ProgressBar(id="reindex-progress", show_eta=False),
            Label("Starting...", id="reindex-status"),
            id="reindex-container",
        )
        overlay = Center(
            Middle(overlay_content),
            id="reindex-overlay",
        )
        self.mount(overlay)

    @work(thread=True)
    def _do_reindex(self) -> None:
        """Run reindex in background thread."""
        try:
            conn = get_db_connection()
            init_db(conn)

            def progress_callback(current: int, total: int, message: str) -> None:
                self.call_from_thread(self._update_reindex_progress, current, total)

            build_index(conn, force=True, progress_callback=progress_callback)
            stats = get_index_stats(conn)
            conn.close()

            self.call_from_thread(self._on_reindex_complete, stats)
        except Exception as e:
            self.call_from_thread(self._on_reindex_error, str(e))

    def _update_reindex_progress(self, current: int, total: int) -> None:
        """Update reindex progress UI."""
        try:
            progress_bar = self.query_one("#reindex-progress", ProgressBar)
            status_label = self.query_one("#reindex-status", Label)
            progress_bar.update(total=total, progress=current)
            status_label.update(f"Reindexing {current} of {total} sessions...")
        except Exception:
            pass  # Overlay might be removed

    def _on_reindex_complete(self, stats: dict[str, int]) -> None:
        """Handle reindex completion."""
        # Remove overlay
        try:
            overlay = self.query_one("#reindex-overlay")
            overlay.remove()
        except Exception:
            pass

        # Clear flag
        self._reindex_in_progress = False

        # Reopen connection
        self.conn = get_db_connection()

        # Notify user
        self.notify(
            f"Reindexed {stats['sessions']} sessions ({stats['messages']} messages)",
            timeout=3,
        )
        if self._app_logger:
            self._app_logger.info(
                "Reindex complete", sessions=stats["sessions"], messages=stats["messages"]
            )

        # Refresh current search if any
        if self.current_query:
            self._do_search(self.current_query)

    def _on_reindex_error(self, error_message: str) -> None:
        """Handle reindex error."""
        # Remove overlay
        try:
            overlay = self.query_one("#reindex-overlay")
            overlay.remove()
        except Exception:
            pass

        # Clear flag
        self._reindex_in_progress = False

        # Reopen connection
        self.conn = get_db_connection()

        # Notify user of error
        self.notify(f"Reindex failed: {error_message}", severity="error", timeout=5)
        if self._app_logger:
            self._app_logger.error("Reindex failed", error=error_message)

    def action_handle_slash(self) -> None:
        """Handle slash key via binding - focus search or type /."""
        if self.focused and isinstance(self.focused, Input):
            # In input - type the character
            search_input = self.query_one("#search-input", SearchInput)
            search_input.insert_text_at_cursor("/")
        else:
            # Not in input - focus and cleanup any leaked slash
            self._focus_search_after_slash()

    def on_key(self, event: Key) -> None:
        """Handle key events - block single chars when Input focused."""
        # Slash is handled by priority binding, not here
        # Only block single-character keys when Input is focused
        # Control combinations (ctrl+k, ctrl+t) should pass through
        if self.focused and isinstance(self.focused, Input) and not event.key.startswith("ctrl+"):
            return


def reset_terminal() -> None:
    """Reset terminal to sane state after TUI exits.

    Matches Textual's cleanup sequences to ensure complete terminal restoration.
    Writes to stderr (where Textual writes) and stdout for complete coverage when
    running in a real TTY. Skip non-TTY streams to avoid leaking escape codes
    into IDE logs or other captured outputs.
    """
    targets = []
    if sys.stderr is not None and sys.stderr.isatty():
        targets.append(sys.stderr)
    if sys.stdout is not None and sys.stdout.isatty():
        targets.append(sys.stdout)
    if not targets:
        return

    reset_sequences = [
        "\x1b[<u",  # Disable Kitty keyboard protocol (must be before alt screen exit)
        "\x1b[?1049l",  # Exit alternate screen buffer
        "\x1b[?1000l",  # Disable mouse tracking (SET_VT200_MOUSE)
        "\x1b[?1002l",  # Disable mouse button tracking
        "\x1b[?1003l",  # Disable all mouse tracking (SET_ANY_EVENT_MOUSE)
        "\x1b[?1006l",  # Disable SGR extended mouse mode
        "\x1b[?1015l",  # Disable urxvt mouse mode (SET_VT200_HIGHLIGHT_MOUSE)
        "\x1b[?1016l",  # Disable mouse pixel mode
        "\x1b[?1004l",  # Disable FocusIn/FocusOut events
        "\x1b[?2004l",  # Disable bracketed paste mode
        "\x1b[?25h",  # Show cursor
        "\x1b[?7h",  # Enable line wrapping
        "\x1b[0m",  # Reset all attributes
    ]
    reset_data = "".join(reset_sequences)
    for target in targets:
        target.write(reset_data)
        target.flush()


_atexit_registered = False
_excepthook_installed = False


def _terminal_excepthook(exc_type: type, exc_value: BaseException, exc_tb: object) -> None:
    """Global exception hook to reset terminal on any uncaught exception."""
    reset_terminal()
    # Call the original excepthook to print the traceback
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def run_app(initial_query: str = "") -> str | None:
    """Run the TUI application."""
    global _atexit_registered, _excepthook_installed
    # Register cleanup only once per process
    if not _atexit_registered:
        atexit.register(reset_terminal)
        _atexit_registered = True
    if not _excepthook_installed:
        sys.excepthook = _terminal_excepthook
        _excepthook_installed = True

    # Handle signals that might leave terminal in bad state
    def signal_handler(signum: int, frame: object) -> None:
        reset_terminal()
        sys.exit(128 + signum)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    try:
        app = SessionSearchApp(initial_query=initial_query)
        return app.run()
    finally:
        reset_terminal()
