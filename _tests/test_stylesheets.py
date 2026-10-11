"""Stylesheet hygiene: tokens, specificity, fonts, breakpoints, dead rules and motion
(css_audit.md B1, B2, B3, B6, B7, B8).

Invariants:
  - B1: no `!important` outside `@media (prefers-reduced-motion: reduce)`, where it is the
    standard way to beat every component's transition, and there only on motion properties.
    Components win by specificity, so a documented card variant such as `.card-no-hover`
    keeps its colours when hovered;
  - B2: the custom-property set is closed: every `var(--x)` in the stylesheets, templates
    and scripts names a declared property, and every declared property is read by a live
    rule (one whose selector can match the site's markup). Colour literals live only in
    the token file (dark-mode.css), the Monokai syntax theme, and an explicit allowlist of
    black-alpha shadows and scrims. `color-scheme` follows the theme on the page and is
    `dark` in the always-dark sidebar, so scrollbars and native controls match;
  - B3: the Google Fonts request asks only for families some `font-family` uses, and for
    each of them the faces the site sets (regular, bold, italic), so the browser never
    synthesises bold or oblique;
  - B6: breakpoints agree. Where a width is both an upper and a lower bound, exactly one
    side includes it (no width at which both or neither apply); no two bounds are
    near-duplicates (30em vs 30.1em); and the sidebar uses one type size at every width;
  - B7: every class selector matches markup the site can emit (templates, pages, scripts,
    kramdown/rouge output) or belongs to the card kit documented in card_guide.md; no two
    stylesheets set the same property for the same selector and media context, so no stale
    rule leaks a declaration into a live one; no vendor-prefixed property whose unprefixed
    form has long replaced it;
  - B8: with `prefers-reduced-motion: reduce`, nothing on the page transitions or animates
    for longer than 10ms (the sidebar, page, toggle, switch and cards included), while
    without the preference the sidebar still slides. The sidebar transitions named
    properties, never `all`, which also animated `z-index`.

The static checks read docs/public/css/*.css with a small hand parser (comments and
`data:` URIs stripped first) and docs/ sources directly, like discovery.py, so they need
no build. The browser checks use the real build for site-wide chrome (sidebar, cards on
the home page) and the designed build where they need several cards. Hover is waited on
with `expect` and finished transitions with `document.getAnimations()`, never a sleep.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from constants import SELECTORS
from playwright.sync_api import Page, expect
from sites import DOCS

CSS_DIR = DOCS / "public" / "css"
JS_DIR = DOCS / "public" / "js"
CARD_GUIDE = DOCS.parent / "_documentation" / "card_guide.md"
HEAD_INCLUDE = DOCS / "_includes" / "head.html"

# The token file holds every theme colour; Monokai is a third-party rouge theme whose
# token colours are its whole content. Colour literals are allowed only in these.
TOKEN_SHEET = "dark-mode.css"
SYNTAX_SHEET = "monokai.css"

# Black-alpha literals elsewhere, each a shadow or scrim that darkens whatever is under it
# and so reads the same in both themes. Keyed by (sheet, selector, property).
BLACK_ALPHA_ALLOWED = {
    ("features.css", ".command-palette", "background"): "scrim behind the open command palette",
    ("features.css", ".command-palette-panel", "box-shadow"): "drop shadow under the palette panel",
}

# The one place `!important` belongs: forcing near-zero durations over every component's
# own transition when the reader asks for reduced motion. The query must apply only then:
# no `not`, and no comma list that also matches some other condition.
IMPORTANT_ALLOWED_MEDIA = "(prefers-reduced-motion: reduce)"
_REDUCED_MOTION_QUERY = re.compile(r"\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)", re.I)
# Inside that block, only these may be forced: anything else is a specificity fix in hiding.
_MOTION_PROPERTY = re.compile(r"(transition|animation)(-[a-z-]+)?|scroll-behavior")

# Classes emitted by kramdown and rouge rather than by this repo's templates. (monokai.css,
# rouge's token theme, is exempt as a whole.)
GENERATED_CLASSES = frozenset(
    {"highlight", "highlighter-rouge", "footnotes", "footnote", "reversefootnote", "hll", "lineno", "gutter"}
)
GENERATED_PREFIXES = ("language-", "rouge-")

# The card kit: variants documented in _documentation/card_guide.md for future pages,
# kept although no template uses them yet (css_audit.md B7).
CARD_KIT = frozenset(
    {
        "card-highlight",
        "card-no-hover",
        "card-flat",
        "card-info",
        "card-warning",
        "card-success",
        "card-header",
        "card-subtitle",
        "card-footer",
        "card-tags",
        "card-tag",
        "card-grid-3",
        "card-grid-4",
    }
)

# Vendor prefixes still needed: iOS Safari ignores the unprefixed text-size-adjust.
PREFIXED_ALLOWED = frozenset({"-webkit-text-size-adjust"})

# Two breakpoints closer than this are one breakpoint written twice (30em vs 30.1em).
NEAR_DUPLICATE_EM = 0.25

# Reduced motion: `0.01ms !important` is the conventional "instant" duration.
INSTANT_S = 0.01
# Elements that move or fade on interaction, each of which must stop under reduced motion.
MOTION_TARGETS = [
    (".sidebar", ""),
    (".wrap", ""),
    (SELECTORS["sidebar_toggle"], ""),
    (".toggle-slider", ""),
    (".toggle-slider", "::before"),
    (SELECTORS["card"], ""),
]

# Viewport widths for the sidebar type-size sweep: phone, each side of the old 30em and
# the 48em breakpoints, tablet and desktop.
SIDEBAR_WIDTHS = [320, 479, 480, 600, 767, 768, 1024, 1280]

THEMES = ["dark", "light"]

# Every CSS named colour (CSS Color 4), matched as whole identifiers in declaration values.
NAMED_COLOURS = frozenset(
    """
    aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown
    burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan
    darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
    darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet
    deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro
    ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki
    lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow
    lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray
    lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine
    mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
    mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace
    olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred
    papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue
    saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue slategray slategrey
    snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow
    yellowgreen
    """.split()
)


# =============================================================================
# Reading the stylesheets
# =============================================================================


@dataclass(frozen=True)
class Declaration:
    prop: str
    value: str
    important: bool


@dataclass(frozen=True)
class Rule:
    sheet: str
    line: int
    media: tuple[str, ...]  # enclosing at-rule preludes, outermost first
    media_lines: tuple[int, ...]  # the line each of those at-rules starts on
    selector: str
    declarations: tuple[Declaration, ...]

    @property
    def selectors(self) -> list[str]:
        return _split_top_level(self.selector, ",")

    @property
    def where(self) -> str:
        context = "".join(f"{m} " for m in self.media)
        return f"{self.sheet}:{self.line} {context}{self.selector}"


_DATA_URI = re.compile(r"""url\(\s*(?:"data:[^"]*"|'data:[^']*'|data:[^)]*)\s*\)""")
_GROUPING_AT_RULES = ("@media", "@supports", "@container", "@layer", "@document", "@keyframes")


def _blank(text: str) -> str:
    """Same length and line breaks, no content: keeps offsets and line numbers valid."""
    return re.sub(r"[^\n]", " ", text)


def _strip_comments(css: str) -> str:
    out, i, quote = [], 0, None
    while i < len(css):
        ch = css[i]
        if quote:
            out.append(ch)
            if ch == "\\":
                out.append(css[i + 1 : i + 2])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif css.startswith("/*", i):
            end = css.find("*/", i + 2)
            end = len(css) if end < 0 else end + 2
            out.append(_blank(css[i:end]))
            i = end
            continue
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _clean(css: str) -> str:
    """Comments and data: URIs blanked out, offsets preserved."""
    css = _strip_comments(css)
    return _DATA_URI.sub(lambda m: "url(data:" + _blank(m.group(0))[9:-1] + ")", css)


def _split_top_level(text: str, sep: str) -> list[str]:
    """Split on `sep` outside strings, brackets and parentheses."""
    parts, depth, quote, start = [], 0, None, 0
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return [" ".join(p.split()) for p in parts if p.strip()]


def _matching_brace(text: str, open_at: int) -> int:
    depth, quote = 0, None
    for i in range(open_at, len(text)):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"unbalanced braces after offset {open_at}")


def _declarations(body: str) -> tuple[Declaration, ...]:
    decls = []
    for part in _split_top_level(body, ";"):
        prop, colon, value = part.partition(":")
        if not colon:
            continue
        prop = prop.strip()
        important = bool(re.search(r"!\s*important\s*$", value, re.I))
        value = re.sub(r"!\s*important\s*$", "", value, flags=re.I).strip()
        decls.append(Declaration(prop if prop.startswith("--") else prop.lower(), value, important))
    return tuple(decls)


def _parse(sheet: str, css: str) -> list[Rule]:
    """Style rules with their at-rule context. Handles the CSS this site writes: nested
    grouping at-rules, flat style rules, no CSS nesting."""
    rules: list[Rule] = []

    def line_of(start: int, end: int) -> int:
        text = css[start:end]
        return css.count("\n", 0, start + len(text) - len(text.lstrip())) + 1

    def block(start: int, end: int, media: tuple[str, ...], media_lines: tuple[int, ...]) -> None:
        i, prelude_at, quote = start, start, None
        while i < end:
            ch = css[i]
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
            elif ch == ";":  # a statement at-rule (@import, @charset)
                prelude_at = i + 1
            elif ch == "{":
                close = _matching_brace(css, i)
                prelude, line = " ".join(css[prelude_at:i].split()), line_of(prelude_at, i)
                if prelude.lower().startswith(_GROUPING_AT_RULES):
                    block(i + 1, close, (*media, prelude), (*media_lines, line))
                else:
                    rules.append(Rule(sheet, line, media, media_lines, prelude, _declarations(css[i + 1 : close])))
                i = prelude_at = close + 1
                continue
            i += 1

    css = _clean(css)
    block(0, len(css), (), ())
    return rules


@cache
def _sheets() -> dict[str, list[Rule]]:
    paths = sorted(CSS_DIR.glob("*.css"))
    assert paths, f"no stylesheets under {CSS_DIR}"
    return {p.name: _parse(p.name, p.read_text(encoding="utf-8")) for p in paths}


def _rules(*, exclude: tuple[str, ...] = ()) -> list[Rule]:
    return [rule for name, rules in _sheets().items() if name not in exclude for rule in rules]


# =============================================================================
# Reading the markup the site can emit
# =============================================================================

TEMPLATE_DIRS = ("_includes", "_layouts", "_pages", "essays")
TEMPLATE_SUFFIXES = {".html", ".md", ".xml", ".json"}
CONTENT_DIRS = ("_posts", "_previews")
VENDORED_JS = frozenset({"fuse.min.js"})  # mathjax/ is a subdirectory and never globbed


def _template_paths() -> list[Path]:
    paths = [p for p in DOCS.iterdir() if p.is_file() and p.suffix in TEMPLATE_SUFFIXES]
    for name in TEMPLATE_DIRS:
        paths += [p for p in (DOCS / name).rglob("*") if p.is_file() and p.suffix in TEMPLATE_SUFFIXES]
    return sorted(paths)


def _script_paths() -> list[Path]:
    return sorted(p for p in JS_DIR.glob("*.js") if p.name not in VENDORED_JS)


def _content_paths() -> list[Path]:
    return sorted(p for name in CONTENT_DIRS if (DOCS / name).is_dir() for p in (DOCS / name).rglob("*.md"))


_IDENT = re.compile(r"-?[A-Za-z_][\w-]*")


@cache
def _markup_words() -> frozenset[str]:
    """Every identifier-like word in the templates and scripts, plus the classes essays set
    with `class="..."` or a kramdown `{: .x}`. Liberal on purpose: a class that appears
    nowhere in that is certainly never emitted."""
    words: set[str] = set()
    for path in _template_paths() + _script_paths():
        words |= set(_IDENT.findall(path.read_text(encoding="utf-8", errors="ignore")))
    for path in _content_paths():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for attr in re.findall(r"""class\s*=\s*["']([^"']*)["']""", text):
            words |= set(attr.split())
        for ial in re.findall(r"\{:([^}]*)\}", text):
            words |= {m[1:] for m in re.findall(r"\.[\w-]+", ial)}
    assert {"sidebar", "masthead", "card"} <= words, "the markup corpus is missing the site's own classes"
    return frozenset(words)


def _classes(selector: str) -> set[str]:
    selector = re.sub(r"\[[^\]]*\]", "", selector)  # attribute selectors can hold dotted values
    return set(re.findall(r"\.(-?[A-Za-z_][\w-]*)", selector))


def _class_is_accounted_for(name: str) -> bool:
    return (
        name in _markup_words() or name in GENERATED_CLASSES or name.startswith(GENERATED_PREFIXES) or name in CARD_KIT
    )


def _selector_is_live(selector: str) -> bool:
    return all(_class_is_accounted_for(c) for c in _classes(selector))


def _rule_is_live(rule: Rule) -> bool:
    return rule.sheet == SYNTAX_SHEET or any(_selector_is_live(s) for s in rule.selectors)


# =============================================================================
# B1: specificity, not !important
# =============================================================================


def _reduced_motion_only(rule: Rule) -> bool:
    """True inside an @media block that applies only when the reader asks for reduced motion."""
    return any(
        _REDUCED_MOTION_QUERY.search(m) and not re.search(r"\bnot\b|,", m, re.I)
        for m in rule.media
        if m.lower().startswith("@media")
    )


def test_no_important_outside_reduced_motion():
    """B1: `!important` appears only inside `@media (prefers-reduced-motion: reduce)`, and
    there only on transition, animation and scroll-behavior properties.

    The old base link rules had more specificity than their comment claimed, and five
    component `!important`s fought them; one of those beat `.card-no-hover`. Hygiene
    (no WCAG criterion); the reduced-motion exception serves 2.3.3.
    """
    declarations = [(rule, d) for rule in _rules() for d in rule.declarations]
    assert len(declarations) > 100, f"only {len(declarations)} declarations parsed: the parser or the paths are wrong"
    offenders = []
    for rule, d in declarations:
        if not d.important:
            continue
        if not _reduced_motion_only(rule):
            offenders.append(f"{rule.where} {{ {d.prop}: {d.value} !important }}")
        elif not _MOTION_PROPERTY.fullmatch(d.prop):
            offenders.append(f"{rule.where} {{ {d.prop}: {d.value} !important }} (not a motion property)")
    assert not offenders, (
        f"{len(offenders)} !important declaration(s) outside @media {IMPORTANT_ALLOWED_MEDIA} or on a "
        "property that isn't about motion; lower the competing base rule with :where() instead:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("theme", THEMES)
def test_no_hover_card_keeps_its_colours_on_hover(page: Page, designed_site, theme: str):
    """B1: a `.card-no-hover` card (card_guide.md) does not change colour when hovered.

    The old `.card:hover .card-title { color: ... !important }` beat the variant's own
    `color: inherit`, so a no-hover card in light showed near-white text on a pale card.
    A regular card is hovered first, to prove the hover lands. Hygiene (no WCAG criterion);
    the failure mode is a 1.4.3 contrast failure.
    """
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
    page.goto(f"{designed_site.url}/")
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    links = page.locator(SELECTORS["card_link"])
    assert links.count() >= 2, f"the designed home page should list at least two cards, found {links.count()}"
    regular, variant = links.nth(0), links.nth(1)
    variant.locator(SELECTORS["card"]).evaluate("el => el.classList.add('card-no-hover')")

    paints = """el => {
      const card = el.querySelector('.card');
      const out = {background: getComputedStyle(card).backgroundColor, border: getComputedStyle(card).borderColor};
      for (const part of ['card-title', 'card-meta', 'card-body']) {
        out[part] = getComputedStyle(card.querySelector('.' + part)).color;
      }
      return out;
    }"""
    # getAnimations() flushes style, so once the pointer is on an element any transition its
    # hover starts is listed, and an empty list means every colour has settled.
    idle = "() => document.getAnimations().length === 0"
    page.wait_for_function(idle)
    regular_before, variant_before = regular.evaluate(paints), variant.evaluate(paints)

    regular.hover()
    expect(regular.locator(SELECTORS["card_title"])).not_to_have_css("color", regular_before["card-title"])

    variant.hover()
    page.wait_for_function("el => el.matches(':hover')", arg=variant.element_handle())
    page.wait_for_function(idle)
    variant_after = variant.evaluate(paints)
    changed = {k: f"{v} -> {variant_after[k]}" for k, v in variant_before.items() if v != variant_after[k]}
    assert not changed, f"a .card-no-hover card changed on hover in {theme} theme: {changed}"


# =============================================================================
# B2: tokens
# =============================================================================

_VAR_REF = re.compile(r"var\(\s*(--[\w-]+)")
_SCRIPT_READ = re.compile(r"""getPropertyValue\(\s*["'](--[\w-]+)""")
_SCRIPT_WRITE = re.compile(r"""setProperty\(\s*["'](--[\w-]+)""")


def _markup_texts() -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8", errors="ignore")) for p in _template_paths() + _script_paths()]


def test_custom_properties_are_declared_and_used():
    """B2: every `var(--x)` names a declared property, and every declared property is read
    by a live rule (a rule whose selector can match markup, see B7).

    Old: --overlay-bg was never read, and --pagination-border/-hover-bg were read only by
    Lanyon's dead `.pagination-item` rules. (--pagination-color was read by Lanyon's
    `.pagination`, which leaked into the live pagination; the two-stylesheet check in B7
    covers that.) Hygiene (no WCAG criterion).
    """
    declared: dict[str, list[str]] = defaultdict(list)
    referenced: dict[str, list[str]] = defaultdict(list)
    live_reads: set[str] = set()
    for rule in _rules():
        live = _rule_is_live(rule)
        for d in rule.declarations:
            if d.prop.startswith("--"):
                declared[d.prop].append(f"{rule.sheet}:{rule.line}")
            for name in _VAR_REF.findall(d.value):
                referenced[name].append(f"{rule.sheet}:{rule.line}")
                if live:
                    live_reads.add(name)
    for path, text in _markup_texts():
        where = str(path.relative_to(DOCS))
        for style in re.findall(r"""style\s*=\s*["']([^"']*)["']""", text):
            for name in re.findall(r"(--[\w-]+)\s*:", style):
                declared[name].append(where)
        for name in _SCRIPT_WRITE.findall(text):  # element.style.setProperty('--x', ...)
            declared[name].append(where)
        for name in _VAR_REF.findall(text) + _SCRIPT_READ.findall(text):
            referenced[name].append(where)
            live_reads.add(name)

    assert declared, "no custom properties found: the parser or the paths are wrong"
    undeclared = {name: sorted(set(at)) for name, at in referenced.items() if name not in declared}
    unread = {name: sorted(set(at)) for name, at in declared.items() if name not in live_reads}
    problems = [f"{name} is read at {at} but never declared" for name, at in sorted(undeclared.items())]
    problems += [
        f"{name} is declared at {at} but "
        + ("read only by dead rules at " + str(sorted(set(referenced[name]))) if name in referenced else "never read")
        for name, at in sorted(unread.items())
    ]
    assert not problems, "custom properties out of step:\n  " + "\n  ".join(problems)


_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_COLOUR_FN = re.compile(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\(\s*[^)]*\)", re.I)
_BLACK_ALPHA = re.compile(r"rgba?\(\s*0\s*,\s*0\s*,\s*0\s*,\s*[\d.]+%?\s*\)|rgba?\(\s*0\s+0\s+0\s*/\s*[\d.]+%?\s*\)")


def _colour_literals(value: str) -> list[str]:
    value = re.sub(r"""url\([^)]*\)|"[^"]*"|'[^']*'""", " ", value)
    found = _HEX.findall(value) + [m.group(0) for m in _COLOUR_FN.finditer(value)]
    words = re.findall(r"(?<![\w-])[A-Za-z]+(?![\w-])", value)
    return found + [w for w in words if w.lower() in NAMED_COLOURS]


def test_colour_literals_only_in_token_files():
    """B2: hard-coded colours (#hex, rgb()/hsl()..., named colours) appear only in the token
    file and the Monokai theme, apart from the allowlisted black-alpha shadows and scrims.

    Old: cards.css hard-coded #f39c12/#27ae60 for the warning/success rules (1.75 and 2.29
    on the light card, under 1.4.11's 3:1), and the search <mark> and palette selection used
    #fff. A literal outside the token file can't follow the theme. Hygiene (no WCAG criterion).
    """
    offenders = []
    checked = 0
    for rule in _rules(exclude=(TOKEN_SHEET, SYNTAX_SHEET)):
        for d in rule.declarations:
            checked += 1
            for literal in _colour_literals(d.value):
                allowed = any(
                    (rule.sheet, selector, d.prop) in BLACK_ALPHA_ALLOWED for selector in rule.selectors
                ) and _BLACK_ALPHA.fullmatch(literal)
                if not allowed:
                    offenders.append(f"{rule.where} {{ {d.prop}: {d.value} }} -> {literal}")
    assert checked, "no declarations read outside the token file"
    assert not offenders, (
        f"{len(offenders)} colour literal(s) outside {TOKEN_SHEET} and {SYNTAX_SHEET}; "
        "add a token instead:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("theme", THEMES)
def test_color_scheme_follows_theme(page: Page, jekyll_server: str, theme: str):
    """B2: the root's computed `color-scheme` is the theme, and the sidebar's is `dark` in
    both themes (it is always dark), so scrollbars and native controls match what's around
    them. Old: `normal` everywhere, so dark mode drew light scrollbars. Hygiene (supports
    1.4.11 for native control chrome).
    """
    page.add_init_script(f"localStorage.setItem('theme', '{theme}')")
    page.goto(f"{jekyll_server}/")
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    sidebar = page.locator(".sidebar")
    assert sidebar.count() == 1, "the page should have one sidebar"
    seen = {
        "html": page.locator("html").evaluate("el => getComputedStyle(el).colorScheme"),
        ".sidebar": sidebar.evaluate("el => getComputedStyle(el).colorScheme"),
    }
    expected = {"html": theme, ".sidebar": "dark"}
    wrong = {k: f"{seen[k]!r}, expected {expected[k]!r}" for k in expected if seen[k] != expected[k]}
    assert not wrong, f"color-scheme in {theme} theme: {wrong}"


# =============================================================================
# B3: fonts
# =============================================================================

# Faces every page uses whatever the stylesheets say: body text, the UA's bold for h1-h6,
# strong, b, th and dt, and the UA's italic for em and i (and the stylesheets' own
# `font-style: italic` on blockquotes). (italic, weight).
FACES_IN_USE = {(False, 400), (False, 700), (True, 400)}


def _google_font_faces(url: str) -> dict[str, list[tuple[bool, int, int]]]:
    """{family: [(italic, min weight, max weight)]} for a Google Fonts css or css2 URL."""
    parts = urlsplit(url)
    families: dict[str, list[tuple[bool, int, int]]] = {}
    for spec in parse_qs(parts.query).get("family", []):
        for item in spec.split("|") if parts.path.rstrip("/").endswith("/css") else [spec]:
            name, _, axes = item.partition(":")
            faces: list[tuple[bool, int, int]] = []
            if parts.path.rstrip("/").endswith("/css2"):
                names, _, tuples = axes.partition("@")
                keys = names.split(",") if names else []
                for values in tuples.split(";") if tuples else [""]:
                    got = dict(zip(keys, values.split(","))) if values else {}
                    lo, _, hi = got.get("wght", "400").partition("..")
                    faces.append((got.get("ital", "0") == "1", int(lo), int(hi or lo)))
            else:
                for variant in axes.split(",") if axes else ["400"]:
                    digits = re.match(r"\d*", variant).group(0)
                    rest = variant[len(digits) :].lower()
                    weight = int(digits) if digits else (700 if rest.startswith("b") else 400)
                    faces.append((rest.endswith("i") or "italic" in rest, weight, weight))
            families[name.strip()] = faces
    return families


def _font_families_in_css() -> set[str]:
    tokens = {d.prop: d.value for rule in _rules() for d in rule.declarations if d.prop.startswith("--")}
    families = set()
    for rule in _rules():
        for d in rule.declarations:
            if d.prop == "font-family":
                value = _VAR_REF.sub(lambda m: tokens.get(m.group(1), ""), d.value).replace(")", "")
                families |= {f.strip().strip("\"'").lower() for f in value.split(",") if f.strip()}
    return families


def test_google_fonts_request_matches_css():
    """B3: the Google Fonts <link> in head.html requests only families some `font-family`
    uses, and for each, regular, bold and italic faces, so none is synthesised.

    Old: `PT+Serif:400,400italic,700|PT+Sans:400` loaded PT Serif, used nowhere, and PT Sans
    only at 400, so headings, strong and dt were faux bold and blockquotes faux oblique.
    Hygiene (no WCAG criterion).
    """
    head = HEAD_INCLUDE.read_text(encoding="utf-8")
    urls = [u.replace("&amp;", "&") for u in re.findall(r"""href=["'](https://fonts\.googleapis\.com/[^"']+)""", head)]
    assert urls, f"no Google Fonts link in {HEAD_INCLUDE}; update this test if fonts are self-hosted"
    used = _font_families_in_css()
    assert used, "no font-family declarations found"
    problems = []
    for url in urls:
        for family, faces in _google_font_faces(url).items():
            if family.lower() not in used:
                problems.append(f"{family!r} is requested but no font-family uses it (used: {sorted(used)})")
                continue
            for italic, weight in sorted(FACES_IN_USE):
                if not any(i == italic and lo <= weight <= hi for i, lo, hi in faces):
                    face = f"{weight}{' italic' if italic else ''}"
                    problems.append(f"{family!r} is used at {face} but the request only has {faces}")
    assert not problems, "Google Fonts request out of step with the CSS:\n  " + "\n  ".join(problems)


# =============================================================================
# B6: breakpoints
# =============================================================================


@dataclass(frozen=True)
class Bound:
    axis: str  # width or height
    upper: bool  # True for max-width / width < X
    em: float
    inclusive: bool
    query: str
    where: str  # sheet:line of the @media block


_UNIT = r"([\d.]+)(px|em|rem)"
_MIN_MAX = re.compile(r"\(\s*(min|max)-(width|height)\s*:\s*" + _UNIT + r"\s*\)")
_RANGE = re.compile(r"\(\s*(width|height)\s*(<=|>=|<|>)\s*" + _UNIT + r"\s*\)")
_RANGE_REVERSED = re.compile(r"\(\s*" + _UNIT + r"\s*(<=|>=|<|>)\s*(width|height)\s*\)")


def _em(number: str, unit: str) -> float:
    return float(number) / 16 if unit == "px" else float(number)


def _bounds() -> list[Bound]:
    """Every width/height bound in every @media block, one entry per block."""
    bounds = set()
    for rule in _rules():
        for prelude, line in zip(rule.media, rule.media_lines):
            if not prelude.lower().startswith("@media"):
                continue
            where = f"{rule.sheet}:{line}"
            for kind, axis, n, unit in _MIN_MAX.findall(prelude):
                bounds.add(Bound(axis, kind == "max", _em(n, unit), True, prelude, where))
            for axis, op, n, unit in _RANGE.findall(prelude):
                bounds.add(Bound(axis, op.startswith("<"), _em(n, unit), op.endswith("="), prelude, where))
            for n, unit, op, axis in _RANGE_REVERSED.findall(prelude):
                bounds.add(Bound(axis, op.startswith(">"), _em(n, unit), op.endswith("="), prelude, where))
    return sorted(bounds, key=lambda b: (b.axis, b.em, b.where))


def test_breakpoints_do_not_overlap():
    """B6: where a width is both an upper and a lower bound, exactly one side includes it.

    `max-width: 48em` and `min-width: 48em` both match at exactly 768px, so both sets of
    rules apply there (and the 30em pair did the same); `width < 48em` with `min-width:
    48em` meets without overlap. Hygiene (no WCAG criterion).
    """
    bounds = _bounds()
    assert bounds, "no width/height media queries found: the parser or the paths are wrong"
    sides: dict[tuple, list[Bound]] = defaultdict(list)
    for b in bounds:
        sides[(b.axis, b.em, b.upper, b.inclusive)].append(b)

    def places(found: list[Bound]) -> str:
        queries = sorted({b.query for b in found})
        return f"{' / '.join(queries)} at {', '.join(b.where for b in found)}"

    problems = []
    for (axis, em, upper, inclusive), uppers in sorted(sides.items()):
        lowers = sides.get((axis, em, False, inclusive), []) if upper else []
        if lowers:
            what = "both sides match" if inclusive else "neither side matches"
            problems.append(f"at {axis} = {em:g}em {what}: {places(uppers)} vs {places(lowers)}")
    assert not problems, "overlapping or gapped breakpoints:\n  " + "\n  ".join(problems)


def test_breakpoints_are_not_near_duplicates():
    """B6: no two breakpoints on the same axis sit within 0.25em of each other.

    Old: 30em and 30.1em, one breakpoint written two ways. Hygiene (no WCAG criterion).
    """
    by_axis: dict[str, dict[float, list[str]]] = defaultdict(lambda: defaultdict(list))
    for b in _bounds():
        by_axis[b.axis][b.em].append(b.where)
    problems = []
    for axis, values in by_axis.items():
        ordered = sorted(values)
        for a, b in zip(ordered, ordered[1:]):
            if b - a < NEAR_DUPLICATE_EM:
                problems.append(f"{axis} {a:g}em (at {', '.join(values[a])}) vs {b:g}em (at {', '.join(values[b])})")
    assert not problems, "near-duplicate breakpoints; use one value:\n  " + "\n  ".join(problems)


FONT_SIZE_JS = "el => getComputedStyle(el).fontSize"


def test_sidebar_uses_one_type_size_at_every_width(page: Page, jekyll_server: str):
    """B6: at every viewport width the sidebar's nav, text and theme-toggle label share one
    font size.

    Old: `.sidebar` shrank its text at 30em but the theme toggle (and the search box and
    item padding) changed at 48em, so between 480 and 768px the sidebar mixed two sizes.
    Hygiene (no WCAG criterion).
    """
    page.goto(f"{jekyll_server}/")
    parts = {"nav item": ".sidebar-nav-item", "sidebar text": ".sidebar-item p", "toggle label": ".theme-toggle"}
    for selector in parts.values():
        assert page.locator(selector).count() > 0, f"{selector} should be in the sidebar"
    mismatches = []
    for width in SIDEBAR_WIDTHS:
        page.set_viewport_size({"width": width, "height": 720})
        # Settled values: a `transition: all` (B8) would otherwise animate the font size.
        page.wait_for_function(f"() => window.innerWidth === {width} && document.getAnimations().length === 0")
        sizes = {name: page.locator(sel).first.evaluate(FONT_SIZE_JS) for name, sel in parts.items()}
        if len(set(sizes.values())) > 1:
            mismatches.append(f"{width}px: {sizes}")
    assert not mismatches, "the sidebar mixes type sizes at:\n  " + "\n  ".join(mismatches)


# =============================================================================
# B7: dead and duplicate rules
# =============================================================================


def _dead_classes() -> dict[str, list[str]]:
    """{class: [sheet:line, ...]} for every class a selector styles that no markup emits.
    monokai.css, rouge's token theme, is exempt."""
    styled: dict[str, dict[str, None]] = defaultdict(dict)
    for rule in _rules(exclude=(SYNTAX_SHEET,)):
        for selector in rule.selectors:
            for name in _classes(selector):
                styled[name][f"{rule.sheet}:{rule.line}"] = None
    assert len(styled) > 20, f"only {len(styled)} classes found: the parser or the paths are wrong"
    return {name: list(at) for name, at in styled.items() if not _class_is_accounted_for(name)}


def test_every_class_selector_is_used():
    """B7: every class in a selector appears in markup the site can emit: the templates,
    pages and index files, the site's own scripts, an essay's class attribute, kramdown's
    and rouge's output, or the card kit allowlist.

    Old: .search-highlight (search.js emits <mark>), .related-posts, .pagination-item and
    .layout-reverse were never emitted, and Lanyon's .pagination and .related rules leaked
    declarations into the live components of the same name. The first clean-up also missed
    .card-meta-item, .related-posts-section, .search-results and .post-tags-label.
    Hygiene (no WCAG criterion).
    """
    dead = _dead_classes()
    problems = [f".{name} at {', '.join(at)}" for name, at in sorted(dead.items())]
    assert not problems, "classes styled but never emitted:\n  " + "\n  ".join(problems)


def test_card_kit_allowlist_is_documented():
    """B7: every class the card kit allowlist exempts from the dead-class check is documented
    in _documentation/card_guide.md, the reason the audit kept them. An undocumented class in
    the allowlist is dead CSS with an excuse. Hygiene (no WCAG criterion).
    """
    guide = CARD_GUIDE.read_text(encoding="utf-8")
    undocumented = sorted(c for c in CARD_KIT if not re.search(rf"(?<![\w-]){re.escape(c)}(?![\w-])", guide))
    assert not undocumented, f"card kit allowlist entries never mentioned in {CARD_GUIDE.name}: {undocumented}"


def test_no_property_declared_by_two_stylesheets():
    """B7: no property is set for the same selector, in the same media context, by two
    stylesheets. Each component's rules live in one file (colours in dark-mode.css, layout
    in lanyon.css, components in their own sheet).

    Old: Lanyon's `.related`, `.pagination` and `.sidebar { color; background-color }`
    restated what features.css, cards.css and dark-mode.css owned, so whichever loaded
    later won and the rest leaked. Hygiene (no WCAG criterion).
    """
    seen: dict[tuple, dict[str, str]] = defaultdict(dict)
    for rule in _rules():
        for selector in rule.selectors:
            for prop in dict.fromkeys(d.prop for d in rule.declarations):
                seen[(rule.media, selector, prop)].setdefault(rule.sheet, rule.where)
    assert seen, "no declarations found"
    duplicates = [
        f"{selector} {{ {prop} }}{' in ' + ' '.join(media) if media else ''}: {' | '.join(at.values())}"
        for (media, selector, prop), at in sorted(seen.items())
        if len(at) > 1
    ]
    assert not duplicates, f"{len(duplicates)} propert(ies) set by two stylesheets:\n  " + "\n  ".join(duplicates)


def test_no_obsolete_vendor_prefixes():
    """B7: no `-webkit-`, `-moz-`, `-ms-` or `-o-` property whose unprefixed form every
    supported browser has (transform, transition, backface-visibility, user-select ...).

    Old: Lanyon carried -webkit-/-ms- transform, transition and backface-visibility,
    -ms-text-size-adjust and -moz-user-select. Hygiene (no WCAG criterion).
    """
    offenders = [
        f"{rule.where} {{ {d.prop} }}"
        for rule in _rules(exclude=(SYNTAX_SHEET,))
        for d in rule.declarations
        if re.match(r"-(webkit|moz|ms|o)-", d.prop) and d.prop not in PREFIXED_ALLOWED
    ]
    assert not offenders, f"{len(offenders)} obsolete vendor-prefixed propert(ies):\n  " + "\n  ".join(offenders)


# =============================================================================
# B8: motion
# =============================================================================

_MOTION_JS = """
(targets) => {
  const seconds = (list) => list.split(',').map(s => s.trim())
    .map(s => s.endsWith('ms') ? parseFloat(s) / 1000 : parseFloat(s));
  const report = (el, pseudo, label) => {
    const style = getComputedStyle(el, pseudo || null);
    const animated = style.animationName.split(',').some(n => n.trim() !== 'none');
    const animation = animated ? Math.max(...seconds(style.animationDuration)) : 0;
    return {label, property: style.transitionProperty + (animated ? '; animation ' + style.animationName : ''),
            duration: style.transitionDuration + (animated ? '; ' + style.animationDuration : ''),
            longest: Math.max(animation, ...seconds(style.transitionDuration))};
  };
  const describe = (el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
    [...el.classList].map(c => '.' + c).join('');
  const named = targets.map(([selector, pseudo]) => {
    const els = [...document.querySelectorAll(selector)];
    const items = els.map(el => report(el, pseudo, describe(el) + pseudo));
    return {selector: selector + pseudo, count: els.length, items};
  });
  const everything = [];
  for (const el of document.querySelectorAll('*')) {
    for (const pseudo of ['', '::before', '::after']) everything.push(report(el, pseudo, describe(el) + pseudo));
  }
  return {named, everything};
}
"""


def _motion(page: Page) -> dict:
    return page.evaluate(_MOTION_JS, [list(t) for t in MOTION_TARGETS])


def test_reduced_motion_stops_transitions(new_context, jekyll_server: str):
    """B8: with `prefers-reduced-motion: reduce`, the sidebar, page wrapper, menu toggle,
    theme switch (and its knob) and cards, and everything else on the page, transition (and
    animate) in 10ms or less; without the preference the sidebar still slides (motion is not
    removed for everyone).

    Old: no reduced-motion handling; the sidebar slid over 0.3s, the switch over 0.4s and
    cards faded over 0.2s regardless. WCAG 2.3.3 Animation from Interactions (AAA).
    """
    durations = {}
    for preference in ("no-preference", "reduce"):
        page = new_context(reduced_motion=preference).new_page()
        response = page.goto(f"{jekyll_server}/")
        assert response is not None and response.ok, f"/ returned {response and response.status}"
        matches = page.evaluate("() => matchMedia('(prefers-reduced-motion: reduce)').matches")
        assert matches == (preference == "reduce"), f"the {preference} context reports reduce={matches}"
        durations[preference] = _motion(page)

    missing = {t["selector"] for run in durations.values() for t in run["named"] if not t["count"]}
    assert not missing, f"elements to measure are missing from the home page: {sorted(missing)}"

    sidebar = next(t for t in durations["no-preference"]["named"] if t["selector"] == ".sidebar")["items"][0]
    assert sidebar["longest"] >= 0.1, f"without a preference the sidebar should still slide, got {sidebar}"

    slow_named = [
        f"{item['label']}: {item['duration']} ({item['property']})"
        for target in durations["reduce"]["named"]
        for item in target["items"]
        if item["longest"] > INSTANT_S
    ]
    slow_other = sorted(
        {
            f"{item['label']}: {item['duration']} ({item['property']})"
            for item in durations["reduce"]["everything"]
            if item["longest"] > INSTANT_S
        }
        - set(slow_named)
    )
    assert not (slow_named or slow_other), (
        f"under prefers-reduced-motion: reduce these still transition for more than {INSTANT_S}s:\n  "
        + "\n  ".join(slow_named + slow_other[:10])
        + (f"\n  ... and {len(slow_other) - 10} more" if len(slow_other) > 10 else "")
    )


def test_sidebar_transitions_named_properties(page: Page, jekyll_server: str):
    """B8: the sidebar transitions the properties that move it, not `all`.

    Old: `.sidebar { transition: all .3s }`, which also animated z-index (and anything a
    later rule changes). Hygiene, in support of WCAG 2.3.3.
    """
    page.goto(f"{jekyll_server}/")
    sidebar = page.locator(".sidebar")
    assert sidebar.count() == 1, "the page should have one sidebar"
    properties = [p.strip() for p in sidebar.evaluate("el => getComputedStyle(el).transitionProperty").split(",")]
    assert not {"all", "z-index"} & set(properties), f"the sidebar should not transition all or z-index: {properties}"
    assert "transform" in properties, f"the sidebar should slide with a transform transition, got {properties}"
