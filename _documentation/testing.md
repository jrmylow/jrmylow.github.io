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

- **`conftest.py`** provides the session-scoped `jekyll_server` fixture. If a
  server already answers at `JEKYLL_URL` (default `http://localhost:4000`) it is
  reused; this is the CI case. Otherwise the fixture runs `jekyll build` once into
  a pytest temp directory, serves it with Python's `http.server`, and stops the
  server afterward. The browser runs headless at 1280x720.
- **`constants.py`** is the single source of shared values: `SELECTORS`, the
  theme colours (`DARK_BG_COLOR`, `LIGHT_BG_COLOR`), `ANIMATION_TIMEOUT`, and the
  `PERF_` budget. Import from here rather than hardcoding, so a UI change is a
  one-line edit.

## Test server

The fixture's design choices, recorded so they don't get undone:

- **Static server, not `jekyll serve`.** WEBrick, the server behind
  `jekyll serve`, stalls about 40 ms per response on reused keep-alive
  connections. At 13 CSS/JS files per page, that added roughly 400 ms to every
  load and dominated the performance budget. `http.server` serves each file in
  about 1 ms.
- **A snapshot built at session start.** Nothing watches for changes; re-run the
  suite to test new content. Building into a temp directory keeps the snapshot
  private, so `make serve` or `make preview` can run alongside a test run
  without either overwriting the other's output.
- **`site.url` override.** `jekyll serve` rewrites `site.url` to localhost in
  development; `jekyll build` does not, so `absolute_url` would point assets at
  production. The fixture writes a one-line config override into its temp
  directory to correct this.
- **Source reads are live.** `discovery.py` and the nav tests read front matter
  from `docs/` directly, not from the snapshot. Editing source mid-run can make
  their expectations drift from the build.

## Hermetic runs

`make test` runs the container with `--network=none`. Any runtime dependency on a
third-party origin fails there, so scripts the site needs are vendored into
`docs/public/js/`; Fuse.js, used by search, is vendored for this reason.
Third-party requests the tests don't depend on, such as Google Fonts and
GoatCounter, fail fast offline and are harmless.

## Red-green-refactor

Features are built test-first:

1. **Red** — write the smallest failing test for the next slice of behaviour;
   run it; confirm it fails for the expected reason.
2. **Green** — write the minimum code to make it pass.
3. **Refactor** — clean up with the test as a safety net.

This is the working loop for new work, not just a description of past work.

## Test content must not depend on real essays

Real posts come and go, so tests never hardcode their URLs:

- `TEST_PAGE_PATH` and a dedicated fixture page are used for page-level checks
  instead of a real post.
- `test_previews.py` walks the source folders, derives each document's URL the
  way Jekyll does (`YYYY-MM-DD-slug` -> `/YYYY/MM/DD/slug/`, honouring an
  explicit `permalink`), and parametrises over whatever it finds. Previews are
  tested in full; posts are sampled to bound runtime.

## Coverage

By area (`_tests/<file>` -> what it guards):

- `test_navigation` — the sidebar nav is derived from `nav_order` front matter
  and the rendered order matches the derived order.
- `test_theme_toggle`, `test_theme_flash` — the toggle switches and persists the
  theme; the inline script sets the theme before paint (no flash on navigation).
- `test_hamburger` — the sidebar toggle icon renders per theme.
- `test_cards` — card grid presence, required card elements, clickable cards,
  hover styling.
- `test_pagination` — the essays landing (max 5 posts + archive link) and the
  paginated `/essays/all/` archive (page info, prev/next).
- `test_search` — sidebar search, the `/search/` page, and `search-index.json`
  shape/contents.
- `test_analytics` — the GoatCounter script and dynamic noscript fallback (see
  `analytics.md`).
- `test_performance` — the budget below.
- `test_previews` — previews are reachable, carry `noindex`, and are absent from
  the listing, archive, search index, and feed.

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
uv run pytest _tests/test_theme_toggle.py::TestThemeToggle::test_toggle_switches_theme
```

Stop `make serve` first. Otherwise the fixture reuses its WEBrick server at
`localhost:4000`, and the performance budget fails.

Pre-commit runs `black` and `ruff` over `_tests/` plus a local Jekyll build
check; install it once with `uv run pre-commit install`.

## Fixture / drafts gotcha

The `jekyll_server` fixture builds **without** `--drafts`, so any page a test
navigates to must be reachable in a normal build. That is why the preview test
fixture lives in `docs/_previews/` (committed), not `docs/_drafts/`.

## CI

The harness is CI-ready: point `JEKYLL_URL` at a running build and the fixture
reuses it instead of building its own. That server must serve a static build
(`jekyll build` plus any static file server), not `jekyll serve`, or the
performance budget fails. Pre-commit intentionally defers the Jekyll build to CI.
Verify whether `.github/workflows/` actually contains the workflow that builds
the site and runs the suite — the harness assumes one exists, but the workflow
file should be confirmed in the repo.

## References
- Playwright (Python): <https://playwright.dev/python/docs/intro>
- pytest: <https://docs.pytest.org/>
- Navigation Timing: <https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Navigation_timing>
- Python `http.server`: <https://docs.python.org/3/library/http.server.html>
- `TCP_NODELAY` and delayed ACK, behind the WEBrick stall: <https://man7.org/linux/man-pages/man7/tcp.7.html>
