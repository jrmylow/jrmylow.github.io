"""Tests for the reading-time estimate on posts and post cards.

Minutes are words / 220, rounded up, at least one. Expectations come from the
designed corpus, whose long post has a known word count.
"""

import math

import corpus
from playwright.sync_api import Page

WPM = 220
LONG_MINUTES = math.ceil(corpus.LONG_WORDS / WPM)
SHORT_POST = corpus.DESIGNED[0]


class TestReadingTime:
    def test_long_post_shows_rounded_up_minutes(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}{designed_site.document(corpus.LONG_POST.filename)['url']}")
        assert f"{LONG_MINUTES} min read" in page.locator(".post-date").inner_text()

    def test_short_post_shows_at_least_one_minute(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}{designed_site.document(SHORT_POST.filename)['url']}")
        assert "1 min read" in page.locator(".post-date").inner_text()

    def test_card_shows_the_posts_minutes(self, page: Page, designed_site):
        url = designed_site.document(corpus.LONG_POST.filename)["url"]
        page.goto(f"{designed_site.url}/essays/all/")
        meta = page.locator(f"a.card-link[href='{url}'] .card-meta")
        assert f"{LONG_MINUTES} min read" in meta.inner_text()
