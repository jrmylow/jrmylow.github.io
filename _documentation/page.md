# Page Layout

The layouts, includes, and the design decisions behind how pages are assembled.
CSS and theming are in `styling.md`.

## Layout hierarchy

`default` is the root layout — the HTML shell, the `head` include, the sidebar,
the masthead, and the content container. Other layouts wrap it:

- `page` — generic content pages (About, Contact).
- `post` — essays/posts, and the `previews` collection (via `_config.yml`
  defaults).
- `index` — the home page.
- `essays` — the `/essays/` landing page.
- `tags` — the tags page.
- `search` — the `/search/` page; near-identical to `page` and a candidate to
  merge with it.

Shared partials live in `_includes`: `head.html`, `sidebar.html`,
`post_card.html`, `toc.html` and `post_toc.html`, and `details_open.html`/`details_close.html`, the
collapsible box used inside Markdown (`collapsible.md`).

## The post card is a single source of truth

Every post preview renders through `_includes/post_card.html`. The caller owns
post selection, ordering, the limit, and the `.card-grid` wrapper; the include
renders exactly one card — title, date, and the first `summary` paragraph (or the
`excerpt` as a fallback). It takes a `heading` parameter so the card title sits
at the correct level beneath each page's surrounding heading. It was extracted to
kill three drifting copies of the same markup across the index, essays landing,
and archive.

## Home page (index)

`_layouts/index.html` + `_pages/index.md`. Intro prose, then the six most recent
posts in a two-column grid (`card-grid-2`), then a "View all essays" link. A
commented-out "Featured Essays" block (posts tagged `top`) is staged for when a
curated `top` tag exists.

## Essays landing (`/essays/`)

Uses the `essays` layout: the Markdown body (intro prose plus a Leslie Lamport
quote) followed by the five most recent posts in a single column
(`card-grid-1`), then a link to the full archive.

## Essays archive (`/essays/all/`)

`docs/essays/all/index.html`, paginated. `jekyll-paginate` only paginates
`index.html` files, which is why the archive is its own `index.html` rather than
a Markdown page. `paginate: 10` and `paginate_path: /essays/all/page/:num/` are
set in `_config.yml`; the template renders `paginator.posts` in a single-column
grid with prev/next controls and a "Page X of Y" line. Note that
`jekyll-paginate` v1 (the GitHub Pages-whitelisted version) has no front-matter
filter — one reason drafts are kept out of the archive by living in a separate
collection rather than behind a flag (see `workflow.md`).

## Card grid

`card-grid` plus a column modifier, `card-grid-1` through `card-grid-4`. Columns
step up at `em` breakpoints (48em / 64em / 80em); every variant is single-column
on mobile. Choose a post count divisible by the column number for an even grid.
Visual detail is in `styling.md`.

## Navigation

The sidebar nav is data-driven. `sidebar.html` collects `site.pages` that declare
a `nav_order`, sorts by it, labels each with `nav_title` (falling back to
`title`), and marks the current page `active`. A page joins the nav by adding
`nav_order` to its front matter; Home is absent because it declares none.
`test_navigation` asserts the rendered order equals the order derived from front
matter.

## Table of contents

kramdown generates heading IDs (`auto_ids: true`, `toc_levels: 1..6` in
`_config.yml`); `toc.html` (allejo/jekyll-toc) builds a list from them, and
`post_toc.html` turns it into a panel that drops down from the header bar,
toggled by a button at the bar's right end (the menu button's mirror image;
both share `.icon-toggle`, see `styling.md`).

- **When.** On by default for posts and previews; `toc: false` in front matter
  turns it off. It lists h2 and h3 only, and a post with fewer than two of them
  gets no panel, no button and no `toc.js` request.
- **Where in the DOM.** `default.html` includes it (with `page.content`) inside
  `.masthead`. The masthead is sticky, so the panel, absolutely positioned
  against its bottom edge, hangs from the header line wherever the page is
  scrolled, and the line stays visible above it. Being absolute rather than
  fixed, it isn't carried off by the transform the open menu puts on `.wrap`.
- **Unroll and fold.** Closed, the panel is clipped to nothing at its top edge;
  opening animates the clip down (it unrolls from the header line), closing
  animates it back up into the bar. Open, the clip edge sits above the panel:
  one on the panel's own top, at a fractional pixel, is antialiased and lets a
  sliver of page text show under the line.
- **Wide (>= 80em).** It hangs in the right margin, from the 38rem column's edge
  to the window's (up to 16rem), and down to the window's bottom: a column edged
  by one rule, like the menu, rather than a box that stops under its list. It covers nothing, so it
  starts open and stays open while the reader scrolls and clicks the page.
  Closing or opening it here is remembered in `localStorage` (key `toc`);
  Escape closes it when focus is inside.
- **Narrow (< 80em).** It covers the screen below the header and starts closed;
  a click on the header bar, Escape, or following one of its links closes it.
  The stored choice doesn't apply here. Its height is the window less the
  header: `toc.js` keeps `--masthead-height` on `<html>` current (CSS falls
  back to 3.7rem, the header's computed height at both type sizes).
- **Crossing the breakpoint.** With the panel open, it morphs between its two
  shapes (full width, the right margin) over 0.3s rather than snapping: `toc.js`
  animates from the old shape on the media query's `change`, leaving the end as
  the live layout. Not a CSS transition: the browser applies the new layout
  before any handler could switch one on, and one left on would make the panel
  lag behind every resize within a shape. Reduced motion skips it.
- **Type.** The menu's scale at every width (0.875rem, then 0.75rem from
  30em, as `.sidebar`): navigation reads smaller than the article, and the
  size doesn't jump at 80em. Phones keep taller entries for touch.
- **State.** One toggle at every width: `data-toc="open|closed"` on `<html>`.
  Resizing across 80em leaves it as the reader left it (only the layout
  changes); the stored desktop choice decides how a page loads, never what a
  resize does. It is set by an inline script before the panel is parsed, so
  the first paint is already right and nothing unrolls on load; transitions switch on (`.toc-ready`) a frame later.
- **Current section.** `toc.js` marks the entry being read with
  `aria-current="location"`: the last heading scrolled past the masthead line
  (`scroll-padding-top`), or the last heading once the page hits the bottom,
  since a short final section can't scroll that far. Following an entry whose
  heading sits in a closed collapsible box opens the box first.

Styles are in `features.css`, section 6; tests in `test_toc.py`.

## Head and metadata

`head.html` sets a canonical link, applies `noindex,nofollow` to the `previews`
collection (and to any page with `noindex: true`), and links the RSS feed. Open
Graph and Twitter Card tags are **not** currently present — a known gap if and
when social-share link previews matter.

## References
- Jekyll pagination: <https://jekyllrb.com/docs/pagination/>
- Jekyll collections: <https://jekyllrb.com/docs/collections/>
- allejo/jekyll-toc: <https://github.com/allejo/jekyll-toc>
- `aria-current`: <https://www.w3.org/TR/wai-aria-1.2/#aria-current>
- kramdown automatic IDs: <https://kramdown.gettalong.org/converter/html.html#auto-ids>
