"""Tests for search functionality."""

from playwright.sync_api import Page

from constants import ANIMATION_TIMEOUT, SELECTORS


class TestSearchBar:
    """Tests for search bar in sidebar."""

    def test_search_bar_visible_in_sidebar(self, page: Page, jekyll_server: str):
        """Search bar should be visible when sidebar is open."""
        page.goto(jekyll_server)

        # Open sidebar
        page.locator(SELECTORS["sidebar_toggle"]).click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        # Search container should be visible
        search_container = page.locator(SELECTORS["search_container"])
        assert (
            search_container.is_visible()
        ), "Search container should be visible in sidebar"

    def test_search_input_exists(self, page: Page, jekyll_server: str):
        """Search input field should exist."""
        page.goto(jekyll_server)

        page.locator(SELECTORS["sidebar_toggle"]).click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        search_input = page.locator(SELECTORS["search_input"])
        assert search_input.count() == 1, "Should have one search input"

    def test_search_bar_position_after_theme_toggle(
        self, page: Page, jekyll_server: str
    ):
        """Search bar should appear after theme toggle in DOM order."""
        page.goto(jekyll_server)

        page.locator(SELECTORS["sidebar_toggle"]).click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        # Check DOM order: theme-toggle should come before search-container
        sidebar = page.locator(".sidebar")

        theme_toggle_index = sidebar.evaluate(
            """el => {
                const children = Array.from(el.querySelectorAll('.theme-toggle, .search-container'));
                const toggle = el.querySelector('.theme-toggle');
                return children.indexOf(toggle);
            }"""
        )

        search_index = sidebar.evaluate(
            """el => {
                const children = Array.from(el.querySelectorAll('.theme-toggle, .search-container'));
                const search = el.querySelector('.search-container');
                return children.indexOf(search);
            }"""
        )

        assert (
            theme_toggle_index < search_index
        ), "Theme toggle should come before search container"
