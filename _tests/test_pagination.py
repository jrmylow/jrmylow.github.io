"""Tests for essays pages and pagination."""

from playwright.sync_api import Page

from constants import SELECTORS


class TestEssaysLandingPage:
    """Tests for the essays landing page (/essays/)."""

    def test_essays_landing_loads(self, page: Page, jekyll_server: str):
        """Essays landing page should load successfully."""
        response = page.goto(f"{jekyll_server}/essays/")
        assert response.status == 200, "Essays page should return 200"

    def test_essays_landing_has_card_grid(self, page: Page, jekyll_server: str):
        """Essays landing should display recent posts in card grid."""
        page.goto(f"{jekyll_server}/essays/")

        card_grid = page.locator(SELECTORS["card_grid"])
        assert card_grid.count() >= 1, "Essays page should have a card grid"

    def test_essays_landing_shows_limited_posts(self, page: Page, jekyll_server: str):
        """Essays landing should show max 5 recent posts."""
        page.goto(f"{jekyll_server}/essays/")

        cards = page.locator(f"{SELECTORS['card_grid']} {SELECTORS['card']}")
        assert cards.count() <= 5, "Landing should show max 5 posts"

    def test_essays_landing_has_archive_link(self, page: Page, jekyll_server: str):
        """Essays landing should link to full archive."""
        page.goto(f"{jekyll_server}/essays/")

        archive_link = page.locator("a[href='/essays/all/']")
        assert archive_link.count() >= 1, "Should have link to /essays/all/"

    def test_essays_in_sidebar(self, page: Page, jekyll_server: str):
        """Essays should appear in sidebar navigation."""
        page.goto(f"{jekyll_server}/")

        page.locator(".sidebar-toggle").click()
        page.wait_for_timeout(400)

        essays_link = page.locator(".sidebar-nav-item", has_text="Essays")
        assert essays_link.count() >= 1, "Essays should appear in sidebar"


class TestEssaysArchivePagination:
    """Tests for pagination on essays archive (/essays/all/)."""

    def test_archive_loads(self, page: Page, jekyll_server: str):
        """Archive page should load successfully."""
        response = page.goto(f"{jekyll_server}/essays/all/")
        assert response.status == 200, "Archive should return 200"

    def test_archive_has_card_grid(self, page: Page, jekyll_server: str):
        """Archive should display posts in card grid."""
        page.goto(f"{jekyll_server}/essays/all/")

        card_grid = page.locator(SELECTORS["card_grid"])
        assert card_grid.count() >= 1, "Archive should have a card grid"

    def test_archive_uses_single_column(self, page: Page, jekyll_server: str):
        """Archive should use single column card layout."""
        page.goto(f"{jekyll_server}/essays/all/")

        card_grid = page.locator(".card-grid-1")
        assert card_grid.count() >= 1, "Archive should use single column"

    def test_archive_has_back_link(self, page: Page, jekyll_server: str):
        """Archive should have link back to essays landing."""
        page.goto(f"{jekyll_server}/essays/all/")

        back_link = page.locator("a[href='/essays/']")
        assert back_link.count() >= 1, "Should have back link"

    def test_pagination_shows_page_info(self, page: Page, jekyll_server: str):
        """Pagination should show page info when multiple pages exist."""
        page.goto(f"{jekyll_server}/essays/all/")

        pagination = page.locator(".pagination")
        if pagination.count() > 0:
            page_info = page.locator(".pagination-info")
            assert page_info.count() == 1, "Should show page info"

            text = page_info.text_content()
            assert "Page" in text, "Should display 'Page X of Y'"

    def test_pagination_next_link(self, page: Page, jekyll_server: str):
        """First page should have next link when multiple pages exist."""
        page.goto(f"{jekyll_server}/essays/all/")

        pagination_info = page.locator(".pagination-info")
        if pagination_info.count() > 0:
            text = pagination_info.text_content()
            if "of 1" not in text:
                next_link = page.locator(".pagination-next a")
                assert next_link.count() > 0, "Should have next link"

    def test_pagination_next_works(self, page: Page, jekyll_server: str):
        """Clicking next should navigate to page 2."""
        page.goto(f"{jekyll_server}/essays/all/")

        next_link = page.locator(".pagination-next a")
        if next_link.count() > 0:
            next_link.click()
            assert "/page/2" in page.url

    def test_page_two_has_prev_link(self, page: Page, jekyll_server: str):
        """Page 2 should have previous link."""
        response = page.goto(f"{jekyll_server}/essays/all/page/2/")

        if response.status == 200:
            prev_link = page.locator(".pagination-prev a")
            assert prev_link.count() > 0, "Page 2 should have prev link"

    def test_prev_link_to_page_one(self, page: Page, jekyll_server: str):
        """Previous on page 2 should link to /essays/all/ (not page/1)."""
        response = page.goto(f"{jekyll_server}/essays/all/page/2/")

        if response.status == 200:
            prev_link = page.locator(".pagination-prev a")
            if prev_link.count() > 0:
                href = prev_link.get_attribute("href")
                assert "/essays/all/" in href
                assert "/page/1" not in href
