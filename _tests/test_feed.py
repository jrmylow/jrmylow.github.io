"""Tests for the Atom feed at /atom.xml.

RFC 4287 fixes the namespace (http://www.w3.org/2005/Atom) and the media type
(application/atom+xml); feed readers match both exactly.
"""

import xml.etree.ElementTree as ET

from playwright.sync_api import Page

ATOM_NS = "http://www.w3.org/2005/Atom"


class TestAtomFeed:
    def test_feed_uses_atom_namespace(self, page: Page, jekyll_server: str):
        response = page.request.get(f"{jekyll_server}/atom.xml")
        assert response.ok, f"/atom.xml returned {response.status}"
        root = ET.fromstring(response.body())
        assert root.tag == f"{{{ATOM_NS}}}feed", f"root should be an Atom feed, got {root.tag}"

    def test_feed_autodiscovery_uses_atom_media_type(self, page: Page, jekyll_server: str):
        page.goto(jekyll_server)
        link = page.locator('head link[rel="alternate"][href$="/atom.xml"]')
        assert link.count() == 1, "expected one feed autodiscovery link"
        assert link.get_attribute("type") == "application/atom+xml"


class TestFeedLinks:
    """Browsers don't surface autodiscovery links, so readers need a visible one."""

    def test_post_links_to_the_feed(self, page: Page, jekyll_server: str, any_post_url: str):
        page.goto(f"{jekyll_server}{any_post_url}")
        assert page.locator(".post a[href$='/atom.xml']").is_visible()

    def test_sidebar_links_to_the_feed(self, page: Page, jekyll_server: str):
        page.goto(jekyll_server)
        page.locator(".sidebar-toggle").click()
        link = page.locator(".sidebar a[href$='/atom.xml']")
        link.wait_for(state="visible")
