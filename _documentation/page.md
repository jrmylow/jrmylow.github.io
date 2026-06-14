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
`post_card.html`, `toc.html`.

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
`_config.yml`); `toc.html` builds the list from them.

## Head and metadata

`head.html` sets a canonical link, applies `noindex,nofollow` to the `previews`
collection (and to any page with `noindex: true`), and links the RSS feed. Open
Graph and Twitter Card tags are **not** currently present — a known gap if and
when social-share link previews matter.

## References
- Jekyll pagination: <https://jekyllrb.com/docs/pagination/>
- Jekyll collections: <https://jekyllrb.com/docs/collections/>
- kramdown automatic IDs: <https://kramdown.gettalong.org/converter/html.html#auto-ids>
