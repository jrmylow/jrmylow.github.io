"""Tests for Tufte-style sidenotes built from kramdown footnotes.

Uses the committed preview fixture docs/_previews/2024-01-01-sidenotes-demo.md,
which has two footnotes, so these are deterministic rather than corpus-dependent.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.skip(reason="sidenotes parked: margin layout doesn't fit Lanyon's centered column")
FIXTURE_PATH = "/2024/01/01/sidenotes-demo/"


@pytest.fixture
def fixture_url(jekyll_server: str) -> str:
    return f"{jekyll_server}{FIXTURE_PATH}"


class TestSidenotesWide:
    """At >= 64em, footnotes become right-margin asides."""

    def test_asides_created_for_each_footnote(self, page: Page, fixture_url: str):
        """One aside.sidenote per footnote (the fixture has two)."""
        page.goto(fixture_url)
        expect(page.locator("aside.sidenote").first).to_be_visible()
        assert page.locator("aside.sidenote").count() == 2

    def test_aside_floats_into_margin(self, page: Page, fixture_url: str):
        """The aside floats right at the default 1280px width."""
        page.goto(fixture_url)
        side = page.locator("aside.sidenote").first
        assert side.evaluate("el => getComputedStyle(el).float") == "right"

    def test_original_footnotes_hidden(self, page: Page, fixture_url: str):
        """The kramdown footnotes block is hidden when sidenotes are shown."""
        page.goto(fixture_url)
        display = page.locator(".footnotes").evaluate("el => getComputedStyle(el).display")
        assert display == "none", "footnotes list should be hidden at wide widths"


class TestSidenotesNarrow:
    """Below 64em, asides collapse and normal footnotes return."""

    def test_asides_hidden_on_narrow(self, page: Page, fixture_url: str):
        """Sidenotes are not shown on a phone-width viewport."""
        page.set_viewport_size({"width": 500, "height": 900})
        page.goto(fixture_url)
        assert page.locator("aside.sidenote").first.is_hidden()

    def test_footnotes_visible_on_narrow(self, page: Page, fixture_url: str):
        """The footnotes list is shown on a phone-width viewport."""
        page.set_viewport_size({"width": 500, "height": 900})
        page.goto(fixture_url)
        display = page.locator(".footnotes").evaluate("el => getComputedStyle(el).display")
        assert display != "none", "footnotes list should be visible on narrow screens"
