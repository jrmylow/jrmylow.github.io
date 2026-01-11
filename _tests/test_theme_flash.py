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

        # Navigate to another page
        page.goto(f"{jekyll_server}/about/")
        page.wait_for_load_state("domcontentloaded")

        # Check body background after page is ready
        # The key is that body should have light background, not dark
        body_bg = page.evaluate("() => getComputedStyle(document.body).backgroundColor")

        assert (
            LIGHT_BG_COLOR in body_bg or "242" in body_bg
        ), f"Body should have light background after navigation, got: {body_bg}"

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
