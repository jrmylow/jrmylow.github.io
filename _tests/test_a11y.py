"""Accessibility tests against WCAG 2.2 Level A and AA.

Two layers:
  - an axe-core scan of every page type, in both themes, limited to the WCAG A/AA rules.
    axe is Deque's maintained rules engine (contrast, names, labels, ARIA); it runs offline
    from the copy bundled in the axe-playwright-python package;
  - a few interaction tests for what a scanner can't see. Each is tied to a success
    criterion and to a failure the audit found (_documentation/css_audit.md): reaching and
    operating the menu by keyboard (2.1.1), a visible focus indicator (2.4.7), focus and
    jump targets not hidden by the sticky masthead (2.4.11), nothing clipped at 320px
    (1.4.10), and the contrast axe doesn't measure: control boundaries (1.4.11) and
    placeholders (1.4.3).

Colours are composited as painted (a11y.py). Content comes from the designed build: its
posts plus the a11y demo preview (footnote, code, wide equation).
"""

import re

import a11y
import corpus
import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page, expect

THEMES = ["dark", "light"]
WCAG_A_AA = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
A11Y_DEMO = "2024-02-01-a11y-demo.md"
QUERY = "designed"  # in every designed post's title, so search and the palette return results
AXE = Axe()


def _open(page: Page, url: str, theme: str) -> None:
    """Load url in the given theme and confirm the theme took."""
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
    page.goto(url)
    expect(page.locator("html")).to_have_attribute("data-theme", theme)


def _demo_url(site) -> str:
    return f"{site.url}{site.document(A11Y_DEMO)['url']}"


def _wait_for_maths(page: Page) -> None:
    expect(page.locator('mjx-container[display="true"] svg').first).to_be_visible()


def _open_sidebar(page: Page) -> None:
    page.locator(".sidebar-toggle").click()
    expect(page.locator("#sidebar")).to_be_visible()


def _open_palette(page: Page) -> None:
    page.keyboard.press("Control+k")
    expect(page.locator(".command-palette-input")).to_be_focused()
    page.keyboard.type(QUERY)
    expect(page.locator(".command-palette-result").first).to_be_visible()


# =============================================================================
# axe-core scan (WCAG A/AA rules)
# =============================================================================

DESIGNED_POST = corpus.DESIGNED[0].filename

# Violations in markup this suite's CSS can't fix, switched off only on the view where they
# fire, so the scan keeps checking everything else there (contrast included). Open items in
# css_audit.md (B9); delete an entry when its fix lands.
KNOWN_MARKUP_ISSUES = {
    # command-palette.js: its role="listbox" has no name, and each role="option" holds a link.
    "command palette": ["aria-input-field-name", "nested-interactive"],
}

# (id, path or callable(site) -> url, ready(page)) for each page type and interactive state.
SCANS = [
    ("home", "/", None),
    ("essays", "/essays/", None),
    ("archive", "/essays/all/", None),
    ("about", "/about/", None),
    ("contact", "/contact/", None),
    ("tags", "/tags/?t=alpha", lambda page: expect(page.locator(".tag-post-item").first).to_be_visible()),
    ("search", f"/search/?q={QUERY}", lambda page: expect(page.locator(".search-result-item").first).to_be_visible()),
    ("post", lambda site: f"{site.url}{site.document(DESIGNED_POST)['url']}", None),
    ("demo", _demo_url, _wait_for_maths),
    ("sidebar open", "/", _open_sidebar),
    ("command palette", "/", _open_palette),
]


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("name, where, ready", SCANS, ids=[scan[0] for scan in SCANS])
def test_axe_finds_no_wcag_violations(page: Page, designed_site, theme: str, name, where, ready):
    """WCAG 2.2 A/AA, automated: axe-core reports no violations of its WCAG A/AA rules.

    Covers 1.4.3 contrast of all rendered text (including code tokens, search highlights
    and the palette's selected row), and names, labels and ARIA (4.1.2). Old failures:
    muted text and search highlights at 2.4-3.7:1, Monokai comments at 3.0:1, and a
    theme switch with no name.
    """
    url = where(designed_site) if callable(where) else f"{designed_site.url}{where}"
    _open(page, url, theme)
    if ready:
        ready(page)
    options = {"runOnly": {"type": "tag", "values": WCAG_A_AA}}
    options["rules"] = {rule: {"enabled": False} for rule in KNOWN_MARKUP_ISSUES.get(name, [])}
    results = AXE.run(page, options=options)
    assert results.violations_count == 0, f"{name} ({theme}): {results.generate_report()}"


# =============================================================================
# 2.1.1 Keyboard, 4.1.2 Name, Role, Value, 2.5.3 Label in Name
# =============================================================================


def test_menu_and_theme_switch_work_from_the_keyboard(page: Page, jekyll_server: str):
    """2.1.1 (A): the menu is reachable and operable by keyboard; 4.1.2, 2.5.3 (A): its
    controls have names, and the switch's name contains its visible label.

    Old: the menu checkbox was `display: none`, so Tab never reached it and keyboard users
    could not open the site's navigation at all.
    """
    _open(page, f"{jekyll_server}/", "dark")
    page.keyboard.press("Tab")
    menu = page.locator("#sidebar-checkbox")
    expect(menu, "the first Tab stop should be the menu").to_be_focused()
    expect(menu).to_have_accessible_name(re.compile(r"\w"))

    page.keyboard.press("Space")
    expect(page.locator("#sidebar")).to_be_visible()
    page.keyboard.press("Tab")
    toggle = page.locator(".theme-toggle")
    switch = toggle.get_by_role("switch")
    expect(switch, "Tab should move into the open menu, to the theme switch").to_be_focused()
    label = toggle.inner_text().strip()
    expect(switch).to_have_accessible_name(re.compile(re.escape(label), re.IGNORECASE))

    page.keyboard.press("Space")
    expect(page.locator("html")).to_have_attribute("data-theme", "light")


def test_escape_closes_the_menu_and_returns_focus(page: Page, jekyll_server: str):
    """2.1.1 (A): Escape closes the open menu; 2.4.3 (A): focus goes back to the menu control
    instead of being left on a control the menu just hid.

    Old: the menu closed only on a click outside it, so a keyboard user had to Shift+Tab
    back through every control in the sidebar to reach the hamburger.
    """
    _open(page, f"{jekyll_server}/", "dark")
    menu = page.locator("#sidebar-checkbox")
    sidebar = page.locator("#sidebar")
    page.keyboard.press("Tab")
    expect(menu).to_be_focused()
    page.keyboard.press("Space")
    expect(sidebar).to_be_visible()
    page.keyboard.press("Tab")  # into the menu, onto a control that closing it will hide
    expect(page.locator(".theme-toggle").get_by_role("switch")).to_be_focused()

    page.keyboard.press("Escape")
    expect(menu).not_to_be_checked()
    expect(sidebar).to_be_hidden()
    expect(menu, "focus should return to the menu control").to_be_focused()


# =============================================================================
# 1.3.1 Info and Relationships, 2.4.6 Headings and Labels
# =============================================================================

HEADINGS_JS = """() => [...document.querySelectorAll('h1, h2, h3, h4, h5, h6')]
  .filter((h) => h.checkVisibility())
  .map((h) => [Number(h.tagName[1]), h.textContent.trim().slice(0, 40)])"""


def test_each_page_has_one_h1_and_no_skipped_heading_levels(page: Page, designed_site):
    """1.3.1 (A), 2.4.6 (AA): every page type has exactly one h1, and headings never skip a
    level going down (h1 then h3), so heading navigation gives a true outline of the page.

    Old: the site title was an h3 on every page, page titles were h3, and the home and
    other non-post pages had no h1 at all.
    """
    page.add_init_script("localStorage.setItem('theme', 'dark')")
    problems = []
    for name, where, ready in SCANS:
        if name in ("sidebar open", "command palette"):
            continue  # states of a page, not page types
        page.goto(where(designed_site) if callable(where) else f"{designed_site.url}{where}")
        if ready:
            ready(page)
        headings = page.evaluate(HEADINGS_JS)
        h1s = [text for level, text in headings if level == 1]
        if len(h1s) != 1:
            problems.append(f"{name}: {len(h1s)} h1 elements {h1s}")
        for (above, _), (level, text) in zip(headings, headings[1:]):
            if level > above + 1:
                problems.append(f"{name}: h{level} {text!r} follows an h{above}")
    assert not problems, "\n  ".join(problems)


# =============================================================================
# 2.4.7 Focus Visible, 2.4.11 Focus Not Obscured (Minimum)
# =============================================================================

# Waits for running transitions, then reads the focused element, the element that shows its
# focus (a visually hidden control draws its ring on its visible face), that element's outline,
# and whether it can be seen: how many sample points inside the viewport have it, not something
# painted over it, as the topmost element.
STOP_JS = """
async (el) => {
  await Promise.all(document.getAnimations().map((a) => a.finished.catch(() => null)));
  const face = el.id === 'sidebar-checkbox' ? document.querySelector('.sidebar-toggle')
    : el.matches('.toggle-switch input') ? el.parentElement.querySelector('.toggle-slider') : el;
  const s = getComputedStyle(face);
  const r = face.getBoundingClientRect();
  const points = [];
  for (const fx of [0.1, 0.5, 0.9]) for (const fy of [0.1, 0.5, 0.9]) {
    points.push([r.left + fx * r.width, r.top + fy * r.height]);
  }
  const onScreen = points.filter(([x, y]) => x >= 0 && y >= 0 && x < innerWidth && y < innerHeight);
  const coveredBy = new Set();
  let seen = 0;
  for (const [x, y] of onScreen) {
    const top = document.elementFromPoint(x, y);
    if (top && (face.contains(top) || top.contains(face) || el.contains(top))) seen++;
    else if (top) coveredBy.add(top.closest('[class]')?.className || top.tagName);
  }
  const name = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
    (typeof el.className === 'string' && el.className ? '.' + el.className.split(' ')[0] : '') +
    ' "' + (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0, 30) + '"';
  return {name, style: s.outlineStyle, width: parseFloat(s.outlineWidth), colour: s.outlineColor,
          offset: parseFloat(s.outlineOffset), onScreen: onScreen.length, seen, coveredBy: [...coveredBy]};
}
"""
FACE_JS = """(el) => el.id === 'sidebar-checkbox' ? document.querySelector('.sidebar-toggle')
  : el.matches('.toggle-switch input') ? el.parentElement.querySelector('.toggle-slider') : el"""
MAX_STOPS = 60


def _focus_problem(page: Page) -> tuple[str, str | None]:
    """(name, problem or None) for the focused element's indicator and visibility."""
    el = page.evaluate_handle("document.activeElement")
    stop = el.evaluate(STOP_JS)
    if stop["onScreen"] == 0:
        return stop["name"], "focused element is off-screen"
    if stop["seen"] == 0:
        return stop["name"], f"entirely hidden under {stop['coveredBy']} (2.4.11)"
    if stop["style"] == "auto":
        return stop["name"], None  # the browser's own ring
    if stop["style"] == "none" or stop["width"] < 2:
        return stop["name"], f"no visible focus indicator: outline {stop['style']} {stop['width']}px (2.4.7)"
    face = el.evaluate_handle(FACE_JS).as_element()
    # An inset ring is painted over the element's own background; an outset one over what surrounds it.
    backdrop = face.evaluate(a11y.TEXT_COLOURS_JS)["bg"] if stop["offset"] < 0 else face.evaluate(a11y.BACKDROP_JS)
    r, g, b, a = a11y.parse_rgb(stop["colour"])
    painted = [a * c + (1 - a) * u for c, u in zip((r, g, b), backdrop)]
    ratio = a11y.contrast(painted, backdrop)
    if ratio < a11y.NON_TEXT_MIN:
        return stop["name"], f"focus ring {stop['colour']} is {ratio:.2f}:1 on {backdrop} (2.4.7, 1.4.11)"
    return stop["name"], None


def _walk(page: Page, start_inside: str | None = None) -> tuple[list[str], list[str]]:
    """Tab through the page (or until focus leaves start_inside), checking every stop."""
    names, problems, first = [], [], None
    if page.evaluate("document.activeElement !== document.body"):
        name, problem = _focus_problem(page)
        names.append(name)
        problems += [f"{name}: {problem}"] if problem else []
    for _ in range(MAX_STOPS):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement === document.body"):
            break
        if start_inside and not page.evaluate(f"!!document.activeElement.closest({start_inside!r})"):
            break
        key = page.evaluate("document.activeElement.outerHTML.slice(0, 200)")
        if key == first:
            break
        first = first or key
        name, problem = _focus_problem(page)
        names.append(name)
        problems += [f"{name}: {problem}"] if problem else []
    return names, problems


def _home_with_menu(page: Page, site) -> None:
    """The home page with the menu open (by mouse, so this doesn't repeat the keyboard test)."""
    page.goto(f"{site.url}/")
    _open_sidebar(page)
    page.evaluate("document.activeElement.blur()")  # a click's focus is not keyboard focus


WALKS = [
    ("home and menu", _home_with_menu, None),
    ("search", lambda page, site: page.goto(f"{site.url}/search/?q={QUERY}"), None),
    ("command palette", lambda page, site: (page.goto(f"{site.url}/"), _open_palette(page)), ".command-palette"),
]


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("name, setup, inside", WALKS, ids=[walk[0] for walk in WALKS])
def test_every_tab_stop_shows_focus(page: Page, designed_site, theme: str, name, setup, inside):
    """2.4.7 (AA): every Tab stop shows a focus indicator at least 2px wide and >= 3:1 against
    what it is painted on; 2.4.11 (AA): no stop is entirely hidden behind the masthead.

    The browser's default ring (`outline-style: auto`) counts as visible. Old: the search
    inputs and the palette input set `outline: none`, the menu could not be reached at all,
    and the palette's selected row drew its ring in the colour of its own fill.
    """
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
    setup(page, designed_site)
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    names, problems = _walk(page, inside)
    assert len(names) >= 3, f"{name} ({theme}): the walk reached too few stops to mean anything: {names}"
    assert not problems, f"{name} ({theme}):\n  " + "\n  ".join(problems)


def test_focus_moving_up_the_page_is_not_hidden_by_the_masthead(page: Page, designed_site):
    """2.4.11 (AA): Shift+Tab up a long page scrolls each stop into view below the sticky masthead.

    Old: `html, body { overflow-x: hidden; height: 100% }` made <body> the scroller, so
    `scroll-padding` could not apply and a stop scrolled to the top landed under the masthead.
    """
    _open(page, _demo_url(designed_site), "dark")
    _wait_for_maths(page)
    page.locator("a.reversefootnote").focus()
    problems = []
    for _ in range(4):  # up through the equation and the blockquote link to the footnote reference
        page.keyboard.press("Shift+Tab")
        name, problem = _focus_problem(page)
        problems += [f"{name}: {problem}"] if problem else []
    assert not problems, "\n  ".join(problems)


def test_footnote_round_trip_lands_below_the_masthead(page: Page, designed_site):
    """2.4.11 (AA): following a footnote and its back-link leaves the target in view, below the masthead."""
    _open(page, _demo_url(designed_site), "dark")
    page.locator('sup[id^="fnref"] a').click()
    page.locator("a.reversefootnote").click()
    target = page.locator(":target")
    expect(target).to_have_count(1)
    top = target.evaluate("el => el.getBoundingClientRect().top")
    masthead_bottom = page.locator(".masthead").evaluate("el => el.getBoundingClientRect().bottom")
    assert top >= masthead_bottom, f"the back-link target is at y={top}, under the masthead (bottom {masthead_bottom})"


# =============================================================================
# 1.4.10 Reflow
# =============================================================================

# Elements inside .content that extend past the viewport with no scrollable ancestor to reach them.
CLIPPED_JS = """
() => {
  const vw = document.documentElement.clientWidth, out = [];
  for (const el of document.querySelectorAll('.content *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || (r.right <= vw + 1 && r.left >= -1)) continue;
    let reachable = false;
    for (let a = el.parentElement; a && a !== document.documentElement; a = a.parentElement) {
      const ox = getComputedStyle(a).overflowX;
      if ((ox === 'auto' || ox === 'scroll') && a.scrollWidth > a.clientWidth) { reachable = true; break; }
    }
    const name = el.tagName.toLowerCase() + '.' + (el.getAttribute('class') || '');
    if (!reachable) out.push(name + ' right=' + Math.round(r.right));
  }
  return {pageScroll: document.documentElement.scrollWidth - vw, clipped: [...new Set(out)].slice(0, 10)};
}
"""


def test_nothing_is_clipped_at_320px(page: Page, designed_site):
    """1.4.10 (AA): at 320 CSS px wide, the page doesn't scroll sideways and nothing is cut off;
    content too wide to reflow (display maths) scrolls inside its own box.

    Old: the wide equation ran past the viewport and `overflow-x: hidden` on html/body cut it
    off with no way to scroll to the rest.
    """
    page.set_viewport_size({"width": 320, "height": 640})
    for url in (f"{designed_site.url}/", _demo_url(designed_site)):
        _open(page, url, "dark")
        if url != f"{designed_site.url}/":
            _wait_for_maths(page)
        result = page.evaluate(CLIPPED_JS)
        assert result["pageScroll"] <= 0, f"{url} scrolls sideways by {result['pageScroll']}px"
        assert not result["clipped"], f"{url}: content cut off at 320px: {result['clipped']}"


# =============================================================================
# Contrast axe doesn't measure: 1.4.11 boundaries, 1.4.3 placeholders
# =============================================================================

PLACEHOLDER_JS = """
(el) => {
  const p = getComputedStyle(el, '::placeholder');
  return {colour: p.color, opacity: parseFloat(p.opacity)};
}
"""


def _placeholder_ratio(locator) -> float:
    placeholder = locator.evaluate(PLACEHOLDER_JS)
    background = locator.evaluate(a11y.TEXT_COLOURS_JS)["bg"]
    r, g, b, a = a11y.parse_rgb(placeholder["colour"])
    alpha = a * placeholder["opacity"]
    return a11y.contrast([alpha * c + (1 - alpha) * u for c, u in zip((r, g, b), background)], background)


def _edge_ratio(locator) -> float:
    """Contrast of a control's edge against what is behind it: its border, else an inset ring, else its fill."""
    style = locator.evaluate(
        "el => { const s = getComputedStyle(el); return [s.borderTopWidth, s.borderTopColor, s.boxShadow, "
        "s.backgroundColor]; }"
    )
    width, border, shadow, fill = style
    if float(width.rstrip("px")) > 0:
        colour = border
    elif "inset" in shadow:
        colour = re.match(r"rgba?\([^)]*\)", shadow).group(0)
    else:
        colour = fill
    return a11y.against_backdrop(locator, colour)


@pytest.mark.parametrize("theme", THEMES)
def test_control_edges_and_placeholders_have_contrast(page: Page, designed_site, theme: str):
    """1.4.11 (AA): the edges that identify controls are >= 3:1 against what is behind them;
    1.4.3 (AA): placeholder text is >= 4.5:1 against its input. axe checks neither.

    Old: the "View all" button's border was the background colour (1.00:1 dark, 1.08:1
    light), the theme switch's track was 1.29:1 on the dark sidebar, and placeholders were
    the body colour at 60% opacity (2.7:1 in light) or the browser's default grey.
    """
    problems = []

    def edge(where: str, locator) -> None:
        ratio = _edge_ratio(locator)
        if ratio < a11y.NON_TEXT_MIN:
            problems.append(f"{where} edge {ratio:.2f}:1, needs {a11y.NON_TEXT_MIN}:1")

    def placeholder(where: str, locator) -> None:
        ratio = _placeholder_ratio(locator)
        if ratio < a11y.TEXT_MIN:
            problems.append(f"{where} placeholder {ratio:.2f}:1, needs {a11y.TEXT_MIN}:1")

    _open(page, f"{designed_site.url}/", theme)
    edge('"View all" button', page.locator(".view-all-link a"))
    edge("card", page.locator(".card").first)
    _open_sidebar(page)
    edge("theme switch track", page.locator(".toggle-slider"))
    placeholder("sidebar search", page.locator(".sidebar .search-input"))

    page.goto(f"{designed_site.url}/search/")
    edge("search page input", page.locator(".search-page-input"))
    placeholder("search page", page.locator(".search-page-input"))
    page.keyboard.press("Control+k")
    expect(page.locator(".command-palette-input")).to_be_focused()
    placeholder("command palette", page.locator(".command-palette-input"))

    assert not problems, f"{theme}:\n  " + "\n  ".join(problems)
