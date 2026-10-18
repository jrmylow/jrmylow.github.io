"""Characterization tests for heading typography.

Structural heading typography (weight + size scale) now lives in lanyon.css;
dark-mode.css carries only heading color. Headings render bold -- the resolved
choice between Lanyon's original `font-weight: 400` and the dark-mode `bold`.
These pin that result so the consolidation stays behavior-preserving.
"""

import re

from playwright.sync_api import Page


def _font_weight(page: Page, selector: str) -> int:
    raw = page.locator(selector).first.evaluate("el => getComputedStyle(el).fontWeight")
    return {"normal": 400, "bold": 700}.get(raw, int(raw))


class TestHeadingTypography:
    """Headings resolve to a single source of truth and render bold."""

    def test_post_title_renders_bold(self, page: Page, jekyll_server: str, any_post_url: str):
        page.goto(f"{jekyll_server}{any_post_url}")
        assert _font_weight(page, "h1.post-title") >= 700, "Post title should render bold"

    def test_page_title_renders_bold(self, page: Page, jekyll_server: str, any_post_url: str):
        page.goto(f"{jekyll_server}/essays/")
        assert _font_weight(page, "h1.page-title") >= 700, "Page title should render bold"

    def test_font_request_matches_the_fonts_used(self, page: Page, jekyll_server: str):
        """The Google Fonts request asks for PT Sans regular, bold and italic, and nothing else.

        The suite runs offline, so this reads the request rather than the loaded font. Old:
        it asked for PT Serif, which no rule uses, and PT Sans at 400 only, so bold headings
        and italic blockquotes were synthesised by the browser.
        """
        page.goto(f"{jekyll_server}/")
        href = page.locator('link[href*="fonts.googleapis.com"]').get_attribute("href")
        families = re.findall(r"family=([^&]+)", href)
        assert families == ["PT+Sans:ital,wght@0,400;0,700;1,400"], f"unexpected font request: {href}"
