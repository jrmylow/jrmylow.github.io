"""Tests for the command palette (Cmd/Ctrl-K): a quick jump to a post by title or tag.

Result expectations are the designed corpus's cases (corpus.py).
"""

import urllib.parse

import corpus
from playwright.sync_api import Page, expect

MAX_RESULTS = 8
IN_EVERY_TITLE = "designed"
TAG_ONLY = "quokka"  # a tag of UNSHARED_TAGS, in no title
NO_MATCH = "xyznonexistent123456"


def _open_and_type(page: Page, site, query: str) -> None:
    page.goto(site.url)
    page.keyboard.press("Control+k")
    page.locator(".command-palette-input").fill(query)


def _selected(page: Page) -> list[str]:
    """Titles of the results marked as selected; there should be exactly one."""
    return page.locator(".command-palette-results li[aria-selected='true']").all_inner_texts()


class TestCommandPalette:
    def test_shortcut_opens_palette(self, page: Page, jekyll_server: str):
        """Ctrl/Cmd-K opens the overlay and focuses the input."""
        page.goto(jekyll_server)
        page.keyboard.press("Control+k")

        expect(page.locator(".command-palette")).to_be_visible()
        expect(page.locator(".command-palette-input")).to_be_focused()

    def test_escape_closes_palette(self, page: Page, jekyll_server: str):
        """Escape hides the overlay."""
        page.goto(jekyll_server)
        page.keyboard.press("Control+k")
        expect(page.locator(".command-palette")).to_be_visible()

        page.keyboard.press("Escape")
        expect(page.locator(".command-palette")).to_be_hidden()

    def test_query_lists_the_matching_post_and_enter_opens_it(self, page: Page, designed_site):
        post = corpus.UNSHARED_TAGS
        _open_and_type(page, designed_site, TAG_ONLY)
        expect(page.locator(".command-palette-result")).to_have_text([post.title])
        assert _selected(page) == [post.title], "the first result starts selected"

        with page.expect_navigation():
            page.keyboard.press("Enter")
        assert page.url == designed_site.page_url(post.filename)

    def test_results_stop_at_eight(self, page: Page, designed_site):
        assert len(corpus.DESIGNED) > MAX_RESULTS, "this case needs more matching posts than the palette shows"
        _open_and_type(page, designed_site, IN_EVERY_TITLE)
        expect(page.locator(".command-palette-result")).to_have_count(MAX_RESULTS)

    def test_down_arrow_selects_the_next_result_and_enter_opens_it(self, page: Page, designed_site):
        _open_and_type(page, designed_site, IN_EVERY_TITLE)
        results = page.locator(".command-palette-result")
        expect(results).to_have_count(MAX_RESULTS)
        titles = results.all_inner_texts()
        second = results.nth(1).get_attribute("href")
        assert _selected(page) == [titles[0]]

        page.keyboard.press("ArrowDown")
        assert _selected(page) == [titles[1]]

        with page.expect_navigation():
            page.keyboard.press("Enter")
        assert urllib.parse.urlsplit(page.url).path == second

    def test_enter_with_no_match_opens_the_search_page_for_the_query(self, page: Page, designed_site):
        _open_and_type(page, designed_site, NO_MATCH)
        with page.expect_navigation():
            page.keyboard.press("Enter")
        assert urllib.parse.urlsplit(page.url).path == "/search/"
        assert urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query) == {"q": [NO_MATCH]}
