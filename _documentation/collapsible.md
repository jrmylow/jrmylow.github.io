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

That renders a closed box showing "A short **summary**". Clicking the summary,
or pressing Enter or Space on it, opens the box.

To start the box expanded:

```liquid
{% include details_open.html summary="Starts open" open=true %}
```

### Parameters

| Parameter | Required | Default | Notes |
|---|---|---|---|
| `summary` | yes | | The always-visible line. Inline Markdown only (bold, italics, code, links), on one line. |
| `open` | no | closed | `true` to start expanded. |

### Rules

- **Headings inside follow the page outline.** A box is part of the page, so its
  headings must not skip a level: in a post (title `h1`) a box at the top level
  starts at `##`. `test_a11y.py` checks this on every page it scans.
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
<details class="collapsible" markdown="1">
<summary markdown="span">…summary…</summary>
```

and `details_close.html` emits `</details>`. Jekyll renders Liquid first, then
converts the result with kramdown, so by the time kramdown runs the post is
Markdown with a raw HTML block in it. kramdown leaves the contents of raw HTML
alone unless the element carries a `markdown` attribute: `markdown="1"` on
`<details>` converts its body as block Markdown, and `markdown="span"` on
`<summary>` converts the summary as inline Markdown. kramdown strips the
attribute from the output.

The open/close behaviour, keyboard support and the expanded state exposed to
screen readers all come from the native `<details>` element. There is no
JavaScript.

## Styling

In `public/css/features.css`, section 5. The box takes the card colours from
`cards.css` (`--code-bg` background, `--header-border-color` border, 8px radius)
so a box in an essay matches the post cards. The browser's default disclosure
triangle is replaced by a chevron drawn from two borders on `summary::before`;
it rotates when the box opens, and the rotation is not animated under
`prefers-reduced-motion`. An open box draws a rule under its summary.

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

Known limitation: some screen readers announce `<summary>` as a button and
flatten any heading put inside it, so keep headings in the body, not the
summary.

## Tests

`_tests/test_details.py`, against the fixture preview
`_tests/fixtures/_previews/2024-03-01-details-demo.md` (designed build only,
never published). It checks that the summary and body are converted Markdown,
that footnotes, reference links and heading ids inside a box behave as they do
outside one, that a box is closed unless `open` is passed and toggles by mouse
and keyboard, and that the box and its marker are styled. `test_a11y.py` runs
the axe scan over the fixture, with every box opened, in both themes.

## Files

- `docs/_includes/details_open.html`, `docs/_includes/details_close.html` — the
  includes
- `docs/public/css/features.css` — section 5, the styles
- `_tests/test_details.py`, `_tests/fixtures/_previews/2024-03-01-details-demo.md`
  — the tests and their fixture

## References

- `<details>` element: <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details>
- kramdown, Markdown inside HTML blocks (`markdown="1"`, `"span"`): <https://kramdown.gettalong.org/syntax.html#html-blocks>
- Jekyll includes and their parameters: <https://jekyllrb.com/docs/includes/>
- Jekyll custom tags (plugins): <https://jekyllrb.com/docs/plugins/tags/>
- GitHub Pages and Jekyll plugins (safe mode): <https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/about-github-pages-and-jekyll#plugins>
- HTML content model of `<a>` (no interactive descendants): <https://html.spec.whatwg.org/multipage/text-level-semantics.html#the-a-element>
- Scott O'Hara on details/summary and assistive technology: <https://www.scottohara.me/blog/2022/09/12/details-summary.html>
- Animating `<details>` to `height: auto`: <https://developer.chrome.com/docs/css-ui/animate-to-height-auto>
