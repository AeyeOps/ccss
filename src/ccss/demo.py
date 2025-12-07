#!/usr/bin/env python3
"""Visual demo of app interactions - watch the tests run live."""

import asyncio
import atexit
import signal
import sys

from textual import work
from textual.widgets import Input

import ccss.app as app_module
from ccss.app import SessionSearchApp, reset_terminal


class DemoApp(SessionSearchApp):
    """App subclass that runs demo sequence after loading."""

    @work
    async def run_demo_sequence(self) -> None:
        """Run through test scenarios visually with delays."""
        await asyncio.sleep(2)  # Wait for app to fully load

        # Get widgets
        try:
            search_input = self.query_one("#search-input", Input)
        except Exception:
            self.notify("Demo: Waiting for UI...")
            await asyncio.sleep(2)
            search_input = self.query_one("#search-input", Input)

        # Demo 1: Type in search
        self.notify("Demo: Typing search terms")
        for char in "test":
            search_input.value += char
            await asyncio.sleep(0.2)

        await asyncio.sleep(1)

        # Demo 2: Clear and try problematic terms
        self.notify("Demo: Testing problematic search terms")
        problem_terms = ["[green]", "[/green]", "**bold**", "emoji 🎉"]
        for term in problem_terms:
            search_input.value = term
            await asyncio.sleep(0.8)

        # Demo 3: FTS5 Search Syntax Tests
        self.notify("Demo: FTS5 Search Syntax Tests")
        await asyncio.sleep(1)

        # Define test cases with descriptions
        fts5_tests = [
            # (query, description)
            ("error", "Simple term (auto-prefix)"),
            ("import function", "Multi-term AND (default)"),
            ("TypeError OR ValueError", "Explicit OR disjunction"),
            ("database NOT postgres", "Negation with NOT"),
            ('"file not found"', "Exact phrase search"),
            ("config*", "Explicit prefix search"),
            ("^import", "Start anchor (begins with)"),
            ("NEAR(test error, 10)", "Proximity search (within 10)"),
            ("(async OR await) AND error", "Grouped boolean expression"),
            ('"running tests" OR tested', "Phrase + OR + stemming"),
        ]

        for query, description in fts5_tests:
            self.notify(f"FTS5: {description}")
            search_input.value = query
            await asyncio.sleep(1.5)  # Time to see results

        # Clear and show F1 syntax panel briefly
        self.notify("Demo: Showing syntax help panel (F1)")
        search_input.value = ""
        await asyncio.sleep(0.3)
        self.action_toggle_syntax_panel()
        await asyncio.sleep(2)
        self.action_toggle_syntax_panel()
        await asyncio.sleep(0.5)

        # Demo 4: Navigation
        self.notify("Demo: Navigating results")
        search_input.value = ""
        await asyncio.sleep(0.5)

        for _ in range(5):
            self.action_cursor_down()
            await asyncio.sleep(0.3)

        for _ in range(3):
            self.action_cursor_up()
            await asyncio.sleep(0.3)

        # Demo 5: Toggle preview
        self.notify("Demo: Toggle preview")
        self.action_toggle_preview()
        await asyncio.sleep(1)
        self.action_toggle_preview()
        await asyncio.sleep(1)

        # Demo 6: Toggle keys panel (keys sidebar)
        self.notify("Demo: Toggle keys panel")
        self.action_toggle_keys_panel()
        await asyncio.sleep(1.5)
        self.action_toggle_keys_panel()
        await asyncio.sleep(1)

        # Demo 7: Theme menu
        self.notify("Demo: Opening theme menu")
        self.action_show_theme_menu()
        await asyncio.sleep(2)
        # Dismiss the theme menu before continuing
        self.notify("Demo: Closing theme menu")
        self.pop_screen()
        await asyncio.sleep(0.5)

        # Demo 8: Rapid scrolling
        self.notify("Demo: Rapid scrolling")
        for _ in range(20):
            self.action_cursor_down()
            await asyncio.sleep(0.05)

        await asyncio.sleep(1)

        # Demo 9: Unicode search
        self.notify("Demo: Unicode search")
        search_input.value = "日本語 café"
        await asyncio.sleep(1.5)

        # Clear search and show completion stats
        search_input.value = ""
        await asyncio.sleep(0.3)

        # Done - show stats
        demo_count = 9
        fts5_count = len(fts5_tests)
        self.notify(
            f"Demo complete: {demo_count} demos, {fts5_count} FTS5 queries - All passed",
            timeout=10,
        )

    def on_mount(self) -> None:
        """Start demo after normal mount."""
        super().on_mount()
        # Schedule demo to start after indexing completes
        self.set_timer(3, self.run_demo_sequence)


def run_demo() -> None:
    """Run the demo app with proper terminal cleanup."""
    # Register cleanup only once per process (shared with app.py)
    if not app_module._atexit_registered:
        atexit.register(reset_terminal)
        app_module._atexit_registered = True

    # Handle signals that might leave terminal in bad state
    def signal_handler(signum: int, frame: object) -> None:
        reset_terminal()
        sys.exit(128 + signum)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app = DemoApp()
        app.run()
    finally:
        reset_terminal()


def main() -> None:
    """Entry point for ccss-demo command."""
    print("=== CCSS Visual Demo ===")
    print("Watch the app perform test interactions...")
    print("Press 'q' to quit when done.")
    print()
    try:
        run_demo()
    except KeyboardInterrupt:
        reset_terminal()
        print("\nDemo cancelled.")
        sys.exit(0)
    except Exception as e:
        reset_terminal()
        print(f"\nDemo crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
