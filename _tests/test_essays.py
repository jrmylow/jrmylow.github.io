"""Tests for the essays landing page and the year-grouped archive."""

import itertools

import pytest
from constants import SELECTORS
from playwright.sync_api import Page

ARCHIVE = "/essays/all/"


def _archive_by_year(page: Page, site) -> list[tuple[str, list[str]]]:
    """The archive as rendered: (year heading, post hrefs under it), in page order."""
    page.goto(f"{site.url}{ARCHIVE}")
    return [
        (
            section.locator("h2").inner_text().strip(),
            [a.get_attribute("href") for a in section.locator(".archive-list a").all()],
        )
        for section in page.locator(".archive-year").all()
    ]


def _expected_by_year(site) -> list[tuple[str, list[str]]]:
    """From Jekyll's manifest, whose posts are newest first: posts grouped by year, newest year first."""
    if site.manifest is None:
        pytest.skip(f"{site.url} has no test manifest: it wasn't built by this suite")
    posts = site.manifest["posts"]
    return [(year, [p["url"] for p in group]) for year, group in itertools.groupby(posts, key=lambda p: p["date"][:4])]


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


class TestEssaysArchive:
    """/essays/all/ is one page listing every post under its year, newest first."""

    def test_archive_loads(self, page: Page, jekyll_server: str):
        response = page.goto(f"{jekyll_server}{ARCHIVE}")
        assert response.status == 200, "Archive should return 200"

    def test_archive_has_back_link(self, page: Page, jekyll_server: str):
        page.goto(f"{jekyll_server}{ARCHIVE}")
        assert page.locator("a[href='/essays/']").count() >= 1, "Should have back link"

    def test_posts_are_grouped_by_year_newest_first(self, page: Page, designed_site):
        """Runs at any --scale-posts: every post appears once, on one page, under its own year."""
        expected = _expected_by_year(designed_site)
        assert len(expected) >= 2, "the designed corpus should span at least two years"
        assert _archive_by_year(page, designed_site) == expected

    def test_real_archive_lists_every_post(self, page: Page, real_site):
        assert _archive_by_year(page, real_site) == _expected_by_year(real_site)

    def test_entries_show_reading_time(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}{ARCHIVE}")
        entries = page.locator(".archive-list li").all()
        assert entries and all("min read" in entry.inner_text() for entry in entries)

    @pytest.mark.allow_http_errors
    def test_archive_is_not_paginated(self, page: Page, jekyll_server: str):
        page.goto(f"{jekyll_server}{ARCHIVE}")
        assert page.locator(SELECTORS["pagination"]).count() == 0
        assert page.goto(f"{jekyll_server}{ARCHIVE}page/2/").status == 404
