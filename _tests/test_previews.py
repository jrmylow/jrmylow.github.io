"""Tests for the `_previews` collection, driven by folder discovery.

Rather than hardcoding URLs (test content comes and goes), this walks the
source folders and derives each document's URL the way Jekyll does:
  - an explicit front-matter `permalink:` wins, otherwise
  - a `YYYY-MM-DD-slug` filename maps to `/YYYY/MM/DD/slug/`
    (matches both `permalink: pretty` posts without categories and the
    `previews` collection's `/:year/:month/:day/:title/` permalink).

Invariants:
  - every `_previews` doc is reachable, rendered as a post, and carries noindex,
    and appears in no listing, archive, search index, or feed;
  - published posts (a sample) are NOT noindexed.

Assumes these essays don't use post categories (none do); a categorised post
would get a different pretty URL than the derivation here.
"""

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

DOC_SUFFIXES = {".md", ".markdown", ".html"}
FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.(?:md|markdown|html)$")
PERMALINK_RE = re.compile(r"^\s*permalink:\s*(.+?)\s*$", re.MULTILINE)

# Sample size for the published-post control; override with POST_SAMPLE_SIZE=0
# to test every post.
POST_SAMPLE_SIZE = int(os.environ.get("POST_SAMPLE_SIZE", "0"))


def _slugify(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title.strip().lower())
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def _front_matter_permalink(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    m = PERMALINK_RE.search(text[3:end])
    if not m:
        return None
    val = m.group(1).strip().strip("'\"")
    if not val.startswith("/"):
        return None
    return val if val.endswith("/") else val + "/"


def _url_for(path: Path) -> str | None:
    explicit = _front_matter_permalink(path)
    if explicit:
        return explicit
    m = FILENAME_RE.match(path.name)
    if not m:
        return None
    yyyy, mm, dd, title = m.groups()
    return f"/{yyyy}/{mm}/{dd}/{_slugify(title)}/"


def _urls_in(dirname: str) -> list[str]:
    d = DOCS / dirname
    if not d.is_dir():
        return []
    urls = []
    for p in sorted(d.iterdir()):
        if p.is_file() and p.suffix in DOC_SUFFIXES:
            url = _url_for(p)
            if url:
                urls.append(url)
    return urls


def _params(urls: list[str], label: str):
    if not urls:
        return [pytest.param(None, marks=pytest.mark.skip(reason=f"no {label} found"))]
    return urls


PREVIEW_URLS = _urls_in("_previews")
ALL_POST_URLS = _urls_in("_posts")
POST_SAMPLE = ALL_POST_URLS if POST_SAMPLE_SIZE <= 0 else ALL_POST_URLS[:POST_SAMPLE_SIZE]


class TestPreviewCollection:
    @pytest.mark.parametrize("url", _params(PREVIEW_URLS, "_previews docs"))
    def test_preview_renders_with_noindex(self, page: Page, jekyll_server: str, url: str):
        resp = page.goto(f"{jekyll_server}{url}")
        assert resp.status == 200, f"Preview {url} should be reachable by direct link"
        assert page.locator(".post-title").count() >= 1, f"{url} should render via the post layout"
        robots = page.locator('meta[name="robots"]')
        assert robots.count() == 1, f"{url} should carry a robots meta tag"
        content = (robots.first.get_attribute("content") or "").lower()
        assert "noindex" in content, f"{url} robots meta should noindex, got {content!r}"

    @pytest.mark.parametrize("url", _params(PREVIEW_URLS, "_previews docs"))
    def test_preview_excluded_from_public_surfaces(self, page: Page, jekyll_server: str, url: str):
        for surface in ("/essays/", "/essays/all/", "/atom.xml"):
            page.goto(f"{jekyll_server}{surface}")
            assert url not in page.content(), f"{url} must not appear on {surface}"

        page.goto(f"{jekyll_server}/search-index.json")
        data = page.evaluate("() => JSON.parse(document.body.innerText)")
        urls = [item.get("url", "") for item in data]
        assert url not in urls, f"{url} must not appear in the search index"

    @pytest.mark.parametrize("url", _params(POST_SAMPLE, "_posts (sample)"))
    def test_published_post_not_noindexed(self, page: Page, jekyll_server: str, url: str):
        page.goto(f"{jekyll_server}{url}")
        robots = page.locator('meta[name="robots"]')
        if robots.count():
            content = (robots.first.get_attribute("content") or "").lower()
            assert "noindex" not in content, f"Published post {url} must not be noindexed"
