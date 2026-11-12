"""Tests for the "Related" block: up to three other posts that share a tag, newest first.

Expectations are the designed corpus's tag cases (corpus.py), written out here by hand so
the test doesn't repeat the template's own logic.
"""

import corpus
import pytest
from playwright.sync_api import Page

RELATED = [
    # Four other posts share a tag with this one. The newest three are listed; the fourth,
    # alpha three, is cut by the limit.
    (corpus.ALPHA_BETA, [corpus.ALPHA, corpus.ALPHA_TWO, corpus.BETA]),
    # Exactly three share a tag, so the limit cuts nothing.
    (corpus.ALPHA, [corpus.ALPHA_TWO, corpus.ALPHA_THREE, corpus.ALPHA_BETA]),
    (corpus.BETA, [corpus.ALPHA_BETA]),
]
NOT_RELATED = [
    pytest.param(corpus.UNSHARED_TAGS, id="tags-nobody-shares"),
    pytest.param(corpus.LINKED, id="no-tags"),
]


class TestRelated:
    @pytest.mark.parametrize("post, related", RELATED, ids=[post.slug for post, _ in RELATED])
    def test_lists_the_newest_three_posts_sharing_a_tag(self, page: Page, designed_site, post, related):
        page.goto(designed_site.page_url(post.filename))
        block = page.locator(".related")
        assert block.locator("h2").inner_text() == "Related"
        links = block.locator(".related-list a")
        assert links.all_inner_texts() == [other.title for other in related]
        hrefs = links.evaluate_all("els => els.map(a => a.getAttribute('href'))")
        assert hrefs == [designed_site.document(other.filename)["url"] for other in related]
        dates = block.locator(".related-date").all_inner_texts()
        assert dates == [f"{other.date:%d %b %Y}" for other in related]

    @pytest.mark.parametrize("post", NOT_RELATED)
    def test_post_with_nothing_related_has_no_block(self, page: Page, designed_site, post):
        page.goto(designed_site.page_url(post.filename))
        assert page.locator(".related").count() == 0
