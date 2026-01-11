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

    def test_sidebar_search_no_live_results(self, page: Page, jekyll_server: str):
        """Sidebar search should not show live results while typing."""
        page.goto(jekyll_server)

        page.locator(SELECTORS["sidebar_toggle"]).click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        search_input = page.locator(SELECTORS["search_input"])
        search_input.fill("test")
        page.wait_for_timeout(300)

        # Sidebar should NOT have results container with content
        sidebar_results = page.locator(".sidebar .search-results")
        assert sidebar_results.count() == 0, "Sidebar should not have results container"

    def test_sidebar_search_redirects_on_enter(self, page: Page, jekyll_server: str):
        """Pressing Enter in sidebar search should redirect to search page."""
        page.goto(jekyll_server)

        page.locator(SELECTORS["sidebar_toggle"]).click()
        page.wait_for_timeout(ANIMATION_TIMEOUT)

        search_input = page.locator(SELECTORS["search_input"])
        search_input.fill("test")
        search_input.press("Enter")

        page.wait_for_url("**/search/**")
        assert "/search/" in page.url, "Should redirect to search page"
        assert "q=test" in page.url, "URL should contain query parameter"


class TestSearchIndex:
    """Tests for search index generation."""

    def test_search_index_json_exists(self, page: Page, jekyll_server: str):
        """Search index JSON file should be generated."""
        response = page.goto(f"{jekyll_server}/search-index.json")
        assert response.status == 200, "search-index.json should exist"

    def test_search_index_is_valid_json(self, page: Page, jekyll_server: str):
        """Search index should be valid JSON."""
        page.goto(f"{jekyll_server}/search-index.json")

        # Try to parse as JSON
        is_valid = page.evaluate(
            """() => {
                try {
                    JSON.parse(document.body.innerText);
                    return true;
                } catch (e) {
                    return false;
                }
            }"""
        )
        assert is_valid, "search-index.json should be valid JSON"

    def test_search_index_contains_posts(self, page: Page, jekyll_server: str):
        """Search index should contain post data."""
        page.goto(f"{jekyll_server}/search-index.json")

        has_posts = page.evaluate(
            """() => {
                const data = JSON.parse(document.body.innerText);
                return Array.isArray(data) && data.length > 0;
            }"""
        )
        assert has_posts, "search-index.json should contain posts"

    def test_search_index_post_has_required_fields(
        self, page: Page, jekyll_server: str
    ):
        """Each post in index should have title, url, and content."""
        page.goto(f"{jekyll_server}/search-index.json")

        has_fields = page.evaluate(
            """() => {
                const data = JSON.parse(document.body.innerText);
                if (!Array.isArray(data) || data.length === 0) return false;
                const post = data[0];
                return 'title' in post && 'url' in post && 'content' in post;
            }"""
        )
        assert has_fields, "Posts should have title, url, and content fields"


class TestSearchResultsPage:
    """Tests for dedicated search results page."""

    def test_search_page_exists(self, page: Page, jekyll_server: str):
        """Search results page should exist."""
        response = page.goto(f"{jekyll_server}/search/")
        assert response.status == 200, "Search page should exist"

    def test_search_page_has_search_input(self, page: Page, jekyll_server: str):
        """Search page should have a search input."""
        page.goto(f"{jekyll_server}/search/")

        search_input = page.locator(".search-page-input")
        assert search_input.count() == 1, "Search page should have search input"

    def test_search_page_displays_results_from_query(
        self, page: Page, jekyll_server: str
    ):
        """Search page should display results based on query parameter."""
        page.goto(f"{jekyll_server}/search/?q=test")
        page.wait_for_timeout(500)

        results = page.locator(".search-result-item")
        assert results.count() > 0, "Should display results for query"

    def test_search_page_shows_query_in_input(self, page: Page, jekyll_server: str):
        """Search input should show the current query."""
        page.goto(f"{jekyll_server}/search/?q=test")

        search_input = page.locator(".search-page-input")
        value = search_input.input_value()
        assert value == "test", "Input should contain query"

    def test_search_page_enter_triggers_new_search(
        self, page: Page, jekyll_server: str
    ):
        """Pressing Enter on search page should trigger new search."""
        page.goto(f"{jekyll_server}/search/?q=test")

        search_input = page.locator(".search-page-input")
        search_input.fill("lorem")
        search_input.press("Enter")

        page.wait_for_url("**/search/?q=lorem**")
        assert "q=lorem" in page.url, "URL should update with new query"

    def test_search_page_no_live_results(self, page: Page, jekyll_server: str):
        """Search page should not show live results while typing."""
        page.goto(f"{jekyll_server}/search/?q=test")
        page.wait_for_timeout(300)

        # Get initial result count
        initial_results = page.locator(".search-result-item").count()

        # Type without pressing Enter
        search_input = page.locator(".search-page-input")
        search_input.fill("xyznonexistent")
        page.wait_for_timeout(300)

        # Results should not change (still showing "test" results)
        current_results = page.locator(".search-result-item").count()
        assert (
            current_results == initial_results
        ), "Results should not change until Enter"

    def test_search_results_are_clickable(self, page: Page, jekyll_server: str):
        """Search results should be clickable links."""
        page.goto(f"{jekyll_server}/search/?q=test")
        page.wait_for_timeout(500)

        result_link = page.locator(".search-result-item").first
        href = result_link.get_attribute("href")
        assert href is not None and len(href) > 0, "Result should have href"

    def test_search_no_results_message(self, page: Page, jekyll_server: str):
        """Should show message when no results found."""
        page.goto(f"{jekyll_server}/search/?q=xyznonexistent123456")
        page.wait_for_timeout(500)

        no_results = page.locator(".search-no-results")
        assert no_results.count() == 1, "Should show no results message"

    def test_fuzzy_search_finds_typos(self, page: Page, jekyll_server: str):
        """Fuzzy search should find results with typos."""
        page.goto(f"{jekyll_server}/search/?q=tset")
        page.wait_for_timeout(500)

        results = page.locator(".search-result-item")
        assert results.count() > 0, "Fuzzy search should find results with typos"
