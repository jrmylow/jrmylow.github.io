"""Tests for post cards: which posts the home and essays pages show, and what a card holds.

Both pages render cards through one include, _includes/post_card.html. Expectations are
the designed corpus (corpus.py), which has more posts than either page shows.
"""

import urllib.parse

import corpus
import pytest
from constants import ALL_CARDS_PAGE, SELECTORS
from playwright.sync_api import Page

HOME_LIMIT = 6
ESSAYS_LIMIT = 5
CARD_PAGES = ("/", "/essays/")

# For each card: how many heading titles, meta lines and bodies it has.
CARD_PARTS_JS = """cards => cards.map(card => [
    card.querySelectorAll('.card-title:is(h1, h2, h3, h4, h5, h6)').length,
    card.querySelectorAll('.card-meta').length,
    card.querySelectorAll('.card-body').length,
])"""


def _card_hrefs(page: Page) -> list[str]:
    return page.locator(SELECTORS["card_link"]).evaluate_all("els => els.map(a => a.getAttribute('href'))")


def _card(page: Page, site, post: corpus.Post):
    return page.locator(f"a.card-link[href='{site.document(post.filename)['url']}']")


def _open_every_card(page: Page, site) -> None:
    """Open the test-only page of every post's card. Not an assertion: an expected failure
    must fail on what it is about, not on this page being missing."""
    page.goto(f"{site.url}/{ALL_CARDS_PAGE}")
    if page.locator(SELECTORS["card"]).count() == 0:
        raise LookupError(f"/{ALL_CARDS_PAGE} shows no cards")


def _text(locator) -> str:
    return " ".join(locator.inner_text().split())


class TestWhichPostsGetCards:
    """Neither limit is reached by the real site yet, so the designed corpus exceeds both."""

    def test_home_shows_the_six_newest_posts_newest_first(self, page: Page, designed_site):
        newest = [post["url"] for post in designed_site.manifest["posts"]]
        assert len(newest) > HOME_LIMIT, "this case needs more posts than the home page shows"
        page.goto(designed_site.url)
        assert _card_hrefs(page) == newest[:HOME_LIMIT]

    def test_essays_landing_shows_the_five_newest_posts_newest_first(self, page: Page, designed_site):
        newest = [post["url"] for post in designed_site.manifest["posts"]]
        page.goto(f"{designed_site.url}/essays/")
        assert _card_hrefs(page) == newest[:ESSAYS_LIMIT]

    def test_real_home_shows_the_newest_real_posts(self, page: Page, real_site):
        if real_site.manifest is None:
            pytest.skip(f"{real_site.url} has no test manifest: it wasn't built by this suite")
        page.goto(real_site.url)
        assert _card_hrefs(page) == [post["url"] for post in real_site.manifest["posts"]][:HOME_LIMIT]


class TestCardContent:
    def test_card_shows_the_title_date_and_reading_time(self, page: Page, designed_site):
        page.goto(designed_site.url)
        card = _card(page, designed_site, corpus.ALPHA)
        assert _text(card.locator(SELECTORS["card_title"])) == corpus.ALPHA.title
        assert _text(card.locator(SELECTORS["card_meta"])) == f"{corpus.ALPHA.date:%d %B %Y} · 1 min read"

    def test_card_body_is_the_summary_when_the_post_has_one(self, page: Page, designed_site):
        page.goto(designed_site.url)
        body = _card(page, designed_site, corpus.ALPHA_TWO).locator(SELECTORS["card_body"])
        assert _text(body) == corpus.ALPHA_TWO.summary

    def test_card_body_is_the_first_paragraph_when_there_is_no_summary(self, page: Page, designed_site):
        assert corpus.ALPHA.summary is None, "this case needs a post with no front-matter summary"
        page.goto(designed_site.url)
        body = _card(page, designed_site, corpus.ALPHA).locator(SELECTORS["card_body"])
        assert _text(body) == corpus.ALPHA.body

    def test_card_is_one_link_around_the_whole_card(self, page: Page, designed_site):
        _open_every_card(page, designed_site)
        assert _card(page, designed_site, corpus.ALPHA).count() == 1

    @pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason="a card is one link around everything in it, and a post with no summary puts its first "
        "paragraph in there, links and all; a link can't hold a link, so the browser splits the card "
        "into several links, some of them empty",
    )
    def test_card_stays_one_link_when_the_first_paragraph_has_a_link(self, page: Page, designed_site):
        """Known bug. The accessibility scan catches it too (empty links), so the corpus dates
        such posts off the home and essays pages. Strict: this fails the day the bug is fixed."""
        _open_every_card(page, designed_site)
        assert _card(page, designed_site, corpus.LINKS_OUT).count() == 1

    @pytest.mark.parametrize("path", CARD_PAGES)
    def test_every_card_has_a_heading_title_a_meta_line_and_a_body(self, page: Page, designed_site, path: str):
        """One include, so one structure. The heading level is each page's choice; it must be a heading."""
        page.goto(f"{designed_site.url}{path}")
        parts = page.locator(SELECTORS["card"]).evaluate_all(CARD_PARTS_JS)
        assert parts and all(counts == [1, 1, 1] for counts in parts), f"{path}: {parts}"


class TestCardGrid:
    def test_card_hover_changes_style(self, page: Page, designed_site):
        """Card should change background on hover."""
        page.goto(designed_site.url)
        page.add_style_tag(content="*, *::before, *::after { transition: none !important; }")
        card = page.locator(SELECTORS["card"]).first
        initial_bg = card.evaluate("el => getComputedStyle(el).backgroundColor")
        card.hover()
        assert card.evaluate("el => getComputedStyle(el).backgroundColor") != initial_bg

    @pytest.mark.parametrize("width, columns", [(1280, 2), (375, 1)])
    def test_home_grid_has_two_columns_on_a_desktop_and_one_on_a_phone(
        self, page: Page, designed_site, width: int, columns: int
    ):
        page.set_viewport_size({"width": width, "height": 800})
        page.goto(designed_site.url)
        tracks = page.locator(SELECTORS["card_grid"]).evaluate("el => getComputedStyle(el).gridTemplateColumns")
        assert len(tracks.split()) == columns, f"at {width}px the grid's columns are {tracks!r}"

    def test_view_all_link_goes_to_the_essays_page(self, page: Page, designed_site):
        page.goto(designed_site.url)
        with page.expect_navigation():
            page.locator(SELECTORS["view_all_link"]).click()
        assert urllib.parse.urlsplit(page.url).path == "/essays/"
