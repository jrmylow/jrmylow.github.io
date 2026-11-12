"""Shared constants for UX tests."""

# Theme colors (CSS computed values)
DARK_BG_COLOR = "rgb(26, 26, 26)"
LIGHT_BG_COLOR = "rgb(242, 237, 231)"

# Header toggle icons (menu, contents): closed, per theme, and open over the sidebar blue
TOGGLE_ICON_COLORS = {"dark": "rgb(255, 255, 255)", "light": "rgb(33, 75, 138)"}
TOGGLE_ICON_OPEN_COLOR = "rgb(255, 255, 255)"

# Written into each session's build so tests can confirm which server they hit
BUILD_TOKEN_FILE = "__test_build_token__.txt"
ALL_CARDS_PAGE = "test-cards.html"  # designed build only: every post's card on one page

# =============================================================================
# Performance Test Constants
# =============================================================================

# Performance thresholds (milliseconds) - based on Core Web Vitals research
# Stricter for local testing since no network latency
PERF_THRESHOLDS = {
    "ttfb_avg": 100,
    "ttfb_p90": 200,
    "dom_interactive_p90": 200,
    "dom_content_loaded_avg": 250,
    "dom_content_loaded_p90": 250,
    "load_complete_avg": 250,
    "load_complete_p90": 250,
}

# Pages to test - stable pages only; test_performance appends a real post at runtime
PERF_STABLE_PAGES = ["/", "/about/", "/contact/", "/essays/"]

# Number of iterations per page for statistical significance
PERF_ITERATIONS = 10

# Absolute maximum for any single page load (outlier detection)
PERF_MAX_LOAD_TIME = 3000

# Resource limits
PERF_MAX_RESOURCES = 20
PERF_MAX_TRANSFER_BYTES = 500 * 1024  # 500KB
PERF_MAX_DOM_NODES = 1500

# =============================================================================
# CSS Selectors
# =============================================================================

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
    "pagination": ".pagination",
    "search_input": ".search-input",
}
