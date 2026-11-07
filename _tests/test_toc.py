"""Tests for the table of contents: _includes/post_toc.html and public/js/toc.js.

Uses the fixture previews _tests/fixtures/_previews/2024-04-0*-toc-*.md, served by the
designed build. The TOC is a panel that hangs from the header line and unrolls downward,
toggled by a button at the header bar's right end. From 80em it hangs in the right
margin, covering nothing, and starts open unless the reader closed it before; below
that it covers the screen under the header, starts closed, and closes like the menu.
It marks the section being read with aria-current="location".
"""

import corpus
import pytest
from constants import DARK_BG_COLOR, LIGHT_BG_COLOR
from playwright.sync_api import Page, expect

DEMO = "2024-04-01-toc-demo.md"
OPT_OUT = "2024-04-02-toc-off-demo.md"
SINGLE = "2024-04-03-toc-single-demo.md"

PANEL = ".toc"
TOGGLE = ".toc-toggle"
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


def _load(page: Page, site, viewport: dict) -> Page:
    page.set_viewport_size(viewport)
    page.goto(_url(site, DEMO))
    expect(page.locator(TOGGLE)).to_be_visible()
    return page


@pytest.fixture
def wide(page: Page, designed_site) -> Page:
    return _load(page, designed_site, WIDE)


@pytest.fixture
def narrow(page: Page, designed_site) -> Page:
    return _load(page, designed_site, NARROW)


def _expect_open(page: Page) -> None:
    expect(page.locator(TOGGLE)).to_have_attribute("aria-expanded", "true")
    expect(page.locator(LINKS).first).to_be_visible()
    expect(page.locator(PANEL)).to_be_in_viewport(ratio=1)


def _expect_closed(page: Page) -> None:
    expect(page.locator(TOGGLE)).to_have_attribute("aria-expanded", "false")
    expect(page.locator(PANEL)).to_be_hidden()
    expect(page.locator(LINKS).first).to_be_hidden()


def _scroll_heading_to_top(page: Page, heading_id: str) -> None:
    """Scroll as an anchor jump would: the heading just below the masthead."""
    page.evaluate(f"document.getElementById({heading_id!r}).scrollIntoView({{block: 'start'}})")


def _rect(page: Page, selector: str) -> dict:
    return page.locator(selector).first.evaluate("el => el.getBoundingClientRect().toJSON()")


def _assert_reaches_the_bottom(page: Page, viewport: dict) -> None:
    """The panel runs down to the window's bottom edge, however short its list."""
    bottom = _rect(page, PANEL)["bottom"]
    assert abs(bottom - viewport["height"]) < 1, f"panel ends at {bottom}, not the window's bottom"


def _assert_hangs_from_the_header(page: Page) -> None:
    """The panel's top is the header's bottom edge: the header line stays in view above it."""
    top, line = _rect(page, PANEL)["top"], _rect(page, ".masthead")["bottom"]
    assert abs(top - line) < 0.5, f"panel top {top} is not at the header line {line}"


class TestContents:
    """The list is the post's h2 and h3 headings, nested, linking to their ids."""

    def test_links_follow_the_headings(self, wide: Page):
        links = wide.locator(LINKS)
        expect(links).to_have_count(len(OUTLINE))
        for i, (_, text, anchor) in enumerate(OUTLINE):
            expect(links.nth(i)).to_have_text(text)
            expect(links.nth(i)).to_have_attribute("href", f"#{anchor}")

    def test_h3_entries_nest_under_their_h2(self, wide: Page):
        nested = [text for level, text, _ in OUTLINE if level == 3]
        expect(wide.locator(".toc-list > li > ul a")).to_have_text(nested)

    def test_panel_is_a_named_navigation_landmark(self, wide: Page):
        expect(wide.get_by_role("navigation", name="Contents")).to_be_visible()

    def test_toggle_is_a_named_button_for_the_panel(self, wide: Page):
        toggle = wide.get_by_role("button", name="Table of contents", exact=True)
        expect(toggle).to_have_attribute("aria-controls", "toc")
        expect(wide.locator("#toc")).to_have_class("toc")


class TestWide:
    """From 80em: open in the right margin, beside the column, until the reader closes it."""

    def test_open_on_load_without_sliding(self, wide: Page):
        _expect_open(wide)
        assert wide.locator(PANEL).evaluate("el => el.getAnimations().length") == 0

    def test_hangs_from_the_header_line(self, wide: Page):
        _assert_hangs_from_the_header(wide)
        _scroll_heading_to_top(wide, "second-section")
        _assert_hangs_from_the_header(wide)

    def test_runs_down_to_the_bottom_of_the_window(self, wide: Page):
        """A column down the margin, not a box cut off under its list (the demo's list is short)."""
        _assert_reaches_the_bottom(wide, WIDE)
        _scroll_heading_to_top(wide, "second-section")
        _assert_reaches_the_bottom(wide, WIDE)
        expect(wide.locator(PANEL)).to_have_css("border-bottom-width", "0px")

    def test_fills_the_right_margin_clear_of_the_column(self, wide: Page):
        panel, column = _rect(wide, PANEL), _rect(wide, ".container.content")
        assert (
            panel["left"] >= column["right"]
        ), f"panel (left {panel['left']}) covers the column (right {column['right']})"
        assert panel["right"] == WIDE["width"], f"panel isn't at the window's edge (right {panel['right']})"

    def test_stays_open_while_reading(self, wide: Page):
        before = _rect(wide, PANEL)
        _scroll_heading_to_top(wide, "second-section")
        wide.locator(".post > p").first.click()
        _expect_open(wide)
        assert _rect(wide, PANEL) == before

    def test_toggle_closes_and_reopens(self, wide: Page):
        wide.locator(TOGGLE).click()
        _expect_closed(wide)
        wide.locator(TOGGLE).click()
        _expect_open(wide)

    def test_closing_is_remembered(self, wide: Page):
        wide.locator(TOGGLE).click()
        _expect_closed(wide)
        wide.reload()
        _expect_closed(wide)
        wide.locator(TOGGLE).click()
        wide.reload()
        _expect_open(wide)

    def test_escape_inside_closes_and_returns_focus(self, wide: Page):
        wide.locator(LINKS).first.focus()
        wide.keyboard.press("Escape")
        _expect_closed(wide)
        expect(wide.locator(TOGGLE)).to_be_focused()

    def test_opening_the_menu_leaves_it_in_place(self, wide: Page):
        """The panel sits outside .wrap, which the open menu transforms."""
        before = _rect(wide, PANEL)
        wide.locator(".sidebar-toggle").click()
        expect(wide.locator("#sidebar")).to_be_visible()
        _expect_open(wide)
        assert _rect(wide, PANEL) == before


class TestNarrow:
    """Below 80em: closed on load; opens over the page and closes like the menu."""

    def test_closed_on_load(self, narrow: Page):
        _expect_closed(narrow)

    def test_covers_the_screen_below_the_header(self, narrow: Page):
        _scroll_heading_to_top(narrow, "second-section")
        narrow.locator(TOGGLE).click()
        _expect_open(narrow)
        _assert_hangs_from_the_header(narrow)
        panel = _rect(narrow, PANEL)
        assert (panel["left"], panel["right"]) == (0, NARROW["width"]), f"panel spans {panel['left']}-{panel['right']}"
        _assert_reaches_the_bottom(narrow, NARROW)

    def test_click_outside_closes_it(self, narrow: Page):
        narrow.locator(TOGGLE).click()
        _expect_open(narrow)
        # The panel covers the page, so outside is the header bar: its empty top padding.
        narrow.locator(".masthead").click(position={"x": NARROW["width"] / 2, "y": 4})
        _expect_closed(narrow)

    def test_escape_closes_it(self, narrow: Page):
        narrow.locator(TOGGLE).click()
        _expect_open(narrow)
        narrow.keyboard.press("Escape")
        _expect_closed(narrow)
        expect(narrow.locator(TOGGLE)).to_be_focused()

    def test_following_a_link_closes_it_and_jumps(self, narrow: Page):
        narrow.locator(TOGGLE).click()
        narrow.locator(LINKS, has_text="Second section").click()
        _expect_closed(narrow)
        expect(narrow.locator("#second-section")).to_be_in_viewport()


class TestThemes:
    """The panel is part of the page: the page's background and colours, in either theme."""

    @pytest.mark.parametrize("theme, bg", [("dark", DARK_BG_COLOR), ("light", LIGHT_BG_COLOR)])
    def test_takes_the_page_background(self, page: Page, designed_site, theme: str, bg: str):
        page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
        _load(page, designed_site, WIDE)
        expect(page.locator(PANEL)).to_have_css("background-color", bg)
        heading = page.locator(".post-title").evaluate("el => getComputedStyle(el).color")
        expect(page.locator(".toc-title")).to_have_css("color", heading)

    def test_follows_a_theme_switch_while_open(self, wide: Page):
        wide.evaluate("localStorage.setItem('theme', 'dark')")
        wide.reload()
        expect(wide.locator(PANEL)).to_have_css("background-color", DARK_BG_COLOR)
        wide.locator(".sidebar-toggle").click()
        wide.locator(".toggle-switch").click()
        expect(wide.locator("html")).to_have_attribute("data-theme", "light")
        _expect_open(wide)
        expect(wide.locator(PANEL)).to_have_css("background-color", LIGHT_BG_COLOR)


class TestType:
    """Entries are set on the menu's type scale at every width: smaller than the article,
    and the same size either side of the 80em breakpoint (old: article-sized below it)."""

    @pytest.mark.parametrize("width", [390, 480, 720, 960, 1279, 1280, 1600])
    def test_entries_match_the_menu_and_sit_below_the_article(self, page: Page, designed_site, width: int):
        page.set_viewport_size({"width": width, "height": 800})
        page.goto(_url(designed_site, DEMO))
        sizes = page.evaluate(
            """() => Object.fromEntries([['entry', '.toc-list a'], ['title', '.toc-title'],
              ['menu', '.sidebar-nav-item'], ['article', '.post > p']].map(([k, s]) =>
              [k, parseFloat(getComputedStyle(document.querySelector(s)).fontSize)]))"""
        )
        assert sizes["entry"] == sizes["title"] == sizes["menu"], f"at {width}px: {sizes}"
        assert sizes["entry"] < sizes["article"], f"at {width}px: {sizes}"


def _resize(page: Page, viewport: dict) -> None:
    """Resize, then wait until the page has handled it. A media-query `change` has no DOM
    change to wait on, but browsers run its listeners before animation-frame callbacks
    (as test_theme_matrix relies on), so one frame after the query flips, toc.js has run.
    Without this, an assertion can pass on the old state before the listener fires."""
    page.set_viewport_size(viewport)
    wide = viewport["width"] >= WIDE["width"]
    page.wait_for_function(f"matchMedia('(min-width: 80em)').matches === {str(wide).lower()}")
    page.evaluate("() => new Promise((done) => requestAnimationFrame(() => done()))")


class TestResize:
    """One toggle: resizing across 80em keeps the panel as the reader left it. The stored
    desktop choice only decides how a page loads. Old: crossing the breakpoint re-applied
    it, so a panel opened on a narrow window shut on widening once the reader had closed
    it on desktop before."""

    @pytest.fixture(params=[None, "open", "closed"], ids=["nothing-stored", "stored-open", "stored-closed"])
    def stored(self, request, page: Page):
        if request.param:
            page.add_init_script(f"localStorage.setItem('toc', '{request.param}')")
        return request.param

    def test_opened_narrow_stays_open_when_widened(self, page: Page, designed_site, stored):
        narrow = _load(page, designed_site, NARROW)
        narrow.locator(TOGGLE).click()
        _expect_open(narrow)
        _resize(narrow, WIDE)
        _expect_open(narrow)

    def test_closed_narrow_stays_closed_when_widened(self, page: Page, designed_site, stored):
        narrow = _load(page, designed_site, NARROW)
        _expect_closed(narrow)
        _resize(narrow, WIDE)
        _expect_closed(narrow)

    def test_open_wide_stays_open_when_narrowed(self, wide: Page):
        _expect_open(wide)
        _resize(wide, NARROW)
        _expect_open(wide)
        wide.locator(TOGGLE).click()
        _expect_closed(wide)

    def test_widening_doesnt_change_the_stored_choice(self, page: Page, designed_site, stored):
        narrow = _load(page, designed_site, NARROW)
        narrow.locator(TOGGLE).click()
        _resize(narrow, WIDE)
        assert narrow.evaluate("localStorage.getItem('toc')") == stored


class TestCurrentSection:
    """The entry for the section being read carries aria-current="location"."""

    def test_none_before_the_first_heading(self, wide: Page):
        expect(wide.locator(CURRENT)).to_have_count(0)

    @pytest.mark.parametrize(
        "anchor, text", [("first-subsection", "First subsection"), ("second-section", "Second section")]
    )
    def test_marks_the_heading_scrolled_to(self, wide: Page, anchor: str, text: str):
        _scroll_heading_to_top(wide, anchor)
        expect(wide.locator(CURRENT)).to_have_text(text)
        expect(wide.locator(CURRENT)).to_have_count(1)

    def test_marks_the_last_heading_at_the_bottom(self, wide: Page):
        """The short last section never reaches the masthead; the bottom of the page marks it."""
        wide.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        expect(wide.locator(CURRENT)).to_have_text("Last section")

    def test_following_a_link_marks_it(self, wide: Page):
        wide.locator(LINKS, has_text="Second subsection").click()
        expect(wide.locator(CURRENT)).to_have_text("Second subsection")


class TestJumps:
    """Following an entry lands on its heading, in view below the masthead."""

    def test_lands_below_the_masthead(self, wide: Page):
        wide.locator(LINKS, has_text="Second section").click()
        expect(wide.locator("#second-section")).to_be_in_viewport()
        assert _rect(wide, "#second-section")["top"] >= _rect(wide, ".masthead")["bottom"]

    def test_opens_a_closed_box_around_its_target(self, wide: Page):
        heading = wide.locator("#hidden-subsection")
        expect(heading).to_be_hidden()
        wide.locator(LINKS, has_text="Hidden subsection").click()
        expect(heading).to_be_visible()
        expect(heading).to_be_in_viewport()


class TestWhenShown:
    """Posts get a TOC by default; `toc: false` or fewer than two headings means none."""

    @pytest.mark.parametrize("filename", [OPT_OUT, SINGLE], ids=["opt-out", "single-heading"])
    def test_absent(self, page: Page, designed_site, filename: str):
        page.goto(_url(designed_site, filename))
        expect(page.locator(".post-title")).to_be_visible()
        expect(page.locator(f"{PANEL}, {TOGGLE}")).to_have_count(0)

    def test_absent_without_headings_and_loads_no_script(self, page: Page, designed_site):
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        page.goto(_url(designed_site, corpus.DESIGNED[0].filename))
        expect(page.locator(f"{PANEL}, {TOGGLE}")).to_have_count(0)
        assert not [url for url in requests if url.endswith("/toc.js")]

    def test_absent_from_pages(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}/about/")
        expect(page.locator(f"{PANEL}, {TOGGLE}")).to_have_count(0)
