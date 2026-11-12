"""Tests for the essays landing page and the year-grouped archive."""

import itertools
import urllib.parse

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
    """The essays landing page (/essays/). Which posts it shows is in test_cards.py."""

    def test_view_all_link_goes_to_the_archive(self, page: Page, jekyll_server: str):
        page.goto(f"{jekyll_server}/essays/")
        with page.expect_navigation():
            page.locator(SELECTORS["view_all_link"]).click()
        assert urllib.parse.urlsplit(page.url).path == ARCHIVE

    def test_essays_is_in_the_sidebar_once(self, page: Page, jekyll_server: str):
        page.goto(f"{jekyll_server}/")
        page.locator(".sidebar-toggle").click()
        link = page.locator(".sidebar-nav-item", has_text="Essays")
        assert link.evaluate_all("els => els.map(a => a.getAttribute('href'))") == ["/essays/"]

    def test_essays_landing_shows_intro_prose(self, page: Page, jekyll_server: str):
        """Essays landing should render the Markdown body (Lamport quote)."""
        page.goto(f"{jekyll_server}/essays/")
        body_text = page.locator(".page").inner_text()
        assert "Leslie Lamport" in body_text, "Intro prose/quote should render in the page body"


class TestEssaysArchive:
    """/essays/all/ is one page listing every post under its year, newest first."""

    def test_back_link_goes_to_the_essays_page(self, page: Page, jekyll_server: str):
        page.goto(f"{jekyll_server}{ARCHIVE}")
        with page.expect_navigation():
            page.get_by_role("link", name="Back to Essays").click()
        assert urllib.parse.urlsplit(page.url).path == "/essays/"

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
