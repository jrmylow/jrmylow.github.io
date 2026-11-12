"""Check that the suite catches known bugs.

mutations.py lists deliberate bugs ("mutations"): each is one small edit to the site's
source, plus the tests that should fail because of it. For each one this script copies
the repo to a temp directory, makes the edit there, and runs those tests on the copy.
The working tree is never touched.

A mutation ends one of three ways:

- caught: a named test failed, which is the point;
- survived: the named tests passed, or all skipped, so they don't check what they claim to;
- broken: the tests couldn't run (the edit broke the build or an import), which tells us
  nothing, so the mutation needs rewriting.

Run it with `make mutate`, or `make mutate ARGS="tag"` for the mutations whose name
contains "tag". It exits non-zero unless every mutation it ran was caught. Mutations
run a few at a time (--jobs); each has its own copy of the repo and its own servers.
"""

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOT_COPIED = (".git", ".venv", "_site", ".jekyll-cache", "__pycache__", ".pytest_cache", ".ruff_cache")
TIMEOUT_SECONDS = 600


@dataclass(frozen=True)
class Mutation:
    name: str  # the bug, in words
    path: str  # the file to edit, relative to the repo root
    old: str  # text that occurs exactly once in that file
    new: str  # what replaces it
    tests: tuple[str, ...]  # test files or node ids, relative to the repo root, that must catch it


@dataclass(frozen=True)
class Result:
    outcome: str  # "caught", "survived" or "broken"
    detail: str  # caught: the first test that failed; otherwise why


class StaleMutation(Exception):
    """The text a mutation replaces isn't in its file exactly once."""


def apply(root: Path, mutation: Mutation) -> None:
    """Make the mutation's edit in the repo at root."""
    path = root / mutation.path
    source = path.read_text(encoding="utf-8")
    count = source.count(mutation.old)
    if count != 1:
        raise StaleMutation(f"{mutation.name}: {mutation.old!r} found {count} times in {mutation.path}, expected once")
    path.write_text(source.replace(mutation.old, mutation.new), encoding="utf-8")


def _read(report: Path, output: str) -> Result:
    """What a pytest run made of a mutation, from its JUnit report and printed summary."""
    if not report.is_file():
        return Result("broken", "pytest wrote no report: " + output.strip()[-300:])
    suite = ET.parse(report).getroot().find("testsuite")
    count = {name: int(suite.get(name, 0)) for name in ("tests", "failures", "errors", "skipped")}
    if count["errors"]:
        return Result("broken", f"{count['errors']} test(s) errored before they could check anything")
    if count["failures"]:
        failed = [line.split()[1] for line in output.splitlines() if line.startswith("FAILED ")]
        return Result("caught", failed[0] if failed else "a test failed")
    if count["tests"] == count["skipped"]:
        return Result("survived", "no named test ran")
    return Result("survived", f"{count['tests'] - count['skipped']} test(s) passed")


def check(mutation: Mutation, root: Path = REPO) -> Result:
    """Run the mutation's tests against a mutated copy of the repo at root."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(root, copy, ignore=shutil.ignore_patterns(*NOT_COPIED))
        apply(copy, mutation)
        report = Path(tmp) / "report.xml"
        # -x: one failure is enough. -p no:cacheprovider: leave nothing behind for the next run.
        command = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", f"--junitxml={report}"]
        try:
            run = subprocess.run(
                [*command, *mutation.tests], cwd=copy, capture_output=True, text=True, timeout=TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired:
            return Result("broken", f"the tests ran for more than {TIMEOUT_SECONDS}s")
        return _read(report, run.stdout)


def main(argv: list[str]) -> int:
    from mutations import MUTATIONS

    parser = argparse.ArgumentParser(description="Check that the suite catches the bugs listed in mutations.py.")
    parser.add_argument("words", nargs="*", help="only run mutations whose name contains one of these")
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="mutations to run at once")
    args = parser.parse_args(argv)

    chosen = [m for m in MUTATIONS if not args.words or any(word in m.name for word in args.words)]
    if not chosen:
        print(f"no mutation's name contains any of {args.words}")
        return 2
    caught = 0
    # Each check is a pytest subprocess on its own copy of the repo, so threads are enough.
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for mutation, result in zip(chosen, pool.map(check, chosen)):
            caught += result.outcome == "caught"
            print(f"{result.outcome:9} {mutation.name}\n          {result.detail}", flush=True)
    print(f"\n{caught} of {len(chosen)} caught")
    return 0 if caught == len(chosen) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
