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

A test earns its place by failing when the behaviour breaks. Three habits keep
that true:

- **State the answer.** Assert the exact list, text or count, not "at least
  one" or "not empty". `count() >= 1` passes on the wrong posts.
- **Design the case.** Put content on both sides of each boundary, and make the
  sides unequal. With alpha on four posts and beta on two, of which one has
  both, "all selected tags", "any selected tag" and "no filter at all" each
  show a different number of posts. With two posts and one tag each, they
  don't.
- **No guards.** A test that skips or passes when its content is missing is not
  testing. If the real site has no post with a series, the series test belongs
  on the designed build, which does.

`make mutate` (below) checks the result: it breaks the site in known ways and
expects the suite to notice.

## Stack and layout

`uv` + `pytest` + `pytest-playwright`. Tests live in `_tests/`.

- **`conftest.py`** provides the session-scoped `real_site` and `designed_site`
  fixtures (below) and `jekyll_server`, the real build's URL, which most tests
  use. The autouse `http_errors` fixture fails tests on HTTP errors (below). The
  browser runs headless at 1280x720.
- **`sites.py`** builds and serves both sites and loads each build's manifest.
  The designed build also gets `/test-cards.html`, a test-only page showing
  every post's card, since the home and essays pages show only the newest few.
- **`corpus.py`** is the designed build's content: named cases as data
  (`ALPHA_BETA`, `LINKS_OUT`, `SERIES_FIRST`, ...), each there to show one
  thing, plus generated filler for scale runs. The fixture files it copies in
  live in `_tests/fixtures/`.
- **`mutate.py`** and **`mutations.py`** are the mutation check (below).
- **`constants.py`** is the single source of shared values: `SELECTORS`, the
  theme colours (`DARK_BG_COLOR`, `LIGHT_BG_COLOR`), and the
  `PERF_` budget. Import from here rather than hardcoding, so a UI change is a
  one-line edit.
- **`a11y.py`** holds the WCAG 2.2 contrast maths for `test_a11y.py`: it
  composites a colour through its alpha, every background behind it and every
  ancestor's `opacity`, as the browser paints it, and reports the same ratios
  axe-core does.

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

axe-core reaches the sealed run as a Python dependency, not a download:
`axe-playwright-python` (in `pyproject.toml`, hash-pinned in `uv.lock`) bundles
Deque's `axe.min.js`, and the wrapper only reads that file and injects it into
the page under test. `make sync`, the networked step, installs it into the venv;
`make test` then runs with no network. Bumping it bumps the axe rules, so read
the new rules' changelog before accepting a lock upgrade.

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

## Mutation check

`_tests/mutations.py` lists known bugs: each is a one-line edit to a template or
script, such as "the tag filter shows posts with any selected tag, not all of
them", with the test files that must catch it. `make mutate` copies the repo to
a temp directory once per bug, makes the edit in the copy, and runs those tests
there. The working tree is never touched.

```sh
make mutate                # every mutation, a few at a time
make mutate ARGS="tag"     # those whose name contains "tag"
```

Each mutation ends one of three ways, and the command fails unless all are
caught:

- **caught** — a named test failed. The output names the test.
- **survived** — the named tests passed, or all skipped. They don't check what
  they appear to.
- **broken** — the tests couldn't run, because the edit broke the build or an
  import. That says nothing about the tests, so rewrite the mutation.

When a bug gets past the suite, add it to the list along with the test that now
catches it. A mutation should be a mistake someone could plausibly make that
leaves the site building. `test_mutate.py` checks, without a build, that each
mutation's text still occurs exactly once in its file, so a mutation the source
has moved away from fails loudly.

The list is not coverage: a feature with no mutation is unchecked, not safe.
It covers tags, related, references, series, search, the command palette and
cards.

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
- `test_header_toggles` — both header toggles (menu, contents), in both themes:
  the icon renders in the theme's colour on the page background, and open, it
  is white on the sidebar blue with a 1px ring; each has hover text matching its
  accessible name.
- `test_cards` — the home page shows the six newest posts and the essays
  landing the five newest, newest first (the designed build has more than
  either); a card shows the title, date and reading time, and the summary when
  the post has one, otherwise its first paragraph; the home grid is two columns
  on a desktop and one on a phone. One strict xfail records a bug: see
  "Known bugs" below.
- `test_essays` — the essays landing's archive link, sidebar entry and intro,
  and the `/essays/all/` archive: one page, every post exactly once under its
  year, years and posts newest first, each entry with a reading time.
- `test_tags` — a post lists its tags, each linking to the tags page filtered
  to it; the cloud lists each tag once, in order, with its post count; each
  selection, by click or by address, shows exactly the posts with every
  selected tag, including when no post has them all, and a tag is not matched
  inside a longer tag; deselecting widens the filter, then empties it.
- `test_related` — "Related" lists the newest three other posts sharing a tag,
  at, under and over the limit; a post with no tags, or tags nobody shares, has
  no block.
- `test_backlinks` — "Referenced by" lists the posts that link to this one,
  newest first; a post nobody links to, or that only links to itself, has no
  block. One strict xfail records a gap: see `page.md`.
- `test_series` — each part lists the series in series order, which differs
  from date order, and marks itself; a series of one has no navigation.
- `test_feed` — `/atom.xml` parses as XML in both builds and uses the Atom
  namespace; its entries are the published posts, newest first, with their
  titles and links (the designed build has a title containing `&` and `<`);
  every entry has a summary, taken from front matter when there is one and
  otherwise from the first paragraph, cut to 50 words; the autodiscovery link
  declares `application/atom+xml`, and the sidebar links to the feed.
- `test_reading_time` — the designed long post rounds up to the expected
  minutes on its page and its card; a one-line post shows one minute.
- `test_reply_by_email` — every post and preview ends with one mailto: link to
  the site address whose subject, percent-decoded, is "Re: " plus the post's
  title (the designed build has a title with spaces, `&` and `<`); the line's
  only other link leads to the contact page; other pages have no such line.
- `test_search` — the sidebar box only redirects to `/search/`;
  `search-index.json` lists every post, newest first, with its title, address
  and tags; a word found only in a tag, only in a title or only in a body finds
  that one post and highlights where it matched; a typo still finds it; markup
  in a title is shown as text. One strict xfail records a bug: see "Known
  bugs" below.
- `test_command_palette` — Ctrl/Cmd-K opens it and Escape closes it; a query
  lists matching posts, at most eight; the down arrow moves the selection and
  Enter opens the selected post, or the search page when nothing matches.
- `test_sidenotes` — footnotes become margin notes on wide screens and stay
  footnotes on narrow ones.
- `test_webmentions` — mentions from a mocked webmention.io render as text,
  and the section is hidden when there are none.
- `test_metadata` — posts carry Open Graph and Twitter Card tags.
- `test_typography`, `test_theme_colours` — characterization tests pinning
  heading weight, the font request, and theme colours across CSS
  consolidations.
- `test_details` — the collapsible box includes: Markdown in the summary and
  body is converted in the post's own pass (footnotes, reference links, heading
  ids), boxes start closed unless `open` is passed, and toggle by mouse and
  keyboard (see `collapsible.md`).
- `test_toc` — the post table of contents (`toc-demo` previews): entries follow
  the h2/h3 outline; the panel hangs from the header line at every scroll
  position; from 80em it opens without animating, in the right margin clear of
  the column, stays open while reading, toggles, remembers being closed, closes
  on Escape from inside, and stays put when the menu opens; below 80em it starts
  closed, covers the screen below the header when opened, closes on a header
  click, Escape or a followed link, and keeps its open or closed state when
  the window is resized across the breakpoint, whatever is stored, morphing
  between its shapes as it crosses (but not when resized within one, or with
  reduced motion); the section
  being read is marked; entries are on the menu's type scale, below the
  article's, at every width; jumps land below the masthead and open a closed box
  around their target; `toc: false`, a single heading, no headings and non-post
  pages get none.
- `test_analytics` — the GoatCounter script and dynamic noscript fallback (see
  `analytics.md`).
- `test_performance` — the budget below.
- `test_previews` — preview fixtures (designed build) are reachable, carry
  `noindex`, and are absent from the listing, archive, search index, and feed;
  published posts (real build) are not noindexed.
- `test_a11y` — accessibility against WCAG 2.2 Level A and AA, in two layers.
  An axe-core scan of every page type in both themes, limited to the A/AA
  rules, covers contrast, names, labels and ARIA. Interaction tests cover what
  a scanner can't see, each tied to a success criterion and to a failure the
  audit found (`css_audit.md`):
  - reaching and operating the menu by keyboard, and closing it with Escape
    with focus returned to its control (2.1.1, 2.4.3);
  - one `<h1>` per page and no skipped heading levels (1.3.1, 2.4.6);
  - a visible focus ring on every Tab stop (2.4.7);
  - focus and jump targets not hidden by the sticky masthead (2.4.11);
  - nothing clipped at 320px, the open table of contents included (1.4.10);
  - icon contrast of the header toggles, closed and open, and of the TOC's
    current-section bar (1.4.11);
  - control-edge and placeholder contrast (1.4.11, 1.4.3).

  The scan ends CSS transitions before it looks, so it judges the colours a
  reader is left with, not a fade part-way through. It adds about 30 seconds to
  a run.
- `test_harness`, `test_discovery`, `test_corpus`, `test_mutate` — the suite
  itself: HTTP errors fail tests, each server is this session's build, each
  manifest lists exactly its build's sources, the pre-commit gates fail when
  they should, discovery refuses a wrong site root, the corpus scales as asked,
  and the mutation check tells caught from survived from broken and leaves the
  repo alone.

## Known bugs

Three tests are marked `xfail(strict=True)`. Each states what should happen,
fails today, and so is reported as an expected failure. Strict means the suite
goes red the day one starts passing, which is the cue to delete its marker.

- **A card breaks when the post's first paragraph has a link**
  (`test_cards.py`). A card is one link around its content; a post with no
  `summary` puts its first paragraph inside, links included, and a link can't
  contain a link, so the browser splits the card into several links, some
  empty. Posts with a `summary` are unaffected, which is why the real site
  hasn't shown it. The accessibility scan fails on such a card too, so
  `corpus.py` dates its linking posts off the home and essays pages.
- **Search excerpts show `&amp;` for `&`** (`test_search.py`).
  `search-index.json` strips tags from a post's HTML, which leaves its
  entities, and the results page escapes them again.
- **"Referenced by" misses `{% post_url %}` links from newer posts**
  (`test_backlinks.py`). See "Post blocks" in `page.md`.

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

Two workflows run on every pull request and every push to `master`, and can be
started by hand from the Actions tab:

- `.github/workflows/test.yml` builds the image, syncs the venv volume, and runs
  `make test IT=` and then `make mutate IT=`, so CI and local runs use the same
  sealed container.
- `.github/workflows/lint.yml` checks `uv.lock` matches `pyproject.toml` and runs
  the pre-commit hooks over every file. It skips the Jekyll build hook, since
  the test workflow already builds the site.

A new push to a pull request cancels its stale runs. `.github/dependabot.yml`
opens one grouped version-update PR a month each for Actions, Python and Ruby.

GitHub Pages builds and deploys `docs/` from `master` itself; neither workflow
deploys. Making `test` and `pre-commit` required checks in the branch rules for
`master` stops a red PR from merging.

To test a server that is already running instead, set `JEKYLL_URL`. It must
serve a static build (`jekyll build` plus any static file server), not
`jekyll serve`, or the performance budget fails. It replaces the real build
only, and tests that need the manifest skip unless that server has one.

## References
- Dan Luu, "How well do agents use test/verification techniques?", on tests that look thorough and aren't: <https://danluu.com/agentic-testing/>
- Petrović and Ivanković, "State of Mutation Testing at Google", the idea behind `make mutate`: <https://research.google/pubs/state-of-mutation-testing-at-google/>
- Playwright (Python): <https://playwright.dev/python/docs/intro>
- Playwright actionability checks: <https://playwright.dev/python/docs/actionability>
- pytest: <https://docs.pytest.org/>
- HTML event loop, where media-query `change` events fire before animation frame callbacks: <https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model>
- `MutationObserver`: <https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver>
- pre-commit `fail` hooks for blocking files by name: <https://adamj.eu/tech/2024/01/24/pre-commit-fail-hook/>
- Navigation Timing: <https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Navigation_timing>
- Python `http.server`: <https://docs.python.org/3/library/http.server.html>
- `TCP_NODELAY` and delayed ACK, behind the WEBrick stall: <https://man7.org/linux/man-pages/man7/tcp.7.html>
