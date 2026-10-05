"""Build and serve the sites under test.

A session builds up to two sites, each from a temp copy of docs/:

- real: docs/ as-is, i.e. production content;
- designed: docs/ with its _posts and _previews replaced by corpus.py's content.

Copies, not symlinks: GitHub Pages builds in safe mode, and a copy doesn't depend on
how symlinks are treated. Both builds get fixtures/test-manifest.json, a Liquid page
recording what Jekyll made of each document (URL, title, date, tags), so tests take
URLs from Jekyll rather than re-deriving its permalink rules.

Sites are served with http.server rather than `jekyll serve`: WEBrick stalls ~40ms
per response on keep-alive connections, which dominated page-load timings. Each
server gets a free port, so a running `make serve` is never picked up by accident.
"""

import contextlib
import json
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import corpus
import pytest
from constants import BUILD_TOKEN_FILE

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
DOCS = REPO / "docs"
MANIFEST = "test-manifest.json"
NOT_SOURCE = ("_site", ".jekyll-cache", ".jekyll-metadata", "_drafts")  # output, caches, local drafts
CONTENT = ("_posts", "_previews")


@dataclass(frozen=True)
class Site:
    url: str
    token: str | None  # None for an external JEKYLL_URL server this session didn't build
    manifest: dict | None  # None if the server was built without the test manifest

    def document(self, filename: str) -> dict:
        """The manifest entry (path, url, title, date, tags) for a post or preview, by source file name."""
        if self.manifest is None:
            pytest.skip(f"{self.url} has no {MANIFEST}: it wasn't built by this suite")
        for entry in self.manifest["posts"] + self.manifest["previews"]:
            if Path(entry["path"]).name == filename:
                return entry
        raise LookupError(f"{filename} is not in {self.url}/{MANIFEST}: Jekyll didn't build it")


def _answers(url: str) -> bool:
    """True if something responds at url."""
    try:
        urllib.request.urlopen(url, timeout=1)
        return True
    except OSError:
        return False


def _free_port() -> int:
    """A port nothing is listening on."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _copy_docs(dest: Path, *, with_content: bool) -> Path:
    ignore = NOT_SOURCE if with_content else NOT_SOURCE + CONTENT
    shutil.copytree(DOCS, dest, ignore=shutil.ignore_patterns(*ignore))
    shutil.copy(TESTS / "fixtures" / MANIFEST, dest / MANIFEST)
    return dest


def real_source(dest: Path) -> Path:
    """docs/ as-is, plus the test manifest."""
    return _copy_docs(dest, with_content=True)


def designed_source(dest: Path, total_posts: int | None = None) -> Path:
    """docs/ layouts and pages with corpus.py's posts and previews, plus the test manifest."""
    src = _copy_docs(dest, with_content=False)
    corpus.write(src, total_posts)
    return src


def _build(src: Path, out: Path, url: str) -> None:
    # `jekyll serve` rewrites site.url to localhost; `jekyll build` doesn't, so
    # absolute_url would point at production without this override.
    override = src.parent / "_config_test.yml"
    override.write_text(f'url: "{url}"\n', encoding="utf-8")
    config = f"{src / '_config.yml'},{override}"
    command = ["bundle", "exec", "jekyll", "build", "--source", str(src), "--destination", str(out), "--config", config]
    subprocess.run(command, check=True, cwd=REPO)


@contextlib.contextmanager
def served(root: Path, make_source: Callable[[Path], Path]) -> Iterator[Site]:
    """Build make_source(root / "src") and serve it on a free port until the block exits."""
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    out = root / "_site"
    _build(make_source(root / "src"), out, url)

    # Lets tests confirm the server they talk to is this session's build.
    token = secrets.token_hex(16)
    (out / BUILD_TOKEN_FILE).write_text(token)
    manifest = json.loads((out / MANIFEST).read_text(encoding="utf-8"))

    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(out)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            if _answers(url):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"http.server did not answer at {url} within 5s")
        yield Site(url, token, manifest)
    finally:
        proc.terminate()
        proc.wait()


def external(url: str) -> Site:
    """An already-running server (JEKYLL_URL). It must answer; its manifest is used if present."""
    if not _answers(url):
        raise RuntimeError(
            f"JEKYLL_URL={url} is set but nothing answers there. Unset it to build and serve "
            "the site here (older dev images set it by default: rerun `make build`)."
        )
    try:
        with urllib.request.urlopen(f"{url}/{MANIFEST}", timeout=5) as response:
            manifest = json.load(response)
    except (urllib.error.URLError, ValueError):
        manifest = None
    return Site(url, None, manifest)
