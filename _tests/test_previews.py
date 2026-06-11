"""Tests for the `_previews` collection, driven by folder discovery.

URLs are not hardcoded (test content comes and goes): preview and post URLs are
discovered from the source tree by `discovery` (see `_tests/discovery.py`),
which derives each URL the way Jekyll does.

Invariants:
  - every `_previews` doc is reachable, renders via the post layout, carries
    noindex, and appears in no listing, archive, search index, or feed;
  - published posts (all by default, or a sample) are NOT noindexed.
"""

import os

import pytest
from discovery import params, post_urls, preview_urls
from playwright.sync_api import Page

# Published-post control: tests every post by default; set POST_SAMPLE_SIZE>0
# to sample only the first N (faster on a large archive).
POST_SAMPLE_SIZE = int(os.environ.get("POST_SAMPLE_SIZE", "0"))

PREVIEW_URLS = preview_urls()
ALL_POST_URLS = post_urls()
POST_SAMPLE = ALL_POST_URLS if POST_SAMPLE_SIZE <= 0 else ALL_POST_URLS[:POST_SAMPLE_SIZE]


class TestPreviewCollection:
    @pytest.mark.parametrize("url", params(PREVIEW_URLS, "_previews docs"))
    def test_preview_renders_with_noindex(self, page: Page, jekyll_server: str, url: str):
        resp = page.goto(f"{jekyll_server}{url}")
        assert resp.status == 200, f"Preview {url} should be reachable by direct link"
        assert page.locator(".post-title").count() >= 1, f"{url} should render via the post layout"
        robots = page.locator('meta[name="robots"]')
        assert robots.count() == 1, f"{url} should carry a robots meta tag"
        content = (robots.first.get_attribute("content") or "").lower()
        assert "noindex" in content, f"{url} robots meta should noindex, got {content!r}"

    @pytest.mark.parametrize("url", params(PREVIEW_URLS, "_previews docs"))
    def test_preview_excluded_from_public_surfaces(self, page: Page, jekyll_server: str, url: str):
        for surface in ("/essays/", "/essays/all/", "/atom.xml"):
            page.goto(f"{jekyll_server}{surface}")
            assert url not in page.content(), f"{url} must not appear on {surface}"

        page.goto(f"{jekyll_server}/search-index.json")
        data = page.evaluate("() => JSON.parse(document.body.innerText)")
        urls = [item.get("url", "") for item in data]
        assert url not in urls, f"{url} must not appear in the search index"

    @pytest.mark.parametrize("url", params(POST_SAMPLE, "_posts (sample)"))
    def test_published_post_not_noindexed(self, page: Page, jekyll_server: str, url: str):
        page.goto(f"{jekyll_server}{url}")
        robots = page.locator('meta[name="robots"]')
        if robots.count():
            content = (robots.first.get_attribute("content") or "").lower()
            assert "noindex" not in content, f"Published post {url} must not be noindexed"
