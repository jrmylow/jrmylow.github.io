"""Tests for client-side webmention display.

The webmention.io API is mocked with Playwright route interception, so these do
not hit the network and do not depend on any real mentions existing.
"""

import json
import re

from playwright.sync_api import Page, expect

API_RE = re.compile(r"webmention\.io/api/mentions\.jf2")


def _mock(page: Page, children):
    page.route(
        API_RE,
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"children": children}),
        ),
    )


class TestWebmentions:
    """Mentions render on posts; the section stays hidden when there are none."""

    def test_mentions_render(self, page: Page, jekyll_server: str, any_post_url: str):
        """A returned mention appears in the webmentions section."""
        _mock(
            page,
            [{"author": {"name": "Ada Lovelace"}, "content": {"text": "Lovely essay"}}],
        )
        page.goto(f"{jekyll_server}{any_post_url}")

        section = page.locator("#webmentions")
        expect(section).to_be_visible()
        expect(section).to_contain_text("Ada Lovelace")
        expect(section).to_contain_text("Lovely essay")

    def test_section_hidden_when_empty(self, page: Page, jekyll_server: str, any_post_url: str):
        """No mentions means the section stays hidden."""
        _mock(page, [])
        page.goto(f"{jekyll_server}{any_post_url}")

        expect(page.locator("#webmentions")).to_be_hidden()

    def test_content_is_text_not_markup(self, page: Page, jekyll_server: str, any_post_url: str):
        """Mention content is inserted as text, never as HTML."""
        _mock(
            page,
            [{"author": {"name": "Grace"}, "content": {"text": "<script>x</script>"}}],
        )
        page.goto(f"{jekyll_server}{any_post_url}")

        expect(page.locator("#webmentions")).to_be_visible()
        # The literal text should be present; no injected script element.
        expect(page.locator(".webmention-content").first).to_contain_text("<script>x</script>")
        assert page.locator("#webmentions script").count() == 0
