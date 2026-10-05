"""Tests for the `_previews` collection.

Invariants:
  - every preview is reachable by direct link, renders via the post layout, carries
    noindex, and appears in no listing, archive, search index, or feed;
  - published posts (all by default, or a sample) are NOT noindexed.

Preview checks run on the designed build, whose fixture previews live in
_tests/fixtures/_previews/; the real site may have none. The published-post check
runs on the real build. URLs come from each build's manifest, i.e. from Jekyll.
"""

import os

import corpus
import discovery
import pytest
from playwright.sync_api import Page

# Published-post control: tests every post by default; set POST_SAMPLE_SIZE>0
# to sample only the first N (faster on a large archive).
POST_SAMPLE_SIZE = int(os.environ.get("POST_SAMPLE_SIZE", "0"))

PREVIEW_FILES = corpus.preview_files()
ALL_POST_FILES = [path.name for path in discovery.post_paths()]
POST_SAMPLE = ALL_POST_FILES if POST_SAMPLE_SIZE <= 0 else ALL_POST_FILES[:POST_SAMPLE_SIZE]


class TestPreviewCollection:
    @pytest.mark.parametrize("name", PREVIEW_FILES)
    def test_preview_renders_with_noindex(self, page: Page, designed_site, name: str):
        url = designed_site.document(name)["url"]
        resp = page.goto(f"{designed_site.url}{url}")
        assert resp.status == 200, f"Preview {url} should be reachable by direct link"
        assert page.locator(".post-title").count() >= 1, f"{url} should render via the post layout"
        robots = page.locator('meta[name="robots"]')
        assert robots.count() == 1, f"{url} should carry a robots meta tag"
        content = (robots.first.get_attribute("content") or "").lower()
        assert "noindex" in content, f"{url} robots meta should noindex, got {content!r}"

    @pytest.mark.parametrize("name", PREVIEW_FILES)
    def test_preview_excluded_from_public_surfaces(self, page: Page, designed_site, name: str):
        url = designed_site.document(name)["url"]
        for surface in ("/essays/", "/essays/all/", "/atom.xml"):
            page.goto(f"{designed_site.url}{surface}")
            assert url not in page.content(), f"{url} must not appear on {surface}"

        page.goto(f"{designed_site.url}/search-index.json")
        data = page.evaluate("() => JSON.parse(document.body.innerText)")
        urls = [item.get("url", "") for item in data]
        assert url not in urls, f"{url} must not appear in the search index"

    @pytest.mark.parametrize("name", discovery.params(POST_SAMPLE, "_posts (sample)"))
    def test_published_post_not_noindexed(self, page: Page, real_site, name: str):
        url = real_site.document(name)["url"]
        page.goto(f"{real_site.url}{url}")
        robots = page.locator('meta[name="robots"]')
        if robots.count():
            content = (robots.first.get_attribute("content") or "").lower()
            assert "noindex" not in content, f"Published post {url} must not be noindexed"
