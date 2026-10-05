import functools
import os

import discovery
import pytest
import sites


def pytest_addoption(parser):
    parser.addoption(
        "--scale-posts",
        type=int,
        default=None,
        metavar="N",
        help="build the designed site with N posts: its designed cases plus generated filler",
    )


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
def real_site(tmp_path_factory):
    """The site built from docs/ as-is (production content), served for the session.

    Set JEKYLL_URL to test an already-running server instead; it must answer.
    """
    external = os.environ.get("JEKYLL_URL")
    if external:
        yield sites.external(external)
        return
    with sites.served(tmp_path_factory.mktemp("real"), sites.real_source) as site:
        yield site


@pytest.fixture(scope="session")
def designed_site(tmp_path_factory, pytestconfig):
    """The site built with corpus.py's content instead of docs/ content, served for the session."""
    make_source = functools.partial(sites.designed_source, total_posts=pytestconfig.getoption("scale_posts"))
    with sites.served(tmp_path_factory.mktemp("designed"), make_source) as site:
        yield site


@pytest.fixture(scope="session")
def jekyll_server(real_site) -> str:
    """URL of the real build; what most tests need."""
    return real_site.url


@pytest.fixture(scope="session")
def build_token(real_site) -> str | None:
    """The token written into this session's real build; None when JEKYLL_URL points at an external server."""
    return real_site.token


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {"headless": True}


@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1280, "height": 720}}
