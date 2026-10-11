"""Focus indicators and component boundaries (css_audit.md A8, A9), in both themes.

Invariants, measured as a reader meets them on the designed build:
  - every Tab stop shows a focus indicator: an outline, or a box-shadow ring, at least 2px
    wide and >= 3:1 against what it is painted over (WCAG 2.4.7, with 1.4.11's 3:1 for the
    indicator's colour), on an element inside the viewport (a ring on a control parked
    off-screen is a ring nobody sees). This holds on every kind of page, with the sidebar
    opened from the keyboard and in the command palette. A focus target that is hidden by
    design shows its focus on its visible face: the sidebar checkbox on the hamburger
    (`.sidebar-toggle`), the theme switch's input on its slider;
  - inside the command palette, whose panel clips its contents, a ring is also whole: the
    panel must not cut it away, on the input or on any result link, including the selected
    row, whose fill is the accent colour;
  - hover and keyboard focus look the same: every colour, border colour or underline that
    hovering an interactive element changes, on it or inside it, keyboard focus changes to
    the same value (2.4.7: a hover-only state tells a keyboard reader nothing);
  - the boundary that identifies a control (card, button, tag, input, result, the palette
    panel, the masthead rule) is >= 3:1 against what is behind it, drawn by its border or
    by its fill (1.4.11), and is drawn in one colour across controls;
  - decorative rules (hr, section dividers, table and list borders, chips) are visible:
    >= 1.3:1 against what is on either side of them. That is a consistency floor, not a
    WCAG minimum: 1.4.11 exempts decoration, but a rule drawn in the background colour
    (1.00:1) is a rule nobody can see.

What A8 and A9 found in the old CSS: `outline: none` on all three search inputs (the
palette's with nothing in its place) and no focus ring of the site's own, so links got
the browser's default `auto` ring, computed as `1px rgb(16, 16, 16)`. Chromium paints it
as a 2px #101010 band with a 1px white edge, which can be seen, so on pages with no
`outline: none` the old CSS fails the site-wide ring the audit introduced (a 2px solid
`--focus-ring`, >= 3:1), not 2.4.7's bare minimum. Also hover-only styling on
cards, post tags, the tag cloud, search page results and tags-page links;
`--border-color` equal to the dark background (1.00:1) and 1.08:1 in light,
`--sidebar-border-color` equal to the light background, and a 17:1 white border on cards.

Colours are composited as painted (a11y.py): through alpha, every background behind the
element and every ancestor's opacity. Transitions are waited out with
document.getAnimations(), never slept through. Pagination buttons share the "View all"
button's styles but render only when there are more posts than `paginate` (10); the
designed build has 3, so they are measured only where present (a `--scale-posts` run).
"""

import re

import a11y
import corpus
import pytest
from constants import SELECTORS
from playwright.sync_api import Locator, Page, expect

THEMES = ["dark", "light"]

A11Y_DEMO = "2024-02-01-a11y-demo.md"
# The designed post with the most tags: it shows several post tags and a related list.
TAGGED_POST = max(corpus.DESIGNED, key=lambda post: len(post.tags)).filename
# A word in every designed title, so search returns several results.
QUERY = corpus.DESIGNED[0].title.split()[0].lower()

# Local until constants.SELECTORS carries them.
SIDEBAR_CONTROL = "#sidebar-checkbox"
SIDEBAR = "#sidebar"
SIDEBAR_SEARCH = ".sidebar .search-input"
SIDEBAR_LINK = ".sidebar-nav-item"
PALETTE = ".command-palette"
PALETTE_PANEL = ".command-palette-panel"
PALETTE_INPUT = ".command-palette-input"
PALETTE_RESULT = ".command-palette-result"
PAGINATION_LINK = ":is(.pagination-prev, .pagination-next) a"

# Focus targets hidden by design, and the visible face that must show their focus.
FOCUS_FACES = {
    SIDEBAR_CONTROL: SELECTORS["sidebar_toggle"],  # a clipped 1px checkbox; its <label> is the hamburger
    SELECTORS["theme_toggle_input"]: ".toggle-slider",  # a 0x0 transparent input; the slider is the switch
}

FOCUS_RING_MIN_PX = 2.0  # the 2.4.13 (AAA) minimum thickness, which this site meets
RULE_MIN = 1.3  # consistency floor for decorative rules (see the module docstring)
MAX_TAB_STOPS = 60  # more than any designed page has; a walk that doesn't come round fails

SIDES = ("top", "right", "bottom", "left")
TOP, BOTTOM = ("top",), ("bottom",)

# An offset-free, blur-free box-shadow is a solid ring as wide as its spread.
SHADOW = re.compile(r"(rgba?\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px\s+([\d.]+)px\s+(-?[\d.]+)px(\s+inset)?")

_DESCRIBE_JS = """(n) => {
  const id = n.id ? '#' + n.id : '';
  const cls = typeof n.className === 'string' && n.className.trim()
    ? '.' + n.className.trim().split(/\\s+/).join('.') : '';
  const text = (n.getAttribute('aria-label') || n.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 30);
  return `<${n.tagName.toLowerCase()}${id}${cls}>` + (text ? ` "${text}"` : '');
}"""

# The focused element, the element that shows its focus (its face) and what the face paints
# round itself. Each element gets an id that is stable for the page load, so a walk can tell
# when focus has come back round; `matched` lists the `reach` selectors the element matches.
STOP_JS = f"""
([faces, reach]) => {{
  const el = document.activeElement;
  if (!el || el === document.body || el === document.documentElement) return null;
  const describe = {_DESCRIBE_JS};
  const ids = (window.__focusWalkIds = window.__focusWalkIds || new WeakMap());
  if (!ids.has(el)) ids.set(el, (window.__focusWalkCount = (window.__focusWalkCount || 0) + 1));
  const box = el.getBoundingClientRect();
  const invisible = (box.width < 2 && box.height < 2) || parseFloat(getComputedStyle(el).opacity) === 0;
  const entry = Object.entries(faces).find(([selector]) => el.matches(selector));
  const face = entry ? document.querySelector(entry[1]) : el;
  const shown = !!face && face.checkVisibility({{opacityProperty: true, visibilityProperty: true}});
  const s = shown ? getComputedStyle(face) : null;
  const r = shown ? face.getBoundingClientRect() : null;
  return {{
    id: ids.get(el),
    element: describe(el),
    face: entry ? entry[1] : null,
    invisible,
    shown,
    onscreen: !!r && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight,
    box: r && [r.left, r.top, r.right, r.bottom].map(Math.round),
    matched: reach.filter((selector) => el.matches(selector)),
    outline: s && {{style: s.outlineStyle, width: parseFloat(s.outlineWidth), colour: s.outlineColor,
                    offset: parseFloat(s.outlineOffset)}},
    shadow: s ? s.boxShadow : 'none',
    backdrop: shown ? ({a11y.BACKDROP_JS})(face) : null,
    fill: shown ? ({a11y.TEXT_COLOURS_JS})(face).bg : null,
  }};
}}
"""

# The properties a hover style changes, for the element and every element inside it. A side
# with no border paints nothing (its colour only follows `color`), so it reads as 'none'.
STATE_JS = f"""
(el) => {{
  const describe = {_DESCRIBE_JS};
  return [el, ...el.querySelectorAll('*')].map((n) => {{
    const s = getComputedStyle(n);
    const values = {{
      'background-color': s.backgroundColor, 'color': s.color, 'text-decoration-line': s.textDecorationLine,
    }};
    for (const side of ['top', 'right', 'bottom', 'left']) {{
      const key = side[0].toUpperCase() + side.slice(1);
      const drawn = s[`border${{key}}Style`] !== 'none' && parseFloat(s[`border${{key}}Width`]) > 0;
      values[`border-${{side}}-color`] = drawn ? s[`border${{key}}Color`] : 'none';
    }}
    return {{node: describe(n), values}};
  }});
}}
"""

# Ancestors that clip the focused element's outline, and on which sides: each ancestor that
# doesn't let overflow show, whose padding box the ring's outer edge crosses.
RING_CLIP_JS = f"""
(el) => {{
  const describe = {_DESCRIBE_JS};
  const s = getComputedStyle(el);
  const grow = Math.max(0, parseFloat(s.outlineOffset) + parseFloat(s.outlineWidth));
  const r = el.getBoundingClientRect();
  const ring = {{top: r.top - grow, left: r.left - grow, bottom: r.bottom + grow, right: r.right + grow}};
  const cut = [];
  for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {{
    const as = getComputedStyle(a);
    if (as.overflowX === 'visible' && as.overflowY === 'visible') continue;
    const b = a.getBoundingClientRect();
    const box = {{
      top: b.top + parseFloat(as.borderTopWidth), left: b.left + parseFloat(as.borderLeftWidth),
      bottom: b.bottom - parseFloat(as.borderBottomWidth), right: b.right - parseFloat(as.borderRightWidth),
    }};
    const sides = [];
    if (ring.top < box.top - 0.5) sides.push('top');
    if (ring.right > box.right + 0.5) sides.push('right');
    if (ring.bottom > box.bottom + 0.5) sides.push('bottom');
    if (ring.left < box.left - 0.5) sides.push('left');
    if (sides.length) cut.push(`${{describe(a)}} (overflow ${{as.overflow}}) cuts it on the ${{sides.join('/')}}`);
  }}
  return cut;
}}
"""

# Each border side's paint, the element's own fill and the backdrop behind it, composited.
EDGES_JS = f"""
(el) => {{
  const s = getComputedStyle(el);
  const side = (name) => {{
    const key = name[0].toUpperCase() + name.slice(1);
    return {{
      style: s[`border${{key}}Style`], width: parseFloat(s[`border${{key}}Width`]), colour: s[`border${{key}}Color`],
    }};
  }};
  return {{
    element: ({_DESCRIBE_JS})(el),
    selected: el.matches('.selected, [aria-pressed="true"], [aria-selected="true"]'),
    sides: Object.fromEntries(['top', 'right', 'bottom', 'left'].map((n) => [n, side(n)])),
    backdrop: ({a11y.BACKDROP_JS})(el),
    fill: ({a11y.TEXT_COLOURS_JS})(el).bg,
  }};
}}
"""


# =============================================================================
# Helpers
# =============================================================================


def _rgb(colour: list) -> str:
    return f"rgb({', '.join(str(round(c)) for c in colour[:3])})"


def _over(css_colour: str, under: list) -> list:
    """A computed colour composited over the opaque `under`."""
    r, g, b, a = a11y.parse_rgb(css_colour)
    return [a * c + (1 - a) * u for c, u in zip((r, g, b), under)]


def _fold_sides(by_side: dict[str, tuple]) -> list[tuple[str, tuple]]:
    """Group border sides that measured the same, so a report says "all sides" once rather than four times."""
    groups: dict[tuple, list[str]] = {}
    for side, measured in by_side.items():
        groups.setdefault(measured, []).append(side)
    return [("all sides" if len(sides) == 4 else "/".join(sides), measured) for measured, sides in groups.items()]


def _use_theme(page: Page, theme: str) -> None:
    """Store `theme` as the reader's choice before any page loads."""
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")


def _goto(page: Page, url: str, theme: str, ready: str) -> None:
    """Load url, confirm the stored theme is the one shown and wait for `ready` to render."""
    page.goto(url)
    expect(page.locator(SELECTORS["html"])).to_have_attribute("data-theme", theme)
    expect(page.locator(ready).first).to_be_visible()
    _settle(page)


def _settle(page: Page) -> None:
    """Wait until no CSS transition or animation is running, so computed styles are final."""
    page.wait_for_function("() => document.getAnimations().length === 0")


def _rest(page: Page) -> None:
    """Nothing hovered or focused: the mouse parked in the empty bottom-right margin, focus dropped."""
    viewport = page.viewport_size
    page.mouse.move(viewport["width"] - 1, viewport["height"] - 1)
    page.evaluate("() => document.activeElement && document.activeElement.blur()")
    _settle(page)


def _keyboard_focus(page: Page, target: Locator) -> None:
    """Focus target as keyboard navigation does, so :focus-visible styles apply."""
    page.keyboard.press("Shift")  # the last input is a key press, so focusing now counts as keyboard focus
    target.focus()
    assert target.evaluate("el => el.matches(':focus-visible')"), "harness: target should match :focus-visible"
    _settle(page)


def _open_palette(page: Page) -> None:
    page.keyboard.press("Control+k")
    expect(page.locator(PALETTE)).to_be_visible()
    expect(page.locator(PALETTE_INPUT)).to_be_focused()
    _settle(page)


def _stop(page: Page, reach: list[str]) -> dict | None:
    return page.evaluate(STOP_JS, [FOCUS_FACES, reach])


def _tab_to(page: Page, selector: str) -> bool:
    """Press Tab until an element matching selector has focus (True), or focus comes round without one."""
    first = None
    for _ in range(MAX_TAB_STOPS):
        page.keyboard.press("Tab")
        stop = _stop(page, [selector])
        if stop is None:
            continue  # focus is in the browser UI, between the last stop and the first
        if stop["matched"]:
            return True
        if first is None:
            first = stop["id"]
        elif stop["id"] == first:
            return False
    return False


def _open_sidebar_from_keyboard(page: Page) -> tuple[str, bool]:
    """Open the sidebar as a keyboard reader does (Tab to its control, Space): (how it was opened, by keyboard).

    Reaching the control is A1's invariant (test_a11y_keyboard.py). Where it can't be reached,
    the sidebar is opened with the mouse instead, so this file still measures what is inside it.
    """
    if _tab_to(page, SIDEBAR_CONTROL):
        page.keyboard.press("Space")
        how, by_keyboard = "opened from the keyboard", True
    else:
        page.locator(SELECTORS["sidebar_toggle"]).click()
        how, by_keyboard = "opened with the mouse (its control is not in the tab order: A1)", False
    expect(page.locator(SIDEBAR)).to_be_visible()
    _settle(page)
    return how, by_keyboard


# =============================================================================
# A8: focus indicators
# =============================================================================


def _rings(stop: dict) -> list[tuple[str, float, str, float]]:
    """(description, width, colour, offset) of each ring the site paints round the face.

    The offset is where the ring starts, outward from the border edge: outline-offset for an
    outline, 0 for an outset box-shadow ring and minus its spread for an inset one. An
    `outline-style: auto` ring is the browser's own, painted however the browser chooses, so
    it isn't one of the site's rings (see _indicator_problem).
    """
    rings = []
    outline = stop["outline"]
    if outline["style"] not in ("none", "hidden", "auto") and outline["width"] > 0:
        what = f"outline {outline['style']} {outline['width']:g}px {outline['colour']}"
        rings.append((what, outline["width"], outline["colour"], outline["offset"]))
    for colour, x, y, blur, spread, inset in SHADOW.findall(stop["shadow"]):
        if float(x) == float(y) == float(blur) == 0 and float(spread) > 0:
            width = float(spread)
            rings.append((f"box-shadow ring {width:g}px {colour}{inset}", width, colour, -width if inset else 0.0))
    return rings


def _ring_contrast(stop: dict, colour: str, width: float, offset: float) -> tuple[float, str]:
    """The ring's worst contrast with what it is painted over, and what that is.

    The part outside the border edge is painted over the backdrop, the part inside over the
    face's own fill (the palette input's ring is inset so its panel can't clip it).
    """
    grounds = []
    if offset + width > 0:
        grounds.append(("backdrop", stop["backdrop"]))
    if offset < 0:
        grounds.append(("own fill", stop["fill"]))
    return min((a11y.contrast(_over(colour, ground), ground), f"{name} {_rgb(ground)}") for name, ground in grounds)


def _indicator_problem(stop: dict) -> str | None:
    """Why this Tab stop shows no visible focus indicator, or None if it shows one."""
    if stop["invisible"] and not stop["face"]:
        return "the focused element is invisible and nothing else shows its focus"
    if not stop["shown"]:
        return f"its focus is shown on {stop['face']}, which is not visible"
    if not stop["onscreen"]:
        # Focus scrolls its target into view, so this is a control nobody can see: in a closed sidebar, say.
        what = stop["face"] or "it"
        return f"{what} is outside the viewport (box {stop['box']}), so its focus indicator can't be seen"
    rings = _rings(stop)
    outline = stop["outline"]
    if not rings and outline["style"] == "auto":
        # Chromium paints `auto 1px rgb(16, 16, 16)` as a 2px #101010 band with a 1px white edge: visible on
        # light pages, mostly not on dark ones. Its computed style says neither, so it isn't measured; the
        # site's own ring (A8's fix: one 2px --focus-ring outline) is what this walk requires.
        return (
            f"only the browser's default ring (outline auto, computed {outline['width']:g}px {outline['colour']}): "
            "the site draws no focus ring of its own"
        )
    if not rings:
        return (
            f"no focus indicator (outline: {outline['style']} {outline['width']:g}px {outline['colour']}; "
            f"box-shadow: {stop['shadow']})"
        )
    reasons = []
    for what, width, colour, offset in rings:
        faults = []
        if width < FOCUS_RING_MIN_PX:
            faults.append(f"{width:g}px wide, needs >= {FOCUS_RING_MIN_PX:g}px")
        ratio, ground = _ring_contrast(stop, colour, width, offset)
        if ratio < a11y.NON_TEXT_MIN:
            faults.append(f"{ratio:.2f}:1 against its {ground}, needs >= {a11y.NON_TEXT_MIN:g}:1")
        if not faults:
            return None
        reasons.append(f"{what}: {', '.join(faults)}")
    return "; ".join(reasons)


def _walk(page: Page, where: str, reach: list[str], from_current: bool = False) -> tuple[list[dict], list[str]]:
    """Tab once round the page, measuring every stop's focus indicator: (stops, offenders).

    The walk ends when focus comes back to its first stop. With from_current, the element
    focused now is the first stop; otherwise the first Tab press finds it.
    """
    stops, offenders, first = [], [], None
    for press in range(MAX_TAB_STOPS + 1):
        if press or not from_current:
            page.keyboard.press("Tab")
        _settle(page)
        stop = _stop(page, reach)
        if stop is None:
            continue  # focus is in the browser UI, between the last stop and the first
        if first is None:
            first = stop["id"]
        elif stop["id"] == first:
            return stops, offenders
        stops.append(stop)
        problem = _indicator_problem(stop)
        if problem:
            face = f" (focus shown on {stop['face']})" if stop["face"] else ""
            offenders.append(f"{stop['element']}{face}: {problem}")
    visited = "\n  ".join(stop["element"] for stop in stops)
    pytest.fail(f"{where}: focus never came back round to the first stop in {MAX_TAB_STOPS} Tabs:\n  {visited}")


def _check_walk(stops: list[dict], offenders: list[str], reach: list[str], where: str) -> None:
    """Fail if the walk missed an element it must reach, then if any stop showed no indicator."""
    missed = [selector for selector in reach if not any(selector in stop["matched"] for stop in stops)]
    visited = "\n  ".join(stop["element"] for stop in stops)
    assert not missed, f"{where}: the Tab walk never reached {missed}, so it can't vouch for them. Stops:\n  {visited}"
    assert not offenders, (
        f"{where}: {len(offenders)} of {len(stops)} Tab stops lack the site's visible focus indicator (WCAG 2.4.7: "
        f"an outline or box-shadow ring >= {FOCUS_RING_MIN_PX:g}px wide and >= {a11y.NON_TEXT_MIN:g}:1 against what "
        "it is painted over, on screen):\n  " + "\n  ".join(offenders)
    )


WALK_PAGES = ["home", "essays", "archive", "about", "contact", "tags", "search", "a11y demo", "post"]


def _walk_page(site, label: str) -> tuple[str, str, list[str]]:
    """(path, selector that shows the page is ready, selectors the walk must reach) for a page."""
    demo = site.document(A11Y_DEMO)
    post = site.document(TAGGED_POST)
    return {
        "home": ("/", SELECTORS["card"], [SELECTORS["card_link"], SELECTORS["view_all_link"]]),
        "essays": ("/essays/", SELECTORS["card"], [SELECTORS["card_link"], SELECTORS["view_all_link"]]),
        "archive": ("/essays/all/", SELECTORS["card"], [SELECTORS["card_link"]]),
        "about": ("/about/", ".page-title", [".page a"]),
        "contact": ("/contact/", ".page-title", [".page a"]),
        "tags": (f"/tags/?t={demo['tags'][0]}", ".tag-post-item:visible", [".tag-cloud-item", ".tag-post-item a"]),
        "search": (
            f"/search/?q={QUERY}",
            ".search-page-results .search-result-item",
            [".search-page-input", ".search-page-results .search-result-item"],
        ),
        "a11y demo": (
            demo["url"],
            'mjx-container[display="true"]',
            [".post-tag", "a.footnote", "blockquote a", 'mjx-container[display="true"]', ".related a"],
        ),
        "post": (post["url"], ".related", [".post-tag", ".related a"]),
    }[label]


@pytest.mark.parametrize("label", WALK_PAGES)
@pytest.mark.parametrize("theme", THEMES)
def test_tab_walk_shows_focus_indicator(page: Page, designed_site, theme: str, label: str):
    """A8 (WCAG 2.4.7): Tab once round each kind of page; every stop shows a visible focus indicator.

    Generic on purpose: an `outline: none` without a replacement, a link left with the
    browser's default `auto` ring instead of the site's, or a focus target parked off-screen,
    is caught wherever it appears. The old CSS failed the first two ways: the search page's
    input had `outline: none` and every link fell back to the default ring.
    """
    path, ready, reach = _walk_page(designed_site, label)
    _use_theme(page, theme)
    _goto(page, f"{designed_site.url}{path}", theme, ready)

    where = f"{theme} {label} {path}"
    stops, offenders = _walk(page, where, reach)

    _check_walk(stops, offenders, reach, where)


@pytest.mark.parametrize("theme", THEMES)
def test_tab_walk_with_sidebar_open(page: Page, designed_site, theme: str):
    """A8 (WCAG 2.4.7): with the sidebar opened from the keyboard, every Tab stop shows a focus indicator.

    The walk starts on the sidebar control itself, ringed on the hamburger while the menu is
    open, then goes through the theme switch (ringed on its slider), the sidebar's search
    input, its links and on into the page. The old sidebar search input had `outline: none`.
    Opened from the keyboard, the control must be one of the stops, so its open-state ring is
    measured rather than assumed.
    """
    reach = [SELECTORS["theme_toggle_input"], SIDEBAR_SEARCH, SIDEBAR_LINK]
    _use_theme(page, theme)
    _goto(page, f"{designed_site.url}/", theme, SELECTORS["card"])
    how, by_keyboard = _open_sidebar_from_keyboard(page)
    if by_keyboard:
        reach.append(SIDEBAR_CONTROL)

    where = f"{theme} home, sidebar {how}"
    stops, offenders = _walk(page, where, reach, from_current=True)

    _check_walk(stops, offenders, reach, where)


@pytest.mark.parametrize("theme", THEMES)
def test_command_palette_input_shows_focus_indicator(page: Page, designed_site, theme: str):
    """A8 (WCAG 2.4.7): Ctrl+K focuses the palette's input, and it shows a whole, visible focus indicator.

    The old palette input had `outline: none` and nothing in its place, so the dialog opened
    with no sign of where typing would go. The input fills a panel that clips its contents
    (`overflow: hidden`), so a ring drawn outside the input would be cut away: it must be
    inset (`outline-offset: -2px`), and is measured against the input's own fill.
    """
    _use_theme(page, theme)
    _goto(page, f"{designed_site.url}/", theme, SELECTORS["card"])
    _open_palette(page)

    stop = _stop(page, [PALETTE_INPUT])
    assert stop and stop["matched"], f"harness: Ctrl+K should focus {PALETTE_INPUT}, focus is on {stop}"
    problem = _indicator_problem(stop)
    assert problem is None, f"{theme} command palette: {stop['element']} has no visible focus indicator: {problem}"

    cut = page.locator(PALETTE_INPUT).evaluate(RING_CLIP_JS)
    assert not cut, f"{theme} command palette: the focus ring on {stop['element']} is clipped: {'; '.join(cut)}"


@pytest.mark.parametrize("theme", THEMES)
def test_tab_walk_in_command_palette(page: Page, designed_site, theme: str):
    """A8 (WCAG 2.4.7): with the palette showing results, every Tab stop inside it shows a whole focus indicator.

    Tab from the input moves through the result links. Each stop is held to the input's
    standard: a ring >= 2px wide, >= 3:1 against what it is painted over, and not cut away
    by the panel, which clips its contents. The walk ends when focus leaves the palette (it
    doesn't trap focus, which is outside A8) or comes back round to the input.

    The first fix gave only the input an inset ring: the result links kept the global
    outset ring, which the panel cut on every row, drawn in --focus-ring, the colour of the
    selected row's fill (1.00:1 there).
    """
    _use_theme(page, theme)
    _goto(page, f"{designed_site.url}/", theme, SELECTORS["card"])
    _open_palette(page)
    page.keyboard.type(QUERY)
    results = page.locator(PALETTE_RESULT)
    expect(results.first).to_be_visible()  # the search index loads on first open
    _settle(page)

    where = f"{theme} command palette, {results.count()} results for {QUERY!r}"
    stops, offenders = [], []
    for _ in range(MAX_TAB_STOPS):
        stop = _stop(page, [f"{PALETTE} *", PALETTE_INPUT, PALETTE_RESULT])
        if stop is None or not stop["matched"] or (stops and stop["id"] == stops[0]["id"]):
            break  # focus left the palette, or came back round to its first stop
        stops.append(stop)
        problems = [problem for problem in [_indicator_problem(stop)] if problem]
        problems += page.evaluate(f"() => ({RING_CLIP_JS})(document.activeElement)")
        if problems:
            offenders.append(f"{stop['element']}: {'; '.join(problems)}")
        page.keyboard.press("Tab")
        _settle(page)

    visited = "\n  ".join(stop["element"] for stop in stops)
    reached = sum(PALETTE_RESULT in stop["matched"] for stop in stops)
    assert stops and PALETTE_INPUT in stops[0]["matched"], f"{where}: the walk should start on {PALETTE_INPUT}"
    assert reached == results.count(), f"{where}: Tab reached {reached} of the results. Stops:\n  {visited}"
    assert not offenders, (
        f"{where}: {len(offenders)} of {len(stops)} Tab stops show no whole, visible focus indicator "
        "(WCAG 2.4.7):\n  " + "\n  ".join(offenders)
    )


# =============================================================================
# A8: hover and focus parity
# =============================================================================


def _hover_components(site) -> list[tuple[str, str, str, bool, bool]]:
    """(label, path, selector, in the sidebar, required) for each interactive element with hover styling.

    `.card-tag` has hover styling too, but no template renders it. Pagination renders only
    with more than `paginate` posts, so it is measured where present.
    """
    post = site.document(TAGGED_POST)
    tag = site.document(A11Y_DEMO)["tags"][0]
    return [
        ("card", "/", SELECTORS["card_link"], False, True),
        ("view all", "/", SELECTORS["view_all_link"], False, True),
        ("post tag", post["url"], ".post-tag", False, True),
        ("tag cloud", f"/tags/?t={tag}", ".tag-cloud-item", False, True),
        ("tags-page post link", f"/tags/?t={tag}", ".tag-post-item a", False, True),
        ("search result", f"/search/?q={QUERY}", ".search-page-results .search-result-item", False, True),
        ("masthead link", "/", ".masthead-title a", False, True),
        ("sidebar link", "/", SIDEBAR_LINK, True, True),
        ("pagination", "/essays/all/", PAGINATION_LINK, False, False),
    ]


def _state(item: Locator) -> list[dict]:
    return item.evaluate(STATE_JS)


def _missed_by_focus(diffs: dict[str, tuple[str, str, str]]) -> str:
    """The hover changes ({prop: (rest, hovered, focused)}) that focus doesn't make, as one line."""
    missed = {prop: values for prop, values in diffs.items() if values[2] != values[1]}
    borders = {prop[len("border-") : -len("-color")]: v for prop, v in missed.items() if prop.startswith("border-")}
    parts = [(prop, v) for prop, v in missed.items() if not prop.startswith("border-")]
    parts += [(f"border-color ({sides})", v) for sides, v in _fold_sides(borders)]
    return "; ".join(
        f"{prop} {rest} at rest, {hover} hovered, but {focus} focused" for prop, (rest, hover, focus) in parts
    )


@pytest.mark.parametrize("theme", THEMES)
def test_hover_styles_have_focus_twins(page: Page, designed_site, theme: str):
    """A8 (WCAG 2.4.7): whatever hovering changes on an interactive element, keyboard focus changes too.

    Each element is measured at rest, hovered, then focused from the keyboard with the mouse
    away. Every background, text colour, border colour or underline that hover changes on
    the element or anything inside it must take the same value under focus. The old CSS
    styled cards, post tags, the tag cloud, search-page results and tags-page links on
    :hover only.
    """
    _use_theme(page, theme)
    offenders, changed = [], set()
    for label, path, selector, in_sidebar, required in _hover_components(designed_site):
        _goto(page, f"{designed_site.url}{path}", theme, ".content")
        if in_sidebar:
            page.locator(SELECTORS["sidebar_toggle"]).click()
            expect(page.locator(SIDEBAR)).to_be_visible()
        items = page.locator(selector).filter(visible=True)
        if required:
            expect(items.first).to_be_visible()  # search results and the tag filter render after load
        for i in range(items.count()):
            item = items.nth(i)
            where = f"{theme} {label} #{i + 1} {path}"
            _rest(page)
            rest = _state(item)
            item.hover()
            _settle(page)
            hovered = _state(item)
            _rest(page)
            _keyboard_focus(page, item)
            focused = _state(item)
            for before, hover, focus in zip(rest, hovered, focused):
                diffs = {
                    prop: (value, hover["values"][prop], focus["values"][prop])
                    for prop, value in before["values"].items()
                    if hover["values"][prop] != value
                }
                if diffs:
                    changed.add(label)
                missed = _missed_by_focus(diffs)
                if missed:
                    offenders.append(f"{where}: {before['node']}: {missed}")

    required = [label for label, *_, needed in _hover_components(designed_site) if needed]
    missing = [label for label in required if label not in changed]
    assert not missing, f"hovering changed nothing on {missing}: the pages didn't render them, or hover styling is gone"
    report = "\n  ".join(offenders)
    header = f"{len(offenders)} elements change on hover but not under keyboard focus (WCAG 2.4.7)"
    assert not offenders, f"{header}:\n  {report}"


# =============================================================================
# A9: boundaries and rules
# =============================================================================


def _edges(locator: Locator, sides: tuple[str, ...]) -> dict:
    """The element's paint, with `drawn`: each named side that has a visible border, and its contrast."""
    edges = locator.evaluate(EDGES_JS)
    backdrop, fill = edges["backdrop"], edges["fill"]
    edges["drawn"] = {
        side: (paint["colour"], a11y.contrast(_over(paint["colour"], backdrop), backdrop))
        for side, paint in edges["sides"].items()
        if side in sides and paint["style"] not in ("none", "hidden") and paint["width"] > 0
    }
    edges["fill_ratio"] = a11y.contrast(fill, backdrop)
    return edges


def _describe_edges(edges: dict) -> str:
    borders = ", ".join(f"{sides} {colour} {ratio:.2f}:1" for sides, (colour, ratio) in _fold_sides(edges["drawn"]))
    return (
        f"border {borders or 'none'}; fill {_rgb(edges['fill'])} {edges['fill_ratio']:.2f}:1; "
        f"against backdrop {_rgb(edges['backdrop'])}"
    )


def _boundary_pages(site) -> list[tuple[str, str, str, bool, list[tuple[str, tuple[str, ...], bool]]]]:
    """(label, path, ready selector, palette open, [(control selector, sides, required)])."""
    post = site.document(TAGGED_POST)
    tag = site.document(A11Y_DEMO)["tags"][0]
    return [
        (
            "home",
            "/",
            SELECTORS["card"],
            False,
            [(SELECTORS["card"], SIDES, True), (SELECTORS["view_all_link"], SIDES, True), (".masthead", BOTTOM, True)],
        ),
        ("essays", "/essays/", SELECTORS["card"], False, [(SELECTORS["view_all_link"], SIDES, True)]),
        ("archive", "/essays/all/", SELECTORS["card"], False, [(PAGINATION_LINK, SIDES, False)]),
        ("post", post["url"], ".post-tag", False, [(".post-tag", SIDES, True)]),
        ("tags", f"/tags/?t={tag}", ".tag-cloud-item", False, [(".tag-cloud-item", SIDES, True)]),
        (
            "search",
            f"/search/?q={QUERY}",
            ".search-page-results .search-result-item",
            False,
            [(".search-page-input", SIDES, True), (".search-page-results .search-result-item", SIDES, True)],
        ),
        ("command palette", "/", SELECTORS["card"], True, [(PALETTE_PANEL, SIDES, True)]),
    ]


def _measure_boundaries(page: Page, site, theme: str) -> tuple[list[tuple[str, str, dict]], list[str]]:
    """[(where, selector, edges)] for every control in its resting state, and the required ones not found."""
    measured, missing = [], []
    for label, path, ready, palette, controls in _boundary_pages(site):
        _goto(page, f"{site.url}{path}", theme, ready)
        if palette:
            _open_palette(page)
        _rest(page)
        for selector, sides, required in controls:
            found = [_edges(item, sides) for item in page.locator(selector).filter(visible=True).all()]
            if required and not found:
                missing.append(f"{selector} on {path}")
            measured += [(f"{theme} {label} {path}", selector, edges) for edges in found]
    return measured, missing


@pytest.mark.parametrize("theme", THEMES)
def test_control_boundaries_contrast(page: Page, designed_site, theme: str):
    """A9 (WCAG 1.4.11): the edge that identifies each control is >= 3:1 against what is behind it.

    Cards, the "View all" button, post tags, the tag cloud, the search page's input and
    results, the command palette's panel and the masthead's bottom rule. The edge can be the
    border or the control's own fill: whichever contrasts more with the backdrop (the palette
    panel, in light, stands out from the dimmed page by its fill). The old `--border-color`
    was the dark background itself (1.00:1) and 1.08:1 in light, and the old tags and
    buttons had no fill to fall back on.
    """
    _use_theme(page, theme)
    measured, missing = _measure_boundaries(page, designed_site, theme)

    assert not missing, f"controls the test must measure were not rendered: {missing}"
    offenders = []
    for where, selector, edges in measured:
        border = min((ratio for _, ratio in edges["drawn"].values()), default=1.0)
        edge = max(border, edges["fill_ratio"])
        if edge < a11y.NON_TEXT_MIN:
            offenders.append(
                f"{where}: {selector} {edges['element']}: edge {edge:.2f}:1 < {a11y.NON_TEXT_MIN:g}:1 "
                f"({_describe_edges(edges)})"
            )
    report = "\n  ".join(offenders)
    assert not offenders, f"{len(offenders)} control boundaries below WCAG 1.4.11's minimum:\n  {report}"


@pytest.mark.parametrize("theme", THEMES)
def test_control_boundaries_share_one_colour(page: Page, designed_site, theme: str):
    """A9, B2 (consistency): every control's resting border is drawn in one colour.

    The audit split borders into two tokens: `--control-border` for boundaries that identify
    controls and `--rule-color` for decoration. The old CSS drew control borders in three
    unrelated colours per theme: the header colour on cards, the masthead and the search
    page's input and results (a 17:1 white in dark), the invisible `--border-color` on
    buttons and tags, and the sidebar's cream on the palette. A selected tag is a state, not
    a resting border, so it is left out.
    """
    _use_theme(page, theme)
    measured, missing = _measure_boundaries(page, designed_site, theme)
    assert not missing, f"controls the test must measure were not rendered: {missing}"

    colours: dict[str, list[str]] = {}
    for where, selector, edges in measured:
        if edges["selected"]:
            continue
        for colour, _ in edges["drawn"].values():
            colours.setdefault(colour, []).append(f"{selector} ({where})")
    assert colours, "no control borders were measured"

    groups = "\n  ".join(f"{colour}: {', '.join(sorted(set(where)))}" for colour, where in colours.items())
    assert len(colours) == 1, f"{theme}: control borders are drawn in {len(colours)} colours, expected one:\n  {groups}"


def _rule_pages(site) -> list[tuple[str, str, str, bool, list[tuple[str, tuple[str, ...], bool]]]]:
    """(label, path, ready selector, palette open, [(rule selector, sides, required)])."""
    demo = site.document(A11Y_DEMO)
    post = site.document(TAGGED_POST)
    tag = demo["tags"][0]
    post_navs = ".related, .backlinks, .series"
    return [
        (
            "a11y demo",
            demo["url"],
            'mjx-container[display="true"]',
            False,
            # The table's outline is drawn by its cells' collapsed borders (border-collapse).
            [("hr", TOP, True), ("td, th", SIDES, True), (post_navs, TOP, False)],
        ),
        ("home", "/", SELECTORS["card"], False, [(".home-intro", BOTTOM, True)]),
        ("post", post["url"], ".related", False, [(post_navs, TOP, True)]),
        (
            "tags",
            f"/tags/?t={tag}",
            ".tag-post-item:visible",
            False,
            [(".tag-posts-container", TOP, True), (".tag-post-item", BOTTOM, True)],
        ),
        ("search", f"/search/?q={QUERY}", ".search-result-tag", False, [(".search-result-tag", SIDES, True)]),
        ("archive", "/essays/all/", SELECTORS["card"], False, [(".pagination", TOP, False)]),
        ("command palette", "/", SELECTORS["card"], True, [(PALETTE_INPUT, BOTTOM, True)]),
    ]


@pytest.mark.parametrize("theme", THEMES)
def test_decorative_rules_visible(page: Page, designed_site, theme: str):
    """A9 (consistency floor, not a WCAG minimum): every decorative rule is >= 1.3:1 against both sides of it.

    The <hr>, the home intro's divider, the related/backlinks/series dividers, table borders,
    the tags page's list rules, search-result tag chips and the palette input's divider. Each
    is measured against the backdrop and against the element's own fill (a striped table
    cell sits on the code background), and the worse counts. 1.4.11 exempts decoration, but
    the old rules were the dark background itself (1.00:1), 1.08:1 in light, or, for the post
    dividers and chips, the light background itself.
    """
    _use_theme(page, theme)
    offenders, missing, count = [], [], 0
    for label, path, ready, palette, rules in _rule_pages(designed_site):
        _goto(page, f"{designed_site.url}{path}", theme, ready)
        if palette:
            _open_palette(page)
        _rest(page)
        for selector, sides, required in rules:
            drawn = 0
            for item in page.locator(selector).filter(visible=True).all():
                edges = _edges(item, sides)
                if not edges["drawn"]:
                    continue  # e.g. the last list item, which has no rule under it
                drawn += 1
                faint = {}
                for side, (colour, ratio) in edges["drawn"].items():
                    fill_ratio = a11y.contrast(_over(colour, edges["fill"]), edges["fill"])
                    if min(ratio, fill_ratio) < RULE_MIN:
                        faint[side] = (colour, ratio, fill_ratio)
                for where, (colour, ratio, fill_ratio) in _fold_sides(faint):
                    offenders.append(
                        f"{theme} {label} {path}: {selector} {edges['element']} {where} rule {colour}: "
                        f"{min(ratio, fill_ratio):.2f}:1 < {RULE_MIN}:1 (backdrop {_rgb(edges['backdrop'])} "
                        f"{ratio:.2f}:1, own fill {_rgb(edges['fill'])} {fill_ratio:.2f}:1)"
                    )
            if required and not drawn:
                missing.append(f"{selector} on {path}")
            count += drawn

    assert not missing, f"rules the test must measure were not drawn: {missing}"
    assert not offenders, (
        f"{len(offenders)} near-invisible rules on the {count} elements measured "
        f"(floor {RULE_MIN}:1 against both sides):\n  " + "\n  ".join(offenders)
    )
