# Testing

The test philosophy, how the suite is organised, what it covers, the performance
budget, and the red-green-refactor loop. The environment these run in is in
`container.md`.

## Philosophy

End-to-end, behavioural testing with Playwright against a real Jekyll build.
Tests assert what a user can observe — rendered DOM, computed styles, resolved
URLs, HTTP status — not implementation details. This is deliberate: the site has
been through several CSS and template consolidations, and behavioural tests stay
green across refactors that would break tests coupled to selectors-as-structure
or to specific markup.

## Stack and layout

`uv` + `pytest` + `pytest-playwright`. Tests live in `_tests/`.

- **`conftest.py`** provides the session-scoped `real_site` and `designed_site`
  fixtures (below) and `jekyll_server`, the real build's URL, which most tests
  use. The autouse `http_errors` fixture fails tests on HTTP errors (below). The
  browser runs headless at 1280x720.
- **`sites.py`** builds and serves both sites and loads each build's manifest.
- **`corpus.py`** is the designed build's content: hand-picked cases as data,
  plus generated filler for scale runs. The fixture files it copies in live in
  `_tests/fixtures/`.
- **`constants.py`** is the single source of shared values: `SELECTORS`, the
  theme colours (`DARK_BG_COLOR`, `LIGHT_BG_COLOR`), and the
  `PERF_` budget. Import from here rather than hardcoding, so a UI change is a
  one-line edit.

## Test server

The fixtures' design choices, recorded so they don't get undone:

- **Static server, not `jekyll serve`.** WEBrick, the server behind
  `jekyll serve`, stalls about 40 ms per response on reused keep-alive
  connections. At 13 CSS/JS files per page, that added roughly 400 ms to every
  load and dominated the performance budget. `http.server` serves each file in
  about 1 ms.
- **Two builds, each a snapshot.** `real_site` builds `docs/` as-is;
  `designed_site` builds the same layouts and pages with `corpus.py`'s posts
  and previews in place of `docs/_posts` and `docs/_previews`. Each builds once,
  on first use, from a temp copy of `docs/` (a copy, not symlinks: Pages builds
  in safe mode). Nothing watches for changes; re-run the suite to test new
  content. The temp copies keep the builds private, so `make serve` or
  `make preview` can run alongside a test run.
- **A manifest, not re-derived URLs.** Each build gets
  `_tests/fixtures/test-manifest.json`, a test-only Liquid page listing every
  post and preview as Jekyll built it: path, URL, title, date and tags.
  `Site.document(filename)` looks one up by source file name, so tests take URLs
  from Jekyll instead of re-deriving its permalink rules. `test_harness.py`
  checks each manifest lists exactly its build's sources.
- **`site.url` override.** `jekyll serve` rewrites `site.url` to localhost in
  development; `jekyll build` does not, so `absolute_url` would point assets at
  production. Each build gets a one-line config override, written outside its
  source copy, to correct this.
- **Source reads are live.** `discovery.py` and the nav tests read front matter
  from `docs/` directly, not from the snapshot. Editing source mid-run can make
  their expectations drift from the build. `discovery.py` raises if `docs/` has
  no `_config.yml`, so a wrong root can't turn content tests into skips.
- **Free ports; external servers only on request.** The fixtures never probe
  `localhost:4000`, so a running `make serve` can't stand in for a build under
  test. Each build gets its own token, and `test_harness.py` checks each server
  returns its own.

## HTTP errors fail tests

`page.goto` does not raise on a 404, so a wrong URL loads an error page and the
test runs against it. The autouse `http_errors` fixture fails any test whose
top-level navigation returns 400 or above. A test that expects an error page
opts out with `@pytest.mark.allow_http_errors` and asserts the status itself.

## Hermetic runs

`make test` runs the container with `--network=none`. Any runtime dependency on a
third-party origin fails there, so scripts the site needs are vendored into
`docs/public/js/`; Fuse.js, used by search, is vendored for this reason.
Third-party requests the tests don't depend on, such as Google Fonts and
GoatCounter, fail fast offline and are harmless.

## Waiting

No fixed sleeps. Playwright actions already wait for an element to be visible,
stable and in view, and `expect(...)` assertions retry until they pass, so wait
on the condition rather than the clock. Two traps:

- `force=True` skips those waits, and one-shot reads such as `is_visible()` or
  `get_attribute()` check once without retrying. Both can catch the sidebar
  mid-transition.
- A negative assertion ("live results never appear") has no event to wait on,
  so it keeps a short fixed window before asserting absence.

An emulated OS preference change arrives as a media-query `change` event, with
no DOM change to wait on. `test_theme_matrix.py` listens for that event itself
and then waits one animation frame. Browsers fire every `change` listener
before animation frame callbacks, so its negative cases need no fixed window.

## Red-green-refactor

Features are built test-first:

1. **Red** — write the smallest failing test for the next slice of behaviour;
   run it; confirm it fails for the expected reason.
2. **Green** — write the minimum code to make it pass.
3. **Refactor** — clean up with the test as a safety net.

This is the working loop for new work, not just a description of past work.

## Test content must not depend on real essays

Real posts come and go, so tests never hardcode their URLs:

- Tests that need particular content run on the designed build, whose content
  is data in `corpus.py`. Fixture files, such as the previews in
  `_tests/fixtures/_previews/`, are copied into the designed build only, so they
  are never published.
- Tests over real content parametrise over the source files that exist
  (`discovery.py`) and take each file's URL from the real build's manifest.
  `POST_SAMPLE_SIZE` limits `test_previews.py`'s published-post check to the
  first N posts; by default it checks every post.

## Coverage

By area (`_tests/<file>` -> what it guards):

- `test_navigation` — the sidebar nav is derived from `nav_order` front matter
  and the rendered order matches the derived order.
- `test_theme_matrix` — the theme over its whole state space: stored choice
  (none, light, dark) × OS preference × load, toggle or OS change. Each case
  checks the theme shown, the background, the toggle checkbox and what is
  stored.
- `test_theme_flash` — `data-theme` is set on `<html>` before the first
  stylesheet is inserted and keeps that value for the rest of the load.
- `test_hamburger` — the sidebar toggle icon renders per theme.
- `test_cards` — card grid presence, required card elements, clickable cards,
  hover styling.
- `test_pagination` — the essays landing (max 5 posts + archive link) and the
  paginated `/essays/all/` archive: the page count follows `paginate`, every
  post appears exactly once, and each page's nav matches its position.
- `test_search` — sidebar search, the `/search/` page, and `search-index.json`
  shape/contents.
- `test_analytics` — the GoatCounter script and dynamic noscript fallback (see
  `analytics.md`).
- `test_performance` — the budget below.
- `test_previews` — preview fixtures (designed build) are reachable, carry
  `noindex`, and are absent from the listing, archive, search index, and feed;
  published posts (real build) are not noindexed.
- `test_harness`, `test_discovery`, `test_corpus` — the suite itself: HTTP
  errors fail tests, each server is this session's build, each manifest lists
  exactly its build's sources, the pre-commit gates fail when they should,
  discovery refuses a wrong site root, and the corpus scales as asked.

Tag and callout suites may also exist depending on what has shipped; check
`_tests/` for the current set.

## Performance budget

The thresholds are regression tripwires for local runs against the test server,
not user-experience targets. They sit at roughly 2-3x measured values: enough
headroom for a busy machine, tight enough that a new render-blocking resource or
a server stall trips them. Metrics come from the browser Navigation Timing API,
averaged over `PERF_ITERATIONS` (10) runs per page with a p90, across
`PERF_TEST_PAGES`. All values live in `constants.py`:

- TTFB: avg < 100 ms, p90 < 200 ms
- DOM Interactive: p90 < 200 ms
- DOMContentLoaded: avg < 250 ms, p90 < 250 ms
- Load complete: avg < 250 ms, p90 < 250 ms
- Per page: < 20 resources, < 500 KB transferred, < 1500 DOM nodes; no single
  page load over 3000 ms.

Measured in September 2026: about 60 ms DOM Interactive, 65 ms DOMContentLoaded
and 72 ms load, averaged across pages. The homepage averages about 95 ms because
it takes each test's cold first load. If the site changes shape, re-measure with
`make test ARGS="-s _tests/test_performance.py"` and re-derive the thresholds.

## Running the suite

```sh
make test                            # canonical: sealed offline in the container
make test IT=                        # same, for CI (drops the TTY flags; no terminal attached)
make test ARGS="-s --durations=25"   # pass flags through to pytest
```

Without the container, run pytest directly; the fixture builds and serves the
site itself (needs Ruby and Bundler on the host):

```sh
uv run pytest
uv run pytest _tests/test_search.py
uv run pytest "_tests/test_theme_matrix.py::test_theme_state[none-light-toggle]"
```

The test servers use free ports, so `make serve` can keep running.

Scale runs build the designed site with N posts in total: its designed cases
plus generated filler, all older than the designed cases. Only tests on the
designed build see them; the real build is always production content.

```sh
make test ARGS="--scale-posts=1000"
```

Pre-commit runs `black` and `ruff` over `_tests/` (ruff's `BLE` rules reject a
blind `except Exception`), a Jekyll build check that fails when the build
fails, and a hook that rejects anything under `docs/_drafts/`. Install it once
with `uv run pre-commit install`.

## Fixtures and drafts

Neither build uses `--drafts`, so any page a test navigates to must be reachable
in a normal build. Test fixtures live in `_tests/fixtures/` and are copied into
the designed build only; nothing test-only is published.

## CI

`.github/workflows/test.yml` runs on every push and pull request. It builds the
image, syncs the venv volume, and runs `make test IT=`, so CI and local runs
use the same sealed container.

To test a server that is already running instead, set `JEKYLL_URL`. It must
serve a static build (`jekyll build` plus any static file server), not
`jekyll serve`, or the performance budget fails. It replaces the real build
only, and tests that need the manifest skip unless that server has one.

## References
- Playwright (Python): <https://playwright.dev/python/docs/intro>
- Playwright actionability checks: <https://playwright.dev/python/docs/actionability>
- pytest: <https://docs.pytest.org/>
- HTML event loop, where media-query `change` events fire before animation frame callbacks: <https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model>
- `MutationObserver`: <https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver>
- pre-commit `fail` hooks for blocking files by name: <https://adamj.eu/tech/2024/01/24/pre-commit-fail-hook/>
- Navigation Timing: <https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Navigation_timing>
- Python `http.server`: <https://docs.python.org/3/library/http.server.html>
- `TCP_NODELAY` and delayed ACK, behind the WEBrick stall: <https://man7.org/linux/man-pages/man7/tcp.7.html>
