from playwright.sync_api import Page


class TestThemeToggle:
    """Tests for light/dark mode toggle functionality."""

    def clear_storage_and_reload(self, page: Page):
        """Clear localStorage and reload for consistent state."""
        page.evaluate("() => localStorage.clear()")
        page.reload()
        page.wait_for_load_state("domcontentloaded")

    def test_toggle_switches_theme(self, page: Page, jekyll_server: str):
        """Clicking toggle should switch theme."""
        page.goto(jekyll_server)
        self.clear_storage_and_reload(page)

        html = page.locator("html")
        initial_theme = html.get_attribute("data-theme")

        # Open sidebar to access toggle
        page.locator(".sidebar-toggle").click()
        page.wait_for_timeout(400)

        # Click the label/toggle container (not the hidden input)
        toggle = page.locator(".toggle-switch")
        toggle.click(force=True)

        # Verify theme changed
        new_theme = html.get_attribute("data-theme")
        assert new_theme != initial_theme

    def test_toggle_switches_to_opposite_theme(self, page: Page, jekyll_server: str):
        """Toggle should alternate between light and dark."""
        page.goto(jekyll_server)
        self.clear_storage_and_reload(page)

        page.locator(".sidebar-toggle").click()
        page.wait_for_timeout(400)

        html = page.locator("html")
        toggle = page.locator(".toggle-switch")

        # Get initial state
        initial_theme = html.get_attribute("data-theme")

        # Click once
        toggle.click(force=True)
        first_toggle_theme = html.get_attribute("data-theme")

        # Click again
        toggle.click(force=True)
        second_toggle_theme = html.get_attribute("data-theme")

        # Should return to initial
        assert second_toggle_theme == initial_theme
        assert first_toggle_theme != initial_theme

    def test_theme_changes_background_color(self, page: Page, jekyll_server: str):
        """Theme toggle should change background color."""
        page.goto(jekyll_server)
        self.clear_storage_and_reload(page)

        body = page.locator("body")
        initial_bg = body.evaluate("el => getComputedStyle(el).backgroundColor")

        # Switch theme
        page.locator(".sidebar-toggle").click()
        page.wait_for_timeout(400)
        page.locator(".toggle-switch").click(force=True)

        new_bg = body.evaluate("el => getComputedStyle(el).backgroundColor")

        assert initial_bg != new_bg

    def test_theme_persists_in_localstorage(self, page: Page, jekyll_server: str):
        """Theme preference should be saved to localStorage."""
        page.goto(jekyll_server)
        self.clear_storage_and_reload(page)

        # Get initial theme from localStorage
        initial_stored = page.evaluate("() => localStorage.getItem('theme')")

        page.locator(".sidebar-toggle").click()
        page.wait_for_timeout(400)
        page.locator(".toggle-switch").click(force=True)

        # Check localStorage changed
        new_stored = page.evaluate("() => localStorage.getItem('theme')")
        assert new_stored is not None
        assert new_stored != initial_stored or initial_stored is None

    def test_theme_persists_after_reload(self, page: Page, jekyll_server: str):
        """Theme should persist after page reload."""
        page.goto(jekyll_server)
        self.clear_storage_and_reload(page)

        # Toggle theme
        page.locator(".sidebar-toggle").click()
        page.wait_for_timeout(400)
        page.locator(".toggle-switch").click(force=True)

        # Get theme after toggle
        html = page.locator("html")
        theme_before_reload = html.get_attribute("data-theme")

        # Reload page
        page.reload()

        # Verify theme persisted
        theme_after_reload = html.get_attribute("data-theme")
        assert theme_after_reload == theme_before_reload

    def test_checkbox_state_matches_light_theme(self, page: Page, jekyll_server: str):
        """Toggle checkbox checked state should indicate light theme."""
        page.goto(jekyll_server)
        self.clear_storage_and_reload(page)

        page.locator(".sidebar-toggle").click()
        page.wait_for_timeout(400)

        toggle_input = page.locator(".theme-toggle input[type='checkbox']")
        html = page.locator("html")

        # Check current state
        is_checked = toggle_input.is_checked()
        current_theme = html.get_attribute("data-theme")

        # Checkbox checked = light theme
        if is_checked:
            assert current_theme == "light"
        else:
            assert current_theme is None or current_theme == "dark"

    def test_dark_theme_colors(self, page: Page, jekyll_server: str):
        """Dark theme should have dark background."""
        page.goto(jekyll_server)

        # Set to dark theme via JS
        page.evaluate("() => { localStorage.setItem('theme', 'dark'); }")
        page.reload()

        body = page.locator("body")
        bg_color = body.evaluate("el => getComputedStyle(el).backgroundColor")

        # Dark theme background should be dark (#1a1a1a = rgb(26, 26, 26))
        assert "rgb(26, 26, 26)" in bg_color or "rgba(26, 26, 26" in bg_color

    def test_light_theme_colors(self, page: Page, jekyll_server: str):
        """Light theme should have light background."""
        page.goto(jekyll_server)

        # Set to light theme via JS
        page.evaluate("() => { localStorage.setItem('theme', 'light'); }")
        page.reload()

        body = page.locator("body")
        bg_color = body.evaluate("el => getComputedStyle(el).backgroundColor")

        # Light theme background should be light (#f2ede7 = rgb(242, 237, 231))
        assert "rgb(242, 237, 231)" in bg_color or "rgba(242, 237, 231" in bg_color
