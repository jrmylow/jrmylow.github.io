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

Because it runs before CSS and before paint, the correct theme is applied with no flash. `dark-mode.js` (deferred) still owns the interactive toggle (`toggleTheme`) and writes the choice to `localStorage` under the `theme` key; the inline script only sets the initial value, falling back to `prefers-color-scheme` when nothing is stored. `test_theme_flash.py` guards all of this.

## Cards

In `cards.css`, `.card-grid` is a CSS grid (gap `1rem`, vertical margin `2rem`); the `card-grid-N` variants set columns at the breakpoints above. A card uses `--code-bg` for its background and `--header-border-color` for its border (radius `8px`, `min-height: 250px`), and transitions background, border, and colour on hover to the sidebar-hover palette. Known wart: the hover text colour uses `!important` to win a specificity battle — flagged for an elector-ordering fix rather than left as intended.

## Other consolidations and notes

- **Hamburger icon:** a `--hamburger-icon` variable (with an active variant that inherits white, since the open sidebar is dark in both themes). It was previously hardcoded in three places.
- **In-content links:** `.container.content a` uses the heading colour, carried over from a removed `.theme-custom-01` body class that was folded into variables. As a result `--link-color` is unused for prose; delete that block to switch prose links to blue.
- **Dead weight slated for removal:** stale vendor prefixes (`-webkit-`/`-ms-` on `transform`/`transition`) and a duplicate `white-space` declaration in `pre`.
- **Sass caveat:** `jekyll-sass-converter` is pinned at 1.5.2. The stylesheets are plain `.css` today, so it never runs; if any file becomes `.scss`, avoid Dart-only syntax (`@use`, `math.div`).

## References
- Render-blocking CSS / FOUC: <https://web.dev/articles/critical-rendering-path/render-blocking-css>
- `prefers-color-scheme`: <https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme>
