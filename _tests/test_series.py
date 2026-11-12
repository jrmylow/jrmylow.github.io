"""Tests for series navigation: a post in a series lists the parts in series order.

Expectations are the designed corpus's series (corpus.py), whose series order differs from
its date order in both directions.
"""

import corpus
import pytest
from playwright.sync_api import Page

PARTS = [corpus.SERIES_FIRST, corpus.SERIES_SECOND, corpus.SERIES_THIRD]  # in series order
NO_SERIES = [
    pytest.param(corpus.SERIES_SOLO, id="series-of-one"),
    pytest.param(corpus.ALPHA, id="not-in-a-series"),
]


class TestSeries:
    @pytest.mark.parametrize("current", PARTS, ids=[part.slug for part in PARTS])
    def test_part_lists_the_series_in_order_and_marks_itself(self, page: Page, designed_site, current):
        """Run from each part: the list is the same, and only the part being read is marked."""
        page.goto(designed_site.page_url(current.filename))
        series = page.locator(".series")
        assert series.locator("h2").inner_text() == f"Series: {corpus.SERIES}"
        assert series.locator(".series-list li").all_inner_texts() == [part.title for part in PARTS]

        marked = series.locator(".series-list li[aria-current='true']")
        assert marked.all_inner_texts() == [current.title]
        assert marked.locator("a").count() == 0, "the part being read is not a link to itself"

        links = series.locator(".series-list a")
        others = [part for part in PARTS if part is not current]
        assert links.all_inner_texts() == [part.title for part in others]
        hrefs = links.evaluate_all("els => els.map(a => a.getAttribute('href'))")
        assert hrefs == [designed_site.document(part.filename)["url"] for part in others]

    @pytest.mark.parametrize("post", NO_SERIES)
    def test_post_without_a_series_to_navigate_has_no_block(self, page: Page, designed_site, post):
        page.goto(designed_site.page_url(post.filename))
        assert page.locator(".series").count() == 0
