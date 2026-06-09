"""Characterization tests for theme colors.

These pin the behaviors the `.theme-custom-01` body class currently provides, so
folding it into the variable-driven layer stays behavior-preserving:
- the open sidebar toggle uses the sidebar background color
- in-content links render in the heading color (not --link-color)

Green with the class present; must stay green after it is removed.
"""

from playwright.sync_api import Page


def _style(page: Page, selector: str, prop: str = "color") -> str:
    return page.locator(selector).first.evaluate(f"el => getComputedStyle(el).{prop}")


class TestThemeColors:
    def test_open_toggle_uses_sidebar_background(self, page: Page, jekyll_server: str):
        """When the sidebar is open, the toggle background matches the sidebar."""
        page.goto(f"{jekyll_server}/")
        sidebar_bg = _style(page, ".sidebar", "backgroundColor")

        # The checkbox is display:none, so set its checked state directly;
        # CSS `:checked ~ .sidebar-toggle` reflects the DOM property immediately.
        page.evaluate("document.getElementById('sidebar-checkbox').checked = true")
        toggle_bg = _style(page, ".sidebar-toggle", "backgroundColor")

        assert toggle_bg == sidebar_bg, f"Open toggle bg {toggle_bg} should match sidebar bg {sidebar_bg}"

    def test_content_links_use_heading_color(self, page: Page, jekyll_server: str):
        """In-content links render in the heading color, not the link color."""
        page.goto(f"{jekyll_server}/essays/")
        link_color = _style(page, ".page a")
        heading_color = _style(page, ".page-title")

        assert (
            link_color == heading_color
        ), f"Content link color {link_color} should match heading color {heading_color}"
