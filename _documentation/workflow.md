# Authoring and Publishing Workflow

How to write, preview, and publish an essay on this site. This is the day-to-day user guide. For the environment the commands run in, see `container.md`; for how pages are assembled, see `page_layout.md`.

## Location encodes state

An essay moves through three folders. Its filename never changes, so its URL is identical at every stage and any link shared early stays valid after publishing.

| Stage | Folder | Committed? | On the live site? |
|---|---|---|---|
| WIP | `docs/_drafts/` | No (gitignored) | No — local preview only |
| Preview | `docs/_previews/` | Yes | Yes, but unlisted + `noindex` |
| Published | `docs/_posts/` | Yes | Yes, listed + indexable |

Use the standard Jekyll filename `YYYY-MM-DD-slug.md`. With `permalink: pretty` and the `previews` collection permalink (both in `_config.yml`), all three stages resolve to the same URL, `/YYYY/MM/DD/slug/`.

### WIP — `docs/_drafts/`
Gitignored. This is where a draft copied out of Obsidian lives while you iterate on wording and check layout. Render it with `make preview` (which serves with `--drafts`). It is local-only: a `.gitignore` entry plus a pre-commit backstop mean `git add .` cannot sweep it into a commit. Hold candid early drafts here - anything you would not want in permanent public history.

### Preview — `docs/_previews/`
Move the file here and commit it. It builds at its permalink but is kept off the public surface: `head.html` applies `noindex,nofollow` to everything in the `previews` collection, and the file is excluded from the essays listing, the `/essays/all/` archive, the tags page, the Fuse search index, and the feed. Reachable only by the link you hand out. This is the "share a draft with a few readers" stage.

### Published — `docs/_posts/`
Move the same file here. Same filename means the same URL, so the link you shared still works. It is now listed and indexable.

Promotion is just moving the file between folders — no front-matter edits, no redirects.

## Front matter

```yaml
---
layout: post            # posts use `post`; the previews collection defaults to
                        # `post` via _config.yml, so previews can omit this
title: "Essay Title"
date: 2026-01-01
summary:                # structured list; the first paragraph shows on cards
  - p: First paragraph of the summary.
  - p: Optional second paragraph (not shown on cards).
tags: [systems, planning]
---
```

If `summary` is absent, the card falls back to the post's auto-generated `excerpt`. To keep a preview out of search engines explicitly on a non-preview page, set `noindex: true`.

## Drafting in Obsidian

The Jekyll repo is not inside the Obsidian vault; copy a finished-enough draft into `docs/_drafts/` when you want to preview it. One gotcha: Obsidian wikilinks `[[like this]]` and embeds `![[like this]]` do **not** render in Jekyll/kramdown. Convert them to standard Markdown links and image paths, or the preview will look broken in ways that are not layout problems.

## Commands

```sh
make preview   # serve at http://127.0.0.1:4000 WITH drafts (WIP loop)
make serve     # serve WITHOUT drafts (closer to the live build)
make test      # run the test suite
```

See `container.md` for the full target list.

## Why this design

- **Git history is permanent.** A committed draft lives forever in history and blame, so candid early drafts stay in the gitignored `_drafts/` and never get committed.
- **Location beats a flag.** A folder per stage is simpler than a `listed:` front-matter flag, and `jekyll-paginate` (v1) cannot filter a flag out of the `/essays/all/` archive cleanly — a separate collection is excluded for free.
- **Permalink continuity.** A final URL chosen up front means publishing is a file move with no dead links.

## Navigation

Pages join the sidebar nav by declaring `nav_order` in their front matter; posts and essays do not appear there. See `page_layout.md` for details.

## References
- Jekyll drafts: <https://jekyllrb.com/docs/posts/#drafts>
- Jekyll collections: <https://jekyllrb.com/docs/collections/>
- GitHub Pages (build environment): <https://docs.github.com/en/pages>
