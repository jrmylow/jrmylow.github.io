"""Theme state over its whole input space: stored choice x OS preference x event.

The contract: an explicit choice (localStorage `theme`) wins; with nothing stored
the site follows the OS preference live, and only a toggle stores a choice.

Every case sets the OS preference. Playwright emulates light by default, so a
test that stores `light` against that default can't tell "used the stored
choice" from "followed the OS".
"""

import itertools

import pytest
from constants import DARK_BG_COLOR, LIGHT_BG_COLOR, SELECTORS
from playwright.sync_api import Page, expect

STORED = [None, "light", "dark"]
OS_THEMES = ["light", "dark"]
EVENTS = ["load", "toggle", "os_change"]
BACKGROUND = {"light": LIGHT_BG_COLOR, "dark": DARK_BG_COLOR}


def _other(theme: str) -> str:
    return "dark" if theme == "light" else "light"


def expected(stored: str | None, os_theme: str, event: str) -> tuple[str, str | None]:
    """(theme shown, value stored) after the event."""
    shown = stored or os_theme
    if event == "load":
        return shown, stored
    if event == "toggle":
        return _other(shown), _other(shown)
    return stored or _other(os_theme), stored  # os_change: the OS preference flips


def _change_os(page: Page, theme: str) -> None:
    """Flip the emulated OS preference and wait until the page has handled it.

    Waits for the change event on a fresh MediaQueryList, then one animation
    frame. Browsers fire every media-query `change` listener before running
    animation frame callbacks (HTML "update the rendering",
    https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model),
    so the site's listener has run by then, whichever order the listeners were called in.
    """
    page.evaluate(
        """() => {
            window.__osChanged = false;
            window.__osQuery = matchMedia('(prefers-color-scheme: light)');
            window.__osQuery.addEventListener('change', () => { window.__osChanged = true; });
        }"""
    )
    page.emulate_media(color_scheme=theme)
    page.wait_for_function("window.__osChanged")
    page.evaluate("() => new Promise((done) => requestAnimationFrame(() => done()))")


CASES = [
    pytest.param(stored, os_theme, event, id=f"{stored or 'none'}-{os_theme}-{event}")
    for stored, os_theme, event in itertools.product(STORED, OS_THEMES, EVENTS)
]


@pytest.mark.parametrize("stored,os_theme,event", CASES)
def test_theme_state(page: Page, jekyll_server: str, stored: str | None, os_theme: str, event: str):
    """Shown theme, background, toggle checkbox and stored value after each event."""
    page.emulate_media(color_scheme=os_theme)
    if stored:
        # An init script runs before any page script, so the choice is in place for the first paint.
        page.add_init_script(f"localStorage.setItem('theme', '{stored}')")
    page.goto(jekyll_server)

    if event == "toggle":
        page.locator(SELECTORS["sidebar_toggle"]).click()
        page.locator(SELECTORS["theme_toggle"]).click()
    elif event == "os_change":
        _change_os(page, _other(os_theme))

    shown, kept = expected(stored, os_theme, event)
    expect(page.locator(SELECTORS["html"])).to_have_attribute("data-theme", shown)
    expect(page.locator(SELECTORS["body"])).to_have_css("background-color", BACKGROUND[shown])
    expect(page.locator(SELECTORS["theme_toggle_input"])).to_be_checked(checked=shown == "light")
    stored_now = page.evaluate("localStorage.getItem('theme')")
    assert stored_now == kept, f"localStorage theme is {stored_now!r}, expected {kept!r}"
