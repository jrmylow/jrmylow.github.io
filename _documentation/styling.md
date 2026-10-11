# Styling and Theming

The CSS architecture, the light/dark theming mechanism, the no-flash fix, and the consolidation decisions. Page structure is in `page_layout.md`.

## Stylesheets and load order

Loaded in this order from `head.html`. Order matters — later files win on equal specificity:

1. `lanyon.css` — layout, structure, typography. The old `poole.css` was merged in here.
2. `dark-mode.css` — the CSS custom properties (the theme) plus the colour applications.
3. `monokai.css` — code syntax highlighting.
4. `cards.css` — the card component system.
5. `tags.css`, `search.css` — feature styling.

## Theming with CSS variables

`dark-mode.css` defines colour variables on `:root` (dark is the default) and overrides them under `[data-theme="light"]`. Elements reference the variables (`--body-bg`, `--heading-color`, `--sidebar-bg`, `--code-bg`, and so on), so a theme switch is just swapping the variable set. The dark background is `rgb(26, 26, 26)`; the light background is `rgb(242, 237, 231)` — the values the tests assert.

Division of labour: structural typography (heading weight, size scale, margins) lives in `lanyon.css`; `dark-mode.css` sets heading **colour only**. This resolves an earlier conflict where both files set heading weight and fought by load order.

Each colour token has one job, and its values per theme are chosen to meet WCAG contrast minimums (the measurements are in `css_audit.md`):

| Token | Job | Floor |
|---|---|---|
| `--body-color`, `--heading-color` | text | 4.5:1 on `--body-bg` and `--code-bg` |
| `--muted-color` | secondary text (dates, meta, placeholders); use it instead of lowering `opacity` | 4.5:1 on `--body-bg` and `--code-bg` |
| `--link-color` / `--on-link-color` | accent fill and the text drawn on it (`mark`, palette selection, chip hover) | 4.5:1 as a pair |
| `--control-border` | boundaries that identify a control: cards, buttons, chips, inputs, the masthead rule | 3:1 on `--body-bg` |
| `--rule-color` | decorative dividers: `hr`, tables, section rules | visible, not a WCAG minimum |
| `--focus-ring` | the global `:focus-visible` outline; `.sidebar` overrides it to white | 3:1 on what it sits on |
| `--sidebar-*` | the sidebar, dark in both themes, and the hover/focus states that borrow its palette | — |

Each theme also sets `color-scheme` (and `.sidebar` is always `dark`), so native scrollbars and form controls match the theme.

## The no-flash fix (FOUC)

**Problem.** CSS defaulted to the dark theme and the theme JS ran deferred on `DOMContentLoaded`, so navigating in light mode briefly flashed dark before the script corrected it.

**Fix.** A small synchronous inline script at the top of `head.html`, before any stylesheet, reads the saved theme and sets `data-theme` on `<html>` before the browser paints:

```html
<script>
  (function() {
    var theme = localStorage.getItem('theme');
    if (!theme) {
      theme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }
    document.documentElement.setAttribute('data-theme', theme);
  })();
</script>
```

Because it runs before CSS and before paint, the correct theme is applied with no flash. `test_theme_flash.py` guards this: an init script records DOM mutations from document start, and for every combination of stored choice and OS preference, `data-theme` must be set before the first stylesheet is inserted and keep that value for the rest of the load.

**Stored choice vs OS.** An explicit choice wins; with nothing stored, the site follows `prefers-color-scheme` live. `dark-mode.js` (deferred) keeps the toggle checkbox in sync, follows OS changes while nothing is stored, and writes `localStorage` (key `theme`) only when the user toggles, so a first visit never pins the OS preference. A toggle flips the theme shown, which is the OS theme when nothing is stored. The key is a contract with returning visitors: renaming it discards their saved choice. `test_theme_matrix.py` checks all 18 combinations of stored choice (none, light, dark), OS preference (light, dark) and event (load, toggle, OS change).

## Cards

In `cards.css`, `.card-grid` is a CSS grid (gap `1rem`, vertical margin `2rem`); the `card-grid-N` variants set columns at the breakpoints above. A card uses `--code-bg` for its background and `--control-border` for its border (radius `8px`, `min-height: 250px`). When its `.card-link` is hovered or keyboard-focused, the card switches to the sidebar-hover palette. The hover rule excludes `.card-no-hover` with `:not()` rather than overriding it. It needs no `!important`, because the in-content link rule it used to fight now has `(0,0,1)` specificity (below).

## Other consolidations and notes

- **Hamburger icon:** a `--hamburger-icon` variable (with an active variant that inherits white, since the open sidebar is dark in both themes). It was previously hardcoded in three places.
- **In-content links:** `:where(.content) a` uses the heading colour, carried over from a removed `.theme-custom-01` body class that was folded into variables. The prose underline rule is `:where(.post, .page, p, li) a`. `:where()` keeps both at `(0,0,1)`, so any component class (`.card-link`, `.post-tag`, `.view-all-link a`) overrides them without `!important`. To make prose links blue, change the value to `var(--link-color)`.
- **Focus:** one global `:focus-visible` outline (`2px solid var(--focus-ring)`, offset `2px`). No rule sets `outline: none`. Hover styles are written `:is(:hover, :focus-visible)` so keyboard users get the same feedback.
- **The sidebar checkbox** is visually hidden but focusable (not `display: none`), so the menu opens from the keyboard; its focus ring is drawn on `.sidebar-toggle`.
- **Scrolling:** the viewport scrolls, not `<body>`. `html { scroll-padding-top: 4.5rem }` keeps anchor jumps and focus scrolling clear of the sticky masthead, which turns static on viewports under 30em tall. Display maths scrolls inside its own box rather than being clipped.
- **Removed dead weight:** vendor prefixes, the duplicate `white-space` in `pre`, Lanyon's `.related-posts`, `.pagination-item` and `.layout-reverse` rules, `.search-highlight`, and the `--pagination-*`, `--overlay-bg` and `--header-border-color` tokens.
- **Sass caveat:** `jekyll-sass-converter` is pinned at 1.5.2. The stylesheets are plain `.css` today, so it never runs; if any file becomes `.scss`, avoid Dart-only syntax (`@use`, `math.div`).

## References
- Render-blocking CSS / FOUC: <https://web.dev/articles/critical-rendering-path/render-blocking-css>
- `MutationObserver`, which `test_theme_flash.py` uses to see write order: <https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver>
- `prefers-color-scheme`: <https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme>
- `:where()` (zero-specificity selectors): <https://developer.mozilla.org/en-US/docs/Web/CSS/:where>
- `:focus-visible`: <https://developer.mozilla.org/en-US/docs/Web/CSS/:focus-visible>
- `color-scheme`: <https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme>
- WCAG 2.2 contrast minimums: [text, 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [non-text, 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
