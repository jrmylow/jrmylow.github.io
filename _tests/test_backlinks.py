"""Tests for the "Referenced by" block: the other posts whose text links to this one.

Expectations are the designed corpus's link cases (corpus.py).
"""

import corpus
import pytest
from playwright.sync_api import Page


def _references(page: Page) -> list[tuple[str, str]]:
    """The block's entries as (title, href), in page order."""
    links = page.locator(".backlinks .backlinks-list a")
    return list(zip(links.all_inner_texts(), links.evaluate_all("els => els.map(a => a.getAttribute('href'))")))


def _entry(site, post: corpus.Post) -> tuple[str, str]:
    return post.title, site.document(post.filename)["url"]


class TestBacklinks:
    def test_lists_the_posts_that_link_here_newest_first(self, page: Page, designed_site):
        """One linker is newer than the linked post and one older; both are listed, and nothing else."""
        page.goto(designed_site.page_url(corpus.LINKED.filename))
        assert page.locator(".backlinks h2").inner_text() == "Referenced by"
        assert _references(page) == [
            _entry(designed_site, corpus.LINKS_OUT),
            _entry(designed_site, corpus.LINKS_OUT_TWO),
        ]

    def test_post_nobody_links_to_has_no_block(self, page: Page, designed_site):
        page.goto(designed_site.page_url(corpus.ALPHA.filename))
        assert page.locator(".backlinks").count() == 0

    def test_post_linking_to_itself_is_not_its_own_reference(self, page: Page, designed_site):
        """Its only inbound link is its own, so it has no block at all."""
        page.goto(designed_site.page_url(corpus.LINKS_OUT.filename))
        assert page.locator(".post a", has_text="itself").get_attribute("href") == page.url.removeprefix(
            designed_site.url
        )
        assert page.locator(".backlinks").count() == 0

    @pytest.mark.xfail(
        strict=True,
        reason="backlinks.html looks for this page's URL in other posts' content, but Jekyll renders posts "
        "oldest first: while this page renders, a newer post's {% post_url %} tag is still a tag, not a URL",
    )
    def test_link_written_with_post_url_counts_too(self, page: Page, designed_site):
        """Known gap. Strict, so this fails, and gets noticed, the day the gap closes."""
        page.goto(designed_site.page_url(corpus.LIQUID_LINKED.filename))
        assert _references(page) == [_entry(designed_site, corpus.LIQUID_LINKS_OUT)]
