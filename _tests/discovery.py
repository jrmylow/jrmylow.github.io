"""Discover posts and previews from the source tree and derive their URLs.

Single source of truth for "what content exists", so tests run against whatever
is in docs/_posts and docs/_previews instead of hardcoded paths that rot when
test content is added or removed.

URL derivation matches Jekyll:
  - an explicit front-matter `permalink:` wins, otherwise
  - a `YYYY-MM-DD-slug` filename maps to `/YYYY/MM/DD/slug/`
    (`permalink: pretty` for posts; the `previews` collection permalink).

Assumes essays don't use post categories (none do); a categorised post would get
a different pretty URL than the derivation here.
"""

import re
from pathlib import Path

import pytest
import yaml

DOCS = Path(__file__).resolve().parent.parent / "docs"
DOC_SUFFIXES = {".md", ".markdown", ".html"}
_FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.(?:md|markdown|html)$")


def _slugify(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title.strip().lower())
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def _front_matter(path: Path) -> dict:
    """Parse a file's YAML front-matter block, or {} if absent/invalid."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)  # ['', '<yaml>', '<body>']
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def url_for(path: Path) -> str | None:
    """The URL Jekyll will serve this document at, or None if underivable."""
    explicit = _front_matter(path).get("permalink")
    if isinstance(explicit, str) and explicit.startswith("/"):
        return explicit if explicit.endswith("/") else explicit + "/"
    m = _FILENAME_RE.match(path.name)
    if not m:
        return None
    yyyy, mm, dd, title = m.groups()
    return f"/{yyyy}/{mm}/{dd}/{_slugify(title)}/"


def _docs_in(dirname: str) -> list[Path]:
    d = DOCS / dirname
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file() and p.suffix in DOC_SUFFIXES)


def post_paths() -> list[Path]:
    return _docs_in("_posts")


def preview_paths() -> list[Path]:
    return _docs_in("_previews")


def post_urls() -> list[str]:
    return [u for p in post_paths() if (u := url_for(p))]


def post_tags() -> list[str]:
    """Sorted, de-duplicated tags declared across published posts.

    Scoped to _posts because the tag cloud and search index are built from
    site.posts; previews are excluded from both.
    """
    seen = set()
    for p in post_paths():
        tags = _front_matter(p).get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        seen.update(t.strip() for t in tags if isinstance(t, str) and t.strip())
    return sorted(seen)


def preview_urls() -> list[str]:
    return [u for p in preview_paths() if (u := url_for(p))]


def tagged_post_urls() -> list[str]:
    """Posts and previews whose front matter declares at least one tag."""
    out = []
    for p in post_paths() + preview_paths():
        if _front_matter(p).get("tags") and (u := url_for(p)):
            out.append(u)
    return out


def params(urls: list[str], label: str):
    """Parametrize values, or a single skip marker when the source folder is
    empty, so missing content skips cleanly instead of erroring at collection."""
    if not urls:
        return [pytest.param(None, marks=pytest.mark.skip(reason=f"no {label} found"))]
    return urls
