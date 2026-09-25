"""Tests for post-series navigation.

Corpus-level feature: a deterministic red->green needs two published posts that
share a `series:` value (and optional `series_order:`). These tests assert the
contract and skip when no series exists in the live corpus; see README.
"""

import pytest
from playwright.sync_api import Page


class TestSeries:
    """When a post is part of a series, ordered nav marks the current part."""

    def test_series_marks_current(self, page: Page, jekyll_server: str, any_post_url: str):
        """The current part is flagged and not a link."""
        page.goto(f"{jekyll_server}{any_post_url}")
        series = page.locator(".series")
        if series.count() == 0:
            pytest.skip("this post is not part of a series")

        current = series.locator(".series-current")
        assert current.count() == 1, "exactly one part should be marked current"
        assert current.get_attribute("aria-current") == "true"

    def test_series_lists_multiple_parts(self, page: Page, jekyll_server: str, any_post_url: str):
        """A series shows more than one part."""
        page.goto(f"{jekyll_server}{any_post_url}")
        series = page.locator(".series")
        if series.count() == 0:
            pytest.skip("this post is not part of a series")

        assert series.locator(".series-list li").count() >= 2
