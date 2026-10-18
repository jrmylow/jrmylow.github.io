# Collapsible Box

A box with an always-visible summary line that expands to show more. It works
inline in any essay or page written in Markdown, and is meant for project
write-ups and asides that would otherwise make a page long.

## Usage

```liquid
{% include details_open.html summary="A short **summary**" %}

## Any heading

The body is ordinary Markdown: *emphasis*, lists, code blocks, footnotes[^1],
[reference links][ref], tables, images.

{% include details_close.html %}
```

That renders a closed box showing "A short **summary**" with a chevron on the
right. Only the chevron opens and closes the box (click it, or Tab to it and
press Enter or Space); the summary text is ordinary text and can hold links.

To give the box a title, a heading run in at the start of the summary:

```liquid
{% include details_open.html title="FunnelSort Implementation" summary="Implementation of a cache-oblivious sort." %}
```

That reads as "**FunnelSort Implementation.** Implementation of a cache-oblivious
sort." but the title is a real `h3`, so screen reader users can jump between
boxes by heading, and `/page/#funnelsort-implementation` links to it.

To start the box expanded:

```liquid
{% include details_open.html summary="Starts open" open=true %}
```

### Parameters

| Parameter | Required | Default | Notes |
|---|---|---|---|
| `summary` | yes | | The always-visible line. Inline Markdown (bold, italics, code, links), on one line. |
| `title` | no | none | A heading run in, bold, at the start of the summary. Inline Markdown. Its id is the slugified title. A full stop is added after it. |
| `heading` | no | `h3` | The title's tag. Pick the level below the heading the box sits under. |
| `open` | no | closed | `true` to start expanded. |

### Rules

- **Headings inside follow the page outline.** A box is part of the page, so its
  headings must not skip a level: in a post (title `h1`) a box at the top level
  starts at `##`. The same goes for `title`: set `heading` to one level below
  the heading the box sits under (the default `h3` suits a box under an `##`).
  `test_a11y.py` checks this on every page it scans.
- **Don't indent the body.** It is ordinary Markdown, so four leading spaces make
  it a code block, as anywhere else. Blank lines around the includes are
  optional; they just read better.
- **Every opening include needs a closing one.** Nothing checks the pairing; a
  missing close swallows the rest of the page into the box.
- **Quote the summary to suit its content.** It is a Liquid string, so a summary
  containing `"` needs single quotes: `summary='An "open" box'`. kramdown curls
  straight quotes in the output.
- **Footnote definitions can go anywhere in the post.** Like reference links,
  they are resolved across the whole post, so a footnote inside a box is
  numbered in sequence and listed in the post's single footnotes list.

## How it works

`details_open.html` emits:

```html
<div class="collapsible" markdown="1">
<div class="collapsible-summary" id="details-summary-N"><h3 class="collapsible-title" id="title-slug" markdown="span">…title…</h3> <span markdown="span">…summary…</span></div>
<details markdown="1">
<summary aria-describedby="details-summary-N"><span class="collapsible-label">Details</span></summary>
```

and `details_close.html` emits `</details></div>`. `N` comes from Liquid's
`{% increment %}`, so every box on a page gets its own id. The `<h3>` appears only
when `title` is given. It and the summary text are separate elements because
kramdown escapes a heading inside `markdown="span"` content. Jekyll renders Liquid first, then
converts the result with kramdown, so by the time kramdown runs the post is
Markdown with a raw HTML block in it. kramdown leaves the contents of raw HTML
alone unless the element carries a `markdown` attribute: `markdown="1"` on the
box and on `<details>` converts the body as block Markdown, and `markdown="span"`
on the title and summary text converts them as inline Markdown. kramdown strips the
attribute from the output.

The summary text sits outside `<details>`, so it is always shown and is never
part of the toggle. The `<summary>` holds only the chevron. The open/close
behaviour, keyboard support and the expanded state exposed to screen readers all
come from that native element; there is no JavaScript. A screen reader hears it
as a button named "Details" (the visually hidden label), described by the title
or, without one, the summary text (`aria-describedby`), with its expanded or
collapsed state.

## Styling

In `public/css/features.css`, section 5. The box takes the card colours from
`cards.css` (`--code-bg` background, `--header-border-color` border, 8px radius)
so a box in an essay matches the post cards. The browser's default disclosure
triangle is replaced by a chevron drawn from two borders on `summary::after`.
The `<summary>` is a 2rem square (above the 24px minimum target size, WCAG
2.5.8), absolutely positioned in space the summary text keeps clear on its
right, and lined up with the text's first line rather than its middle so it
stays put when the box opens. The chevron points down when closed and up when
open, and the turn is not animated under `prefers-reduced-motion`. An open box
draws a rule between the summary text and the body.

A title is styled by one rule: `display: inline` and `font-size: inherit` on
`.collapsible-title`, plus a full stop in `::after`. Headings are already bold
(`lanyon.css`), and vertical margins don't apply to inline elements, so nothing
else needs overriding. Pick the heading level by the page's structure, never to
borrow a size: `h4`-`h6` look the same here but tell screen readers the box is
nested deeper than it is.

The summary text must stay a plain block. An earlier version made it a flex
container to line the chevron up with the text; flex turns every text run and
link into a separate item, so a link in the summary was laid out beside its
sentence instead of in it. `test_details.py` guards this.

The box itself opens instantly. Animating the height is possible with
`::details-content` and `interpolate-size: allow-keywords`, but needs
`overflow: clip` on the content, and browser support is incomplete; see the
references if it is ever wanted.

## Design decisions

Recorded so they don't get undone.

- **Two includes, not a custom block tag.** The ideal syntax would be a block
  tag (`{% details %}…{% enddetails %}`), but custom Liquid tags are Ruby plugins
  in `_plugins/`. GitHub Pages builds this site in safe mode, which ignores
  `_plugins/` and only runs whitelisted plugins. Getting a custom tag would mean
  building and deploying the site from a GitHub Actions workflow instead.
- **Not `{% capture %}` plus `markdownify`.** The obvious alternative captures
  the body into a variable and passes it to one include that runs
  `{{ include.detail | markdownify }}`. That converts the body in a separate
  kramdown pass, which can't see the rest of the post: footnotes and reference
  links inside the box came out as literal `[^1]` and `[text][ref]`. With
  `markdown="1"` the whole post is converted in one pass, so both work.
- **Not a whole-card link.** `post_card.html` wraps its card in an `<a>`. A
  collapsible box can hold links, and HTML forbids interactive content inside
  `<a>`, so the box is its own element and shares only the card's colours.
- **Only the chevron toggles.** An earlier version put the summary text inside
  `<summary>`, so clicking anywhere on it toggled the box. Screen readers treat
  `<summary>` as a button, and a link inside a button is a nested control: some
  never announce it, and focus behaves unpredictably (WCAG 4.1.2; axe's
  `nested-interactive` rule, which `test_a11y.py` runs). Moving the text out of
  `<summary>` lets summaries hold links, at the cost of a smaller click target.
- **No JavaScript.** A `<button aria-expanded>` with a script could put the
  chevron anywhere, but would need a fallback for when the script doesn't run
  and would lose the browser's built-in behaviour, such as Chrome opening a
  closed box when find-in-page matches text inside it.

## Tests

`_tests/test_details.py`, against the fixture preview
`_tests/fixtures/_previews/2024-03-01-details-demo.md` (designed build only,
never published). It checks that the summary and body are converted Markdown,
that footnotes, reference links and heading ids inside a box behave as they do
outside one, that a box is closed unless `open` is passed, that only the
chevron toggles it (by mouse and keyboard), that the chevron is named, described
and big enough to hit, that a link in the summary stays in its sentence and
outside the toggle, that a title is a heading at the given level with a slug id,
runs in on the summary's line at its size, and describes the chevron, and that
the box and its marker are styled. `test_a11y.py` runs
the axe scan over the fixture, with every box opened, in both themes.

## Files

- `docs/_includes/details_open.html`, `docs/_includes/details_close.html` — the
  includes
- `docs/public/css/features.css` — section 5, the styles
- `_tests/test_details.py`, `_tests/fixtures/_previews/2024-03-01-details-demo.md`
  — the tests and their fixture

## References

- W3C WAI, headings and their levels: <https://www.w3.org/WAI/tutorials/page-structure/headings/>
- WebAIM screen reader survey (navigating by headings): <https://webaim.org/projects/screenreadersurvey10/>
- `<details>` element: <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details>
- kramdown, Markdown inside HTML blocks (`markdown="1"`, `"span"`): <https://kramdown.gettalong.org/syntax.html#html-blocks>
- Jekyll includes and their parameters: <https://jekyllrb.com/docs/includes/>
- Jekyll custom tags (plugins): <https://jekyllrb.com/docs/plugins/tags/>
- GitHub Pages and Jekyll plugins (safe mode): <https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/about-github-pages-and-jekyll#plugins>
- HTML content model of `<a>` (no interactive descendants): <https://html.spec.whatwg.org/multipage/text-level-semantics.html#the-a-element>
- axe `nested-interactive` rule: <https://dequeuniversity.com/rules/axe/4.12/nested-interactive>
- Scott O'Hara on details/summary and assistive technology: <https://www.scottohara.me/blog/2022/09/12/details-summary.html>
- Animating `<details>` to `height: auto`: <https://developer.chrome.com/docs/css-ui/animate-to-height-auto>
