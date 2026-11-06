"""Tests for the header toggles: the menu's (hamburger, left) and the table of contents'
(list, right, on posts with a TOC).

Both share one face (.icon-toggle in lanyon.css): an icon masked over currentColor, so
a single colour token per theme paints both. Closed, the icon takes the theme's colour on
the page background; open, the toggle takes the sidebar's blue, the same in both themes,
with a white icon and a 1px ring. The viewport is below 80em, where the TOC starts closed.
"""

import pytest
from constants import DARK_BG_COLOR, LIGHT_BG_COLOR, TOGGLE_ICON_COLORS, TOGGLE_ICON_OPEN_COLOR
from playwright.sync_api import Page, expect

TOC_DEMO = "2024-04-01-toc-demo.md"
NARROW = {"width": 1024, "height": 768}
PAGE_BG = {"dark": DARK_BG_COLOR, "light": LIGHT_BG_COLOR}

# name -> (selector, url(site), selector that shows once it is open)
TOGGLES = {
    "menu": (".sidebar-toggle", lambda site: f"{site.url}/", "#sidebar"),
    "contents": (".toc-toggle", lambda site: f"{site.url}{site.document(TOC_DEMO)['url']}", ".toc-list a"),
}

ICON_JS = """el => {
  const s = getComputedStyle(el, '::before');
  return {colour: s.backgroundColor, width: s.width, height: s.height, mask: s.maskImage || s.webkitMaskImage};
}"""


def _load(page: Page, site, name: str, theme: str):
    selector, url, _ = TOGGLES[name]
    page.set_viewport_size(NARROW)
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
    page.goto(url(site))
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    toggle = page.locator(selector)
    expect(toggle).to_be_visible()
    return toggle


def _style(locator, prop: str) -> str:
    return locator.evaluate(f"el => getComputedStyle(el).{prop}")


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("name", TOGGLES)
def test_closed_icon_takes_the_theme_colour(page: Page, designed_site, name: str, theme: str):
    toggle = _load(page, designed_site, name, theme)
    icon = toggle.evaluate(ICON_JS)
    assert (icon["width"], icon["height"]) == ("32px", "32px"), f"{name} icon is {icon['width']} x {icon['height']}"
    assert "url(" in icon["mask"], f"{name} icon has no mask: {icon['mask']}"
    assert icon["colour"] == TOGGLE_ICON_COLORS[theme], f"{name} icon in {theme}: {icon['colour']}"
    assert _style(toggle, "backgroundColor") == PAGE_BG[theme]


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("name", TOGGLES)
def test_open_toggle_is_white_on_the_sidebar_blue(page: Page, designed_site, name: str, theme: str):
    toggle = _load(page, designed_site, name, theme)
    toggle.click()
    expect(page.locator(TOGGLES[name][2]).first).to_be_visible()
    sidebar_blue = _style(page.locator(".sidebar"), "backgroundColor")
    assert toggle.evaluate(ICON_JS)["colour"] == TOGGLE_ICON_OPEN_COLOR
    assert _style(toggle, "backgroundColor") == sidebar_blue
    assert "0px 0px 0px 1px" in _style(toggle, "boxShadow"), f"{name}: open ring is {_style(toggle, 'boxShadow')}"


def test_the_toggles_show_different_icons(page: Page, designed_site):
    contents = _load(page, designed_site, "contents", "dark")
    menu = page.locator(TOGGLES["menu"][0])
    assert menu.evaluate(ICON_JS)["mask"] != contents.evaluate(ICON_JS)["mask"]
