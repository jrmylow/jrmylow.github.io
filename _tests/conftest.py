import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

import discovery
import pytest

JEKYLL_BUILD = "bundle exec jekyll build --source docs".split()


def _answers(url: str) -> bool:
    """True if something responds at url."""
    try:
        urllib.request.urlopen(url, timeout=1)
        return True
    except OSError:
        return False


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
def jekyll_server(tmp_path_factory):
    """
    Build the site once into a temp dir and serve it statically for the session.

    If a server already answers at JEKYLL_URL (e.g. CI), reuse it.
    Uses http.server rather than `jekyll serve`: WEBrick stalls ~40ms per
    response on keep-alive connections, which dominated page-load timings.
    """
    base_url = os.environ.get("JEKYLL_URL", "http://localhost:4000")
    if _answers(base_url):
        yield base_url
        return

    # `jekyll serve` rewrites site.url to localhost in dev; `build` does not, so
    # absolute_url would point at production without this override.
    tmp = tmp_path_factory.mktemp("jekyll")
    site = tmp / "_site"
    override = tmp / "_config_test.yml"
    override.write_text(f'url: "{base_url}"\n')
    subprocess.run([*JEKYLL_BUILD, "--destination", str(site), "--config", f"docs/_config.yml,{override}"], check=True)

    port = str(urllib.parse.urlsplit(base_url).port or 80)
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", port, "--bind", "127.0.0.1", "--directory", str(site)],
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
def browser_type_launch_args():
    return {"headless": True}


@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1280, "height": 720}}
