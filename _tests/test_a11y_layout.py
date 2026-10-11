"""Page layout for readers who scroll, zoom, set a larger default font or use a phone
(css_audit.md A6, A7, B4, B5).

Invariants:
  - the viewport, not `<body>`, is the page's scroll container, so `scroll-padding` applies
    to in-page jumps and focus scrolling;
  - following a footnote reference, following the footnote's back-link, loading a page at a
    `#fragment`, and moving keyboard focus onto a link near the top edge each leave the
    target below the sticky masthead and inside the viewport (WCAG 2.4.11 Focus Not
    Obscured, and the same reading for anchor targets), on a desktop and a phone viewport;
  - on a short viewport (landscape phone, high zoom) the masthead is not sticky, so once
    the reader scrolls it no longer covers the top of the content;
  - at 320 CSS px wide nothing scrolls the page sideways, and no content (element or run of
    text) is clipped out of reach: anything wider than the viewport sits in a box the
    reader can scroll sideways, and that box is in the Tab order. This holds with the
    sidebar open too. The display equation is such a box, and the arrow keys scroll it
    (1.4.10 Reflow);
  - the root font size is relative to the reader's browser default: it scales with that
    default and is never smaller than it (1.4.4 Resize Text, best practice);
  - every text input renders at 16px or more while focused, on a phone and a desktop
    width, so iOS Safari does not zoom the page when it takes focus.

Content comes from the designed build: the a11y demo preview has a footnote below the fold,
a heading followed by enough text to scroll it to the top, a link in a blockquote and a
display equation too wide for a phone. The other A7 pages are the designed build's listing,
tag, search and post pages.

Waiting: jumps and focus scrolling are read once the scroll position has held still for a
few animation frames (and web fonts and MathJax have finished), never after a fixed sleep.
The reader's default font size is set through Chromium's DevTools protocol
(`Page.setFontSizes`), the same setting as chrome://settings/fonts.
"""

import corpus
import pytest
from constants import SELECTORS
from playwright.sync_api import Locator, Page, expect

A11Y_DEMO = "2024-02-01-a11y-demo.md"
# The demo's "## Trailing" heading: twenty paragraphs follow it, so a jump to it can put it
# at the top of the viewport rather than being clamped by the end of the page.
TRAILING_HEADING = "#trailing"
# The demo's footnote reference, its back-link, and the first link after the reference.
FOOTNOTE_REF = "a.footnote"
FOOTNOTE_BACKLINK = "a.reversefootnote"
BLOCKQUOTE_LINK = ".post blockquote a"
DISPLAY_MATHS = 'mjx-container[display="true"]'

SIDEBAR_TOGGLE = SELECTORS["sidebar_toggle"]
SIDEBAR_SEARCH_INPUT = SELECTORS["search_input"]
# Local until constants.SELECTORS carries them.
MASTHEAD = ".masthead"
SEARCH_PAGE_INPUT = ".search-page-input"
PALETTE_INPUT = ".command-palette-input"

VIEWPORTS = {"desktop": {"width": 1280, "height": 720}, "phone": {"width": 375, "height": 667}}
# Below 30em tall, the height at which the masthead stops being sticky.
SHORT_VIEWPORT = {"width": 900, "height": 300}
# WCAG 1.4.10: content must reflow at 320 CSS px wide.
REFLOW_VIEWPORT = {"width": 320, "height": 640}

# A word in every designed title and a tag several designed posts carry, so the search and
# tag pages render results.
QUERY = corpus.DESIGNED[0].title.split()[0].lower()
TAG = corpus.DESIGNED[0].tags[0]
TAGGED_POST = max(corpus.DESIGNED, key=lambda post: len(post.tags)).filename

# iOS Safari zooms the page when a focused input's text is smaller than this.
IOS_NO_ZOOM_PX = 16
# The browser's default font size, and a larger one a reader might choose.
DEFAULT_FONT_PX = 16
LARGER_FONT_PX = 24

# Resolves once web fonts are in, MathJax (if the page loads it) has typeset, and every
# scroll position on the page has held still for three animation frames.
_SETTLE_JS = """
async () => {
  await document.fonts.ready;
  if (window.MathJax && MathJax.startup && MathJax.startup.promise) await MathJax.startup.promise;
  const frame = () => new Promise(r => requestAnimationFrame(r));
  const position = () => {
    const els = [document.scrollingElement, document.body, document.activeElement].filter(Boolean);
    return els.map(e => `${e.scrollLeft},${e.scrollTop}`).join(';');
  };
  let last = position(), still = 0;
  for (let i = 0; still < 3 && i < 600; i++) {
    await frame();
    const now = position();
    if (now === last) still++; else { still = 0; last = now; }
  }
}
"""

# Where the element and the masthead sit in the viewport, and which box scrolled.
_PLACEMENT_JS = """
(el, masthead) => {
  const r = el.getBoundingClientRect();
  const m = document.querySelector(masthead).getBoundingClientRect();
  return {
    top: r.top, bottom: r.bottom,
    mastheadTop: m.top, mastheadBottom: m.bottom,
    viewport: window.innerHeight,
    pageScroll: document.scrollingElement.scrollTop,
    bodyScroll: document.body.scrollTop,
  };
}
"""

# Visible content at least partly outside the viewport's width that the reader can't scroll
# to: it has no ancestor with sideways scrolling (overflow-x auto or scroll, and something to
# scroll). `overflow: hidden` doesn't count, which is how the old `<body>` clipped content.
# Elements and text are both checked: a long word or URL runs out of its paragraph without
# widening the paragraph's box, so only its text's own extent shows it. Each clipped subtree
# is reported once, at its outermost element. Also returned: every sideways-scrollable box
# that holds such content but is out of the Tab order (tabIndex < 0), and the content that
# did overflow into a scrollable box (`reachable`), so a caller can tell the sweep saw any.
_REFLOW_JS = """
() => {
  const vw = document.documentElement.clientWidth;
  const label = (el) => {
    const cls = typeof el.className === 'string' ? el.className.trim().split(/\\s+/).filter(Boolean) : [];
    return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + cls.map(c => '.' + c).join('');
  };
  // The nearest box from `start` outwards that the reader can scroll sideways, or null.
  const scroller = (start) => {
    for (let a = start; a && a !== document.documentElement; a = a.parentElement) {
      const ox = getComputedStyle(a).overflowX;
      if ((ox === 'auto' || ox === 'scroll') && a.scrollWidth > a.clientWidth) return a;
    }
    return null;
  };
  const outside = (r) => r.width > 1 && r.height > 1 && (r.left < -0.5 || r.right > vw + 0.5);
  const span = (r) => `x=${Math.round(r.left)}..${Math.round(r.right)}`;
  const clipped = [], unfocusable = [], reachable = [];
  const seen = new Set(), hidden = new Set(), shown = new Set([document.body]);
  const inBox = (box, what) => {
    reachable.push(what);
    if (box.tabIndex < 0 && !unfocusable.includes(label(box))) unfocusable.push(label(box));
  };
  for (const el of document.body.querySelectorAll('*')) {
    if (!el.checkVisibility({visibilityProperty: true})) continue;
    // Visually hidden subtrees (the sr-only pattern, MathJax's assistive MathML) are not shown to clip.
    const s = getComputedStyle(el);
    if (hidden.has(el.parentElement) || s.clip !== 'auto' || s.clipPath !== 'none') { hidden.add(el); continue; }
    shown.add(el);
    const r = el.getBoundingClientRect();
    if (!outside(r)) continue;
    const box = scroller(el.parentElement);
    if (box) { inBox(box, label(el)); continue; }
    if (!seen.has(el.parentElement)) clipped.push(`${label(el)} spans ${span(r)}`);
    seen.add(el);
  }
  const texts = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let t = texts.nextNode(); t; t = texts.nextNode()) {
    const parent = t.parentElement;
    if (!shown.has(parent) || seen.has(parent) || !/\\S/.test(t.data)) continue;
    const range = document.createRange();
    range.selectNodeContents(t);
    const r = range.getBoundingClientRect();
    if (!outside(r)) continue;
    const box = scroller(parent);
    if (box) { inBox(box, `text in ${label(parent)}`); continue; }
    clipped.push(`text "${t.data.trim().slice(0, 40)}" in ${label(parent)} spans ${span(r)}`);
  }
  const page = document.scrollingElement;
  return {
    viewport: vw, pageScrollWidth: page.scrollWidth, pageClientWidth: page.clientWidth,
    clipped, unfocusable, reachable,
  };
}
"""

# Resolves once the sidebar has finished opening: its checkbox is checked and no transition
# is still running on the sidebar, the page wrapper or the toggle.
_SIDEBAR_OPEN_JS = """
() => document.querySelector('#sidebar-checkbox').checked
  && ['.sidebar', '.wrap', '.sidebar-toggle'].every(sel => document.querySelector(sel).getAnimations().length === 0)
"""


def _settle(page: Page) -> None:
    page.evaluate(_SETTLE_JS)


def _demo_url(designed_site) -> str:
    return f"{designed_site.url}{designed_site.document(A11Y_DEMO)['url']}"


def _obscured(target: Locator, what: str) -> str | None:
    """Why `target` is hidden by the masthead or out of the viewport, or None if it is in clear view."""
    p = target.evaluate(_PLACEMENT_JS, MASTHEAD)
    # The band the masthead hides: from the top of the viewport to its bottom edge, while it is there.
    covered_to = p["mastheadBottom"] if p["mastheadTop"] <= 0 < p["mastheadBottom"] else 0.0
    if p["top"] >= covered_to - 0.5 and p["bottom"] <= p["viewport"] + 0.5:
        return None
    return (
        f"{what}: spans y={p['top']:.0f}..{p['bottom']:.0f}, masthead covers y=0..{covered_to:.0f}, "
        f"viewport is {p['viewport']}px tall (page scrollTop={p['pageScroll']}, body scrollTop={p['bodyScroll']})"
    )


def _font_px(locator: Locator) -> float:
    return locator.evaluate("el => parseFloat(getComputedStyle(el).fontSize)")


def _set_default_font_size(page: Page, px: int) -> None:
    """Set the reader's default font size, as chrome://settings/fonts does."""
    cdp = page.context.new_cdp_session(page)
    cdp.send("Page.setFontSizes", {"fontSizes": {"standard": px, "fixed": round(px * 13 / 16)}})
    cdp.detach()


def _assert_default_font_size(page: Page, px: int) -> None:
    """Setup check: the loaded page resolves `font-size: medium` (the browser default) to `px`."""
    medium = page.evaluate(
        "() => { const d = document.createElement('div'); d.style.fontSize = 'medium'; document.body.append(d);"
        " const v = parseFloat(getComputedStyle(d).fontSize); d.remove(); return v; }"
    )
    assert medium == px, f"Setup: the browser's default font size is {medium}px, not the {px}px set over CDP"


class TestAnchorTargetsClearOfMasthead:
    @pytest.mark.parametrize("viewport", VIEWPORTS.values(), ids=VIEWPORTS.keys())
    def test_footnote_round_trip_lands_below_masthead(self, page: Page, designed_site, viewport):
        """A6, WCAG 2.4.11: the footnote and, after its back-link, the reference land in clear view.

        Old CSS made `<body>` the scroll container, so `scroll-padding-top` never applied and
        the back-jump put the reference at y=0, under the 74px sticky masthead.
        """
        page.set_viewport_size(viewport)
        page.goto(_demo_url(designed_site))
        ref = page.locator(FOOTNOTE_REF)
        expect(ref).to_have_count(1)
        ref_id = ref.evaluate("a => a.parentElement.id")
        note_id = ref.evaluate("a => decodeURIComponent(a.hash.slice(1))")

        problems = []
        ref.click()
        expect(page.locator(":target")).to_have_id(note_id)
        _settle(page)
        problems.append(_obscured(page.locator(":target"), f"footnote #{note_id} after following the reference"))

        page.locator(f":target {FOOTNOTE_BACKLINK}").click()
        expect(page.locator(":target")).to_have_id(ref_id)
        _settle(page)
        problems.append(_obscured(page.locator(":target"), f"reference #{ref_id} after the footnote's back-link"))

        problems = [p for p in problems if p]
        assert not problems, f"In-page jumps hidden at {viewport['width']}x{viewport['height']}:\n  " + "\n  ".join(
            problems
        )

    @pytest.mark.parametrize("viewport", VIEWPORTS.values(), ids=VIEWPORTS.keys())
    def test_fragment_load_lands_below_masthead(self, page: Page, designed_site, viewport):
        """A6, WCAG 2.4.11: loading a page at `#heading` shows that heading below the masthead."""
        page.set_viewport_size(viewport)
        page.goto(f"{_demo_url(designed_site)}{TRAILING_HEADING}")
        heading = page.locator(TRAILING_HEADING)
        expect(heading).to_have_count(1)
        _settle(page)

        problem = _obscured(heading, f"heading {TRAILING_HEADING} loaded as the URL fragment")
        assert not problem, f"At {viewport['width']}x{viewport['height']}: {problem}"

    @pytest.mark.parametrize("viewport", VIEWPORTS.values(), ids=VIEWPORTS.keys())
    def test_keyboard_focus_not_hidden_under_masthead(self, page: Page, designed_site, viewport):
        """A6, WCAG 2.4.11: a link that takes keyboard focus while under the masthead is scrolled clear of it.

        The page is scrolled so the link sits 20px from the top, under the sticky masthead,
        and focus arrives by Tab from the link before it. With `scroll-padding-top` honoured,
        the browser treats the masthead's band as out of view and scrolls the link below it.
        """
        page.set_viewport_size(viewport)
        page.goto(_demo_url(designed_site))
        _settle(page)
        link = page.locator(BLOCKQUOTE_LINK)
        expect(link).to_have_count(1)

        # Scroll whichever box scrolls (the viewport, or a scrolling <body>) to put the link at y=20.
        link.evaluate(
            "el => { const dy = el.getBoundingClientRect().top - 20; window.scrollBy(0, dy); "
            "document.body.scrollBy(0, dy); }"
        )
        _settle(page)
        start = link.evaluate("el => el.getBoundingClientRect().top")
        assert abs(start - 20) < 2, f"Setup: could not scroll the link to y=20 (it is at y={start:.0f})"

        page.locator(FOOTNOTE_REF).evaluate("el => el.focus({preventScroll: true})")
        page.keyboard.press("Tab")
        expect(link).to_be_focused()
        _settle(page)

        problem = _obscured(link, "blockquote link after Tab")
        assert not problem, f"At {viewport['width']}x{viewport['height']}: {problem}"


class TestScrollContainer:
    def test_viewport_is_the_scroll_container(self, page: Page, designed_site):
        """A6: scrolling the page scrolls the viewport (document.scrollingElement), not `<body>`.

        `scroll-padding` and the browser's own scroll features act on the viewport; old CSS
        (`html, body { overflow-x: hidden; height: 100% }`) moved the scrolling into `<body>`.
        """
        page.goto(_demo_url(designed_site))
        page.mouse.move(640, 400)
        page.mouse.wheel(0, 800)
        page.wait_for_function("() => document.scrollingElement.scrollTop > 0 || document.body.scrollTop > 0")
        _settle(page)

        page_scroll, body_scroll = page.evaluate("() => [document.scrollingElement.scrollTop, document.body.scrollTop]")
        assert page_scroll > 0 and body_scroll == 0, (
            f"Scrolling moved the wrong box: document.scrollingElement.scrollTop={page_scroll}, "
            f"body.scrollTop={body_scroll}; the viewport should scroll and <body> should not"
        )

    def test_masthead_scrolls_away_on_short_viewport(self, page: Page, designed_site):
        """A6, WCAG 2.4.11 / 1.4.10: below 30em tall the masthead is not sticky.

        On a landscape phone or at high zoom a sticky 74px bar would hide a quarter of the
        viewport and anything focused beneath it; once the reader scrolls, it must be gone.
        """
        page.set_viewport_size(SHORT_VIEWPORT)
        page.goto(_demo_url(designed_site))
        masthead = page.locator(MASTHEAD)
        expect(masthead).to_be_visible()
        height = masthead.evaluate("el => el.getBoundingClientRect().height")

        page.mouse.move(SHORT_VIEWPORT["width"] / 2, SHORT_VIEWPORT["height"] / 2)
        page.mouse.wheel(0, 1000)
        page.wait_for_function("() => document.scrollingElement.scrollTop > 0 || document.body.scrollTop > 0")
        _settle(page)

        bottom, position = masthead.evaluate("el => [el.getBoundingClientRect().bottom, getComputedStyle(el).position]")
        assert bottom <= 0, (
            f"After scrolling, the masthead ({height:.0f}px, position: {position}) still covers "
            f"y=0..{bottom:.0f} of a {SHORT_VIEWPORT['height']}px-tall viewport"
        )


class TestReflow:
    def _pages(self, designed_site) -> list[tuple[str, str | None]]:
        """(path, selector that shows the page has rendered its content) for each page to check."""
        return [
            (designed_site.document(A11Y_DEMO)["url"], DISPLAY_MATHS),
            (designed_site.document(TAGGED_POST)["url"], ".post-title"),
            ("/", ".card"),
            ("/essays/", ".card"),
            ("/essays/all/", ".card"),
            ("/about/", None),
            (f"/tags/?t={TAG}", ".tag-post-item:visible"),
            (f"/search/?q={QUERY}", ".search-result-item"),
        ]

    @staticmethod
    def _sweep(page: Page, where: str) -> tuple[list[str], dict]:
        """Run the reflow sweep on the loaded page; return its failures, labelled with `where`, and its raw result."""
        found = page.evaluate(_REFLOW_JS)
        problems = []
        if found["pageScrollWidth"] > found["pageClientWidth"]:
            problems.append(
                f"{where}: page scrolls sideways (scrollWidth {found['pageScrollWidth']} > "
                f"{found['pageClientWidth']})"
            )
        problems += [f"{where}: clipped out of reach: {c}" for c in found["clipped"]]
        problems += [f"{where}: scrolls sideways but is not in the Tab order: {u}" for u in found["unfocusable"]]
        return problems, found

    def test_nothing_clipped_or_scrolling_sideways_at_320px(self, page: Page, designed_site):
        """A7 (and A6's fix), WCAG 1.4.10: at 320px wide, nothing scrolls the page sideways or is cut off out of reach.

        Old CSS hid the overflow on `<body>`: the page didn't scroll sideways, but the demo's
        display equation ran to x=444 with no way to scroll to the rest of it. The demo is
        swept again with the sidebar open, which slides in over the page: with `<body>` no
        longer hiding overflow, nothing it moves may push the page sideways either.
        """
        page.set_viewport_size(REFLOW_VIEWPORT)
        demo = designed_site.document(A11Y_DEMO)["url"]
        problems = []
        for path, ready in self._pages(designed_site):
            page.goto(f"{designed_site.url}{path}")
            if ready:
                expect(page.locator(ready).first).to_be_attached()
            _settle(page)
            found_here, found = self._sweep(page, path)
            problems += found_here
            if path == demo:
                # The equation overflows 320px on either build: clipped (old) or in its scroll box (fixed).
                assert found["clipped"] or found["reachable"], (
                    f"Setup: nothing on {path} is wider than {REFLOW_VIEWPORT['width']}px (its display "
                    "equation should be), so the sweep checks nothing"
                )
                page.locator(SIDEBAR_TOGGLE).click()
                page.wait_for_function(_SIDEBAR_OPEN_JS)
                _settle(page)
                problems += self._sweep(page, f"{path} (sidebar open)")[0]
        assert not problems, f"Reflow failures at {REFLOW_VIEWPORT['width']}px wide:\n  " + "\n  ".join(problems)

    def test_wide_equation_scrolls_in_its_own_box(self, page: Page, designed_site):
        """A7, WCAG 1.4.10 / 2.1.1: a display equation wider than a phone scrolls inside its own box, by keyboard too.

        Each display-maths container fits the viewport, has more to show than its width
        (otherwise the fixture no longer tests anything), scrolls sideways, is in the Tab
        order, and moves when the reader presses the right arrow key with it focused.
        """
        page.set_viewport_size(REFLOW_VIEWPORT)
        page.goto(_demo_url(designed_site))
        _settle(page)
        containers = page.locator(DISPLAY_MATHS)
        assert containers.count() > 0, "The a11y demo should render at least one display equation"

        problems = []
        for i in range(containers.count()):
            box = containers.nth(i)
            m = box.evaluate(
                "el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el); return {"
                "left: r.left, right: r.right, vw: document.documentElement.clientWidth, "
                "scrollWidth: el.scrollWidth, clientWidth: el.clientWidth, overflowX: s.overflowX, "
                "tabIndex: el.tabIndex, content: el.firstElementChild.getBoundingClientRect().width}; }"
            )
            name = f"display equation {i + 1}"
            assert m["content"] > m["vw"], (
                f"Setup: {name} is {m['content']:.0f}px wide, not wider than the {m['vw']}px viewport, "
                "so this test checks nothing"
            )
            if m["left"] < -0.5 or m["right"] > m["vw"] + 0.5:
                problems.append(f"{name}: its box spans x={m['left']:.0f}..{m['right']:.0f}, past the viewport")
            if m["overflowX"] not in ("auto", "scroll") or m["scrollWidth"] <= m["clientWidth"]:
                problems.append(
                    f"{name}: does not scroll sideways (overflow-x: {m['overflowX']}, "
                    f"scrollWidth {m['scrollWidth']}, clientWidth {m['clientWidth']}) though its content "
                    f"is {m['content']:.0f}px wide"
                )
            if m["tabIndex"] < 0:
                problems.append(f"{name}: not in the Tab order (tabIndex {m['tabIndex']})")

            box.focus()
            expect(box).to_be_focused()
            for _ in range(3):
                page.keyboard.press("ArrowRight")
            _settle(page)
            scrolled = box.evaluate("el => el.scrollLeft")
            if scrolled <= 0:
                problems.append(f"{name}: ArrowRight with it focused did not scroll it (scrollLeft {scrolled})")
        assert not problems, "Display maths at 320px:\n  " + "\n  ".join(problems)


@pytest.mark.only_browser("chromium")  # the default font size is set over Chromium's DevTools protocol
class TestReaderFontSize:
    @pytest.mark.parametrize("width", [375, 1280])
    def test_root_font_size_scales_with_reader_default(self, page: Page, designed_site, width: int):
        """B4, WCAG 1.4.4 (best practice): raising the browser's default font size raises the page's text in step.

        Old CSS set `html { font-size: 16px }` (20px at >= 38em), which ignores the default.
        The breakpoints are in em, so they move with the default too: 375px is narrower than
        38em, and 1280px wider, at both 16px and 24px, so each width keeps one layout and the
        ratio between the two readings must be exactly the ratio between the defaults.
        """
        page.set_viewport_size({"width": width, "height": 720})
        url = _demo_url(designed_site)
        sizes = {}
        for default in (DEFAULT_FONT_PX, LARGER_FONT_PX):
            _set_default_font_size(page, default)
            page.goto(url)
            _assert_default_font_size(page, default)
            paragraph = page.locator(".post p").first
            expect(paragraph).to_be_visible()
            sizes[default] = (_font_px(page.locator("html")), _font_px(paragraph))

        expected = LARGER_FONT_PX / DEFAULT_FONT_PX
        problems = []
        for i, what in enumerate(("root (html)", "body paragraph")):
            small, large = sizes[DEFAULT_FONT_PX][i], sizes[LARGER_FONT_PX][i]
            if abs(large / small - expected) > 0.01:
                problems.append(
                    f"{what}: {small}px at a {DEFAULT_FONT_PX}px default, {large}px at {LARGER_FONT_PX}px "
                    f"(x{large / small:.2f}, expected x{expected:.2f})"
                )
        assert not problems, f"At {width}px wide the text ignores the reader's default size:\n  " + "\n  ".join(
            problems
        )

    def test_root_font_size_never_below_reader_default(self, page: Page, designed_site):
        """B4, WCAG 1.4.4 (best practice): with a 24px default, the root size is never under 24px at any width.

        800px is the telling width: wider than 38em at a 16px default but narrower at 24px.
        Old CSS fell back to its 16px rule there, so a larger default made the text smaller.
        """
        _set_default_font_size(page, LARGER_FONT_PX)
        problems = []
        for width in (375, 800, 1280):
            page.set_viewport_size({"width": width, "height": 720})
            page.goto(_demo_url(designed_site))
            _assert_default_font_size(page, LARGER_FONT_PX)
            root = _font_px(page.locator("html"))
            if root < LARGER_FONT_PX:
                problems.append(f"{width}px wide: root font-size {root}px")
        assert not problems, f"Root font size below the reader's {LARGER_FONT_PX}px default:\n  " + "\n  ".join(
            problems
        )


class TestInputTextSize:
    @pytest.mark.parametrize("width", [375, 1280])
    def test_text_inputs_at_least_16px_when_focused(self, page: Page, designed_site, width: int):
        """B5: every text input is >= 16px while focused, so iOS Safari doesn't zoom the page on focus.

        Covers the sidebar search, the /search/ page input and the command palette, each
        measured as it holds focus, then sweeps every other text-entry field on the page.
        Old CSS set the sidebar input to .875rem (14px) on phones and .75rem (15px) on desktops.
        """
        page.set_viewport_size({"width": width, "height": 720})
        page.goto(f"{designed_site.url}/search/")
        measured = {}

        page.locator(SIDEBAR_TOGGLE).click()
        sidebar_input = page.locator(SIDEBAR_SEARCH_INPUT)
        expect(sidebar_input).to_be_visible()
        sidebar_input.focus()
        expect(sidebar_input).to_be_focused()
        measured["sidebar search (.search-input)"] = _font_px(sidebar_input)
        page.locator(SIDEBAR_TOGGLE).click()
        expect(sidebar_input).to_be_hidden()

        page_input = page.locator(SEARCH_PAGE_INPUT)
        page_input.focus()
        expect(page_input).to_be_focused()
        measured["search page (.search-page-input)"] = _font_px(page_input)

        page.keyboard.press("Control+k")
        palette_input = page.locator(PALETTE_INPUT)
        expect(palette_input).to_be_focused()
        measured["command palette (.command-palette-input)"] = _font_px(palette_input)

        others = page.evaluate(
            """(known) => Array.from(document.querySelectorAll(
                 'textarea, [contenteditable=""], [contenteditable="true"], input:not([type]), '
                 + 'input[type=text], input[type=search], input[type=email], input[type=url], '
                 + 'input[type=tel], input[type=password], input[type=number]'))
               .filter(el => !known.some(sel => el.matches(sel)))
               .map(el => [el.outerHTML.slice(0, 80), parseFloat(getComputedStyle(el).fontSize)])""",
            [SIDEBAR_SEARCH_INPUT, SEARCH_PAGE_INPUT, PALETTE_INPUT],
        )
        measured.update(dict(others))

        small = {name: px for name, px in measured.items() if px < IOS_NO_ZOOM_PX}
        assert not small, f"Text inputs under {IOS_NO_ZOOM_PX}px at {width}px wide (iOS zooms on focus): " + ", ".join(
            f"{name}: {px}px" for name, px in small.items()
        )
