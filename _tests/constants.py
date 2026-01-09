"""Shared constants for UX tests."""

# Theme colors (CSS computed values)
DARK_BG_COLOR = "rgb(26, 26, 26)"
LIGHT_BG_COLOR = "rgb(242, 237, 231)"

# Icon colors
WHITE_HEX = "ffffff"
WHITE_HEX_SHORT = "fff"

# Animation/transition timing (ms)
ANIMATION_TIMEOUT = 400

# CSS Selectors
SELECTORS = {
    "sidebar_toggle": ".sidebar-toggle",
    "theme_toggle": ".toggle-switch",
    "theme_toggle_input": ".theme-toggle input[type='checkbox']",
    "html": "html",
    "body": "body",
    "card": ".card",
    "card_grid": ".card-grid",
    "card_link": ".card-link",
    "card_title": ".card-title",
    "card_meta": ".card-meta",
    "card_body": ".card-body",
    "view_all_link": ".view-all-link a",
}

# Test page URL path (use this instead of posts)
TEST_PAGE_PATH = "/2020/04/12/post1/"
