"""Tests for the collapsible box: _includes/details_open.html and details_close.html.

Uses the fixture preview _tests/fixtures/_previews/2024-03-01-details-demo.md, served
by the designed build. The includes open and close a box around Markdown that kramdown
converts in the same pass as the rest of the post, so footnotes, reference links and
heading ids inside a box must behave as they do outside one.

The summary text sits outside the toggle, so it can hold links; only the chevron, a
native <details>/<summary>, opens and closes the box.
"""

import re

import pytest
from playwright.sync_api import Page, expect

FIXTURE = "2024-03-01-details-demo.md"
BOX = ".collapsible"
SUMMARY = ".collapsible-summary"
TOGGLE = "details > summary"
TITLE = ".collapsible-title"


@pytest.fixture
def fixture_url(designed_site) -> str:
    return f"{designed_site.url}{designed_site.document(FIXTURE)['url']}"


@pytest.fixture
def boxes(page: Page, fixture_url: str):
    page.goto(fixture_url)
    expect(page.locator(BOX)).to_have_count(4)
    return page.locator(BOX)


class TestMarkup:
    """The summary and body are Markdown, converted with the rest of the post."""

    def test_summary_renders_inline_markdown(self, boxes):
        expect(boxes.first.locator(f"{SUMMARY} strong")).to_have_text("closed")

    def test_summary_keeps_quotes(self, boxes):
        """A single-quoted summary can hold double quotes (kramdown curls them)."""
        expect(boxes.nth(1).locator(SUMMARY)).to_have_text(re.compile(r'An ["“]open["”] box'))

    def test_summary_link_sits_outside_the_toggle(self, boxes):
        """A link in the summary is never nested inside the toggle (WCAG 4.1.2)."""
        box = boxes.nth(2)
        expect(box.locator(f"{SUMMARY} a")).to_have_attribute("href", "https://example.com/")
        expect(box.locator(f"{TOGGLE} a")).to_have_count(0)

    def test_body_renders_block_markdown(self, boxes):
        box = boxes.first
        expect(box.locator("h2")).to_have_text("Inside the box")
        expect(box.locator("p em")).to_have_text("emphasis")
        expect(box.locator("ul > li")).to_have_count(2)

    def test_heading_inside_gets_an_id(self, boxes):
        expect(boxes.first.locator("h2")).to_have_id("inside-the-box")

    def test_reference_link_defined_outside_resolves(self, boxes):
        link = boxes.first.locator("details a", has_text="reference link")
        expect(link).to_have_attribute("href", "https://example.com/")

    def test_footnotes_join_the_posts_one_list(self, page: Page, boxes):
        """A footnote inside a box is numbered with, and listed alongside, the rest."""
        expect(page.locator(".footnotes")).to_have_count(1)
        expect(page.locator(".footnotes li")).to_have_count(2)
        expect(boxes.first.locator('sup[id^="fnref"]')).to_have_text("2")

    def test_no_unconverted_markdown_leaks(self, page: Page, boxes):
        text = page.locator(".post").inner_text()
        assert "[^" not in text and "][ref]" not in text and "**" not in text


class TestBehaviour:
    """Closed unless `open` is passed; only the chevron toggles it, by mouse or keyboard."""

    def test_closed_by_default(self, boxes):
        box = boxes.first
        expect(box.locator("details")).not_to_have_attribute("open", "")
        expect(box.locator(SUMMARY)).to_be_visible()
        expect(box.locator("h2")).to_be_hidden()

    def test_open_param_starts_open(self, boxes):
        box = boxes.nth(1)
        expect(box.locator("details")).to_have_attribute("open", "")
        expect(box.locator("details p")).to_be_visible()

    def test_chevron_toggles(self, boxes):
        box = boxes.first
        box.locator(TOGGLE).click()
        expect(box.locator("h2")).to_be_visible()
        box.locator(TOGGLE).click()
        expect(box.locator("h2")).to_be_hidden()

    def test_summary_text_does_not_toggle(self, boxes):
        box = boxes.first
        box.locator(SUMMARY).click()
        expect(box.locator("details")).not_to_have_attribute("open", "")
        expect(box.locator("h2")).to_be_hidden()

    def test_keyboard_toggles(self, page: Page, boxes):
        """2.1.1 (A): the chevron is a Tab stop and Enter opens the box."""
        toggle = boxes.first.locator(TOGGLE)
        toggle.focus()
        expect(toggle).to_be_focused()
        page.keyboard.press("Enter")
        expect(boxes.first.locator("h2")).to_be_visible()

    def test_chevron_is_named_and_described(self, boxes):
        """4.1.2 (A): the icon-only toggle has a name, and the summary describes it."""
        toggle = boxes.first.locator(TOGGLE)
        expect(toggle).to_have_accessible_name("Details")
        expect(toggle).to_have_accessible_description(re.compile("closed box"))

    def test_chevron_is_a_big_enough_target(self, boxes):
        """2.5.8 (AA): the toggle is at least 24 by 24 CSS pixels."""
        size = boxes.first.locator(TOGGLE).bounding_box()
        assert size["width"] >= 24 and size["height"] >= 24, size


class TestStyle:
    """The box reads as a box, with its own disclosure marker."""

    def test_box_stands_out_from_the_page(self, page: Page, boxes):
        box_bg = boxes.first.evaluate("el => getComputedStyle(el).backgroundColor")
        page_bg = page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")
        assert box_bg != page_bg

    def test_default_marker_replaced(self, boxes):
        toggle = boxes.first.locator(TOGGLE)
        assert toggle.evaluate("el => getComputedStyle(el).listStyleType") == "none"
        marker = toggle.evaluate("el => getComputedStyle(el, '::after').content")
        assert marker not in ("none", "normal")

    def test_marker_turns_when_opened(self, page: Page, boxes):
        page.emulate_media(reduced_motion="reduce")
        toggle = boxes.first.locator(TOGGLE)
        closed = toggle.evaluate("el => getComputedStyle(el, '::after').transform")
        toggle.click()
        expect(boxes.first.locator("h2")).to_be_visible()
        opened = toggle.evaluate("el => getComputedStyle(el, '::after').transform")
        assert closed != opened


# Line boxes of a summary's text, and where its content box starts.
SUMMARY_GEOMETRY_JS = """el => {
    const box = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    const range = document.createRange();
    range.selectNodeContents(el);
    const lines = [...range.getClientRects()].filter(r => r.width > 0);
    return {
        contentLeft: box.left + parseFloat(style.borderLeftWidth) + parseFloat(style.paddingLeft),
        textLeft: Math.min(...lines.map(r => r.left)),
        textRight: Math.max(...lines.map(r => r.right)),
        firstTop: lines[0].top,
        firstBottom: lines[0].bottom,
    };
}"""

# Where the text just before a summary's link ends, and where the link starts.
LINK_IN_FLOW_JS = """el => {
    const link = el.querySelector("a");
    const range = document.createRange();
    range.selectNodeContents(link.previousSibling);
    const before = [...range.getClientRects()].pop();
    const start = link.getClientRects()[0];
    return { beforeTop: before.top, beforeRight: before.right, top: start.top, left: start.left };
}"""


class TestSummaryLayout:
    """The summary is one flow of text, with the chevron beside it on the right."""

    def test_text_starts_at_the_left_edge(self, boxes):
        geometry = boxes.first.locator(SUMMARY).evaluate(SUMMARY_GEOMETRY_JS)
        assert abs(geometry["textLeft"] - geometry["contentLeft"]) < 1, geometry

    def test_chevron_sits_right_of_wrapped_text_on_its_first_line(self, boxes):
        box = boxes.nth(2)
        geometry = box.locator(SUMMARY).evaluate(SUMMARY_GEOMETRY_JS)
        toggle = box.locator(TOGGLE).bounding_box()
        outer = box.bounding_box()
        assert geometry["textRight"] <= toggle["x"], (geometry, toggle)
        assert toggle["x"] + toggle["width"] <= outer["x"] + outer["width"], (toggle, outer)
        middle = toggle["y"] + toggle["height"] / 2
        assert geometry["firstTop"] <= middle <= geometry["firstBottom"], (geometry, toggle)

    def test_chevron_stays_put_when_opened(self, boxes):
        box = boxes.first
        closed = box.locator(TOGGLE).bounding_box()
        box.locator(TOGGLE).click()
        expect(box.locator("h2")).to_be_visible()
        assert box.locator(TOGGLE).bounding_box() == closed

    def test_link_stays_in_its_sentence(self, boxes):
        """A link in a wrapping summary continues the line its sentence is on.

        Old: the summary was a flex container, so each text run and the link became
        separate flex items and the link floated off beside the paragraph.
        """
        where = boxes.nth(2).locator(SUMMARY).evaluate(LINK_IN_FLOW_JS)
        assert abs(where["top"] - where["beforeTop"]) < 2, where
        assert 0 <= where["left"] - where["beforeRight"] < 2, where


# Where a run-in title's last line ends, and where the summary text after it starts.
RUN_IN_JS = """el => {
    const title = el.querySelector(".collapsible-title");
    const text = title.nextElementSibling;
    const end = [...title.getClientRects()].pop();
    const start = text.getClientRects()[0];
    return { titleTop: end.top, titleRight: end.right, textTop: start.top, textLeft: start.left };
}"""


class TestTitle:
    """An optional title: a heading run in at the start of the summary, outside the toggle."""

    def test_title_is_a_heading_at_the_given_level(self, boxes):
        title = boxes.nth(3).locator(TITLE)
        expect(title).to_have_text("A titled box")
        assert title.evaluate("el => el.tagName") == "H2"

    def test_title_gets_an_id_from_its_text(self, boxes):
        """So a project can be linked to, as /page/#its-title."""
        expect(boxes.nth(3).locator(TITLE)).to_have_id("a-titled-box")

    def test_title_sits_outside_the_toggle(self, boxes):
        box = boxes.nth(3)
        expect(box.locator(f"{SUMMARY} {TITLE}")).to_have_count(1)
        expect(box.locator(f"{TOGGLE} {TITLE}")).to_have_count(0)

    def test_untitled_boxes_have_no_title(self, boxes):
        expect(boxes.first.locator(TITLE)).to_have_count(0)

    def test_chevron_is_described_by_the_title(self, boxes):
        """The title's CSS full stop may be read too; it only adds a pause."""
        expect(boxes.nth(3).locator(TOGGLE)).to_have_accessible_description(re.compile(r"^A titled box\.?$"))

    def test_summary_runs_on_after_the_title(self, boxes):
        """The title and summary share a line, as bold run-in text would."""
        where = boxes.nth(3).locator(SUMMARY).evaluate(RUN_IN_JS)
        assert abs(where["textTop"] - where["titleTop"]) < 2, where
        assert 0 <= where["textLeft"] - where["titleRight"] < 12, where

    def test_title_is_bold_at_the_summary_size(self, boxes):
        summary = boxes.nth(3).locator(SUMMARY)
        title = summary.locator(TITLE)
        size = "el => getComputedStyle(el).fontSize"
        assert title.evaluate(size) == summary.evaluate(size)
        assert int(title.evaluate("el => getComputedStyle(el).fontWeight")) >= 700
