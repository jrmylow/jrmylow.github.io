"""Colour helpers for the accessibility tests (test_a11y_*.py).

WCAG 2.2 relative luminance and contrast ratio, plus page-side functions that
resolve what a reader actually sees. Text and border colours are composited
through their own alpha, every background behind them, and every ancestor's
`opacity` (each ancestor's opacity applies to its whole subtree against the
backdrop beneath it, as browsers paint it). Background images are ignored: no
text on this site sits on one.

The page-side functions walk DOM ancestry, not visual stacking, which is exact
for this site's layout (no text is positioned over an unrelated element).
"""

from playwright.sync_api import Locator

# The minimums from WCAG 2.2 1.4.3 (text) and 1.4.11 (UI component boundaries,
# focus indicators). Large text is >= 24px, or >= 18.66px (14pt) at bold.
TEXT_MIN = 4.5
LARGE_TEXT_MIN = 3.0
NON_TEXT_MIN = 3.0

_COMPOSITE_JS = """
(el, paint) => {
  const parse = (s) => {
    const m = s && s.match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    const p = m[1].split(/[\\s,\\/]+/).filter(Boolean).map(parseFloat);
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  };
  const over = (top, under) => [0, 1, 2].map(i => top[3] * top[i] + (1 - top[3]) * under[i]);
  const mix = (a, b, t) => [0, 1, 2].map(i => t * a[i] + (1 - t) * b[i]);

  const chain = [];
  for (let n = el; n && n.nodeType === 1; n = n.parentElement) chain.unshift(n);

  let cur = [255, 255, 255];  // the canvas, before the root background is painted
  const groups = [];          // [backdrop under the node, node opacity] for each opacity < 1
  for (const n of chain) {
    const style = getComputedStyle(n);
    const opacity = parseFloat(style.opacity);
    if (opacity < 1) groups.push([cur, opacity]);
    const bg = parse(style.backgroundColor);
    if (bg && bg[3] > 0) cur = over(bg, cur);
  }
  const background = cur;
  let fg = paint ? over(parse(paint(getComputedStyle(el))), cur) : cur;
  let bgOut = background;
  for (let i = groups.length - 1; i >= 0; i--) {
    const [under, opacity] = groups[i];
    fg = mix(fg, under, opacity);
    bgOut = mix(bgOut, under, opacity);
  }
  return {fg: fg.map(Math.round), bg: bgOut.map(Math.round)};
}
"""

# Effective [r, g, b] of the element's text and of the background behind it.
TEXT_COLOURS_JS = f"(el) => ({_COMPOSITE_JS})(el, (s) => s.color)"

# Effective [r, g, b] behind the element: its parent's composited background.
BACKDROP_JS = f"(el) => ({_COMPOSITE_JS})(el.parentElement, null).bg"


def luminance(rgb: list[float]) -> float:
    """WCAG 2.2 relative luminance of an sRGB colour given as 0-255 channels."""

    def channel(value: float) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: list[float], b: list[float]) -> float:
    """WCAG 2.2 contrast ratio between two colours, 1.0 to 21.0."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def parse_rgb(css: str) -> list[float]:
    """[r, g, b, a] from a computed `rgb()`/`rgba()` string."""
    inner = css[css.index("(") + 1 : css.rindex(")")]
    parts = [float(p) for p in inner.replace(",", " ").replace("/", " ").split()]
    return parts if len(parts) == 4 else parts + [1.0]


def text_contrast(locator: Locator) -> tuple[float, list[int], list[int]]:
    """(ratio, fg, bg) for the element's text as rendered, opacity and alpha included."""
    colours = locator.evaluate(TEXT_COLOURS_JS)
    return contrast(colours["fg"], colours["bg"]), colours["fg"], colours["bg"]


def text_minimum(locator: Locator) -> float:
    """The 1.4.3 minimum for the element's text: 3:1 if large, else 4.5:1."""
    size, weight = locator.evaluate(
        "el => { const s = getComputedStyle(el); return [parseFloat(s.fontSize), s.fontWeight]; }"
    )
    large = size >= 24 or (size >= 18.66 and int(weight) >= 700)
    return LARGE_TEXT_MIN if large else TEXT_MIN


def against_backdrop(locator: Locator, css_colour: str) -> float:
    """Contrast of a computed colour (a border or outline) composited over the element's backdrop."""
    backdrop = locator.evaluate(BACKDROP_JS)
    r, g, b, a = parse_rgb(css_colour)
    painted = [a * c + (1 - a) * u for c, u in zip((r, g, b), backdrop)]
    return contrast(painted, backdrop)
