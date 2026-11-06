"""Tests for the table of contents: _includes/post_toc.html and public/js/toc.js.

Uses the fixture previews _tests/fixtures/_previews/2024-04-0*-toc-*.md, served by the
designed build. From 80em the TOC is open and fixed in the right margin, beside the
column, while the post scrolls; below that it is a closed box above the post. It marks
the section being read with aria-current="location".
"""

import corpus
import pytest
from playwright.sync_api import Page, expect

DEMO = "2024-04-01-toc-demo.md"
OPT_OUT = "2024-04-02-toc-off-demo.md"
SINGLE = "2024-04-03-toc-single-demo.md"

TOC = ".toc"
LINKS = ".toc-list a"
CURRENT = ".toc-list a[aria-current='location']"
WIDE = {"width": 1280, "height": 720}  # 80em, the breakpoint
NARROW = {"width": 1024, "height": 768}

# The demo's h2/h3 outline, in order: (level, text, id)
OUTLINE = [
    (2, "First section", "first-section"),
    (3, "First subsection", "first-subsection"),
    (3, "Second subsection", "second-subsection"),
    (2, "Second section", "second-section"),
    (3, "Hidden subsection", "hidden-subsection"),
    (2, "Last section", "last-section"),
]


def _url(site, filename: str) -> str:
    return f"{site.url}{site.document(filename)['url']}"


@pytest.fixture
def demo(page: Page, designed_site) -> Page:
    page.set_viewport_size(WIDE)
    page.goto(_url(designed_site, DEMO))
    expect(page.locator(TOC)).to_be_visible()
    return page


def _scroll_heading_to_top(page: Page, heading_id: str) -> None:
    """Scroll as an anchor jump would: the heading just below the masthead."""
    page.evaluate(f"document.getElementById({heading_id!r}).scrollIntoView({{block: 'start'}})")


def _rect(page: Page, selector: str) -> dict:
    return page.locator(selector).first.evaluate("el => el.getBoundingClientRect().toJSON()")


class TestContents:
    """The list is the post's h2 and h3 headings, nested, linking to their ids."""

    def test_links_follow_the_headings(self, demo: Page):
        links = demo.locator(LINKS)
        expect(links).to_have_count(len(OUTLINE))
        for i, (_, text, anchor) in enumerate(OUTLINE):
            expect(links.nth(i)).to_have_text(text)
            expect(links.nth(i)).to_have_attribute("href", f"#{anchor}")

    def test_h3_entries_nest_under_their_h2(self, demo: Page):
        nested = [text for level, text, _ in OUTLINE if level == 3]
        expect(demo.locator(".toc-list > li > ul a")).to_have_text(nested)

    def test_is_a_named_navigation_landmark(self, demo: Page):
        expect(demo.get_by_role("navigation", name="Contents")).to_be_visible()


class TestWide:
    """From 80em: open, fixed in the right margin, clear of the column and the masthead."""

    def test_open_on_load(self, demo: Page):
        expect(demo.locator(f"{TOC} details")).to_have_attribute("open", "")
        expect(demo.locator(LINKS).first).to_be_visible()

    def test_sits_right_of_the_column_inside_the_window(self, demo: Page):
        toc, column = _rect(demo, TOC), _rect(demo, ".container.content")
        assert toc["left"] >= column["right"], f"TOC (left {toc['left']}) overlaps the column (right {column['right']})"
        assert toc["right"] <= WIDE["width"], f"TOC runs off the window (right {toc['right']})"

    def test_below_the_masthead(self, demo: Page):
        assert _rect(demo, TOC)["top"] >= _rect(demo, ".masthead")["bottom"]

    def test_stays_in_view_while_scrolling(self, demo: Page):
        before = _rect(demo, TOC)["top"]
        _scroll_heading_to_top(demo, "last-section")
        expect(demo.locator(CURRENT)).to_have_text("Last section")
        assert _rect(demo, TOC)["top"] == before


class TestNarrow:
    """Below 80em: a closed box in the column, above the post's first paragraph."""

    @pytest.fixture
    def narrow(self, page: Page, designed_site) -> Page:
        page.set_viewport_size(NARROW)
        page.goto(_url(designed_site, DEMO))
        return page

    def test_closed_on_load(self, narrow: Page):
        expect(narrow.locator(".toc-summary")).to_be_visible()
        expect(narrow.locator(f"{TOC} details")).not_to_have_attribute("open", "")
        expect(narrow.locator(LINKS).first).to_be_hidden()

    def test_in_the_column_above_the_post(self, narrow: Page):
        toc, column = _rect(narrow, TOC), _rect(narrow, ".container.content")
        first = _rect(narrow, ".post > p")
        assert column["left"] <= toc["left"] and toc["right"] <= column["right"]
        assert toc["bottom"] <= first["top"]

    def test_summary_opens_it(self, narrow: Page):
        narrow.locator(".toc-summary").click()
        expect(narrow.locator(LINKS).first).to_be_visible()

    def test_follows_the_breakpoint(self, narrow: Page):
        details = narrow.locator(f"{TOC} details")
        narrow.set_viewport_size(WIDE)
        expect(details).to_have_attribute("open", "")
        narrow.set_viewport_size(NARROW)
        expect(details).not_to_have_attribute("open", "")


class TestCurrentSection:
    """The entry for the section being read carries aria-current="location"."""

    def test_none_before_the_first_heading(self, demo: Page):
        expect(demo.locator(CURRENT)).to_have_count(0)

    @pytest.mark.parametrize(
        "anchor, text", [("first-subsection", "First subsection"), ("second-section", "Second section")]
    )
    def test_marks_the_heading_scrolled_to(self, demo: Page, anchor: str, text: str):
        _scroll_heading_to_top(demo, anchor)
        expect(demo.locator(CURRENT)).to_have_text(text)
        expect(demo.locator(CURRENT)).to_have_count(1)

    def test_marks_the_last_heading_at_the_bottom(self, demo: Page):
        """The short last section never reaches the masthead; the bottom of the page marks it."""
        demo.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        expect(demo.locator(CURRENT)).to_have_text("Last section")

    def test_following_a_link_marks_it(self, demo: Page):
        demo.locator(LINKS, has_text="Second subsection").click()
        expect(demo.locator(CURRENT)).to_have_text("Second subsection")


class TestJumps:
    """Following an entry lands on its heading, in view below the masthead."""

    def test_lands_below_the_masthead(self, demo: Page):
        demo.locator(LINKS, has_text="Second section").click()
        heading = demo.locator("#second-section")
        expect(heading).to_be_in_viewport()
        assert _rect(demo, "#second-section")["top"] >= _rect(demo, ".masthead")["bottom"]

    def test_opens_a_closed_box_around_its_target(self, demo: Page):
        heading = demo.locator("#hidden-subsection")
        expect(heading).to_be_hidden()
        demo.locator(LINKS, has_text="Hidden subsection").click()
        expect(heading).to_be_visible()
        expect(heading).to_be_in_viewport()


class TestWhenShown:
    """Posts get a TOC by default; `toc: false` or fewer than two headings means none."""

    @pytest.mark.parametrize("filename", [OPT_OUT, SINGLE], ids=["opt-out", "single-heading"])
    def test_absent(self, page: Page, designed_site, filename: str):
        page.goto(_url(designed_site, filename))
        expect(page.locator(".post-title")).to_be_visible()
        expect(page.locator(TOC)).to_have_count(0)

    def test_absent_without_headings_and_loads_no_script(self, page: Page, designed_site):
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        page.goto(_url(designed_site, corpus.DESIGNED[0].filename))
        expect(page.locator(TOC)).to_have_count(0)
        assert not [url for url in requests if url.endswith("/toc.js")]

    def test_absent_from_pages(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}/about/")
        expect(page.locator(TOC)).to_have_count(0)
