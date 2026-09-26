"""The suite's own guarantees: it fails on HTTP errors, tests the build it made, and its gates gate."""

import os
import re
import shlex
import shutil
import subprocess
import urllib.request
from pathlib import Path

import pytest
import yaml
from constants import BUILD_TOKEN_FILE
from playwright.sync_api import Page

REPO = Path(__file__).resolve().parent.parent


def _precommit_hooks() -> dict:
    config = yaml.safe_load((REPO / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    return {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}


@pytest.mark.allow_http_errors
def test_http_error_log_flags_a_404_navigation(page: Page, jekyll_server: str, http_errors):
    """page.goto doesn't raise on a 404; the autouse log must record it and fail the check."""
    page.goto(f"{jekyll_server}/definitely-not-a-page/")
    with pytest.raises(AssertionError, match="404"):
        http_errors.check()


def test_server_is_this_sessions_build(jekyll_server: str, build_token: str | None):
    """The suite tests the site it built, not whatever happens to be listening."""
    if build_token is None:
        pytest.skip("JEKYLL_URL is set: testing an external server on purpose")
    with urllib.request.urlopen(f"{jekyll_server}/{BUILD_TOKEN_FILE}", timeout=5) as response:
        assert response.read().decode() == build_token


@pytest.mark.skipif(shutil.which("bundle") is None, reason="needs bundle; runs in the container")
def test_precommit_build_hook_fails_on_a_broken_build(tmp_path):
    """The Jekyll hook must exit non-zero when the build fails, not print 'Skipping' and pass."""
    shutil.copytree(REPO / "docs", tmp_path / "docs", ignore=shutil.ignore_patterns("_site", "_drafts"))
    hook = shlex.split(_precommit_hooks()["jekyll-build"]["entry"])
    env = {**os.environ, "BUNDLE_GEMFILE": str(REPO / "Gemfile")}

    def run_hook():
        return subprocess.run(hook, cwd=tmp_path, env=env, capture_output=True, text=True)

    control = run_hook()
    assert control.returncode == 0, f"hook fails on the unbroken site:\n{control.stdout}{control.stderr}"

    (tmp_path / "docs" / "broken.md").write_text("---\n---\n{% if true %}\n")
    broken = run_hook()
    assert broken.returncode != 0, f"hook passed a broken build:\n{broken.stdout}"


def test_precommit_rejects_drafts():
    """workflow.md promises a pre-commit backstop that keeps docs/_drafts/ out of commits."""
    blockers = [
        hook
        for hook in _precommit_hooks().values()
        if hook.get("language") == "fail" and re.search(hook.get("files", "^$"), "docs/_drafts/2026-01-01-wip.md")
    ]
    assert blockers, "no `language: fail` hook matches docs/_drafts/"
    assert not any(re.search(hook["files"], "docs/_posts/2026-01-01-wip.md") for hook in blockers)
