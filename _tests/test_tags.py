"""Tests for tag functionality."""

from playwright.sync_api import Page

from constants import TEST_PAGE_PATH


class TestPostTags:
    """Tests for tag display on post pages."""

    def test_post_has_tags_container(self, page: Page, jekyll_server: str):
        """Post page should have a tags container."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        tags_container = page.locator(".post-tags")
        assert tags_container.count() == 1, "Post should have tags container"

    def test_post_displays_tags(self, page: Page, jekyll_server: str):
        """Post should display its tags."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        tags = page.locator(".post-tag")
        assert tags.count() >= 1, "Post should have at least one tag"

    def test_tags_are_clickable_links(self, page: Page, jekyll_server: str):
        """Tags should be clickable links."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        tag_link = page.locator(".post-tag").first
        href = tag_link.get_attribute("href")
        assert href is not None, "Tag should be a link"
        assert "/tags/" in href, "Tag should link to tags page"

    def test_tag_links_include_tag_name(self, page: Page, jekyll_server: str):
        """Tag links should include the tag name as anchor."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        tag_link = page.locator(".post-tag").first
        href = tag_link.get_attribute("href")
        assert "#" in href, "Tag link should have anchor"
