"""Tests for the collapsible box: _includes/details_open.html and details_close.html.

Uses the fixture preview _tests/fixtures/_previews/2024-03-01-details-demo.md, served
by the designed build. The includes open and close a <details> around Markdown that
kramdown converts in the same pass as the rest of the post, so footnotes, reference
links and heading ids inside a box must behave as they do outside one.
"""

import re

import pytest
from playwright.sync_api import Page, expect

FIXTURE = "2024-03-01-details-demo.md"
BOX = "details.collapsible"


@pytest.fixture
def fixture_url(designed_site) -> str:
    return f"{designed_site.url}{designed_site.document(FIXTURE)['url']}"


@pytest.fixture
def boxes(page: Page, fixture_url: str):
    page.goto(fixture_url)
    expect(page.locator(BOX)).to_have_count(2)
    return page.locator(BOX)


class TestMarkup:
    """The summary and body are Markdown, converted with the rest of the post."""

    def test_summary_renders_inline_markdown(self, boxes):
        expect(boxes.first.locator("summary strong")).to_have_text("closed")

    def test_summary_keeps_quotes(self, boxes):
        """A single-quoted summary can hold double quotes (kramdown curls them)."""
        expect(boxes.nth(1).locator("summary")).to_have_text(re.compile(r'An ["“]open["”] box'))

    def test_body_renders_block_markdown(self, boxes):
        box = boxes.first
        expect(box.locator("h3")).to_have_text("Inside the box")
        expect(box.locator("p em")).to_have_text("emphasis")
        expect(box.locator("ul > li")).to_have_count(2)

    def test_heading_inside_gets_an_id(self, boxes):
        expect(boxes.first.locator("h3")).to_have_id("inside-the-box")

    def test_reference_link_defined_outside_resolves(self, boxes):
        link = boxes.first.locator("a", has_text="reference link")
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
    """Closed unless `open` is passed; the summary toggles it by mouse and keyboard."""

    def test_closed_by_default(self, boxes):
        box = boxes.first
        expect(box).not_to_have_attribute("open", "")
        expect(box.locator("h3")).to_be_hidden()

    def test_open_param_starts_open(self, boxes):
        box = boxes.nth(1)
        expect(box).to_have_attribute("open", "")
        expect(box.locator("p")).to_be_visible()

    def test_click_toggles(self, boxes):
        box = boxes.first
        box.locator("summary").click()
        expect(box.locator("h3")).to_be_visible()
        box.locator("summary").click()
        expect(box.locator("h3")).to_be_hidden()

    def test_keyboard_toggles(self, page: Page, boxes):
        """2.1.1 (A): the summary is a Tab stop and Enter opens the box."""
        box = boxes.first
        box.locator("summary").focus()
        expect(box.locator("summary")).to_be_focused()
        page.keyboard.press("Enter")
        expect(box.locator("h3")).to_be_visible()


class TestStyle:
    """The box reads as a box, with its own disclosure marker."""

    def test_box_stands_out_from_the_page(self, page: Page, boxes):
        box_bg = boxes.first.evaluate("el => getComputedStyle(el).backgroundColor")
        page_bg = page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")
        assert box_bg != page_bg

    def test_default_marker_replaced(self, boxes):
        summary = boxes.first.locator("summary")
        assert summary.evaluate("el => getComputedStyle(el).listStyleType") == "none"
        marker = summary.evaluate("el => getComputedStyle(el, '::before').content")
        assert marker not in ("none", "normal")

    def test_marker_turns_when_opened(self, page: Page, boxes):
        page.emulate_media(reduced_motion="reduce")
        summary = boxes.first.locator("summary")
        closed = summary.evaluate("el => getComputedStyle(el, '::before').transform")
        summary.click()
        expect(boxes.first.locator("h3")).to_be_visible()
        opened = summary.evaluate("el => getComputedStyle(el, '::before').transform")
        assert closed != opened
