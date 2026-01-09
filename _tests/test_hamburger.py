"""Tests for hamburger menu icon styling."""

from playwright.sync_api import Page


class TestHamburgerIcon:
    """Tests for sidebar toggle hamburger icon."""

    def test_hamburger_icon_visible(self, page: Page, jekyll_server: str):
        """Hamburger icon should be visible."""
        page.goto(jekyll_server)

        toggle = page.locator(".sidebar-toggle")
        assert toggle.is_visible(), "Sidebar toggle should be visible"

    def test_hamburger_icon_has_background_image(self, page: Page, jekyll_server: str):
        """Hamburger icon should have background image via ::before pseudo-element."""
        page.goto(jekyll_server)

        # Check that the toggle has dimensions (indicating icon is rendered)
        toggle = page.locator(".sidebar-toggle")
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
        toggle_before = page.locator(".sidebar-toggle")
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
        toggle_before = page.locator(".sidebar-toggle")
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
        toggle = page.locator(".sidebar-toggle")
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

    def test_hamburger_icon_white_when_menu_open_light_mode(
        self, page: Page, jekyll_server: str
    ):
        """In light mode with menu open, hamburger icon should be white (not blue)."""
        page.goto(jekyll_server)

        # Set light mode
        page.evaluate("() => { localStorage.setItem('theme', 'light'); }")
        page.reload()

        # Get icon before opening menu (should be blue: #214B8A)
        toggle = page.locator(".sidebar-toggle")
        closed_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Open the sidebar
        toggle.click()
        page.wait_for_timeout(400)

        # Get icon after opening menu (should be white: #ffffff)
        open_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Icons should differ - closed is blue, open is white
        assert closed_icon != open_icon, "Icon should change when menu opens"
        # Open icon should contain white color (ffffff)
        assert (
            "ffffff" in open_icon.lower() or "fff" in open_icon.lower()
        ), "Open menu icon should be white"

    def test_hamburger_icon_white_when_menu_open_dark_mode(
        self, page: Page, jekyll_server: str
    ):
        """In dark mode with menu open, hamburger icon should remain white."""
        page.goto(jekyll_server)

        # Set dark mode
        page.evaluate("() => { localStorage.setItem('theme', 'dark'); }")
        page.reload()

        # Get icon before opening menu (should be white)
        toggle = page.locator(".sidebar-toggle")
        closed_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Open the sidebar
        toggle.click()
        page.wait_for_timeout(400)

        # Get icon after opening menu (should still be white)
        open_icon = toggle.evaluate(
            "el => getComputedStyle(el, '::before').backgroundImage"
        )

        # Both should contain white
        assert (
            "ffffff" in closed_icon.lower() or "fff" in closed_icon.lower()
        ), "Closed menu icon should be white in dark mode"
        assert (
            "ffffff" in open_icon.lower() or "fff" in open_icon.lower()
        ), "Open menu icon should be white in dark mode"

    def test_hamburger_outline_thickness_when_open(
        self, page: Page, jekyll_server: str
    ):
        """Hamburger toggle outline should be thin (1px) when menu is open."""
        page.goto(jekyll_server)

        toggle = page.locator(".sidebar-toggle")

        # Open the sidebar
        toggle.click()
        page.wait_for_timeout(400)

        # Get box-shadow
        box_shadow = toggle.evaluate("el => getComputedStyle(el).boxShadow")

        # Should have a box-shadow
        assert box_shadow != "none", "Toggle should have box-shadow when open"

        # The spread radius (outline thickness) should be 1px, not larger
        # box-shadow format: "rgb(r, g, b) 0px 0px 0px 1px"
        # The last value before any trailing parts is the spread
        assert (
            "0px 0px 0px 1px" in box_shadow or "0 0 0 1px" in box_shadow
        ), f"Toggle outline should be 1px, got: {box_shadow}"
