"""Tests for the reply-by-email link at the foot of each post.

The link is a mailto: to the site's address with the subject set to the post's title.
A mailto: URL is read literally, not as a form: "+" is a plus sign, not a space
(RFC 6068), and an unencoded "&" ends the subject. Liquid's two URL filters each get
one of those wrong, so the subject is compared after percent-decoding only.
"""

import urllib.parse

import corpus
import discovery
import pytest
from playwright.sync_api import Page

LINK = ".post .reply-by-email a"
EMAIL = discovery.site_config()["author"]["email"]
PREVIEW = corpus.preview_files()[0]


def _reply(page: Page, site, url: str) -> tuple[str, dict[str, str]]:
    """The reply link on one page, as (address, {header: percent-decoded value})."""
    page.goto(f"{site.url}{url}")
    links = page.locator(LINK)
    assert links.count() == 1, f"{url} should have one reply link, found {links.count()}"
    href = urllib.parse.urlsplit(links.get_attribute("href"))
    assert href.scheme == "mailto"
    headers = dict(pair.split("=", 1) for pair in href.query.split("&"))
    return href.path, {name: urllib.parse.unquote(value) for name, value in headers.items()}


class TestReplyByEmail:
    def test_post_links_to_the_site_address(self, page: Page, designed_site):
        address, _ = _reply(page, designed_site, designed_site.document(corpus.DESIGNED[0].filename)["url"])
        assert address == EMAIL
        assert page.locator(LINK).inner_text() == "Reply by email"

    def test_subject_is_the_post_title(self, page: Page, designed_site):
        """The escaping post's title has spaces, "&" and "<": the subject must survive all three."""
        post = designed_site.document(corpus.ESCAPING_POST.filename)
        _, headers = _reply(page, designed_site, post["url"])
        assert headers == {"subject": f"Re: {post['title']}"}

    def test_previews_have_it_too(self, page: Page, designed_site):
        """A preview is shared to get feedback, so the reply link matters most there."""
        preview = designed_site.document(PREVIEW)
        _, headers = _reply(page, designed_site, preview["url"])
        assert headers == {"subject": f"Re: {preview['title']}"}

    def test_other_pages_have_none(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}/about/")
        assert page.locator(".reply-by-email").count() == 0

    def test_every_published_post_has_it(self, page: Page, real_site):
        if real_site.manifest is None:
            pytest.skip(f"{real_site.url} has no test manifest: it wasn't built by this suite")
        for post in real_site.manifest["posts"]:
            address, headers = _reply(page, real_site, post["url"])
            assert address == EMAIL
            assert headers == {"subject": f"Re: {post['title']}"}
