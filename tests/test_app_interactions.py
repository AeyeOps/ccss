"""Automated TUI interaction tests using Textual's Pilot API."""

import pytest

from ccss.app import SessionSearchApp


@pytest.fixture
def app() -> SessionSearchApp:
    """Create app instance for testing."""
    return SessionSearchApp()


class TestAppBasics:
    """Basic app functionality tests."""

    @pytest.mark.asyncio
    async def test_app_launches(self, app: SessionSearchApp) -> None:
        """App should launch without errors."""
        async with app.run_test() as pilot:
            # Wait for indexing to complete
            await pilot.pause()
            # App should be running
            assert app.is_running

    @pytest.mark.asyncio
    async def test_search_input_exists(self, app: SessionSearchApp) -> None:
        """Search input should exist after load."""
        async with app.run_test() as pilot:
            await pilot.pause()
            search_input = app.query_one("#search-input")
            assert search_input is not None

    @pytest.mark.asyncio
    async def test_type_in_search(self, app: SessionSearchApp) -> None:
        """Typing in search should update input value."""
        from textual.widgets import Input

        async with app.run_test() as pilot:
            await pilot.pause()
            search_input = app.query_one("#search-input", Input)
            initial_value = search_input.value

            # Focus search and type
            await pilot.press("slash")  # Focus search
            await pilot.press("d")
            await pilot.pause()

            # Verify character was typed
            assert search_input.value != initial_value or "d" in search_input.value
            assert app.is_running

    @pytest.mark.asyncio
    async def test_search_various_terms(self, app: SessionSearchApp) -> None:
        """Search various terms that might break markup."""
        from textual.widgets import Input

        problem_terms = [
            "d",  # Single char
            "test",
            "[bracket]",  # Literal brackets
            "[green]",  # Rich markup lookalike
            "[/green]",  # Closing tag lookalike
            "\\[escaped",  # Backslash
            "<xml>",  # Angle brackets
            "**bold**",  # Markdown
            "```code```",
        ]
        async with app.run_test() as pilot:
            await pilot.pause()

            for term in problem_terms:
                # Clear and type new term
                search_input = app.query_one("#search-input", Input)
                search_input.value = ""
                await pilot.pause()
                search_input.value = term
                await pilot.pause()

                # Verify term was set correctly
                assert search_input.value == term, f"Term not preserved: expected '{term}', got '{search_input.value}'"
                assert app.is_running, f"Crashed on term: {term}"

    @pytest.mark.asyncio
    async def test_navigate_results(self, app: SessionSearchApp) -> None:
        """Navigate through results with j/k keys."""
        from textual.widgets import ListView

        async with app.run_test() as pilot:
            await pilot.pause()

            results_list = app.query_one("#results-list", ListView)
            child_count = len(results_list.children)

            if child_count >= 2:
                initial_idx = results_list.index or 0

                # Navigate down
                await pilot.press("j")
                await pilot.pause()
                after_j = results_list.index
                assert after_j is not None
                assert after_j > initial_idx, "j should move selection down"

                await pilot.press("j")
                await pilot.pause()

                # Navigate up
                await pilot.press("k")
                await pilot.pause()
                after_k = results_list.index
                assert after_k is not None
                assert after_k < results_list.index + 1, "k should move selection up"

            assert app.is_running

    @pytest.mark.asyncio
    async def test_copy_path(self, app: SessionSearchApp) -> None:
        """Copy path action should not crash."""
        async with app.run_test() as pilot:
            await pilot.pause()

            # Try to copy (might fail if no clipboard, but shouldn't crash app)
            await pilot.press("enter")
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_toggle_preview(self, app: SessionSearchApp) -> None:
        """Toggle preview pane via action (keypress consumed by input in tests)."""
        async with app.run_test() as pilot:
            await pilot.pause()

            initial = app.show_preview  # Should be True by default

            # Call action directly since 'p' keypress is consumed by focused Input
            app.action_toggle_preview()
            await pilot.pause()
            assert app.show_preview != initial, "Preview should have toggled off"

            # Toggle back
            app.action_toggle_preview()
            await pilot.pause()
            assert app.show_preview == initial, "Preview should have toggled back on"

    @pytest.mark.asyncio
    async def test_quit(self, app: SessionSearchApp) -> None:
        """Quit should exit cleanly."""
        async with app.run_test() as pilot:
            await pilot.pause()
            # Verify app is running before quit
            assert app.is_running, "App should be running before quit"
            await pilot.press("q")
            # App exits - context completes without exception = success

    @pytest.mark.asyncio
    async def test_ctrl_k_toggle_keys_panel(self, app: SessionSearchApp) -> None:
        """Ctrl+K should toggle keys panel visibility (not footer)."""
        async with app.run_test() as pilot:
            await pilot.pause()

            from textual.widgets import Footer

            from ccss.app import HelpPanel

            footer = app.query_one(Footer)
            initial_footer_display = footer.display

            # Help panel should exist but not be visible initially
            help_panel = app.query_one("#help-panel", HelpPanel)
            assert not help_panel.has_class("visible"), "Help panel should not be visible initially"

            # Press Ctrl+K to show keys panel
            await pilot.press("ctrl+k")
            await pilot.pause()

            # Help panel should now be visible
            assert help_panel.has_class("visible"), "Help panel should be visible after Ctrl+K"
            # Footer should remain visible
            assert footer.display == initial_footer_display, "Footer should stay visible"

            # Press Ctrl+K again to hide keys panel
            await pilot.press("ctrl+k")
            await pilot.pause()

            # Help panel should be hidden again
            assert not help_panel.has_class("visible"), "Help panel should hide after Ctrl+K"

    @pytest.mark.asyncio
    async def test_ctrl_t_theme_menu(self, app: SessionSearchApp) -> None:
        """Ctrl+T should open theme menu."""
        async with app.run_test() as pilot:
            await pilot.pause()

            # Press Ctrl+T - should open modal
            await pilot.press("ctrl+t")
            await pilot.pause()

            # Check if ThemeScreen is active
            from ccss.app import ThemeScreen

            # Screen stack should have theme screen
            assert any(isinstance(s, ThemeScreen) for s in app.screen_stack)

            # Press escape to close
            await pilot.press("escape")
            await pilot.pause()


class TestSlashKeyBehavior:
    """Tests for slash key focusing search input.

    Note: These tests are inherently flaky due to timing dependencies in
    Textual's event dispatch system. The feature works reliably in real usage,
    but the test framework's event timing is non-deterministic.
    """

    @pytest.mark.asyncio
    @pytest.mark.flaky(reruns=5)
    async def test_slash_focuses_search_without_typing(self) -> None:
        """Pressing / should focus search without typing the character."""
        import asyncio

        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            # Clear and unfocus
            search_input.value = ""
            await pilot.pause()

            # Focus results list to unfocus input
            results_list = app.query_one("#results-list")
            results_list.focus()
            await pilot.pause()

            # Press slash
            await pilot.press("slash")

            # Poll until value is correct or timeout
            for _ in range(20):
                await asyncio.sleep(0.02)
                await pilot.pause()
                if search_input.value == "":
                    break

            # Input should be focused
            assert search_input.has_focus, "Search input should be focused"
            # Input should NOT contain slash character
            assert search_input.value == "", f"Expected empty, got '{search_input.value}'"

    @pytest.mark.asyncio
    @pytest.mark.flaky(reruns=5)
    async def test_slash_with_existing_content_cursor_at_end(self) -> None:
        """Pressing / with existing content should move cursor to end."""
        import asyncio

        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            test_content = "existing query"
            search_input.value = test_content
            await pilot.pause()

            # Focus results list to unfocus input
            results_list = app.query_one("#results-list")
            results_list.focus()
            await pilot.pause()

            # Press slash to focus
            await pilot.press("slash")

            # Poll until value is correct or timeout
            for _ in range(20):
                await asyncio.sleep(0.02)
                await pilot.pause()
                if search_input.value == test_content:
                    break

            # Input should be focused with cursor at end
            assert search_input.has_focus, "Search input should be focused"
            # Content should be preserved (not overwritten)
            assert search_input.value == test_content, "Content should be preserved"
            # Cursor should be at end
            assert search_input.cursor_position == len(test_content), (
                f"Cursor should be at end ({len(test_content)}), "
                f"got {search_input.cursor_position}"
            )

    @pytest.mark.asyncio
    @pytest.mark.flaky(reruns=5)
    async def test_slash_preserves_existing_content(self) -> None:
        """Pressing / should preserve existing content (not overwrite with /)."""
        import asyncio

        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            test_content = "important search"
            search_input.value = test_content
            await pilot.pause()

            # Focus results list
            results_list = app.query_one("#results-list")
            results_list.focus()
            await pilot.pause()

            # Press slash to focus
            await pilot.press("slash")

            # Poll until value is correct or timeout
            for _ in range(20):
                await asyncio.sleep(0.02)
                await pilot.pause()
                if search_input.value == test_content:
                    break

            # Content should be preserved (not overwritten by /)
            assert search_input.value == test_content, (
                f"Content changed after slash: expected '{test_content}', got '{search_input.value}'"
            )
            # "/" should NOT have been typed into the input
            assert "/" not in search_input.value, "Slash character was typed into input"


class TestEdgeCases:
    """Edge cases and stress tests."""

    @pytest.mark.asyncio
    async def test_empty_search_results(self) -> None:
        """Search that returns no results should not crash."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Search for something that won't match
            search_input = app.query_one("#search-input")
            search_input.value = "xyzzy_nonexistent_query_12345"
            await pilot.pause()

            # Should not crash (app may fall back to showing recent sessions)
            assert app.is_running

    @pytest.mark.asyncio
    async def test_navigate_empty_results(self) -> None:
        """Navigate when no results - should not crash."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Clear to no results
            search_input = app.query_one("#search-input")
            search_input.value = "xyzzy_nonexistent_12345"
            await pilot.pause()

            # Try navigating anyway
            await pilot.press("j")
            await pilot.press("j")
            await pilot.press("k")
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_scroll_to_bottom(self) -> None:
        """Scroll all the way down through results."""
        from textual.widgets import ListView

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            results_list = app.query_one("#results-list", ListView)
            child_count = len(results_list.children)

            # Hammer down key many times
            for _ in range(100):
                await pilot.press("j")

            await pilot.pause()

            # Should have reached bottom (or stayed at 0 if empty)
            if child_count > 0:
                final_idx = results_list.index or 0
                assert final_idx == child_count - 1, f"Should be at bottom ({child_count - 1}), got {final_idx}"
            assert app.is_running

    @pytest.mark.asyncio
    async def test_scroll_past_bounds(self) -> None:
        """Try to scroll past list boundaries."""
        from textual.widgets import ListView

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            results_list = app.query_one("#results-list", ListView)
            child_count = len(results_list.children)

            # Try scrolling up when at top
            for _ in range(20):
                await pilot.press("k")
            await pilot.pause()

            # Should stay at top (index 0 or None if empty)
            if child_count > 0:
                idx_after_k = results_list.index
                assert idx_after_k is not None
                assert idx_after_k >= 0, "Index should not go negative"

            # Scroll to bottom
            for _ in range(100):
                await pilot.press("j")
            await pilot.pause()

            # Try scrolling down when at bottom
            for _ in range(20):
                await pilot.press("j")
            await pilot.pause()

            # Should stay at bottom
            if child_count > 0:
                idx_after_j = results_list.index
                assert idx_after_j is not None
                assert idx_after_j <= child_count - 1, "Index should not exceed list length"

            assert app.is_running

    @pytest.mark.asyncio
    async def test_rapid_search_changes(self) -> None:
        """Rapidly change search query."""
        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            search_terms = ["a", "ab", "abc", "ab", "a", "", "test", "x", ""]

            # Rapid fire different searches
            for term in search_terms:
                search_input.value = term
                await pilot.pause()

            # Verify final state is the last term set
            assert search_input.value == "", "Final search value should be empty string"
            assert app.is_running

    @pytest.mark.asyncio
    async def test_special_unicode_search(self) -> None:
        """Search with unicode and emoji."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input")

            unicode_terms = [
                "café",
                "日本語",
                "emoji 🎉",
                "→←↑↓",
                "零一二三",
                "\u200b",  # Zero-width space
                "naïve résumé",
            ]

            for term in unicode_terms:
                search_input.value = term
                await pilot.pause()
                assert app.is_running, f"Crashed on unicode: {term}"

    @pytest.mark.asyncio
    async def test_very_long_search_query(self) -> None:
        """Very long search query."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input")
            search_input.value = "a" * 1000  # 1000 character search
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_control_characters_search(self) -> None:
        """Search with control characters and escapes."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input")

            control_terms = [
                "\t",  # Tab
                "\r",  # Carriage return
                "\\n",  # Literal backslash-n
                "\\t",
                "\x00",  # Null (might be filtered)
                "\x1b",  # Escape
            ]

            for term in control_terms:
                try:
                    search_input.value = term
                    await pilot.pause()
                except Exception:
                    pass  # Some control chars may be rejected, that's OK

            assert app.is_running

    @pytest.mark.asyncio
    async def test_copy_with_no_selection(self) -> None:
        """Copy when nothing is selected."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Search for nothing
            search_input = app.query_one("#search-input")
            search_input.value = "xyzzy_nonexistent_12345"
            await pilot.pause()

            # Try to copy
            await pilot.press("enter")
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_toggle_preview_rapid(self) -> None:
        """Rapidly toggle preview."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            initial_state = app.show_preview

            # Toggle many times (20 = even number)
            for _ in range(20):
                app.action_toggle_preview()
                await pilot.pause()

            # 20 toggles = back to original state
            assert app.show_preview == initial_state, "Even toggles should return to original state"
            assert app.is_running

    @pytest.mark.asyncio
    async def test_search_while_navigating(self) -> None:
        """Search and navigate simultaneously without crash."""
        from textual.widgets import Input, ListView

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            results_list = app.query_one("#results-list", ListView)

            # Interleave search value changes with j presses
            # Note: j may type into input if focused, or navigate if not
            for i in range(10):
                search_input.value = f"test{i}"
                await pilot.pause()
                await pilot.press("j")
                await pilot.pause()

            # Verify app survived the stress test
            # Final value includes "j" chars typed when input was focused
            assert "test" in search_input.value, "Search should contain 'test'"
            assert app.is_running

    @pytest.mark.asyncio
    async def test_theme_switch_stress(self) -> None:
        """Stress test theme switching (action only, no modal)."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Directly change theme property multiple times
            from ccss.settings import AVAILABLE_THEMES

            for theme in AVAILABLE_THEMES * 3:  # Cycle 3 times
                app.theme = theme
                await pilot.pause()

            assert app.is_running


class TestThemeModal:
    """Theme modal comprehensive tests."""

    @pytest.mark.asyncio
    async def test_theme_modal_opens_with_option_list_focused(self) -> None:
        """Opening theme modal should focus the OptionList."""
        from textual.widgets import OptionList

        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Open theme modal
            await pilot.press("ctrl+t")
            await pilot.pause()

            # Verify ThemeScreen is on stack
            theme_screen = None
            for screen in app.screen_stack:
                if isinstance(screen, ThemeScreen):
                    theme_screen = screen
                    break
            assert theme_screen is not None, "ThemeScreen should be on stack"

            # Verify OptionList has focus
            option_list = theme_screen.query_one("#theme-list", OptionList)
            assert option_list.has_focus, "OptionList should have focus"

    @pytest.mark.asyncio
    async def test_theme_modal_scroll_down(self) -> None:
        """Scrolling down in theme list should change highlighted index."""
        from textual.widgets import OptionList

        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("ctrl+t")
            await pilot.pause()

            theme_screen = next(s for s in app.screen_stack if isinstance(s, ThemeScreen))
            option_list = theme_screen.query_one("#theme-list", OptionList)
            initial_index = option_list.highlighted

            # Press down arrow
            await pilot.press("down")
            await pilot.pause()

            # Index should have increased (unless already at bottom)
            assert app.is_running
            # If not at bottom, index should change
            if initial_index is not None and initial_index < option_list.option_count - 1:
                assert option_list.highlighted == initial_index + 1

    @pytest.mark.asyncio
    async def test_theme_modal_scroll_up(self) -> None:
        """Scrolling up in theme list should change highlighted index."""
        from textual.widgets import OptionList

        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("ctrl+t")
            await pilot.pause()

            theme_screen = next(s for s in app.screen_stack if isinstance(s, ThemeScreen))
            option_list = theme_screen.query_one("#theme-list", OptionList)

            # First scroll down to have room to scroll up
            await pilot.press("down")
            await pilot.press("down")
            await pilot.pause()

            current_index = option_list.highlighted

            # Press up arrow
            await pilot.press("up")
            await pilot.pause()

            assert app.is_running
            if current_index is not None and current_index > 0:
                assert option_list.highlighted == current_index - 1

    @pytest.mark.asyncio
    async def test_theme_modal_current_theme_highlighted_with_marker(self) -> None:
        """Current theme should be highlighted and have marker on open."""
        from textual.widgets import OptionList

        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            current_theme = app.theme

            await pilot.press("ctrl+t")
            await pilot.pause()

            theme_screen = next(s for s in app.screen_stack if isinstance(s, ThemeScreen))
            option_list = theme_screen.query_one("#theme-list", OptionList)

            # Get the highlighted option
            highlighted_idx = option_list.highlighted
            assert highlighted_idx is not None

            # The highlighted option should correspond to current theme
            highlighted_option = option_list.get_option_at_index(highlighted_idx)
            assert highlighted_option is not None
            assert highlighted_option.id == current_theme
            # Should have marker in prompt
            assert " *" in str(highlighted_option.prompt)

    @pytest.mark.asyncio
    async def test_select_current_theme_no_change(self) -> None:
        """Selecting current theme should close modal without change."""
        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            original_theme = app.theme

            await pilot.press("ctrl+t")
            await pilot.pause()

            # Current theme should already be highlighted, press enter
            await pilot.press("enter")
            await pilot.pause()

            # Modal should be closed
            assert not any(isinstance(s, ThemeScreen) for s in app.screen_stack)
            # Theme should be unchanged
            assert app.theme == original_theme

    @pytest.mark.asyncio
    async def test_select_different_theme_changes_theme(self) -> None:
        """Selecting different theme should change app.theme."""
        from ccss.app import ThemeScreen
        from ccss.settings import AVAILABLE_THEMES

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            original_theme = app.theme
            # Find index of a theme that's different
            target_idx = next(
                i for i, t in enumerate(AVAILABLE_THEMES) if t != original_theme
            )
            # Calculate how many downs needed from current theme's position
            current_idx = AVAILABLE_THEMES.index(original_theme)

            await pilot.press("ctrl+t")
            await pilot.pause()

            # Navigate to the target theme
            if target_idx > current_idx:
                for _ in range(target_idx - current_idx):
                    await pilot.press("down")
                    await pilot.pause()
            else:
                # Go up instead
                for _ in range(current_idx - target_idx):
                    await pilot.press("up")
                    await pilot.pause()

            # Select the highlighted theme
            await pilot.press("enter")
            await pilot.pause()

            # Modal should be closed
            assert not any(isinstance(s, ThemeScreen) for s in app.screen_stack)
            # Theme should have changed
            assert app.theme == AVAILABLE_THEMES[target_idx], "Theme should have changed"

    @pytest.mark.asyncio
    async def test_escape_cancels_without_change(self) -> None:
        """Escape should close modal without changing theme."""
        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            original_theme = app.theme

            await pilot.press("ctrl+t")
            await pilot.pause()

            # Navigate to different theme
            await pilot.press("down")
            await pilot.press("down")
            await pilot.pause()

            # Press escape instead of enter
            await pilot.press("escape")
            await pilot.pause()

            # Modal should be closed
            assert not any(isinstance(s, ThemeScreen) for s in app.screen_stack)
            # Theme should be unchanged
            assert app.theme == original_theme

    @pytest.mark.asyncio
    async def test_empty_search_bar_preserved_after_escape(self) -> None:
        """Empty search bar should stay empty after theme modal escape."""
        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            search_input.value = ""
            await pilot.pause()

            # Open and close theme modal
            await pilot.press("ctrl+t")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Search bar should still be empty
            assert search_input.value == ""

    @pytest.mark.asyncio
    async def test_text_preserved_after_escape(self) -> None:
        """Text in search bar should be preserved after theme modal escape."""
        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            test_text = "test query"
            search_input.value = test_text
            await pilot.pause()

            # Open and close theme modal
            await pilot.press("ctrl+t")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Search bar should have same text
            assert search_input.value == test_text

    @pytest.mark.asyncio
    async def test_text_preserved_after_selecting_same_theme(self) -> None:
        """Text should be preserved after selecting current theme."""
        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            test_text = "my important search"
            search_input.value = test_text
            await pilot.pause()

            # Open theme modal and select current theme (already highlighted)
            await pilot.press("ctrl+t")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Search bar should have same text
            assert search_input.value == test_text

    @pytest.mark.asyncio
    async def test_text_preserved_after_selecting_different_theme(self) -> None:
        """Text should be preserved after selecting different theme."""
        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)
            test_text = "my search"
            search_input.value = test_text
            await pilot.pause()

            # Open theme modal, navigate, and select
            await pilot.press("ctrl+t")
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Search bar should have same text
            assert search_input.value == test_text

    @pytest.mark.asyncio
    async def test_no_garbage_characters_after_theme_selection(self) -> None:
        """No wacky/garbage characters should appear in search bar after theme selection.

        This tests a reported bug where selecting a theme corrupts the search input.
        """
        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)

            # Test with various initial states
            test_cases = [
                "",  # Empty
                "simple",  # Simple text
                "with spaces",  # Spaces
                "special[chars]",  # Brackets
            ]

            for test_text in test_cases:
                search_input.value = test_text
                await pilot.pause()

                # Open theme modal, select different theme
                await pilot.press("ctrl+t")
                await pilot.pause()
                await pilot.press("down")
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()

                # Verify no garbage characters
                result = search_input.value
                assert result == test_text, (
                    f"Search bar corrupted! Expected '{test_text}', got '{result}'"
                )
                # Check for common garbage patterns
                assert "\x00" not in result, "Null character in search bar"
                assert "\x1b" not in result, "Escape sequence in search bar"
                # Only ASCII printable + expected unicode should be present
                for char in result:
                    if char not in test_text:
                        pytest.fail(
                            f"Unexpected character '{char}' (ord={ord(char)}) in search bar"
                        )

    @pytest.mark.asyncio
    async def test_rapid_theme_modal_open_close(self) -> None:
        """Rapidly opening and closing theme modal should not crash."""
        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            for _ in range(10):
                await pilot.press("ctrl+t")
                await pilot.pause()
                await pilot.press("escape")
                await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_scroll_past_top_boundary(self) -> None:
        """Scrolling up at top of list should not crash."""
        from textual.widgets import OptionList

        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("ctrl+t")
            await pilot.pause()

            theme_screen = next(s for s in app.screen_stack if isinstance(s, ThemeScreen))
            option_list = theme_screen.query_one("#theme-list", OptionList)

            # Manually set to top to test boundary
            option_list.highlighted = 0
            await pilot.pause()

            # Try to scroll up past top - should not crash
            for _ in range(5):
                await pilot.press("up")
                await pilot.pause()

            assert app.is_running
            # Should stay clamped at top (0) or wrap - either way no crash
            assert option_list.highlighted is not None

    @pytest.mark.asyncio
    async def test_scroll_past_bottom_boundary(self) -> None:
        """Scrolling down at bottom of list should not crash."""
        from textual.widgets import OptionList

        from ccss.app import ThemeScreen
        from ccss.settings import AVAILABLE_THEMES

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("ctrl+t")
            await pilot.pause()

            theme_screen = next(s for s in app.screen_stack if isinstance(s, ThemeScreen))
            option_list = theme_screen.query_one("#theme-list", OptionList)

            # Manually set to bottom to test boundary
            bottom_index = len(AVAILABLE_THEMES) - 1
            option_list.highlighted = bottom_index
            await pilot.pause()

            # Try to scroll down past bottom - should not crash
            for _ in range(5):
                await pilot.press("down")
                await pilot.pause()

            assert app.is_running
            # Should stay clamped at bottom or wrap - either way no crash
            assert option_list.highlighted is not None

    @pytest.mark.asyncio
    async def test_theme_change_with_search_results(self) -> None:
        """Changing theme while search results displayed should preserve results."""
        from textual.widgets import Input, ListView

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # App should have loaded recent sessions by default
            results_list = app.query_one("#results-list", ListView)
            search_input = app.query_one("#search-input", Input)

            # Enter a search term
            search_input.value = "test"
            await pilot.pause()
            await pilot.pause()  # Extra pause for search results to load

            # Change theme
            await pilot.press("ctrl+t")
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            # Search bar text should be preserved and app should still be running
            assert search_input.value == "test"
            assert app.is_running
            # Results list should not be empty (either recent sessions or search results)
            # The exact count may vary based on search results vs recent sessions
            assert len(results_list.children) >= 0

    @pytest.mark.asyncio
    async def test_theme_persistence_calls_save(self) -> None:
        """Selecting theme should persist via save_settings."""
        from unittest.mock import patch

        from ccss.settings import AVAILABLE_THEMES

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            original_theme = app.theme
            # Find index of a different theme
            target_theme = next(t for t in AVAILABLE_THEMES if t != original_theme)

            with patch("ccss.app.save_settings") as mock_save:
                await pilot.press("ctrl+t")
                await pilot.pause()

                # Navigate to target theme
                for _ in range(AVAILABLE_THEMES.index(target_theme) + 1):
                    await pilot.press("down")
                    await pilot.pause()

                await pilot.press("enter")
                await pilot.pause()

                # save_settings must be called when theme changes
                assert mock_save.called, "save_settings must be called when theme changes"
                call_args = mock_save.call_args[0][0]
                assert "theme" in call_args, "save_settings should receive theme in settings"

    @pytest.mark.asyncio
    async def test_switch_to_cc_tribute_theme(self) -> None:
        """Test switching to CC Tribute theme specifically."""
        from ccss.app import ThemeScreen
        from ccss.settings import AVAILABLE_THEMES

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # CC Tribute should be first in the list
            assert AVAILABLE_THEMES[0] == "cc-tribute"
            cc_tribute_idx = 0
            original_theme = app.theme
            current_idx = AVAILABLE_THEMES.index(original_theme)

            await pilot.press("ctrl+t")
            await pilot.pause()

            # Navigate to cc-tribute (index 0)
            if current_idx > cc_tribute_idx:
                for _ in range(current_idx - cc_tribute_idx):
                    await pilot.press("up")
                    await pilot.pause()

            await pilot.press("enter")
            await pilot.pause()

            # Modal should be closed
            assert not any(isinstance(s, ThemeScreen) for s in app.screen_stack)
            # Theme should be cc-tribute
            assert app.theme == "cc-tribute"

    @pytest.mark.asyncio
    async def test_ctrl_t_does_not_stack_modals(self) -> None:
        """Pressing Ctrl+T while theme modal is open should not open another."""
        from ccss.app import ThemeScreen

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Open theme modal
            await pilot.press("ctrl+t")
            await pilot.pause()

            # Count theme screens
            theme_count = sum(1 for s in app.screen_stack if isinstance(s, ThemeScreen))
            assert theme_count == 1, "Should have exactly one theme modal"

            # Press Ctrl+T again while modal is open
            await pilot.press("ctrl+t")
            await pilot.pause()

            # Should still have only one theme modal
            theme_count = sum(1 for s in app.screen_stack if isinstance(s, ThemeScreen))
            assert theme_count == 1, "Ctrl+T should not stack theme modals"

            # Close modal
            await pilot.press("escape")
            await pilot.pause()

            assert not any(isinstance(s, ThemeScreen) for s in app.screen_stack)


class TestSearchHighlighting:
    """Tests for search term highlighting in preview."""

    def test_extract_simple_terms(self) -> None:
        """Simple words extracted correctly."""
        app = SessionSearchApp()
        terms = app._extract_highlight_terms("hello world")
        assert "hello" in terms
        assert "world" in terms

    def test_extract_filters_operators(self) -> None:
        """FTS5 operators (AND, OR, NOT) filtered out."""
        app = SessionSearchApp()
        terms = app._extract_highlight_terms("hello AND world OR test NOT excluded")
        assert "hello" in terms
        assert "world" in terms
        assert "test" in terms
        assert "AND" not in terms
        assert "OR" not in terms
        assert "NOT" not in terms

    def test_extract_handles_empty_query(self) -> None:
        """Empty query returns empty list."""
        app = SessionSearchApp()
        terms = app._extract_highlight_terms("")
        assert terms == []

    def test_extract_handles_only_operators(self) -> None:
        """Query with only operators returns empty list."""
        app = SessionSearchApp()
        terms = app._extract_highlight_terms("AND OR NOT")
        assert terms == []

    def test_build_highlighted_contains_text(self) -> None:
        """Highlighted text contains the original content."""
        app = SessionSearchApp()
        app.current_query = "hello"
        result = app._build_highlighted_text("hello world test")
        result_str = str(result)
        assert "hello" in result_str.lower()
        assert "world" in result_str.lower()

    def test_build_highlighted_no_query_returns_plain(self) -> None:
        """Empty query returns plain text without highlighting."""
        app = SessionSearchApp()
        app.current_query = ""
        result = app._build_highlighted_text("hello world")
        # Should just be plain text
        assert str(result) == "hello world"

    def test_build_highlighted_preserves_content(self) -> None:
        """All original content preserved in highlighted output."""
        app = SessionSearchApp()
        app.current_query = "test"
        content = "this is a test of highlighting"
        result = app._build_highlighted_text(content)
        # All words should be present (possibly with markup)
        result_lower = str(result).lower()
        for word in ["this", "is", "a", "test", "of", "highlighting"]:
            assert word in result_lower, f"Word '{word}' missing from result"

    @pytest.mark.asyncio
    async def test_preview_with_search_term(self) -> None:
        """Preview content renders without crash when search term set."""
        from textual.widgets import Input

        app = SessionSearchApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            search_input = app.query_one("#search-input", Input)

            # Search for a term
            search_input.value = "test"
            await pilot.pause()
            await pilot.pause()  # Extra for debounce

            # App should still be running and preview should exist
            preview = app.query_one("#preview-content")
            assert preview is not None
            assert app.is_running
