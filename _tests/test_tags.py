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
        """Tag links should include the tag name as query param."""
        page.goto(f"{jekyll_server}{TEST_PAGE_PATH}")

        tag_link = page.locator(".post-tag").first
        tag_name = tag_link.text_content().strip()
        href = tag_link.get_attribute("href")
        assert f"t={tag_name}" in href, f"Tag link should have query param, got: {href}"

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
    """Tests for /tags/ page structure."""

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

    def test_tags_page_has_posts_container(self, page: Page, jekyll_server: str):
        """Tags page should have a container for posts."""
        page.goto(f"{jekyll_server}/tags/")

        container = page.locator(".tag-posts-container")
        assert container.count() == 1, "Should have posts container"

    def test_tags_page_has_post_items(self, page: Page, jekyll_server: str):
        """Tags page should have post items (hidden by default)."""
        page.goto(f"{jekyll_server}/tags/")

        posts = page.locator(".tag-post-item")
        assert posts.count() >= 1, "Should have post items in DOM"

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


class TestTagFiltering:
    """Tests for multi-tag filtering functionality."""

    def test_posts_hidden_by_default(self, page: Page, jekyll_server: str):
        """Posts should be hidden when no tags are selected."""
        page.goto(f"{jekyll_server}/tags/")

        posts = page.locator(".tag-post-item:visible")
        assert posts.count() == 0, "No posts should be visible by default"

    def test_clicking_tag_shows_posts(self, page: Page, jekyll_server: str):
        """Clicking a tag should show posts with that tag."""
        page.goto(f"{jekyll_server}/tags/")

        # Click first tag
        tag = page.locator(".tag-cloud-item").first
        tag.click()

        # Posts should now be visible
        posts = page.locator(".tag-post-item:visible")
        assert posts.count() >= 1, "Posts should be visible after selecting tag"

    def test_clicking_tag_toggles_selected_state(self, page: Page, jekyll_server: str):
        """Clicking a tag should toggle its selected state."""
        page.goto(f"{jekyll_server}/tags/")

        tag = page.locator(".tag-cloud-item").first

        # Click to select
        tag.click()
        assert "selected" in tag.get_attribute("class"), "Tag should have selected class"

        # Click to deselect
        tag.click()
        assert "selected" not in tag.get_attribute("class"), "Tag should not have selected class"

    def test_deselecting_tag_hides_posts(self, page: Page, jekyll_server: str):
        """Deselecting all tags should hide all posts."""
        page.goto(f"{jekyll_server}/tags/")

        tag = page.locator(".tag-cloud-item").first

        # Select then deselect
        tag.click()
        tag.click()

        posts = page.locator(".tag-post-item:visible")
        assert posts.count() == 0, "Posts should be hidden after deselecting all tags"

    def test_multiple_tags_filter_with_and_logic(self, page: Page, jekyll_server: str):
        """Selecting multiple tags should show only posts matching ALL tags."""
        page.goto(f"{jekyll_server}/tags/")

        # Get all tags and select first two
        tags = page.locator(".tag-cloud-item")
        if tags.count() >= 2:
            tags.nth(0).click()
            initial_count = page.locator(".tag-post-item:visible").count()

            tags.nth(1).click()
            filtered_count = page.locator(".tag-post-item:visible").count()

            # AND logic: second tag should reduce or maintain count, not increase
            assert filtered_count <= initial_count, "Adding tag should filter (AND), not expand results"

    def test_url_updates_with_selected_tags(self, page: Page, jekyll_server: str):
        """URL should update with selected tags as query param."""
        page.goto(f"{jekyll_server}/tags/")

        tag = page.locator(".tag-cloud-item").first
        tag_name = tag.get_attribute("data-tag")
        tag.click()

        assert f"t={tag_name}" in page.url or f"t%3D{tag_name}" in page.url, (
            f"URL should contain selected tag. URL: {page.url}"
        )

    def test_url_query_preselects_tags(self, page: Page, jekyll_server: str):
        """Loading page with query param should pre-select tags."""
        page.goto(f"{jekyll_server}/tags/?t=tag1")

        tag = page.locator(".tag-cloud-item[data-tag='tag1']")
        assert "selected" in tag.get_attribute("class"), "Tag should be pre-selected from URL"

        posts = page.locator(".tag-post-item:visible")
        assert posts.count() >= 1, "Posts should be visible from URL selection"

    def test_posts_have_data_tags_attribute(self, page: Page, jekyll_server: str):
        """Posts should have data-tags attribute for filtering."""
        page.goto(f"{jekyll_server}/tags/")

        post = page.locator(".tag-post-item").first
        data_tags = post.get_attribute("data-tags")
        assert data_tags is not None, "Post should have data-tags attribute"

    def test_tag_cloud_items_have_data_tag_attribute(self, page: Page, jekyll_server: str):
        """Tag cloud items should have data-tag attribute."""
        page.goto(f"{jekyll_server}/tags/")

        tag = page.locator(".tag-cloud-item").first
        data_tag = tag.get_attribute("data-tag")
        assert data_tag is not None and len(data_tag) > 0, "Tag should have data-tag attribute"
