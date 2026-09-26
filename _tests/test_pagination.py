"""Tests for essays pages and pagination."""

import math

import discovery
import pytest
from constants import SELECTORS
from playwright.sync_api import Page

# The archive's expected shape, computed from the sources so every assertion runs at any corpus size.
CONFIG = discovery.site_config()
PAGE_SIZE = CONFIG["paginate"]
POST_URLS = discovery.post_urls()
PAGES = max(1, math.ceil(len(POST_URLS) / PAGE_SIZE))


def archive_path(n: int) -> str:
    """Archive page n: page 1 is the archive root; later pages follow paginate_path."""
    return "/essays/all/" if n == 1 else CONFIG["paginate_path"].replace(":num", str(n))


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

        essays_link = page.locator(".sidebar-nav-item", has_text="Essays")
        assert essays_link.count() >= 1, "Essays should appear in sidebar"

    def test_essays_landing_shows_intro_prose(self, page: Page, jekyll_server: str):
        """Essays landing should render the Markdown body (Lamport quote)."""
        page.goto(f"{jekyll_server}/essays/")
        body_text = page.locator(".page").inner_text()
        assert "Leslie Lamport" in body_text, "Intro prose/quote should render in the page body"


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

    @pytest.mark.allow_http_errors
    def test_archive_has_exactly_the_expected_pages(self, page: Page, jekyll_server: str):
        """Pages 1..N exist for N = ceil(posts / paginate), and page N+1 does not."""
        for n in range(1, PAGES + 1):
            assert page.goto(f"{jekyll_server}{archive_path(n)}").status == 200, f"archive page {n} is missing"
        extra = page.goto(f"{jekyll_server}{archive_path(PAGES + 1)}")
        assert extra.status == 404, f"archive has an unexpected page {PAGES + 1}"

    def test_archive_lists_every_post_exactly_once(self, page: Page, jekyll_server: str):
        """Across the archive each post appears once, PAGE_SIZE per page except the last."""
        listed, sizes = [], []
        for n in range(1, PAGES + 1):
            page.goto(f"{jekyll_server}{archive_path(n)}")
            links = page.locator(f"{SELECTORS['card_grid']} {SELECTORS['card_link']}").all()
            listed += [link.get_attribute("href") for link in links]
            sizes.append(len(links))

        assert sorted(listed) == sorted(POST_URLS)
        assert sizes == [PAGE_SIZE] * (PAGES - 1) + [len(POST_URLS) - PAGE_SIZE * (PAGES - 1)]

    @pytest.mark.skipif(PAGES > 1, reason="archive spans several pages")
    def test_single_page_archive_has_no_nav(self, page: Page, jekyll_server: str):
        """With one page of posts the template renders no pagination nav."""
        page.goto(f"{jekyll_server}{archive_path(1)}")
        assert page.locator(SELECTORS["pagination"]).count() == 0

    @pytest.mark.skipif(PAGES == 1, reason="archive fits on one page; multi-page nav needs the designed corpus")
    @pytest.mark.parametrize("n", range(1, PAGES + 1))
    def test_nav_matches_position(self, page: Page, jekyll_server: str, n: int):
        """Page n reads 'Page n of N' and links only to its neighbours (page 1 is the archive root)."""
        page.goto(f"{jekyll_server}{archive_path(n)}")
        assert page.locator(SELECTORS["pagination_info"]).inner_text().strip() == f"Page {n} of {PAGES}"

        prev_links = page.locator(f"{SELECTORS['pagination_prev']} a").all()
        next_links = page.locator(f"{SELECTORS['pagination_next']} a").all()
        assert [a.get_attribute("href") for a in prev_links] == ([archive_path(n - 1)] if n > 1 else [])
        assert [a.get_attribute("href") for a in next_links] == ([archive_path(n + 1)] if n < PAGES else [])
