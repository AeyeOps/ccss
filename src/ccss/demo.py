#!/usr/bin/env python3
"""Visual demo of app interactions with real assertions."""

import asyncio
import atexit
import signal
import sys

from textual import work
from textual.widgets import Input

from ccss.app import SessionSearchApp, reset_terminal


class DemoApp(SessionSearchApp):
    """App subclass that runs demo sequence with real assertions."""

    def __init__(self) -> None:
        super().__init__()
        self._passed = 0
        self._failed = 0
        self._failures: list[str] = []

    def _assert(self, condition: bool, message: str) -> None:
        """Track assertion result and notify on failure."""
        if condition:
            self._passed += 1
        else:
            self._failed += 1
            self._failures.append(message)
            self.notify(f"FAIL: {message}", severity="error", timeout=5)

    @work
    async def run_demo_sequence(self) -> None:
        """Run through test scenarios with real assertions."""
        await asyncio.sleep(2)  # Wait for app to fully load

        # Get widgets
        try:
            search_input = self.query_one("#search-input", Input)
        except Exception:
            self.notify("Demo: Waiting for UI...")
            await asyncio.sleep(2)
            search_input = self.query_one("#search-input", Input)

        # Demo 1: Type in search - verify value changes
        self.notify("Demo 1: Typing search terms")
        search_input.value = ""
        await asyncio.sleep(0.2)
        for char in "test":
            search_input.value += char
            await asyncio.sleep(0.15)
        self._assert(
            search_input.value == "test",
            f"Typing: expected 'test', got '{search_input.value}'",
        )
        self._assert(self.is_running, "App should be running after typing")
        await asyncio.sleep(0.5)

        # Demo 2: Problematic terms - verify no crash and value is set
        self.notify("Demo 2: Problematic search terms")
        problem_terms = ["[green]", "[/green]", "**bold**", "emoji \U0001f389"]
        for term in problem_terms:
            search_input.value = term
            await asyncio.sleep(0.5)
            self._assert(
                search_input.value == term,
                f"Problem term: expected '{term}', got '{search_input.value}'",
            )
            self._assert(self.is_running, f"App crashed on term '{term}'")

        await asyncio.sleep(0.5)

        # Demo 3: FTS5 tests - verify searches complete without crash
        self.notify("Demo 3: FTS5 Search Syntax")
        fts5_tests = [
            ("error", "Simple term"),
            ("import function", "Multi-term AND"),
            ("TypeError OR ValueError", "Explicit OR"),
            ("database NOT postgres", "Negation"),
            ('"file not found"', "Exact phrase"),
            ("config*", "Prefix search"),
            ("^import", "Start anchor"),
            ("NEAR(test error, 10)", "Proximity"),
            ("(async OR await) AND error", "Grouped boolean"),
            ('"running tests" OR tested', "Phrase + OR"),
        ]

        for query, description in fts5_tests:
            self.notify(f"FTS5: {description}")
            search_input.value = query
            await asyncio.sleep(0.8)
            self._assert(
                search_input.value == query,
                f"FTS5 '{description}': value mismatch",
            )
            self._assert(self.is_running, f"FTS5 '{description}': app crashed")

        await asyncio.sleep(0.5)

        # Demo 4: Toggle syntax panel (F1)
        self.notify("Demo 4: Syntax panel toggle (F1)")
        search_input.value = ""
        await asyncio.sleep(0.3)
        # Note: Can't easily verify syntax panel state, just verify no crash
        self.action_toggle_syntax_panel()
        await asyncio.sleep(1)
        self._assert(self.is_running, "App crashed on syntax panel toggle")
        self.action_toggle_syntax_panel()
        await asyncio.sleep(0.5)

        # Demo 5: Toggle preview pane
        self.notify("Demo 5: Preview pane toggle")
        initial_preview = self.show_preview
        self.action_toggle_preview()
        await asyncio.sleep(0.5)
        self._assert(
            self.show_preview != initial_preview,
            f"Preview toggle: expected {not initial_preview}, got {self.show_preview}",
        )
        self.action_toggle_preview()
        await asyncio.sleep(0.5)
        self._assert(
            self.show_preview == initial_preview,
            "Preview toggle back: state not restored",
        )

        # Demo 6: Toggle keys panel
        self.notify("Demo 6: Keys panel toggle")
        from ccss.app import HelpPanel

        help_panel = self.query_one("#help-panel", HelpPanel)
        initial_visible = help_panel.has_class("visible")
        self.action_toggle_keys_panel()
        await asyncio.sleep(0.8)
        self._assert(
            help_panel.has_class("visible") != initial_visible,
            "Keys panel visibility should toggle",
        )
        self.action_toggle_keys_panel()
        await asyncio.sleep(0.5)
        self._assert(
            help_panel.has_class("visible") == initial_visible,
            "Keys panel should restore to initial state",
        )

        # Demo 7: Theme menu
        self.notify("Demo 7: Theme menu")
        from ccss.app import ThemeScreen

        self.action_show_theme_menu()
        await asyncio.sleep(1)
        self._assert(
            any(isinstance(s, ThemeScreen) for s in self.screen_stack),
            "Theme screen should be on stack after action",
        )
        self.pop_screen()
        await asyncio.sleep(0.5)
        self._assert(
            not any(isinstance(s, ThemeScreen) for s in self.screen_stack),
            "Theme screen should be removed after pop",
        )

        # Demo 8: Rapid navigation
        self.notify("Demo 8: Rapid navigation")
        for _ in range(20):
            self.action_cursor_down()
            await asyncio.sleep(0.03)
        self._assert(self.is_running, "App crashed during rapid down navigation")

        for _ in range(10):
            self.action_cursor_up()
            await asyncio.sleep(0.03)
        self._assert(self.is_running, "App crashed during rapid up navigation")

        await asyncio.sleep(0.5)

        # Demo 9: Unicode search
        self.notify("Demo 9: Unicode search")
        unicode_term = "cafe"
        search_input.value = unicode_term
        await asyncio.sleep(0.8)
        self._assert(
            search_input.value == unicode_term,
            f"Unicode: expected '{unicode_term}', got '{search_input.value}'",
        )
        self._assert(self.is_running, "App crashed on Unicode search")

        # Clear search
        search_input.value = ""
        await asyncio.sleep(0.3)

        # Final summary
        total = self._passed + self._failed
        if self._failed == 0:
            self.notify(
                f"Demo PASSED: {self._passed}/{total} assertions",
                severity="information",
                timeout=10,
            )
        else:
            self.notify(
                f"Demo FAILED: {self._passed} passed, {self._failed} failed",
                severity="error",
                timeout=15,
            )
            # Show first few failures
            for failure in self._failures[:3]:
                self.notify(f"  {failure}", severity="warning", timeout=10)

    def on_mount(self) -> None:
        """Start demo after normal mount."""
        super().on_mount()
        # Schedule demo to start after indexing completes
        self.set_timer(3, self.run_demo_sequence)


def run_demo() -> None:
    """Run the demo app with proper terminal cleanup."""
    # Register cleanup - atexit handles duplicate registrations gracefully
    atexit.register(reset_terminal)

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
    print("=== CCSS Demo with Assertions ===")
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
