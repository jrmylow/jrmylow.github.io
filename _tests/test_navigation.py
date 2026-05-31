"""Tests for sidebar navigation, derived from page front-matter.

Nav membership and order are driven by a `nav_order` front-matter key, sorted
ascending. The test does NOT hardcode the order: it reads `nav_order` out of
the page sources (via PyYAML) and asserts the rendered nav matches that derived
list. Renumber `nav_order` freely and the test recomputes the expectation.

Mirrors the Liquid in _includes/sidebar.html:
    site.pages | where_exp: "p", "p.nav_order" | sort: "nav_order"
with label = nav_title | default: title.
"""

from pathlib import Path
from typing import List, Optional

import yaml
from constants import ANIMATION_TIMEOUT, SELECTORS
from playwright.sync_api import Page

# --- Front-matter discovery (matches Jekyll's site.pages) --------------------


def _site_root() -> Path:
    """Locate the Jekyll site source, whether at repo root or under docs/."""
    here = Path(__file__).resolve()
    for base in [here.parent, *here.parents]:
        for cand in (base / "_pages", base / "docs" / "_pages"):
            if cand.is_dir():
                return cand.parent
    raise FileNotFoundError("Could not locate a _pages directory")


def _front_matter(path: Path) -> Optional[dict]:
    """Parse a file's YAML front-matter block, or None if absent/invalid."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)  # ['', '<yaml>', '<body>']
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _candidate_pages(root: Path) -> List[Path]:
    """Files Jekyll treats as pages: _pages/** plus root-level .md/.html."""
    paths: List[Path] = []
    pages_dir = root / "_pages"
    if pages_dir.is_dir():
        paths += [p for p in pages_dir.rglob("*") if p.is_file()]
    for ext in ("*.md", "*.markdown", "*.html"):
        paths += list(root.glob(ext))
    return paths


def expected_nav_labels() -> List[str]:
    """Ordered nav labels derived from front-matter, sorted by nav_order."""
    root = _site_root()
    entries = []
    for path in _candidate_pages(root):
        fm = _front_matter(path)
        if not fm or "nav_order" not in fm:
            continue
        order = fm["nav_order"]
        if not isinstance(order, int):
            continue  # nav_order must be an integer to participate
        label = fm.get("nav_title") or fm.get("title") or ""
        entries.append((order, label))
    entries.sort(key=lambda e: e[0])
    return [label for _, label in entries]


# --- Helpers -----------------------------------------------------------------


def _open_sidebar(page: Page, jekyll_server: str):
    page.goto(f"{jekyll_server}/")
    page.locator(SELECTORS["sidebar_toggle"]).click()
    page.wait_for_timeout(ANIMATION_TIMEOUT)


def _nav_labels(page: Page) -> List[str]:
    return [line.strip() for line in page.locator(".sidebar-nav-item").all_text_contents()]


# --- Tests -------------------------------------------------------------------


class TestPathResolution:
    """Guards the site/page resolver independent of any nav_order front-matter.

    Distinguishes "no page declares nav_order yet" from "resolver found nothing",
    so an empty nav result can never be silently misattributed to a path bug.
    """

    def test_site_root_has_pages_dir(self):
        """Resolver locates a site root containing a _pages directory."""
        root = _site_root()
        assert (root / "_pages").is_dir(), f"No _pages under resolved root {root}"

    def test_candidate_pages_found(self):
        """Page discovery returns the known page sources, by filename."""
        names = {p.name for p in _candidate_pages(_site_root())}
        for expected in ("about.md", "contact.md", "essays.md", "tags.md"):
            assert expected in names, f"{expected} not discovered; got {sorted(names)}"


class TestNavDiscovery:
    """Guards that front-matter discovery is working."""

    def test_core_pages_opt_in(self):
        """About, Essays, Tags, Contact should declare nav_order (any order)."""
        labels = set(expected_nav_labels())
        assert {
            "About",
            "Essays",
            "Tags",
            "Contact",
        } <= labels, f"Core nav pages missing from front-matter discovery: {labels}"

    def test_home_not_in_nav(self):
        """Home/Welcome has no nav_order, so it must not be discovered."""
        labels = expected_nav_labels()
        assert "Home" not in labels and "Welcome" not in labels, f"Home should not declare nav_order: {labels}"


class TestNavRendering:
    """The rendered nav must match the front-matter-derived order exactly."""

    def test_nav_matches_front_matter(self, page: Page, jekyll_server: str):
        """Rendered sidebar nav equals nav_order-sorted labels from sources."""
        expected = expected_nav_labels()
        assert expected, "No nav pages discovered; parser or paths are wrong"

        _open_sidebar(page, jekyll_server)
        assert _nav_labels(page) == expected, f"Rendered nav {_nav_labels(page)} != derived {expected}"
