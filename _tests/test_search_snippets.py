"""Tests for search result highlighting and excerpts."""

import pytest
from playwright.sync_api import Page, expect


def _first_title_word(page: Page, jekyll_server: str) -> str:
    page.goto(f"{jekyll_server}/search-index.json")
    return page.evaluate(
        """() => {
            const data = JSON.parse(document.body.innerText);
            const title = (data[0] && data[0].title) || '';
            return (title.split(/\\s+/).find(w => w.length >= 3) || '').toLowerCase();
        }"""
    )


class TestSearchHighlighting:
    """Matched terms are wrapped in <mark>; results keep an excerpt."""

    def test_results_contain_a_highlight(self, page: Page, jekyll_server: str):
        """A query taken from a real title highlights at least one match."""
        word = _first_title_word(page, jekyll_server)
        if not word:
            pytest.skip("no indexable post titles")

        page.goto(f"{jekyll_server}/search/?q={word}")
        expect(page.locator(".search-result-item").first).to_be_visible()

        assert page.locator(".search-result-item mark").count() > 0, "matched terms should be wrapped in <mark>"

    def test_results_have_excerpt(self, page: Page, jekyll_server: str):
        """Each result still renders an excerpt element."""
        word = _first_title_word(page, jekyll_server)
        if not word:
            pytest.skip("no indexable post titles")

        page.goto(f"{jekyll_server}/search/?q={word}")
        expect(page.locator(".search-result-item").first).to_be_visible()

        assert page.locator(".search-result-excerpt").count() > 0, "results should include an excerpt"

    def test_highlight_escapes_markup(self, page: Page, jekyll_server: str):
        """Highlighting must not inject raw HTML from index content."""
        word = _first_title_word(page, jekyll_server)
        if not word:
            pytest.skip("no indexable post titles")

        page.goto(f"{jekyll_server}/search/?q={word}")
        expect(page.locator(".search-result-item").first).to_be_visible()

        # Only <mark> should appear inside a title span; no stray tags.
        stray = page.locator(".search-result-title *:not(mark)").count()
        assert stray == 0, "title should contain only text and <mark> elements"
