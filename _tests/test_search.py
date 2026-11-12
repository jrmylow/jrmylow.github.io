"""Tests for search: the sidebar box, the index, and the results page.

Result expectations are the designed corpus's cases (corpus.py). Each query is a word that
one designed post has in exactly one place (its tags, its title or its body), so a result
shows where the match was made as well as that a match was made.
"""

import urllib.parse

import corpus
import pytest
from constants import SELECTORS
from playwright.sync_api import Page, expect

TAG_ONLY = "quokka"  # a tag of UNSHARED_TAGS, in no title or body
TITLE_WORD = "markup"  # in MARKUP_TITLE's title only
TITLE_TYPO = "markpu"  # the same word with two letters swapped
BODY_WORD = "itself"  # in LINKS_OUT's body only
NO_MATCH = "xyznonexistent123456"

RESULT_JS = """els => els.map(el => ({
    title: el.querySelector('.search-result-title').textContent,
    href: el.getAttribute('href'),
    tags: [...el.querySelectorAll('.search-result-tag')].map(tag => tag.textContent),
    titleMarks: [...el.querySelectorAll('.search-result-title mark')].map(mark => mark.textContent),
    titleElements: el.querySelectorAll('.search-result-title *:not(mark)').length,
    excerpt: el.querySelector('.search-result-excerpt').textContent.trim(),
    excerptMarks: [...el.querySelectorAll('.search-result-excerpt mark')].map(mark => mark.textContent),
}))"""


def _search(page: Page, site, query: str) -> list[dict]:
    """Open the results page for query and return its results, once the search has finished."""
    page.goto(f"{site.url}/search/?q={query}")
    expect(page.locator(".search-result-item, .search-no-results").first).to_be_visible()
    return page.locator(".search-result-item").evaluate_all(RESULT_JS)


def _query_in_url(page: Page) -> str:
    return urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)["q"][0]


class TestSidebarSearch:
    """The sidebar box only sends you to the results page; it shows no results itself."""

    def test_box_is_shown_below_the_theme_toggle_when_the_sidebar_opens(self, page: Page, jekyll_server: str):
        page.goto(jekyll_server)
        page.locator(SELECTORS["sidebar_toggle"]).click()
        expect(page.locator(SELECTORS["search_input"])).to_be_visible()
        order = page.locator(".sidebar").evaluate(
            "el => [...el.querySelectorAll('.theme-toggle, .search-container')].map(child => child.className)"
        )
        assert order == ["theme-toggle", "search-container"]

    def test_sidebar_search_text_is_at_least_16px(self, page: Page, jekyll_server: str):
        """The sidebar search box's text is at least 16px, on phones and desktops.

        iOS Safari zooms the whole page when an input under 16px takes focus. Old: 14px on
        phones, 15px from 48em.
        """
        for width in (375, 1280):
            page.set_viewport_size({"width": width, "height": 800})
            page.goto(jekyll_server)
            page.locator(SELECTORS["sidebar_toggle"]).click()
            size = page.locator(SELECTORS["search_input"]).evaluate("el => parseFloat(getComputedStyle(el).fontSize)")
            assert size >= 16, f"sidebar search text is {size}px at {width}px wide; iOS zooms below 16px"

    def test_typing_shows_no_results_in_the_sidebar(self, page: Page, designed_site):
        page.goto(designed_site.url)
        page.locator(SELECTORS["sidebar_toggle"]).click()
        page.locator(SELECTORS["search_input"]).fill(TAG_ONLY)
        page.wait_for_timeout(300)  # nothing to wait for: give live results a chance to appear
        assert page.locator(".sidebar .search-result-item").count() == 0
        assert urllib.parse.urlsplit(page.url).path == "/"

    def test_enter_opens_the_results_page_for_the_query(self, page: Page, designed_site):
        page.goto(designed_site.url)
        page.locator(SELECTORS["sidebar_toggle"]).click()
        box = page.locator(SELECTORS["search_input"])
        box.fill(TAG_ONLY)
        with page.expect_navigation():
            box.press("Enter")
        assert urllib.parse.urlsplit(page.url).path == "/search/"
        assert _query_in_url(page) == TAG_ONLY
        expect(page.locator(".search-result-title")).to_have_text([corpus.UNSHARED_TAGS.title])


class TestSearchIndex:
    def test_index_has_every_post_newest_first_with_its_title_address_and_tags(self, page: Page, designed_site):
        """Checked against Jekyll's own record of the posts. Previews aren't posts, so aren't indexed."""
        index = page.request.get(f"{designed_site.url}/search-index.json").json()
        indexed = [(entry["title"], entry["url"], entry["tags"]) for entry in index]
        assert indexed == [(post["title"], post["url"], post["tags"]) for post in designed_site.manifest["posts"]]

    def test_index_content_is_the_posts_text_without_markup(self, page: Page, designed_site):
        index = page.request.get(f"{designed_site.url}/search-index.json").json()
        content = {entry["title"]: entry["content"].strip() for entry in index}
        assert content[corpus.ALPHA.title] == corpus.ALPHA.body
        assert content[corpus.LINKS_OUT.title] == "Links to the linked post and to itself."


class TestSearchResults:
    def test_word_found_only_in_a_tag_finds_that_post(self, page: Page, designed_site):
        post = corpus.UNSHARED_TAGS
        [result] = _search(page, designed_site, TAG_ONLY)
        assert (result["title"], result["href"]) == (post.title, designed_site.document(post.filename)["url"])
        assert result["tags"] == list(post.tags)
        assert (result["excerpt"], result["excerptMarks"]) == (post.body, []), "no match in the body: plain opening"

    def test_title_match_is_highlighted_and_markup_in_the_title_is_shown_as_text(self, page: Page, designed_site):
        [result] = _search(page, designed_site, TITLE_WORD)
        assert result["title"] == corpus.MARKUP_TITLE.title, "the title's <i> must show as typed"
        assert result["titleElements"] == 0, "the title's <i> became an element"
        assert result["titleMarks"] == [TITLE_WORD]
        assert result["tags"] == [], "an untagged post shows no tag chips"

    def test_body_match_is_highlighted_in_the_excerpt(self, page: Page, designed_site):
        [result] = _search(page, designed_site, BODY_WORD)
        assert result["title"] == corpus.LINKS_OUT.title
        assert BODY_WORD in result["excerptMarks"]
        assert result["titleMarks"] == [], "the title doesn't contain the word"

    @pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason="the index's content is the post's HTML with tags stripped, which leaves entities such as "
        "&amp; in it, and the results page then escapes those a second time",
    )
    def test_excerpt_shows_ampersands_and_angle_brackets_as_written(self, page: Page, designed_site):
        """Known bug: "R&D: a < b" in a body shows as "R&amp;D: a &lt; b" in its excerpt.
        Strict, so this fails, and gets noticed, the day the bug is fixed."""
        post = corpus.ESCAPING_POST
        excerpts = {result["title"]: result["excerpt"] for result in _search(page, designed_site, "escaping")}
        assert excerpts[post.title] == post.body

    def test_typo_still_finds_the_post(self, page: Page, designed_site):
        results = _search(page, designed_site, TITLE_TYPO)
        assert [result["title"] for result in results] == [corpus.MARKUP_TITLE.title]

    def test_query_matching_nothing_says_so(self, page: Page, designed_site):
        assert _search(page, designed_site, NO_MATCH) == []
        assert page.locator(".search-no-results").all_inner_texts() == ["No results found"]

    def test_box_shows_the_query_and_enter_searches_again(self, page: Page, designed_site):
        _search(page, designed_site, TAG_ONLY)
        box = page.locator(".search-page-input")
        expect(box).to_have_value(TAG_ONLY)

        box.fill(TITLE_WORD)
        page.wait_for_timeout(300)  # nothing to wait for: give live results a chance to appear
        expect(page.locator(".search-result-title")).to_have_text([corpus.UNSHARED_TAGS.title])

        with page.expect_navigation():
            box.press("Enter")
        assert _query_in_url(page) == TITLE_WORD
        expect(page.locator(".search-result-title")).to_have_text([corpus.MARKUP_TITLE.title])

    def test_search_page_uses_shared_page_width(self, page: Page, jekyll_server: str):
        """Search content uses the shared .page wrapper at container width."""
        page.set_viewport_size({"width": 1280, "height": 900})

        page.goto(f"{jekyll_server}/about/")
        about = page.locator(".page").first.bounding_box()

        page.goto(f"{jekyll_server}/search/")
        search = page.locator(".page").first.bounding_box()

        assert about and search, "Both pages should render a .page wrapper"
        assert (
            abs(about["width"] - search["width"]) < 1
        ), f"Search width {search['width']} should match site page width {about['width']}"
