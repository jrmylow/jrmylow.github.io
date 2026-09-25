"""Tests for Open Graph / Twitter Card metadata via jekyll-seo-tag.

Red until `{% seo %}` is added to head.html and jekyll-seo-tag is enabled in
_config.yml (the gem is already bundled by github-pages).
"""

from playwright.sync_api import Page


class TestSocialMetadata:
    """Posts expose Open Graph and Twitter Card tags."""

    def test_og_title_present(self, page: Page, jekyll_server: str, any_post_url: str):
        page.goto(f"{jekyll_server}{any_post_url}")
        assert page.locator('meta[property="og:title"]').count() == 1, "expected an og:title meta tag"

    def test_og_type_is_article(self, page: Page, jekyll_server: str, any_post_url: str):
        page.goto(f"{jekyll_server}{any_post_url}")
        og_type = page.locator('meta[property="og:type"]').get_attribute("content")
        assert og_type == "article", "posts should declare og:type=article"

    def test_twitter_card_present(self, page: Page, jekyll_server: str, any_post_url: str):
        page.goto(f"{jekyll_server}{any_post_url}")
        assert page.locator('meta[name="twitter:card"]').count() == 1, "expected a twitter:card meta tag"
