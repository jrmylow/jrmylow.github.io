"""Tests for the related-by-tag block.

This is a corpus-level feature (it ranges over site.posts), so a true red->green
needs at least two published posts sharing a tag. These tests assert the block's
structural contract and skip when the live corpus has no tag overlap; see
README for the fixture note.
"""

import pytest
from playwright.sync_api import Page


class TestRelated:
    """When shown, the block links to at most three other posts."""

    def test_related_excludes_current_post(self, page: Page, jekyll_server: str, any_post_url: str):
        """The related list never links back to the current post."""
        page.goto(f"{jekyll_server}{any_post_url}")
        related = page.locator(".related")
        if related.count() == 0:
            pytest.skip("no tag-related posts in the current corpus")

        hrefs = related.locator("a").evaluate_all("els => els.map(a => a.getAttribute('href'))")
        assert all(any_post_url not in (h or "") for h in hrefs), "related list should not include the current post"

    def test_related_capped_at_three(self, page: Page, jekyll_server: str, any_post_url: str):
        """At most three related posts are shown."""
        page.goto(f"{jekyll_server}{any_post_url}")
        related = page.locator(".related")
        if related.count() == 0:
            pytest.skip("no tag-related posts in the current corpus")

        assert related.locator(".related-list li").count() <= 3

    def test_old_related_posts_block_gone(self, page: Page, jekyll_server: str, any_post_url: str):
        """The old site.related_posts markup is no longer emitted."""
        page.goto(f"{jekyll_server}{any_post_url}")
        assert (
            page.locator(".related-posts").count() == 0
        ), "old .related-posts block should be replaced by .related-list"
