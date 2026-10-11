"""Text contrast (WCAG 2.2 1.4.3 Contrast (Minimum)) across the site, in both themes.

Invariants, measured as a reader sees them (text colour composited through its
own alpha, every background behind it and every ancestor's `opacity`; see a11y.py):
  - every visible element with its own text (a text node, or the typed value
    of a text input) meets 4.5:1, or 3:1 for large text, on every kind of page
    the site serves, with the sidebar closed and open;
  - the text inside cards, the "View all" button, post tags, the tag cloud
    (including a tag selected by clicking it) and search results still does
    while hovered and while keyboard-focused;
  - so does the command palette's selected row, which sits on the accent;
  - so do the placeholders of both search inputs and of the palette's input,
    against the input they sit in;
  - so does every token in a Monokai code block, including console output and
    untokenised text, which take the block's base colour, and comments.

Only inactive controls are exempt, as 1.4.3 allows: `.pagination-disabled`,
`[aria-disabled="true"]` and `:disabled`.

Findings A3 (muted text made with `opacity`), A4 (text on accent fills) and A5
(Monokai) of _documentation/css_audit.md. Everything runs on the designed build:
corpus.py's posts plus the a11y demo preview, which holds the code blocks.
Transitions are waited out with document.getAnimations(), never slept through.
"""

import a11y
import corpus
import pytest
from constants import SELECTORS
from playwright.sync_api import Locator, Page, expect

THEMES = ["dark", "light"]

A11Y_DEMO = "2024-02-01-a11y-demo.md"
# The designed post with the most tags: it shows several post tags and a related list.
TAGGED_POST = max(corpus.DESIGNED, key=lambda post: len(post.tags)).filename
# A word in every designed title, so search and the palette return several results.
QUERY = corpus.DESIGNED[0].title.split()[0].lower()
NO_MATCH_QUERY = "qqqzzzxxxjjj"

# Inactive components, which 1.4.3 exempts.
EXEMPT = '.pagination-disabled, [aria-disabled="true"], :disabled'

# Text the audit measured below the minimum. The sweep must reach every one of
# them, so a page that fails to render its results can't pass by omission.
AUDITED = (
    "card-meta",
    "tag-post-date",
    "related-date",
    "search-result-date",
    "search-result-tag",
    "search-result-excerpt",
    "search-no-results",
    "mark",
    "go",
    "c1",
)

SWEEP_ATTR = "data-a11y-sweep"

# Every visible element at or under root with its own non-whitespace text (a text
# node, or the value typed into a text input), unless it is inside `exempt`: its
# tag and classes, a text snippet, and its effective text and background colours.
# Each is tagged with SWEEP_ATTR so it can be found again.
_SWEEP_JS = f"""
(root, exempt) => {{
  const colours = {a11y.TEXT_COLOURS_JS};
  document.querySelectorAll('[{SWEEP_ATTR}]').forEach(el => el.removeAttribute('{SWEEP_ATTR}'));
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const typed = 'textarea, input:is(:not([type]), [type="text"], [type="search"])';
  const found = [];
  for (const el of [root, ...root.querySelectorAll('*')]) {{
    if (skip.has(el.tagName)) continue;
    const text = (el.matches(typed) ? [el.value] : Array.from(el.childNodes)
      .filter(n => n.nodeType === Node.TEXT_NODE)
      .map(n => n.textContent)).join(' ').replace(/\\s+/g, ' ').trim();
    if (!text) continue;
    if (!el.checkVisibility({{opacityProperty: true, visibilityProperty: true}})) continue;
    if (exempt && el.closest(exempt)) continue;
    const id = String(found.length);
    el.setAttribute('{SWEEP_ATTR}', id);
    const classes = typeof el.className === 'string' ? el.className.split(/\\s+/).filter(Boolean) : [];
    const {{fg, bg}} = colours(el);
    found.push({{id, tag: el.tagName.toLowerCase(), classes, text: text.slice(0, 40), fg, bg}});
  }}
  return found;
}}
"""

# The ::placeholder colour and opacity, the input's own composited background,
# and whether the placeholder is showing at all.
_PLACEHOLDER_JS = f"""
(el) => {{
  const ph = getComputedStyle(el, '::placeholder');
  return {{colour: ph.color, opacity: parseFloat(ph.opacity), bg: ({a11y.TEXT_COLOURS_JS})(el).bg,
          shown: el.matches(':placeholder-shown')}};
}}
"""


def _rgb(colour: list) -> str:
    return f"rgb({', '.join(str(round(c)) for c in colour)})"


def _use_theme(page: Page, theme: str) -> None:
    """Store `theme` as the reader's choice before any page loads."""
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")


def _goto(page: Page, url: str, theme: str) -> None:
    """Load url and confirm the stored theme is the one shown."""
    page.goto(url)
    expect(page.locator(SELECTORS["html"])).to_have_attribute("data-theme", theme)


def _settle(page: Page) -> None:
    """Wait until no CSS transition or animation is running, so computed colours are final."""
    page.wait_for_function("() => document.getAnimations().length === 0")


def _sweep(page: Page, root: Locator, where: str, exempt: str = EXEMPT) -> tuple[list, list]:
    """(measured, offenders) for the text-bearing elements at or under root.

    Each offender is one readable line: where, element, text, ratio, minimum, colours.
    """
    measured = root.evaluate(_SWEEP_JS, exempt)
    offenders = []
    for item in measured:
        ratio = a11y.contrast(item["fg"], item["bg"])
        if ratio >= a11y.TEXT_MIN:
            continue
        minimum = a11y.text_minimum(page.locator(f'[{SWEEP_ATTR}="{item["id"]}"]'))
        if ratio < minimum:
            element = ".".join([item["tag"], *item["classes"]])
            offenders.append(
                f"{where}: <{element}> {item['text']!r} {ratio:.2f}:1 < {minimum}:1 "
                f"({_rgb(item['fg'])} on {_rgb(item['bg'])})"
            )
    return measured, offenders


def _names(measured: list) -> set:
    """The tag names and classes of the measured elements."""
    return {item["tag"] for item in measured} | {c for item in measured for c in item["classes"]}


def _report(offenders: list, what: str) -> str:
    return f"{len(offenders)} {what} below the WCAG 1.4.3 minimum:\n  " + "\n  ".join(offenders)


def _open_sidebar(page: Page) -> None:
    page.locator(SELECTORS["sidebar_toggle"]).click()
    expect(page.locator(".sidebar")).to_be_visible()
    _settle(page)


def _rest(page: Page) -> None:
    """Nothing hovered or focused: the mouse parked in the empty left margin, focus dropped."""
    page.mouse.move(0, page.viewport_size["height"] - 1)
    page.evaluate("() => document.activeElement && document.activeElement.blur()")
    _settle(page)


def _keyboard_focus(page: Page, target: Locator) -> None:
    """Focus target as keyboard navigation does, so :focus-visible styles apply."""
    page.keyboard.press("Shift")  # the last input is a key press, so focusing now counts as keyboard focus
    target.focus()
    assert target.evaluate("el => el.matches(':focus-visible')"), "harness: target should match :focus-visible"
    _settle(page)


def _pages(site) -> list:
    """(label, path, selector that shows the page is ready) for each kind of page the site serves."""
    demo = site.document(A11Y_DEMO)
    post = site.document(TAGGED_POST)
    return [
        ("home", "/", ".card"),
        ("essays", "/essays/", ".card"),
        ("archive", "/essays/all/", ".card"),
        ("about", "/about/", ".page-title"),
        ("contact", "/contact/", ".page-title"),
        ("not found", "/404.html", ".content h1"),
        ("tags", f"/tags/?t={demo['tags'][0]}", ".tag-post-item:visible"),
        ("search", f"/search/?q={QUERY}", ".search-result-item mark"),
        ("search, no results", f"/search/?q={NO_MATCH_QUERY}", ".search-no-results"),
        ("a11y demo", demo["url"], 'mjx-container[display="true"]'),
        ("tagged post", post["url"], ".related-date"),
    ]


@pytest.mark.parametrize("theme", THEMES)
def test_text_contrast_sweep(page: Page, designed_site, theme: str):
    """A3, A4, A5 (WCAG 1.4.3): every visible text on every kind of page meets its contrast minimum.

    Generic on purpose: muted text faded with `opacity`, white on the accent
    and unstyled code tokens are caught wherever they appear. The sidebar is
    `visibility: hidden` while closed, so it is swept again open.
    """
    _use_theme(page, theme)
    offenders, reached = [], set()
    for label, path, ready in _pages(designed_site):
        _goto(page, f"{designed_site.url}{path}", theme)
        expect(page.locator(ready).first).to_be_visible()
        _settle(page)
        measured, found = _sweep(page, page.locator(SELECTORS["body"]), f"{theme} {label} {path}")
        assert measured, f"{label} {path}: the sweep found no visible text"
        offenders += found
        reached |= _names(measured)

    _goto(page, f"{designed_site.url}/", theme)
    _open_sidebar(page)
    measured, found = _sweep(page, page.locator(".sidebar"), f"{theme} home, sidebar open")
    assert measured, "the open sidebar should have visible text"
    offenders += found

    missed = [name for name in AUDITED if name not in reached]
    assert not missed, f"the sweep never reached {missed}; the pages didn't render what it is meant to measure"
    assert not offenders, _report(offenders, "texts")


def _components(site) -> list:
    """(label, path, selector) for each interactive component with hover/focus styling."""
    post = site.document(TAGGED_POST)
    return [
        ("card", "/", SELECTORS["card_link"]),
        ("view all", "/", SELECTORS["view_all_link"]),
        ("post tag", post["url"], ".post-tag"),
        ("tag cloud", "/tags/", ".tag-cloud-item"),
        ("search result", f"/search/?q={QUERY}", ".search-page-results .search-result-item"),
    ]


@pytest.mark.parametrize("theme", THEMES)
def test_interactive_state_text_contrast(page: Page, designed_site, theme: str):
    """A3, A4 (WCAG 1.4.3): text inside interactive components keeps its contrast when hovered or focused.

    Hover and focus swap the background (cards, chips and results go to the
    sidebar's navy), so text that passes at rest can fail in a state: a faded
    date, a chip left in the body colour, a <mark> still on the accent. Each
    component is measured focused from the keyboard, then hovered; a tag in the
    cloud also once it is selected by a click.
    """
    _use_theme(page, theme)
    offenders = []
    for label, path, selector in _components(designed_site):
        _goto(page, f"{designed_site.url}{path}", theme)
        items = page.locator(selector)
        expect(items.first).to_be_visible()
        selected = page.locator(f'{selector}:is(.selected, [aria-pressed="true"])')
        for i, item in enumerate(items.all()):
            where = f"{theme} {label} #{i + 1} {path}"
            states = ("focused", "hovered", "selected") if label == "tag cloud" else ("focused", "hovered")
            for state in states:
                _rest(page)
                if state == "focused":
                    _keyboard_focus(page, item)
                elif state == "hovered":
                    item.hover()
                    _settle(page)
                else:  # selected by a click, then neither hovered nor focused
                    item.click()
                    expect(selected).to_have_count(i + 1)
                    _rest(page)
                measured, found = _sweep(page, item, f"{where}, {state}")
                assert measured, f"{where}, {state}: no visible text to measure"
                offenders += found

    assert not offenders, _report(offenders, "texts in interactive states")


@pytest.mark.parametrize("theme", THEMES)
def test_command_palette_selected_row_contrast(page: Page, designed_site, theme: str):
    """A4 (WCAG 1.4.3): the palette's selected row, text on the accent fill, meets 4.5:1.

    It was #fff on the accent: 2.64:1 in dark, 3.68:1 in light. The whole panel
    is swept, so the other rows and the input are held to the same minimum.
    """
    _use_theme(page, theme)
    _goto(page, f"{designed_site.url}/", theme)
    _open_palette(page)
    field = page.locator(".command-palette-input")
    field.fill(QUERY)
    selected = page.locator('.command-palette-results li[aria-selected="true"]')
    expect(selected).to_have_count(1)
    _settle(page)

    _, offenders = _sweep(page, page.locator(".command-palette-panel"), f"{theme} command palette")
    assert selected.locator(f"[{SWEEP_ATTR}]").count() > 0, "the selected row's text should have been measured"
    assert field.get_attribute(SWEEP_ATTR) is not None, "the query typed into the input should have been measured"
    assert not offenders, _report(offenders, "palette texts")


def _open_palette(page: Page) -> None:
    """Open the command palette from the keyboard; it focuses its input."""
    page.keyboard.press("Control+k")
    expect(page.locator(".command-palette")).to_be_visible()
    expect(page.locator(".command-palette-input")).to_be_focused()


def _placeholder_offenders(field: Locator, where: str) -> list:
    """[] if the field's placeholder meets its 1.4.3 minimum against the input, else one readable offender line.

    The colour is read from `::placeholder` and composited, with its opacity,
    over the input's own background.
    """
    expect(field).to_be_visible()
    info = field.evaluate(_PLACEHOLDER_JS)
    assert info["shown"], f"{where} should be empty, with its placeholder showing"
    r, g, b, a = a11y.parse_rgb(info["colour"])
    alpha = a * info["opacity"]
    painted = [alpha * c + (1 - alpha) * u for c, u in zip((r, g, b), info["bg"])]
    ratio = a11y.contrast(painted, info["bg"])
    minimum = a11y.text_minimum(field)
    if ratio >= minimum:
        return []
    return [
        f"{where}::placeholder {ratio:.2f}:1 < {minimum}:1 "
        f"({info['colour']} at opacity {info['opacity']} on {_rgb(info['bg'])})"
    ]


@pytest.mark.parametrize("theme", THEMES)
def test_search_placeholder_contrast(page: Page, designed_site, theme: str):
    """A3 (WCAG 1.4.3): placeholder text in both search inputs meets 4.5:1 against the input.

    Placeholders were the body colour at 0.6 opacity: 2.76:1 and 2.67:1 in
    light. Dark passed before the fix (5.22:1 and 4.55:1); it is held to the
    same minimum.
    """
    _use_theme(page, theme)
    _goto(page, f"{designed_site.url}/search/", theme)
    _open_sidebar(page)
    offenders = []
    for selector in (f".sidebar {SELECTORS['search_input']}", ".search-page-input"):
        offenders += _placeholder_offenders(page.locator(selector), f"{theme} {selector}")
    assert not offenders, _report(offenders, "placeholders")


@pytest.mark.parametrize("theme", THEMES)
def test_command_palette_placeholder_contrast(page: Page, designed_site, theme: str):
    """A3 (WCAG 1.4.3): the palette input's placeholder ("Search essays...") meets 4.5:1 against the input.

    The site's third placeholder, held to the same minimum as the search
    inputs'. It had no ::placeholder rule, so it kept Chromium's default
    #757575: 3.78:1 in dark, 3.96:1 in light.
    """
    _use_theme(page, theme)
    _goto(page, f"{designed_site.url}/", theme)
    _open_palette(page)
    offenders = _placeholder_offenders(page.locator(".command-palette-input"), f"{theme} .command-palette-input")
    assert not offenders, _report(offenders, "placeholders")


def _code_blocks(page: Page, site, theme: str) -> list:
    """The a11y demo's highlighted code blocks (Python with comments, then a console session)."""
    _use_theme(page, theme)
    _goto(page, f"{site.url}{site.document(A11Y_DEMO)['url']}", theme)
    blocks = page.locator("div.highlight")
    expect(blocks.first).to_be_visible()
    _settle(page)
    return blocks.all()


@pytest.mark.parametrize("theme", THEMES)
def test_code_block_text_contrast(page: Page, designed_site, theme: str):
    """A5 (WCAG 1.4.3): every token in a Monokai code block meets 4.5:1, in both themes.

    `.highlight` had no base colour, so what the sheet doesn't colour (console
    output `.go`, the prompt `.gp`, untokenised text) took the body colour:
    1.87:1 on the dark block in light. Comments (`.c1`) were #75715e, 3.03:1, and
    the pink of operators (`.o`) and imports was #f92672, 3.93:1.
    """
    offenders, reached = [], set()
    for i, block in enumerate(_code_blocks(page, designed_site, theme)):
        measured, found = _sweep(page, block, f"{theme} code block #{i + 1}")
        offenders += found
        reached |= _names(measured)

    for name, what in (
        ("go", "console output"),
        ("gp", "prompt"),
        ("c1", "comment"),
        ("o", "operator"),
        ("code", "untokenised"),
    ):
        assert name in reached, f"the demo's code should render {what} text ({name}) to measure; reached {reached}"
    assert not offenders, _report(offenders, "code texts")
