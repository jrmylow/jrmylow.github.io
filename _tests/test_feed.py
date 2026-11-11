"""Tests for the Atom feed at /atom.xml.

RFC 4287 fixes the namespace (http://www.w3.org/2005/Atom) and the media type
(application/atom+xml); feed readers match both exactly.

The feed tests run on both builds. The real build shows the feed holds whatever is
published; the designed build has the cases real posts may never contain: text that
XML must escape, a summary that differs from the body, and a long first paragraph.
"""

import xml.etree.ElementTree as ET

import corpus
import pytest
from playwright.sync_api import Page

ATOM_NS = "http://www.w3.org/2005/Atom"
ATOM = {"atom": ATOM_NS}
SUMMARY_WORDS = 50  # an excerpt-derived summary is cut to this many words


@pytest.fixture(params=["real_site", "designed_site"])
def site(request):
    return request.getfixturevalue(request.param)


def _feed(page: Page, site) -> ET.Element:
    """The parsed feed. A feed that isn't well-formed XML fails here, as it would in a reader."""
    response = page.request.get(f"{site.url}/atom.xml")
    assert response.ok, f"/atom.xml returned {response.status}"
    return ET.fromstring(response.body())


def _entry(page: Page, site, post: corpus.Post) -> ET.Element:
    """The feed entry for one designed post, found by its link."""
    link = f"{site.url}{site.document(post.filename)['url']}"
    for entry in _feed(page, site).findall("atom:entry", ATOM):
        if entry.find("atom:link", ATOM).get("href") == link:
            return entry
    raise LookupError(f"no feed entry links to {link}")


class TestAtomFeed:
    def test_feed_uses_atom_namespace(self, page: Page, site):
        root = _feed(page, site)
        assert root.tag == f"{{{ATOM_NS}}}feed", f"root should be an Atom feed, got {root.tag}"

    def test_entries_are_the_published_posts(self, page: Page, site):
        """Every post, newest first, with the title a reader should see and a link to the post."""
        if site.manifest is None:
            pytest.skip(f"{site.url} has no test manifest: it wasn't built by this suite")
        entries = _feed(page, site).findall("atom:entry", ATOM)
        listed = [(e.findtext("atom:title", namespaces=ATOM), e.find("atom:link", ATOM).get("href")) for e in entries]
        assert listed == [(post["title"], f"{site.url}{post['url']}") for post in site.manifest["posts"]]

    def test_feed_autodiscovery_uses_atom_media_type(self, page: Page, jekyll_server: str):
        page.goto(jekyll_server)
        link = page.locator('head link[rel="alternate"][href$="/atom.xml"]')
        assert link.count() == 1, "expected one feed autodiscovery link"
        assert link.get_attribute("type") == "application/atom+xml"


class TestEntrySummary:
    """Readers show the summary in their list view; without one they fall back to the full content."""

    def test_every_entry_has_an_html_summary(self, page: Page, site):
        """type="html": a front-matter summary is an HTML fragment, as on the post card."""
        for entry in _feed(page, site).findall("atom:entry", ATOM):
            title = entry.findtext("atom:title", namespaces=ATOM)
            summary = entry.find("atom:summary", ATOM)
            assert summary is not None, f"{title!r} has no summary"
            assert summary.get("type") == "html", f"{title!r} summary should be type html"
            assert (summary.text or "").strip(), f"{title!r} has an empty summary"

    def test_front_matter_summary_wins_over_the_excerpt(self, page: Page, designed_site):
        summary = _entry(page, designed_site, corpus.ESCAPING_POST).findtext("atom:summary", namespaces=ATOM)
        assert summary == corpus.ESCAPING_POST.summary

    def test_post_without_a_summary_uses_its_first_paragraph(self, page: Page, designed_site):
        post = corpus.DESIGNED[0]
        assert post.summary is None, "this case needs a post with no front-matter summary"
        assert _entry(page, designed_site, post).findtext("atom:summary", namespaces=ATOM) == post.body

    def test_long_first_paragraph_is_cut(self, page: Page, designed_site):
        summary = _entry(page, designed_site, corpus.LONG_POST).findtext("atom:summary", namespaces=ATOM)
        assert len(corpus.LONG_POST.body.split()) > SUMMARY_WORDS, "this case needs a body longer than the cut"
        assert len(summary.split()) == SUMMARY_WORDS
        assert summary.endswith("...")


class TestFeedLinks:
    """Browsers don't surface autodiscovery links, so readers need a visible one."""

    def test_sidebar_links_to_the_feed(self, page: Page, jekyll_server: str):
        page.goto(jekyll_server)
        page.locator(".sidebar-toggle").click()
        link = page.locator(".sidebar a[href$='/atom.xml']")
        link.wait_for(state="visible")
