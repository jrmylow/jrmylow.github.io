import os
import signal
import subprocess
import sys
import time

import discovery
import pytest


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
def jekyll_server():
    """
    Start Jekyll server before tests, stop after.

    In CI, Jekyll is started separately, so we just return the URL.
    Locally, we start and stop the server.
    """
    base_url = os.environ.get("JEKYLL_URL", "http://localhost:4000")

    # Check if server is already running (CI environment)
    import urllib.request

    try:
        urllib.request.urlopen(base_url, timeout=2)
        # Server already running, just return URL
        yield base_url
        return
    except Exception:
        pass

    # Start server locally
    if sys.platform == "win32":
        proc = subprocess.Popen(
            [
                "bundle",
                "exec",
                "jekyll",
                "serve",
                "--source",
                "docs",
                "--destination",
                "docs/_site",
                "--port",
                "4000",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        proc = subprocess.Popen(
            [
                "bundle",
                "exec",
                "jekyll",
                "serve",
                "--source",
                "docs",
                "--destination",
                "docs/_site",
                "--port",
                "4000",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

    # Wait for server to start
    for _ in range(10):
        time.sleep(1)
        try:
            urllib.request.urlopen(base_url, timeout=2)
            break
        except Exception:
            continue

    yield base_url

    # Cleanup
    if sys.platform == "win32":
        proc.terminate()
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {"headless": True}


@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1280, "height": 720}}
