"""No flash of the wrong theme: data-theme is on <html> before any stylesheet exists.

The CSS defaults to dark and keys the light theme on data-theme, so the attribute
must be set before the first stylesheet is inserted and keep that value for the
rest of the load. An init script records DOM mutations from document start, in
document order, so this needs no timing.

Cases cover every stored choice x OS preference, so a script that sets the wrong
theme first and corrects it later (a flash) fails as well.
"""

import itertools

import pytest
from playwright.sync_api import Page

# Logs each data-theme write on <html> (with the value it replaced) and each
# stylesheet insertion, starting before the parser creates <html>.
RECORDER = """
(() => {
  const log = [];
  const SHEETS = 'link[rel~="stylesheet" i], style';
  const isSheet = (node) => node.nodeType === 1 && (node.matches(SHEETS) || node.querySelector(SHEETS) !== null);
  const take = (records) => {
    for (const record of records) {
      if (record.type === 'attributes') {
        if (record.target === document.documentElement) log.push({kind: 'theme', old: record.oldValue});
      } else {
        for (const node of record.addedNodes) if (isSheet(node)) log.push({kind: 'stylesheet'});
      }
    }
  };
  const observer = new MutationObserver(take);
  observer.observe(document, {
    subtree: true, childList: true, attributes: true, attributeFilter: ['data-theme'], attributeOldValue: true,
  });
  window.__paintOrder = () => { take(observer.takeRecords()); return log; };
})();
"""

CASES = [
    pytest.param(stored, os_theme, id=f"{stored or 'none'}-{os_theme}")
    for stored, os_theme in itertools.product([None, "light", "dark"], ["light", "dark"])
]


def _paint_order(page: Page) -> tuple[list[str], list[str | None]]:
    """(event kinds in document order, each value data-theme took, in order)."""
    log = page.evaluate("window.__paintOrder()")
    final = page.evaluate("document.documentElement.getAttribute('data-theme')")
    olds = [entry["old"] for entry in log if entry["kind"] == "theme"]
    # A record carries the value its write replaced, so write n's value is record n+1's old value.
    writes = olds[1:] + [final] if olds else []
    return [entry["kind"] for entry in log], writes


@pytest.mark.parametrize("stored,os_theme", CASES)
def test_theme_is_set_before_first_stylesheet(page: Page, jekyll_server: str, stored: str | None, os_theme: str):
    """data-theme precedes every stylesheet and never changes afterwards during load."""
    page.emulate_media(color_scheme=os_theme)
    if stored:
        page.add_init_script(f"localStorage.setItem('theme', '{stored}')")
    page.add_init_script(RECORDER)
    page.goto(f"{jekyll_server}/about/")

    kinds, writes = _paint_order(page)
    assert "stylesheet" in kinds, f"the recorder saw no stylesheet, so nothing was measured: {kinds}"
    assert "theme" in kinds, "data-theme was never set on <html>"
    assert kinds.index("theme") < kinds.index("stylesheet"), f"data-theme set after a stylesheet was inserted: {kinds}"
    assert set(writes) == {stored or os_theme}, f"data-theme took {writes}; expected only {stored or os_theme!r}"
