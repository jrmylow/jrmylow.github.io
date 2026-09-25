"""Tests for the backlinks ("Referenced by") block.

Corpus-level feature: a deterministic red->green needs two published posts where
one links to the other. These tests assert the contract and skip when no
backlinks exist in the live corpus; see README for the fixture note.
"""

import pytest
from playwright.sync_api import Page


class TestBacklinks:
    """When shown, backlinks point at other posts, never at self."""

    def test_backlinks_absent_or_valid(self, page: Page, jekyll_server: str, any_post_url: str):
        """If the block exists it has at least one link to another post."""
        page.goto(f"{jekyll_server}{any_post_url}")
        backlinks = page.locator(".backlinks")
        if backlinks.count() == 0:
            pytest.skip("no backlinks for this post in the current corpus")

        hrefs = backlinks.locator("a").evaluate_all("els => els.map(a => a.getAttribute('href'))")
        assert len(hrefs) >= 1
        assert all(any_post_url not in (h or "") for h in hrefs), "a post should not be listed as referencing itself"

    def test_backlinks_heading(self, page: Page, jekyll_server: str, any_post_url: str):
        """The block, when present, is labelled 'Referenced by'."""
        page.goto(f"{jekyll_server}{any_post_url}")
        backlinks = page.locator(".backlinks")
        if backlinks.count() == 0:
            pytest.skip("no backlinks for this post in the current corpus")

        assert "Referenced by" in backlinks.locator("h2").inner_text()
