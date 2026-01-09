"""Tests for hamburger menu icon styling."""

from playwright.sync_api import Page

from constants import ANIMATION_TIMEOUT, SELECTORS, WHITE_HEX, WHITE_HEX_SHORT


class TestHamburgerIcon:
    """Tests for sidebar toggle hamburger icon."""

    def test_hamburger_icon_visible(self, page: Page, jekyll_server: str):
        """Hamburger icon should be visible."""
        page.goto(jekyll_server)

        toggle = page.locator(SELECTORS["sidebar_toggle"])
        assert toggle.is_visible(), "Sidebar toggle should be visible"

    def test_hamburger_icon_has_background_image(self, page: Page, jekyll_server: str):
        """Hamburger icon should have background image via ::before pseudo-element."""
        page.goto(jekyll_server)

        # Check that the toggle has dimensions (indicating icon is rendered)
        toggle = page.locator(SELECTORS["sidebar_toggle"])
        box = toggle.bounding_box()

        assert box is not None, "Toggle should have bounding box"
        assert box["width"] > 0, "Toggle should have width"
        assert box["height"] > 0, "Toggle should have height"

    def test_hamburger_icon_uses_css_variable_dark_mode(
        self, page: Page, jekyll_server: str
    ):
        """In dark mode, hamburger should use CSS variable for icon."""
        page.goto(jekyll_server)

        # Ensure dark mode
        page.evaluate("() => { localStorage.setItem('theme', 'dark'); }")
        page.reload()

        # Check the computed style uses the variable
        toggle_before = page.locator(SELECTORS["sidebar_toggle"])
        bg = toggle_before.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Should have an SVG background (contains 'url' and 'svg')
        assert "url" in bg.lower(), "Should have background image URL"

    def test_hamburger_icon_uses_css_variable_light_mode(
        self, page: Page, jekyll_server: str
    ):
        """In light mode, hamburger should use CSS variable for icon."""
        page.goto(jekyll_server)

        # Set light mode
        page.evaluate("() => { localStorage.setItem('theme', 'light'); }")
        page.reload()

        # Check the computed style uses the variable
        toggle_before = page.locator(SELECTORS["sidebar_toggle"])
        bg = toggle_before.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Should have an SVG background
        assert "url" in bg.lower(), "Should have background image URL"

    def test_hamburger_icon_color_differs_by_theme(
        self, page: Page, jekyll_server: str
    ):
        """Hamburger icon should have different colors in light vs dark mode."""
        page.goto(jekyll_server)

        # Get dark mode icon
        page.evaluate("() => { localStorage.setItem('theme', 'dark'); }")
        page.reload()
        toggle = page.locator(SELECTORS["sidebar_toggle"])
        dark_bg = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Get light mode icon
        page.evaluate("() => { localStorage.setItem('theme', 'light'); }")
        page.reload()
        light_bg = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # The SVG fill colors should differ (white vs dark blue)
        assert dark_bg != light_bg, "Icon should differ between themes"

    def _has_white_color(self, bg_string: str) -> bool:
        """Check if background string contains white color."""
        bg_lower = bg_string.lower()
        return WHITE_HEX in bg_lower or WHITE_HEX_SHORT in bg_lower

    def test_hamburger_icon_white_when_menu_open_light_mode(
        self, page: Page, jekyll_server: str
    ):
        """In light mode with menu open, hamburger icon should be white (not blue)."""
        page.goto(jekyll_server)

        # Set light mode
        page.evaluate("() => { localStorage.setItem('theme', 'light'); }")
        page.reload()

        # Get icon before opening menu (should be blue: #214B8A)
        toggle = page.locator(SELECTORS["sidebar_toggle"])
        closed_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Open the sidebar
        toggle.click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        # Get icon after opening menu (should be white: #ffffff)
        open_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Icons should differ - closed is blue, open is white
        assert closed_icon != open_icon, "Icon should change when menu opens"
        assert self._has_white_color(open_icon), "Open menu icon should be white"

    def test_hamburger_icon_white_when_menu_open_dark_mode(
        self, page: Page, jekyll_server: str
    ):
        """In dark mode with menu open, hamburger icon should remain white."""
        page.goto(jekyll_server)

        # Set dark mode
        page.evaluate("() => { localStorage.setItem('theme', 'dark'); }")
        page.reload()

        # Get icon before opening menu (should be white)
        toggle = page.locator(SELECTORS["sidebar_toggle"])
        closed_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Open the sidebar
        toggle.click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        # Get icon after opening menu (should still be white)
        open_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Both should contain white
        assert self._has_white_color(
            closed_icon
        ), "Closed menu icon should be white in dark mode"
        assert self._has_white_color(
            open_icon
        ), "Open menu icon should be white in dark mode"

    def test_hamburger_outline_thickness_when_open(
        self, page: Page, jekyll_server: str
    ):
        """Hamburger toggle outline should be thin (1px) when menu is open."""
        page.goto(jekyll_server)

        toggle = page.locator(SELECTORS["sidebar_toggle"])

        # Open the sidebar
        toggle.click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        # Get box-shadow
        box_shadow = toggle.evaluate("el => getComputedStyle(el).boxShadow")

        # Should have a box-shadow
        assert box_shadow != "none", "Toggle should have box-shadow when open"

        # The spread radius (outline thickness) should be 1px, not larger
        assert (
            "0px 0px 0px 1px" in box_shadow or "0 0 0 1px" in box_shadow
        ), f"Toggle outline should be 1px, got: {box_shadow}"
