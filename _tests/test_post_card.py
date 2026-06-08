"""Characterization tests for the shared post-card component.

Home, Essays, and the paginated archive render post previews through one
include, _includes/post_card.html, taking `post` and `heading` params.
Extracting the include is a pure refactor: the card's structure is a single
source of truth, so the inner markup must be identical across every page.

These tests assert that invariant (same structure everywhere) without pinning
the heading level to a literal -- the level is a free per-call choice, so the
tests never need editing when you retune it.
"""

from playwright.sync_api import Page

CARD = ".card"
CARD_TITLE = ".card-title"
PAGES = ("/", "/essays/", "/essays/all/")


def _first_card_title_tag(page: Page, jekyll_server: str, path: str) -> str:
    page.goto(f"{jekyll_server}{path}")
    page.wait_for_selector(CARD)
    return page.locator(f"{CARD} {CARD_TITLE}").first.evaluate("el => el.tagName.toLowerCase()")


class TestCardStructure:
    """Every post card exposes the same inner structure (one source of truth)."""

    def test_card_parts_present(self, page: Page, jekyll_server: str):
        for path in PAGES:
            page.goto(f"{jekyll_server}{path}")
            page.wait_for_selector(CARD)
            card = page.locator(CARD).first
            assert card.locator(".card-content").count() == 1, path
            assert card.locator(".card-title").count() == 1, path
            assert card.locator(".card-meta").count() == 1, path
            assert card.locator(".card-body").count() == 1, path

    def test_card_title_is_a_heading(self, page: Page, jekyll_server: str):
        """Card title is some heading element (h1-h6), level unspecified."""
        for path in PAGES:
            tag = _first_card_title_tag(page, jekyll_server, path)
            assert tag in {"h1", "h2", "h3", "h4", "h5", "h6"}, f"{path}: {tag}"

    def test_card_links_to_post(self, page: Page, jekyll_server: str):
        """Card is wrapped in a card-link anchor pointing at a real URL."""
        page.goto(f"{jekyll_server}/essays/")
        page.wait_for_selector(f"a.card-link {CARD}")
        href = page.locator("a.card-link").first.get_attribute("href")
        assert href and href not in ("", "#"), f"card-link href missing: {href!r}"
