"""Tests for tag-aware search."""

from playwright.sync_api import Page, expect


class TestTagIndex:
    """The index carries tags and results surface them."""

    def test_index_has_tags_field(self, page: Page, jekyll_server: str):
        """Each indexed post exposes a tags array."""
        page.goto(f"{jekyll_server}/search-index.json")

        ok = page.evaluate(
            """() => {
                const data = JSON.parse(document.body.innerText);
                if (!Array.isArray(data) || data.length === 0) return false;
                return 'tags' in data[0] && Array.isArray(data[0].tags);
            }"""
        )
        assert ok, "index posts should have a tags array"

    def test_search_by_tag_returns_results(self, page: Page, jekyll_server: str, any_post_tag: str):
        """Searching a real tag returns at least one result."""
        page.goto(f"{jekyll_server}/search/?q={any_post_tag}")
        expect(page.locator(".search-result-item").first).to_be_visible()

    def test_results_render_tag_chips(self, page: Page, jekyll_server: str, any_post_tag: str):
        """Results for a tagged post show tag chips."""
        page.goto(f"{jekyll_server}/search/?q={any_post_tag}")
        expect(page.locator(".search-result-item").first).to_be_visible()

        assert page.locator(".search-result-tag").count() > 0, "tagged results should render tag chips"
