# CSS Audit: Accessibility and Consistency

An audit of the seven stylesheets under `docs/public/css/`. It lists the problems found and the CSS to replace each one with. This is a proposal, and none of it is applied yet. Theming background is in `styling.md`.

## Method

- Built the site (`jekyll build`, dev config) and served it statically.
- Ran axe-core 4.10.2 (WCAG 2.0/2.1/2.2 A+AA and best-practice tags) on 8 pages (`/`, `/essays/`, `/essays/all/`, `/about/`, `/contact/`, `/tags/?t=…`, `/search/?q=sort`, the funnelsort post). Each page ran in both themes at 1280px and 400px, plus the home page with the sidebar open.
- Used Playwright to measure what axe can't: border contrast, hover and focus states, Tab order, the jump to an in-page anchor under the sticky masthead, and overflow at 320px.
- Applied every replacement below to a scratch copy and re-ran all of the above, then ran the full pytest suite with the changes in the tree.

| | Baseline | With proposals |
|---|---|---|
| axe `color-contrast` | 15 selectors failing | 0 |
| axe `label` | theme switch unnamed | 0 |
| Sidebar reachable by Tab | no | yes; Space opens it, Tab continues into it |
| Footnote back-jump lands at | y=0, under the 74px masthead | y=90px |
| Display maths at 320px | clipped, can't be scrolled to | scrolls inside its own box; page stays 320px wide |
| pytest | 163 passed, 12 skipped | 163 passed, 12 skipped |

## Findings

Ranked by severity. **A** = fails WCAG 2.2 A/AA. **B** = consistency or robustness.

| ID | Issue | WCAG | Files |
|---|---|---|---|
| A1 | The sidebar can't be opened from the keyboard | 2.1.1 (A), 4.1.2 (A) | lanyon.css, sidebar.html |
| A2 | Theme switch: no name, no focus indicator, emoji read aloud | 4.1.2 (A), 2.4.7 (AA) | lanyon.css, sidebar.html |
| A3 | Muted text made with `opacity` falls below 4.5:1 in light | 1.4.3 (AA) | cards, search, tags, features |
| A4 | Text on accent fills (`mark`, palette selection, chip hover) | 1.4.3 (AA) | search, features, cards, dark-mode |
| A5 | Monokai: no base colour; comments at 3.03:1 | 1.4.3 (AA) | monokai.css |
| A6 | Sticky masthead covers anchor and focus targets | 2.4.11 (AA) | lanyon.css |
| A7 | Display maths clipped at narrow widths | 1.4.10 (AA) | lanyon.css |
| A8 | `outline: none` on inputs; hover-only states | 2.4.7 (AA) | search, features, cards, tags |
| A9 | Control borders invisible (1.00:1 dark, 1.08:1 light) | 1.4.11 (AA) | dark-mode + all |
| B1 | Specificity fight that forces five `!important`s, one of which breaks `.card-no-hover` | — | dark-mode, lanyon, cards, tags |
| B2 | Token problems: dead tokens, a 17:1 white card border, hard-coded colours, no `color-scheme` | — | dark-mode + all |
| B3 | Fonts: PT Serif loaded and never used; bold and italic are synthesised | — | head.html, lanyon |
| B4 | Root `font-size` set in px overrides the reader's default size | 1.4.4 (best practice) | lanyon.css |
| B5 | 14px sidebar search input triggers the iOS zoom on focus | — | search.css |
| B6 | Breakpoints disagree; overlapping min/max queries | — | lanyon, cards |
| B7 | Dead and duplicate rules, some of which leak declarations | — | lanyon, search, features |
| B8 | No `prefers-reduced-motion` handling; `transition: all` | 2.3.3 (AAA) | lanyon.css |
| B9 | Heading levels and landmarks (HTML, outside CSS) | 1.3.1 (A), best practice | layouts |

---

### A1. The sidebar can't be opened from the keyboard

**Evidence.** Tab visits 6 links, then `body`, then wraps. `.sidebar-checkbox { display: none }` takes the only control out of the tab order and the accessibility tree. The `<label class="sidebar-toggle">` has no text, so it has no name either.

**Replace** (lanyon.css):

```css
/* before */
.sidebar-checkbox {
  display: none;
  position: absolute;
  opacity: 0;
  -webkit-user-select: none;
     -moz-user-select: none;
          user-select: none;
}

/* after: visually hidden, still focusable; the label is its visible face */
.sidebar-checkbox {
  position: fixed;          /* fixed, so focusing it never scrolls the page */
  top: 0;
  left: 0;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  border: 0;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

#sidebar-checkbox:focus-visible ~ .sidebar-toggle {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}
```

Remove `#sidebar-checkbox:focus ~ …` from the two "open" rules (`.sidebar-toggle:active::before, …` and `.sidebar-toggle:active, …`). Once the checkbox can take focus, those selectors would make a *closed* menu look open.

**HTML** (`_includes/sidebar.html`):

```html
<input type="checkbox" class="sidebar-checkbox" id="sidebar-checkbox" aria-label="Menu" aria-controls="sidebar">
```

**Follow-up (JS, not validated):** `script.js` closes the sidebar on an outside click but not on Escape. Add an Escape handler for keyboard users.

### A2. Theme switch

**Evidence.** axe `label` fails because `<span>Toggle dark mode</span>` sits outside the `<label>`. The input is `0×0` and `.toggle-slider` has no outline, so focus is invisible. Generated `content: "🌙"` is exposed to assistive tech. In dark mode the track (`#1a1a1a`) is 1.29:1 against the sidebar.

**Replace** (lanyon.css):

```css
.toggle-slider {
  /* …existing… */
  box-shadow: inset 0 0 0 1px var(--sidebar-color);   /* track edge, ~10:1 on the sidebar */
}

.toggle-switch input:focus-visible + .toggle-slider {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.toggle-slider:before {
  content: "🌙";        /* fallback for browsers without alt-text syntax */
  content: "🌙" / "";   /* decorative: empty alt text */
  /* … */
}

input:checked + .toggle-slider:before {
  content: "☀️";
  content: "☀️" / "";
  /* … */
}
```

Delete `.theme-toggle:hover { background-color: transparent; }`: it has no effect.

**HTML:** checked means *light*, but the visible label says "Toggle dark mode". Name the switch for what "on" means:

```html
<input type="checkbox" role="switch" aria-label="Light theme" onchange="toggleTheme()">
```

### A3. Muted text via `opacity`

**Evidence (axe, light theme):** `.card-meta` and `.search-result-date` 3.27:1, `.search-result-excerpt` and `.search-result-tag` 4.0:1. Computed with the same blend: `.post-tags-label` and `.tag-post-date` 3.39:1, `.related-date` and both placeholders 2.77:1. Each multiplies `--body-color` by 0.6 to 0.8 opacity over a pale background.

**Replace:** add a muted token and use it instead of `opacity` everywhere (`.card-meta`, `.card-subtitle`, `.post-tags-label`, `.tag-post-date`, `.related-date`, `.search-result-date`, `.search-result-tag`, `.search-no-results`, placeholders). Delete `.search-result-excerpt { opacity: .8 }`.

```css
/* dark-mode.css */
:root               { --muted-color: #a8a8a8; }  /* 7.32 on bg, 5.79 on --code-bg */
[data-theme="light"] { --muted-color: #5f5b57; }  /* 5.78 on bg, 5.37 on --code-bg */

/* e.g. cards.css */
.card-meta {
  color: var(--muted-color);   /* was: color: var(--body-color); opacity: 0.7; */
}

/* search.css: placeholders need opacity: 1 to cancel Firefox's default 0.54 */
.search-input::placeholder,
.search-page-input::placeholder {
  color: var(--muted-color);
  opacity: 1;
}
```

`.search-result-tag` also goes from `0.7rem` (11.2px on mobile) to `0.75rem`.

### A4. Text on accent fills

**Evidence (axe):** search `<mark>` is `#fff` on `#5aa5e6` at 2.63:1 (dark) and 3.68:1 on `#268bd2` (light). Inside the 0.8-opacity excerpt it drops to 2.41 and 2.83. The command palette's selected row is `#fff` on `#5aa5e6`, 2.64:1. `.card-tag:hover` in light is 3.16:1. The light `--link-color` `#268bd2` is itself only 3.16:1 on the background.

**Replace** (dark-mode.css), and use the pair wherever text sits on the accent:

```css
:root                { --on-link-color: #1a1a1a; }               /* 6.6 on #5aa5e6 */
[data-theme="light"] { --link-color: #1b6497;                    /* 5.44 on bg (was #268bd2, 3.16) */
                       --on-link-color: #ffffff; }               /* 6.33 */

.search-result-item mark                                    { color: var(--on-link-color); } /* was #fff */
.command-palette-results li[aria-selected="true"] .command-palette-result { color: var(--on-link-color); } /* was #fff */
.card-tag:is(:hover, :focus-visible)                        { color: var(--on-link-color); } /* was var(--body-bg) */
```

### A5. Monokai

**Evidence.** `.highlight` sets backgrounds but no base `color`, so any token class the sheet doesn't list (`.go` console output, `.gp` prompt, `.gt` traceback …) inherits `--body-color`. In light that is `#515151` on `#272822`, 1.87:1. Comments `#75715e` are 3.03:1, and `.err` is 2.27:1. `.hll` matches the `pre` background, so highlighted lines don't show.

**Replace** (monokai.css):

```css
.highlight,
.highlight pre { color: #f8f8f2; background-color: #272822; }    /* 13.94 */
.highlight .hll { background-color: #49483e; }
.highlight .c, .highlight .cm, .highlight .cp,
.highlight .c1, .highlight .cs, .highlight .gu { color: #949079; } /* 4.62, was #75715e 3.03 */
.highlight .err { color: #f8f8f2; background-color: #960050; }    /* 8.17 */
```

### A6. Sticky masthead covers anchor and focus targets

**Evidence.** `html, body { overflow-x: hidden; height: 100% }` turns `body` into the scroll container (measured: `body.scrollTop=2078`, `html.scrollTop=0`). That disables `scroll-padding` on the viewport. Following a footnote back-link put `#fnref:1` at y=0, under the 74px sticky masthead. Tabbing to a link near the top edge hides it the same way.

**Replace** (lanyon.css):

```css
/* before */
html, body { overflow-x: hidden; height: 100%; margin: 0; padding: 0; }
body { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }

/* after */
html, body { margin: 0; padding: 0; }

html {
  -webkit-text-size-adjust: 100%;
          text-size-adjust: 100%;
  scroll-padding-top: 4.5rem;          /* masthead is ~3.7rem at both root sizes */
}

/* On short viewports (landscape phones, 400% zoom) a sticky bar costs too much height */
@media (max-height: 30em) {
  html { scroll-padding-top: 0; }
  .masthead { position: static; }
}
```

`.wrap { min-height: 100vh }` already provides the full-height layout. With the sidebar open or closed, at 320px and 1280px, `scrollWidth == clientWidth` after this change. The sidebar is `position: fixed`, so it never caused horizontal overflow.

### A7. Display maths clipped

**Evidence.** At 320px, MathJax SVGs on the funnelsort post reach x=446px. `overflow-x: hidden` (A6) clipped them with no way to scroll to the rest.

**Add** (lanyon.css):

```css
mjx-container[display="true"] {
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}
```

MathJax already gives each container `tabindex="0"`, so the new scroll region is keyboard-operable (measured: `430/288` scroll/client width, `tabindex=0`).

### A8. Focus indicators

**Evidence.** `.search-input`, `.search-page-input` and `.command-palette-input` set `outline: none`. The first two fall back to a 1px border colour change (cream to `#5aa5e6` on the sidebar, 2.27:1 between states). The palette input has nothing. Hover-only states with no focus equivalent: `.card:hover`, `.card-link:hover .card-title`, `.post-tag:hover`, `.card-tag:hover`, `.search-result-item:hover` (search page), `.tag-post-item a:hover`.

**Replace:** one focus ring, defined once.

```css
/* dark-mode.css */
:root                { --focus-ring: #5aa5e6; }   /* 6.6 on bg, 5.22 on --code-bg */
[data-theme="light"] { --focus-ring: #1b6497; }   /* 5.44 on bg, 5.06 on --code-bg */
.sidebar             { --focus-ring: #ffffff; }   /* sidebar is dark in both themes: 13.5 */

/* lanyon.css */
a:hover,
a:focus-visible { text-decoration: underline; }   /* was a:focus */

:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}
```

Delete every `outline: none`. For the palette, inset the ring so the panel's `overflow: hidden` doesn't clip it: `.command-palette-input:focus-visible { outline-offset: -2px; }`. Give each hover rule a focus twin with `:is(:hover, :focus-visible)`:

```css
.card-link { border-radius: 8px; }   /* ring follows the card's corners */
.card-link:is(:hover, :focus-visible) .card-title { text-decoration: underline; }
.card-link:is(:hover, :focus-visible) .card:not(.card-no-hover) { … }
:is(.post-tag, .tag-cloud-item):is(:hover, :focus-visible), … { … }
.search-page-results .search-result-item:is(:hover, :focus-visible) { … }
```

### A9. Borders that vanish

**Evidence.** Dark `--border-color` is `#1a1a1a`, the same as `--body-bg` (1.00:1). Light is `#e5e5e5` on `#f2ede7` (1.08:1). The "View all essays →" and pagination buttons are styled links with no underline, and in both themes they lose their outline. The `hr` and table borders disappear in dark. `--sidebar-border-color` (`#f2ede7`) equals light `--body-bg`, so the `.related`, `.backlinks`, `.series` and `.webmentions` dividers, the palette border, and the search-result chip borders vanish in light. Meanwhile `--header-border-color` puts a 17.4:1 white border on every card in dark.

**Replace:** split the job between two tokens, and keep `--sidebar-border-color` for inside the sidebar (and hover states that use the sidebar palette).

```css
/* dark-mode.css */
:root {
  --rule-color: #444444;       /* decorative dividers: hr, tables, section rules (1.79) */
  --control-border: #767676;   /* boundaries that identify controls: buttons, cards, inputs (3.83 bg / 3.03 code-bg) */
}
[data-theme="light"] {
  --rule-color: #cfc7bd;       /* 1.44 */
  --control-border: #857e76;   /* 3.44 bg / 3.20 code-bg */
}
```

- Rename `var(--border-color)` to `var(--rule-color)` throughout, and drop the Poole double rule on `hr` (`border-bottom: 1px solid var(--body-bg)`).
- Use `--control-border` for `.card`, `.view-all-link a`, `.pagination-prev/next a`, `.post-tag`, `.tag-cloud-item`, `.search-page-input`, `.search-page-results .search-result-item`, `.command-palette-panel` and `.masthead`.
- Use `--rule-color` for `.related`, `.backlinks`, `.series`, `.webmentions`, `.command-palette-input` (bottom), `.search-result-tag`, `.home-intro`, `.tag-post-item` and `.tag-posts-container`.
- Delete `--header-border-color`.

---

### B1. Specificity fight

**Evidence.** `.container.content a` is (0,2,1); the comment beside it says (0,3,0). `.post a, .page a, p a, li a` is (0,1,1). Components fight back with five `!important`s: three in cards.css and two in tags.css. The `!important` in `.card:hover .card-title` also beats `.card-no-hover`'s `color: inherit`. A no-hover card in light would show near-white text on `#eae5df`. When I removed the tags `!important` alone, `test_tag_no_underline_on_hover` failed, which confirms the cause.

**Replace:** lower the base rules to (0,0,1) with `:where()`, so any class wins.

```css
/* dark-mode.css: replaces `.post a, .page a {…}` and `.container.content a {…}` */
:where(.content) a { color: var(--heading-color); }

/* lanyon.css */
:where(.post, .page, p, li) a { text-decoration: underline; }
```

Then delete all five `!important`s. Write `.card-no-hover` as an exclusion (`.card:not(.card-no-hover)` in the hover rules) rather than an override. `test_content_links_use_heading_color` still passes. To make prose links blue later, change the one value.

### B2. Tokens

- **Dead:** `--pagination-color`, `--pagination-border` and `--pagination-hover-bg` (used only by the dead Lanyon pagination, B7), plus `--overlay-bg`.
- **Hard-coded:** `#fff` (A4), and `#f39c12` / `#27ae60` on `.card-warning` / `.card-success`. In light those are 1.75 and 2.29 on `--code-bg`, below 1.4.11's 3:1. Make them tokens:

  ```css
  :root                { --warning-color: #f39c12; --success-color: #27ae60; }  /* 6.28 / 4.79 on dark code-bg */
  [data-theme="light"] { --warning-color: #9a5b00; --success-color: #1e7a45; }  /* 4.33 / 4.27 on light code-bg */
  ```

- **No `color-scheme`:** measured `normal`. Scrollbars (sidebar, palette results) and native control chrome render light in dark mode.

  ```css
  :root                { color-scheme: dark; }
  [data-theme="light"] { color-scheme: light; }
  .sidebar             { color-scheme: dark; }   /* the sidebar is dark in both themes */
  ```

### B3. Fonts

`head.html` requests `PT+Serif:400,400italic,700%7CPT+Sans:400`. No rule uses PT Serif. PT Sans comes only at 400, so every bold heading, `strong`, `dt` and `.search-result-title` is synthesised bold, and italic blockquotes are synthesised oblique. `font-family` is also repeated six times, because inputs don't inherit it.

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=PT+Sans:ital,wght@0,400;0,700;1,400&display=swap">
```

```css
/* lanyon.css */
:root { --font-sans: "PT Sans", Helvetica, Arial, sans-serif;
        --font-mono: Menlo, Monaco, "Courier New", monospace; }
html  { font-family: var(--font-sans); }
button, input { font: inherit; }   /* then delete the 6 repeated font-family lines */
```

### B4. Root font size in px

`html { font-size: 16px }` and `20px` at ≥38em override a reader's browser default font-size setting. Zoom still works, so this is not a 1.4.4 failure, but anyone who set a larger default loses it.

```css
html { font-size: 100%; }
@media (min-width: 38em) { html { font-size: 125%; } }   /* 20px at the default 16px */
```

### B5. iOS input zoom

On mobile, `.search-input` is `.875rem` = 14px. iOS Safari zooms the page when an input under 16px takes focus.

```css
.search-input { font-size: 1rem; }
@media (min-width: 48em) { .search-input { font-size: max(16px, 0.75rem); } }
```

### B6. Breakpoints

The breakpoints in use are 30em, 30.1em, 38em, 48em, 56em, 64em and 80em. The sidebar text shrinks at 30em, but the theme toggle, search input and item padding change at 48em, so between those widths the sidebar mixes two type sizes. `@media (max-width: 48em)` and `(min-width: 48em)` both match at exactly 768px, and the 30em pair overlaps the same way.

- Move `.sidebar { font-size: .75rem }` to `min-width: 48em`.
- Use range syntax for the max queries: `@media (width < 48em)`, and `(width < 30em)` in cards.css.
- Delete the `@media (min-width: 30.1em) { .sidebar-toggle { position: fixed } }` block; the rule already applies.

### B7. Dead and duplicate rules

| Rule | Why |
|---|---|
| lanyon `.related { padding: 2rem 0; border-top: … heading-color }` | features.css redefines `.related`; Lanyon's `padding-bottom: 2rem` still leaks, and the two disagree on the border |
| lanyon `.related-posts*` | no template emits it (`related.html` uses `.related-list`) |
| lanyon `.pagination`, `.pagination-item*` | cards.css owns pagination; Lanyon's `overflow: hidden` and `color: var(--pagination-color)` still leak |
| lanyon `.layout-reverse*` | the body class is never set |
| lanyon `.sidebar { color; background-color; font-family }`, `.sidebar a { color }` | overridden by dark-mode.css or inherited |
| lanyon `-webkit-`/`-ms-` `transform`/`transition`/`backface-visibility`, `-ms-text-size-adjust` | already flagged in `styling.md` |
| lanyon `pre { white-space: pre; white-space: pre-wrap; word-break: break-all; word-wrap: break-word }` | replace with `white-space: pre-wrap; overflow-wrap: anywhere;`, so identifiers break only when they can't fit |
| search.css `.search-highlight` | `search.js` emits `<mark>`, never this class |
| features.css header lists "2. Sidenotes" | the section doesn't exist (parked, and `sidenotes.js` isn't loaded); mark it as parked |
| cards.css `card-highlight/-no-hover/-flat/-info/-warning/-success/-header/-subtitle/-footer/-tags/-tag` | unused, but documented in `card_guide.md`. Keep them and tokenise per A9/B2 |

### B8. Motion

Nothing respects `prefers-reduced-motion`: the sidebar slides over 0.3s, the switch over 0.4s, and there are hover fades. `.sidebar { transition: all }` also animates `z-index`.

```css
.sidebar { transition: transform .3s ease-in-out, visibility .3s, box-shadow .3s; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### B9. Outside CSS (not validated here)

- **No `<h1>` on any non-post page:** axe `page-has-heading-one` on 7 of the 8 pages (all but the post). The masthead title is `<h3>`, and page titles are `<h3 class="page-title">` while post titles are `<h1>`. Proposal: make the masthead a `<p>`/`<div>` and `page.html`'s title an `<h1>`. That means updating `test_typography.py` (`h3.page-title`). The size scale (1.3, 1.2, 1.1, 1.0em) also leaves `h4` the same size as body text. A 1.25 ratio (h1 1.95, h2 1.56, h3 1.25em) would separate the levels; this is a design call.
- **Landmarks:** there is no `<main>`, so axe reports `landmark-one-main` and 100+ `region` nodes. Use `<header class="masthead">` and `<main class="container content">` in `default.html`; the CSS selectors stay the same.
- **State via ARIA, not classes:** use `.tag-cloud-item[aria-pressed="true"]` instead of `.selected` (and set `aria-pressed` in `tag-filter.js`), and `.sidebar-nav-item[aria-current="page"]` instead of `.active`. The proposed tags.css matches both during migration. The command palette already does this with `aria-selected`.
- **kramdown footnotes:** axe flags `doc-noteref` on `<sup>` and the deprecated `doc-endnote`. That markup comes from kramdown, not this repo.

## Suggested order

1. A1, A2, A6+A7: keyboard access, the switch, and the scroll container, done together because A7 depends on A6.
2. The new tokens (`--muted-color`, `--on-link-color`, `--rule-color`, `--control-border`, `--focus-ring`, `color-scheme`), then A3, A4, A8 and A9, which consume them.
3. B1 (`:where()`) with the `!important` removals, so cards and tags stay right.
4. A5 Monokai, then B3–B8 cleanup.

## References

- WCAG 2.2 Understanding: [1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [1.4.11 Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), [1.4.10 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [1.4.4 Resize Text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html), [2.1.1 Keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html), [2.4.7 Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html), [2.4.11 Focus Not Obscured (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html), [2.3.3 Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html), [4.1.2 Name, Role, Value](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html)
- WAI-ARIA APG: [Switch pattern](https://www.w3.org/WAI/ARIA/apg/patterns/switch/), [Disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/)
- axe-core rule docs: <https://dequeuniversity.com/rules/axe/4.10>
- CSS Overflow 3, overflow propagation from `body` to the viewport (why A6's scroll container appears): <https://www.w3.org/TR/css-overflow-3/#overflow-propagation>
- MDN: [`:focus-visible`](https://developer.mozilla.org/en-US/docs/Web/CSS/:focus-visible), [`:where()`](https://developer.mozilla.org/en-US/docs/Web/CSS/:where), [`scroll-padding-top`](https://developer.mozilla.org/en-US/docs/Web/CSS/scroll-padding-top), [`color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme), [`content` (alt-text syntax)](https://developer.mozilla.org/en-US/docs/Web/CSS/content), [`::placeholder`](https://developer.mozilla.org/en-US/docs/Web/CSS/::placeholder), [`prefers-reduced-motion`](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion), [media query range syntax](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_media_queries/Using_media_queries), [`font-synthesis`](https://developer.mozilla.org/en-US/docs/Web/CSS/font-synthesis)
- Google Fonts CSS2 API (axes, `display=swap`): <https://developers.google.com/fonts/docs/css2>
- Scott O'Hara, "Inclusively Hidden" (the visually-hidden pattern in A1): <https://www.scottohara.me/blog/2017/04/14/inclusively-hidden.html>
- Sara Soueidan, "A guide to designing accessible, WCAG-conformant focus indicators": <https://www.sarasoueidan.com/blog/focus-indicators/>
- Josh W. Comeau, "The Surprising Truth About Pixels and Accessibility" (B4): <https://www.joshwcomeau.com/css/surprising-truth-about-pixels-and-accessibility/>
- CSS-Tricks, "16px or Larger Text Prevents iOS Form Zoom" (B5): <https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/>
