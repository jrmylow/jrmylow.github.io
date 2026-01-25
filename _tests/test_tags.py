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

    def test_tag_no_underline_on_hover(self, page: Page, jekyll_server: str):
        """Tags should not have underline on hover."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        tag = page.locator(".post-tag").first

        # Check before hover
        decoration_before = tag.evaluate("el => getComputedStyle(el).textDecoration")
        assert "underline" not in decoration_before, "Tag should not have underline"

        # Check on hover
        tag.hover()
        decoration_after = tag.evaluate("el => getComputedStyle(el).textDecoration")
        assert "underline" not in decoration_after, "Tag should not have underline on hover"

    def test_tag_hover_color_light_mode(self, page: Page, jekyll_server: str):
        """Tag text should change color on hover in light mode."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        # Set light mode
        page.evaluate("() => localStorage.setItem('theme', 'light')")
        page.reload()

        tag = page.locator(".post-tag").first

        # Get color before hover
        color_before = tag.evaluate("el => getComputedStyle(el).color")

        # Hover
        tag.hover()

        # Get color after hover
        color_after = tag.evaluate("el => getComputedStyle(el).color")

        assert color_before != color_after, (
            f"Tag color should change on hover. Before: {color_before}, After: {color_after}"
        )


class TestTagsPage:
    """Tests for /tags/ page."""

    def test_tags_page_exists(self, page: Page, jekyll_server: str):
        """Tags page should exist and return 200."""
        response = page.goto(f"{jekyll_server}/tags/")
        assert response.status == 200, "Tags page should exist"

    def test_tags_page_has_tag_cloud(self, page: Page, jekyll_server: str):
        """Tags page should have a tag cloud."""
        page.goto(f"{jekyll_server}/tags/")

        tag_cloud = page.locator(".tag-cloud")
        assert tag_cloud.count() == 1, "Should have tag cloud"

    def test_tag_cloud_has_items(self, page: Page, jekyll_server: str):
        """Tag cloud should contain tag items."""
        page.goto(f"{jekyll_server}/tags/")

        items = page.locator(".tag-cloud-item")
        assert items.count() >= 1, "Tag cloud should have items"

    def test_tag_cloud_items_are_links(self, page: Page, jekyll_server: str):
        """Tag cloud items should be anchor links."""
        page.goto(f"{jekyll_server}/tags/")

        item = page.locator(".tag-cloud-item").first
        href = item.get_attribute("href")
        assert href is not None, "Tag cloud item should be a link"
        assert "#" in href, "Should link to anchor on same page"

    def test_tags_page_has_tag_sections(self, page: Page, jekyll_server: str):
        """Tags page should have sections for each tag."""
        page.goto(f"{jekyll_server}/tags/")

        sections = page.locator(".tag-section")
        assert sections.count() >= 1, "Should have tag sections"

    def test_tag_section_has_id(self, page: Page, jekyll_server: str):
        """Tag sections should have id for anchor linking."""
        page.goto(f"{jekyll_server}/tags/")

        section = page.locator(".tag-section").first
        section_id = section.get_attribute("id")
        assert section_id is not None, "Tag section should have id"

    def test_tag_section_lists_posts(self, page: Page, jekyll_server: str):
        """Tag sections should list posts with that tag."""
        page.goto(f"{jekyll_server}/tags/")

        posts = page.locator(".tag-post-item")
        assert posts.count() >= 1, "Should list posts under tags"

    def test_clicking_tag_from_post_navigates_to_section(
        self, page: Page, jekyll_server: str
    ):
        """Clicking tag on post should navigate to correct section."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        tag_link = page.locator(".post-tag").first
        tag_name = tag_link.text_content().strip()
        tag_link.click()

        # Should be on tags page with hash
        assert "/tags/" in page.url, "Should navigate to tags page"
        assert f"#{tag_name}" in page.url, "URL should have tag anchor"

    def test_tag_cloud_hover_color_light_mode(self, page: Page, jekyll_server: str):
        """Tag cloud item text should change color on hover in light mode."""
        page.goto(f"{jekyll_server}/tags/")

        # Set light mode
        page.evaluate("() => localStorage.setItem('theme', 'light')")
        page.reload()

        tag = page.locator(".tag-cloud-item").first

        # Get color before hover
        color_before = tag.evaluate("el => getComputedStyle(el).color")

        # Hover
        tag.hover()

        # Get color after hover
        color_after = tag.evaluate("el => getComputedStyle(el).color")

        assert color_before != color_after, (
            f"Tag cloud color should change on hover. Before: {color_before}, After: {color_after}"
        )

    def test_tag_section_no_highlight_animation(self, page: Page, jekyll_server: str):
        """Tag section should not have highlight animation when targeted."""
        page.goto(f"{jekyll_server}/tags/#tag1")

        section = page.locator(".tag-section#tag1")
        animation = section.evaluate("el => getComputedStyle(el).animationName")

        assert animation == "none", f"Tag section should have no animation, got: {animation}"

    def test_tag_cloud_no_underline_on_hover(self, page: Page, jekyll_server: str):
        """Tag cloud items should not have underline on hover."""
        page.goto(f"{jekyll_server}/tags/")

        tag = page.locator(".tag-cloud-item").first

        # Check before hover
        decoration_before = tag.evaluate("el => getComputedStyle(el).textDecoration")
        assert "underline" not in decoration_before, "Tag cloud item should not have underline"

        # Check on hover
        tag.hover()
        decoration_after = tag.evaluate("el => getComputedStyle(el).textDecoration")
        assert "underline" not in decoration_after, "Tag cloud item should not have underline on hover"
