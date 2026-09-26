import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request

import discovery
import pytest
from constants import BUILD_TOKEN_FILE

JEKYLL_BUILD = "bundle exec jekyll build --source docs".split()
BUILD_TOKEN = pytest.StashKey[str]()


def _answers(url: str) -> bool:
    """True if something responds at url."""
    try:
        urllib.request.urlopen(url, timeout=1)
        return True
    except OSError:
        return False


def _free_port() -> int:
    """A port nothing is listening on, so the test server can't collide with `make serve`."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class HttpErrorLog:
    """Top-level navigations in one test that returned HTTP >= 400."""

    def __init__(self, page):
        self.page = page
        self.errors: list[str] = []
        page.on("response", self._record)

    def _record(self, response) -> None:
        request = response.request
        if request.is_navigation_request() and request.frame == self.page.main_frame and response.status >= 400:
            self.errors.append(f"{response.status} {response.url}")

    def check(self) -> None:
        assert not self.errors, f"Navigation returned HTTP errors: {self.errors}"


@pytest.fixture(autouse=True)
def http_errors(request):
    """
    Fail any test whose top-level navigation returns HTTP >= 400.

    page.goto doesn't raise on a 404, so without this a wrong URL loads an error
    page and the test runs against it. Tests that expect an error page opt out
    with @pytest.mark.allow_http_errors and assert the status themselves.
    """
    if "page" not in request.fixturenames:
        yield None
        return
    log = HttpErrorLog(request.getfixturevalue("page"))
    yield log
    if not request.node.get_closest_marker("allow_http_errors"):
        log.check()


@pytest.fixture
def any_post_url() -> str:
    """A representative published post URL; skips if _posts is empty."""
    urls = discovery.post_urls()
    if not urls:
        pytest.skip("no _posts found in source tree")
    return urls[0]


@pytest.fixture
def any_post_tag() -> str:
    """A tag declared by some published post; skips if none exist."""
    tags = discovery.post_tags()
    if not tags:
        pytest.skip("no post tags found in source tree")
    return tags[0]


@pytest.fixture(scope="session")
def jekyll_server(tmp_path_factory, pytestconfig):
    """
    Build the site once into a temp dir and serve it statically for the session.

    Serves on a free port, so a running `make serve` is never picked up by
    accident. Set JEKYLL_URL to test an already-running server instead; it
    must answer. Uses http.server rather than `jekyll serve`: WEBrick stalls
    ~40ms per response on keep-alive connections, which dominated page-load timings.
    """
    external = os.environ.get("JEKYLL_URL")
    if external:
        if not _answers(external):
            raise RuntimeError(
                f"JEKYLL_URL={external} is set but nothing answers there. Unset it to build and serve "
                "the site here (older dev images set it by default: rerun `make build`)."
            )
        yield external
        return

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    # `jekyll serve` rewrites site.url to localhost in dev; `build` does not, so
    # absolute_url would point at production without this override.
    tmp = tmp_path_factory.mktemp("jekyll")
    site = tmp / "_site"
    override = tmp / "_config_test.yml"
    override.write_text(f'url: "{base_url}"\n')
    subprocess.run([*JEKYLL_BUILD, "--destination", str(site), "--config", f"docs/_config.yml,{override}"], check=True)

    # Lets tests confirm the server they talk to is this session's build.
    token = secrets.token_hex(16)
    (site / BUILD_TOKEN_FILE).write_text(token)
    pytestconfig.stash[BUILD_TOKEN] = token

    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(site)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            if _answers(base_url):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"http.server did not answer at {base_url} within 5s")
        yield base_url
    finally:
        proc.terminate()
        proc.wait()


@pytest.fixture(scope="session")
def build_token(jekyll_server, pytestconfig) -> str | None:
    """The token written into this session's build; None when JEKYLL_URL points at an external server."""
    return pytestconfig.stash.get(BUILD_TOKEN, None)


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {"headless": True}


@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1280, "height": 720}}
