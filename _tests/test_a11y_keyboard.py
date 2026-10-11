"""Keyboard and assistive-tech access to the sidebar and the theme switch (css_audit.md A1, A2).

The sidebar is a CSS-only disclosure: a visually hidden checkbox (`#sidebar-checkbox`)
drives it, and its `<label class="sidebar-toggle">` is the hamburger a reader sees. The
theme switch is a second checkbox inside the sidebar, drawn by `.toggle-slider`.

Invariants:
  - the sidebar control is the first Tab stop on a fresh load and has a text name; Space
    opens the sidebar and the next Tab continues into it (WCAG 2.1.1, 4.1.2);
  - while the closed control has keyboard focus, the hamburger shows a focus ring (>= 2px,
    >= 3:1 against what is behind it) that it does not show unfocused, and still looks
    closed (2.4.7, 1.4.11);
  - the theme switch has a text name, its moon/sun glyph (or any pictograph) is decoration
    that assistive tech does not read, and keyboard focus on it shows a ring on the slider
    that is absent without focus (4.1.2, 1.1.1, 2.4.7);
  - the switch track's edge is >= 3:1 against the sidebar in both themes (1.4.11);
  - a keyboard-only reader can open the sidebar and change the theme;
  - the switch's name contains the label shown beside it (2.5.3).

Everything is measured as a reader meets it: focus moves with real key presses, names come
from the accessibility tree, and colours are composited as painted (a11y.py). The sidebar is
the same on every page, so the tests use the real build's home page.

Waiting: key presses move focus and toggle checkboxes synchronously, so focus and checked
state are read straight after them. `.toggle-slider` transitions every property
(`transition: .4s`) and the hamburger its transform, so computed styles are read once the
element's running transitions have finished (`getAnimations()`), never after a fixed sleep:
a style read at the start of a transition would still show the old value.
"""

import re
import unicodedata

import pytest
from a11y import BACKDROP_JS, NON_TEXT_MIN, TEXT_COLOURS_JS, against_backdrop, contrast, parse_rgb
from constants import SELECTORS
from playwright.sync_api import Locator, Page, expect

THEMES = ["dark", "light"]

# Local until constants.SELECTORS carries them.
SIDEBAR_CONTROL = "#sidebar-checkbox"
SIDEBAR = "#sidebar"
THEME_SWITCH = SELECTORS["theme_toggle_input"]
THEME_REGION = ".theme-toggle"
SWITCH_TRACK = ".toggle-slider"

FOCUS_RING_MIN_PX = 2.0  # the 2.4.13 (AAA) minimum thickness, which this site meets
DECORATIVE_GLYPHS = ("\U0001f319", "\u2600")  # moon, sun (the sun is followed by U+FE0F)
TEXT_NAME = re.compile(r"[A-Za-z]")  # a name a screen reader can say, not just a glyph
MAX_TAB_STOPS = 40

# One line describing document.activeElement, for failure messages.
DESCRIBE_FOCUS_JS = """() => {
  const el = document.activeElement;
  if (!el || el === document.body) return '(body: focus has left the page for the browser UI)';
  const id = el.id ? '#' + el.id : '';
  const cls = typeof el.className === 'string' && el.className.trim()
    ? '.' + el.className.trim().split(/\\s+/).join('.') : '';
  const text = (el.getAttribute('aria-label') || el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 40);
  return `${el.tagName.toLowerCase()}${id}${cls} "${text}"`;
}"""

# Resolves once every running transition on the element and its pseudo-elements has ended.
SETTLED_JS = "el => Promise.all(el.getAnimations({subtree: true}).map(a => a.finished.catch(() => null)))"

OUTLINE_JS = """el => {
  const s = getComputedStyle(el);
  return {style: s.outlineStyle, width: parseFloat(s.outlineWidth), colour: s.outlineColor};
}"""

# What says "open" or "closed" about the hamburger: the button face and its icon.
TOGGLE_LOOK_JS = """el => {
  const s = getComputedStyle(el), icon = getComputedStyle(el, '::before');
  return {background: s.backgroundColor, colour: s.color, icon: icon.backgroundImage};
}"""

TRACK_PAINT_JS = """el => {
  const s = getComputedStyle(el);
  return {
    border: {width: parseFloat(s.borderTopWidth), style: s.borderTopStyle, colour: s.borderTopColor},
    shadow: s.boxShadow,
    background: s.backgroundColor,
  };
}"""

SHADOW = re.compile(
    r"(rgba?\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px\s+([\d.]+)px\s+(-?[\d.]+)px(\s+inset)?",
)


def _load(page: Page, url: str, theme: str) -> None:
    """Load url with theme as the stored choice, and confirm it is the theme shown."""
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
    page.goto(url)
    expect(page.locator(SELECTORS["html"])).to_have_attribute("data-theme", theme)


def _focused(page: Page) -> str:
    return page.evaluate(DESCRIBE_FOCUS_JS)


def _has_focus(locator: Locator) -> bool:
    return locator.evaluate("el => el === document.activeElement")


def _tab_to(page: Page, target: Locator, what: str) -> None:
    """Press Tab until target has focus; fail with the Tab stops visited if it never does."""
    visited: list[str] = []
    for _ in range(MAX_TAB_STOPS):
        page.keyboard.press("Tab")
        if _has_focus(target):
            return
        stop = _focused(page)
        if visited and stop == visited[0]:
            break  # wrapped round: the whole tab order has been seen
        visited.append(stop)
    pytest.fail(
        f"Tab never reached {what} on {page.url}. Tab stops, in order, until the order wrapped:\n  "
        + "\n  ".join(visited)
    )


def _open_sidebar_with_mouse(page: Page) -> None:
    """Open the sidebar the way a mouse user does, independent of keyboard access to it."""
    page.locator(SELECTORS["sidebar_toggle"]).click()
    expect(page.locator(SIDEBAR)).to_be_visible()


def _settle(locator: Locator) -> None:
    locator.evaluate(SETTLED_JS)


def _outline(locator: Locator) -> dict:
    """locator's computed outline once its transitions have finished."""
    _settle(locator)
    return locator.evaluate(OUTLINE_JS)


def _describe(outline: dict) -> str:
    return f"outline: {outline['style']} {outline['width']}px {outline['colour']}"


def _focus_ring_problems(locator: Locator, what: str, unfocused: dict) -> list[str]:
    """Why locator's outline isn't a visible focus indicator (empty if it is).

    unfocused is its outline before it had focus: an outline that is there either way
    doesn't show where focus is, however thick and bright it is.
    """
    outline = _outline(locator)
    if outline["style"] == "none" or outline["width"] == 0:
        return [f"{what}: no outline ({_describe(outline)})"]
    if outline == unfocused:
        return [f"{what}: focus doesn't change it; the same outline is there without focus ({_describe(outline)})"]
    problems = []
    if outline["width"] < FOCUS_RING_MIN_PX:
        problems.append(f"{what}: outline is {outline['width']}px wide, needs >= {FOCUS_RING_MIN_PX}px")
    ratio = against_backdrop(locator, outline["colour"])
    if ratio < NON_TEXT_MIN:
        backdrop = locator.evaluate(BACKDROP_JS)
        problems.append(
            f"{what}: outline {outline['colour']} is {ratio:.2f}:1 against its backdrop rgb{tuple(backdrop)}, "
            f"needs >= {NON_TEXT_MIN}:1"
        )
    return problems


def _icon(image: str) -> str:
    """A readable stand-in for an icon's data-URI SVG: its fill colour."""
    fill = re.search(r"fill=[^%#]*(?:%23|#)([0-9a-fA-F]{3,8})", image)
    return f"svg fill #{fill.group(1)}" if fill else image[:60]


def _look(toggle: Locator) -> dict:
    """The hamburger's face and icon, read after its transitions so a change can't be missed."""
    _settle(toggle)
    look = toggle.evaluate(TOGGLE_LOOK_JS)
    return {**look, "icon": _icon(look["icon"])}


def _over(colour: list[float], under: list[float]) -> list[float]:
    """colour ([r, g, b, a]) composited over the opaque under ([r, g, b])."""
    alpha = colour[3]
    return [alpha * c + (1 - alpha) * u for c, u in zip(colour[:3], under)]


def _track_edge(track: Locator) -> tuple[list[float], str]:
    """The colour painted at the switch track's outer edge, and what paints it.

    A visible border is the edge; failing that, a ring (a box-shadow with no offset or blur):
    an outer ring painted over the sidebar, or an inset ring painted over the track's fill;
    failing both, the fill itself.
    """
    paint = track.evaluate(TRACK_PAINT_JS)
    fill = track.evaluate(TEXT_COLOURS_JS)["bg"]  # the track's own fill over everything behind it
    backdrop = track.evaluate(BACKDROP_JS)
    border = paint["border"]
    if border["style"] not in ("none", "hidden") and border["width"] >= 1:
        return _over(parse_rgb(border["colour"]), backdrop), f"border {border['colour']}"
    rings = [
        (colour, bool(inset))
        for colour, x, y, blur, spread, inset in SHADOW.findall(paint["shadow"])
        if float(x) == float(y) == float(blur) == 0 and float(spread) >= 1
    ]
    outer = [colour for colour, inset in rings if not inset]  # outside any inset ring, so it is the edge
    if outer:
        return _over(parse_rgb(outer[0]), backdrop), f"outer ring {outer[0]}"
    if rings:
        colour = rings[0][0]
        return _over(parse_rgb(colour), fill), f"inset ring {colour} over fill rgb{tuple(fill)}"
    return fill, f"fill {paint['background']} (no border or ring)"


# =============================================================================
# A1: the sidebar control
# =============================================================================


def test_sidebar_control_is_first_tab_stop(page: Page, jekyll_server: str):
    """A1 (WCAG 2.1.1): the first Tab from a fresh load lands on the sidebar control.

    It sits first in the DOM, so a keyboard reader meets it before the content. The old CSS
    hid the checkbox with `display: none`, which took the only way to open the sidebar out
    of the tab order: Tab went straight to the masthead link.
    """
    page.goto(f"{jekyll_server}/")
    control = page.locator(SIDEBAR_CONTROL)
    expect(control).to_have_count(1)

    page.keyboard.press("Tab")

    assert _has_focus(control), (
        f"The first Tab stop on {page.url} should be the sidebar control ({SIDEBAR_CONTROL}), "
        f"but focus went to {_focused(page)}"
    )


def test_sidebar_control_has_accessible_name(page: Page, jekyll_server: str):
    """A1 (WCAG 4.1.2): the sidebar control is exposed to assistive tech with a text name.

    The old checkbox was `display: none` (absent from the accessibility tree) and its
    `<label>` is an empty box drawn by CSS, so it had no name to announce.
    """
    page.goto(f"{jekyll_server}/")
    control = page.locator(SIDEBAR_CONTROL)
    expect(control).to_have_count(1)

    expect(
        control, f"The sidebar control ({SIDEBAR_CONTROL}) on {page.url} needs a text accessible name"
    ).to_have_accessible_name(TEXT_NAME)


def test_space_opens_sidebar_and_tab_continues_into_it(page: Page, jekyll_server: str):
    """A1 (WCAG 2.1.1): Space on the focused control opens the sidebar; the next Tab enters it.

    The sidebar follows the control in the DOM and is `visibility: hidden` while closed, so
    once open its controls (the theme switch first) are the next Tab stops.
    """
    page.goto(f"{jekyll_server}/")
    control = page.locator(SIDEBAR_CONTROL)
    sidebar = page.locator(SIDEBAR)
    _tab_to(page, control, f"the sidebar control ({SIDEBAR_CONTROL})")
    expect(control).not_to_be_checked()
    expect(sidebar).to_be_hidden()

    page.keyboard.press("Space")

    expect(control, "Space on the focused sidebar control should check it").to_be_checked()
    expect(sidebar, "Space on the sidebar control should open the sidebar").to_be_visible()

    page.keyboard.press("Tab")

    inside = sidebar.evaluate("el => el.contains(document.activeElement)")
    assert inside, f"After opening the sidebar, Tab should move into it ({SIDEBAR}), but focus went to {_focused(page)}"


@pytest.mark.parametrize("theme", THEMES)
def test_closed_sidebar_control_shows_focus_ring(page: Page, jekyll_server: str, theme: str):
    """A1 (WCAG 2.4.7, 1.4.11): keyboard focus on the closed control rings the hamburger.

    The checkbox itself is a clipped 1px box, so its visible face, `.sidebar-toggle`, must
    carry the indicator: an outline >= 2px wide and >= 3:1 against the page behind it,
    which it doesn't have without focus.
    """
    _load(page, f"{jekyll_server}/", theme)
    control = page.locator(SIDEBAR_CONTROL)
    toggle = page.locator(SELECTORS["sidebar_toggle"])
    expect(toggle).to_be_visible()
    unfocused = _outline(toggle)
    _tab_to(page, control, f"the sidebar control ({SIDEBAR_CONTROL})")
    expect(control).not_to_be_checked()

    problems = _focus_ring_problems(toggle, SELECTORS["sidebar_toggle"], unfocused)

    assert not problems, (
        f"No visible focus indicator while the closed sidebar control has keyboard focus "
        f"({theme} theme, {page.url}):\n  " + "\n  ".join(problems)
    )


@pytest.mark.parametrize("theme", THEMES)
def test_focus_does_not_make_closed_toggle_look_open(page: Page, jekyll_server: str, theme: str):
    """A1 (WCAG 2.4.7): with keyboard focus but unchecked, the hamburger still looks closed.

    The old CSS styled `#sidebar-checkbox:focus ~ .sidebar-toggle` like the open state (dark
    sidebar fill, white icon). Unreachable while the checkbox was `display: none`, those
    rules would show a closed menu as open as soon as the control can take focus. The open
    look is measured too, to show the comparison can tell the two apart. Focus is shown by
    the ring (test above), not by a change of state.
    """
    _load(page, f"{jekyll_server}/", theme)
    control = page.locator(SIDEBAR_CONTROL)
    toggle = page.locator(SELECTORS["sidebar_toggle"])
    closed = _look(toggle)

    _tab_to(page, control, f"the sidebar control ({SIDEBAR_CONTROL})")
    expect(control).not_to_be_checked()
    focused = _look(toggle)
    page.keyboard.press("Space")
    expect(control).to_be_checked()
    opened = _look(toggle)

    assert opened != closed, f"Sanity: the open toggle should look different from the closed one, got {opened}"
    changed = [f"{key}: {closed[key]} -> {focused[key]}" for key in closed if focused[key] != closed[key]]
    assert not changed, (
        f"Keyboard focus alone changed the closed sidebar toggle's look ({theme} theme, {page.url}); "
        f"open looks like {opened}:\n  " + "\n  ".join(changed)
    )


# =============================================================================
# A2: the theme switch
# =============================================================================


def test_theme_switch_has_text_name(page: Page, jekyll_server: str):
    """A2 (WCAG 4.1.2): the theme switch's accessible name is words, not its glyph.

    Its visible text sat outside the `<label>`, so the old switch took its name from the
    label's generated content and was announced as the moon emoji.
    """
    _load(page, f"{jekyll_server}/", "dark")
    _open_sidebar_with_mouse(page)
    switch = page.locator(THEME_SWITCH)
    expect(switch).to_have_count(1)

    expect(switch, f"The theme switch ({THEME_SWITCH}) needs a text accessible name").to_have_accessible_name(TEXT_NAME)
    for glyph in DECORATIVE_GLYPHS:
        expect(switch, f"The theme switch's name should not include {glyph!r}").not_to_have_accessible_name(
            re.compile(re.escape(glyph))
        )


def test_theme_switch_name_contains_its_visible_label(page: Page, jekyll_server: str):
    """A2 (WCAG 2.5.3 Label in Name): the switch's accessible name contains the text shown as its label.

    A speech-input user operates a control by saying the label they see, which works only if
    the accessible name contains that text. The label is whatever `.theme-toggle` shows
    beside the switch, read from the page rather than hardcoded. The first fix named the switch
    for what "on" means ("Light theme") but kept the visible "Toggle dark mode".
    """
    _load(page, f"{jekyll_server}/", "dark")
    _open_sidebar_with_mouse(page)
    region = page.locator(THEME_REGION)
    expect(region.get_by_role("checkbox").or_(region.get_by_role("switch"))).to_have_count(1)
    label = " ".join(region.inner_text().split())
    assert TEXT_NAME.search(label), f"{THEME_REGION} should show a text label beside the switch, got {label!r}"

    # name= without exact=True is a case-insensitive substring match against the accessible name.
    named = region.get_by_role("switch", name=label).or_(region.get_by_role("checkbox", name=label))

    assert named.count() == 1, (
        f"The theme switch's accessible name should contain its visible label {label!r} ({page.url}). "
        f"Accessibility tree of {THEME_REGION}:\n{region.aria_snapshot()}"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_theme_switch_glyph_is_decorative(page: Page, jekyll_server: str, theme: str):
    """A2 (WCAG 1.1.1, 4.1.2): the switch's moon/sun glyph is hidden from assistive tech.

    The glyph is `::before` generated content, which browsers expose as text unless it is
    given empty alternative text (`content: "..." / ""`). The accessibility tree of the
    whole switch region must not contain it, in either state (moon in dark, sun in light),
    nor any other pictograph (Unicode category So: emoji, dingbats, symbols) standing in
    for words.
    """
    _load(page, f"{jekyll_server}/", theme)
    _open_sidebar_with_mouse(page)
    region = page.locator(THEME_REGION)
    expect(region.get_by_role("checkbox").or_(region.get_by_role("switch"))).to_have_count(1)

    snapshot = region.aria_snapshot()

    exposed = sorted({ch for ch in snapshot if ch in DECORATIVE_GLYPHS or unicodedata.category(ch) == "So"})
    assert not exposed, (
        f"Decorative glyph(s) {exposed} are exposed to assistive tech ({theme} theme, {page.url}). "
        f"Accessibility tree of {THEME_REGION}:\n{snapshot}"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_theme_switch_shows_focus_ring(page: Page, jekyll_server: str, theme: str):
    """A2 (WCAG 2.4.7, 1.4.11): keyboard focus on the switch rings its slider.

    The input is 0x0 and transparent, so `.toggle-slider`, its visible face, must carry an
    outline >= 2px wide and >= 3:1 against the sidebar, which it doesn't have without focus.
    The sidebar is opened with the mouse so this holds apart from A1.
    """
    _load(page, f"{jekyll_server}/", theme)
    _open_sidebar_with_mouse(page)
    switch = page.locator(THEME_SWITCH)
    track = page.locator(SWITCH_TRACK)
    expect(track).to_be_visible()
    unfocused = _outline(track)
    _tab_to(page, switch, f"the theme switch ({THEME_SWITCH})")

    problems = _focus_ring_problems(track, SWITCH_TRACK, unfocused)

    assert not problems, (
        f"No visible focus indicator while the theme switch has keyboard focus ({theme} theme, {page.url}):\n  "
        + "\n  ".join(problems)
    )


@pytest.mark.parametrize("theme", THEMES)
def test_theme_switch_track_edge_contrast(page: Page, jekyll_server: str, theme: str):
    """A2 (WCAG 1.4.11): the switch track's edge is >= 3:1 against the sidebar.

    The track has no border, so its edge is whatever paints its outermost pixel: an inset
    ring if it has one, else its fill. The old dark track (#1a1a1a fill, no ring) was 1.29:1
    on the sidebar, so the switch's shape disappeared. In light the switch is on and its
    track filled pale; that case passed before the fix and guards the on state.
    """
    _load(page, f"{jekyll_server}/", theme)
    _open_sidebar_with_mouse(page)
    switch = page.locator(THEME_SWITCH)
    track = page.locator(SWITCH_TRACK)
    expect(track).to_be_visible()
    # The track's fill follows the switch, not the theme: confirm it shows this theme's state.
    on = theme == "light"
    expect(switch, f"In {theme} the theme switch should be {'on' if on else 'off'}").to_be_checked(checked=on)
    _settle(track)

    edge, source = _track_edge(track)
    backdrop = track.evaluate(BACKDROP_JS)
    ratio = contrast(edge, backdrop)

    assert ratio >= NON_TEXT_MIN, (
        f"The theme switch track's edge is {ratio:.2f}:1 against the sidebar rgb{tuple(backdrop)}, needs >= "
        f"{NON_TEXT_MIN}:1 ({theme} theme, {page.url}). Edge painted by {source}: rgb{tuple(round(c) for c in edge)}"
    )


def test_keyboard_only_theme_change(page: Page, jekyll_server: str):
    """A1, A2 (WCAG 2.1.1): from a fresh load, the keyboard alone opens the sidebar and switches theme.

    Tab to the sidebar control, Space to open, Tab to the theme switch, Space to flip it:
    the theme shown and the stored choice both change.
    """
    _load(page, f"{jekyll_server}/", "dark")
    control = page.locator(SIDEBAR_CONTROL)
    switch = page.locator(THEME_SWITCH)

    _tab_to(page, control, f"the sidebar control ({SIDEBAR_CONTROL})")
    page.keyboard.press("Space")
    expect(page.locator(SIDEBAR)).to_be_visible()
    _tab_to(page, switch, f"the theme switch ({THEME_SWITCH})")
    page.keyboard.press("Space")

    expect(page.locator(SELECTORS["html"]), "Space on the theme switch should change the theme").to_have_attribute(
        "data-theme", "light"
    )
    expect(switch).to_be_checked()
    assert page.evaluate("localStorage.getItem('theme')") == "light", "The keyboard choice should be stored"
