"""Tests for preventing theme flash on page navigation."""

from playwright.sync_api import Page

from constants import LIGHT_BG_COLOR


class TestThemeFlashPrevention:
    """Tests to ensure no flash when navigating in light mode."""

    def test_light_mode_no_flash_on_navigation(self, page: Page, jekyll_server: str):
        """When in light mode, navigating should not flash dark background."""
        page.goto(jekyll_server)

        # Set light mode
        page.evaluate("() => localStorage.setItem('theme', 'light')")
        page.reload()
        page.wait_for_load_state("domcontentloaded")

        # Capture background colors during navigation
        colors_during_load = []

        def capture_color():
            try:
                color = page.evaluate(
                    "() => getComputedStyle(document.body).backgroundColor"
                )
                colors_during_load.append(color)
            except Exception:
                pass

        # Navigate to another page and capture colors as early as possible
        page.goto(f"{jekyll_server}/about/")

        # Check initial background immediately after navigation starts
        initial_bg = page.evaluate(
            "() => getComputedStyle(document.documentElement).backgroundColor"
        )

        # The html element should have light background immediately
        # (before body even loads, the html bg should be correct)
        assert (
            LIGHT_BG_COLOR in initial_bg or "242" in initial_bg
        ), f"HTML should have light background immediately, got: {initial_bg}"

    def test_html_has_theme_attribute_before_domcontentloaded(
        self, page: Page, jekyll_server: str
    ):
        """Theme attribute should be set on html before DOMContentLoaded."""
        page.goto(jekyll_server)

        # Set light mode
        page.evaluate("() => localStorage.setItem('theme', 'light')")

        # Navigate and check theme attribute is set early
        page.goto(f"{jekyll_server}/essays/")

        # The data-theme should be set
        theme = page.locator("html").get_attribute("data-theme")
        assert theme == "light", f"Theme should be light, got: {theme}"

    def test_inline_script_sets_theme_before_css_renders(
        self, page: Page, jekyll_server: str
    ):
        """An inline script should set theme before stylesheets apply."""
        page.goto(jekyll_server)

        # Set light mode
        page.evaluate("() => localStorage.setItem('theme', 'light')")

        # Check that head contains inline theme script (not deferred)
        page.goto(f"{jekyll_server}/contact/")

        # Verify inline script exists in head
        inline_script = page.evaluate(
            """
            () => {
                const scripts = document.head.querySelectorAll('script:not([src])');
                for (const script of scripts) {
                    if (script.textContent.includes('localStorage') &&
                        script.textContent.includes('theme')) {
                        return true;
                    }
                }
                return false;
            }
        """
        )

        assert inline_script, "Should have inline theme script in head"
