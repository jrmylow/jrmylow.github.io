"""Shared constants for UX tests."""

# Theme colors (CSS computed values)
DARK_BG_COLOR = "rgb(26, 26, 26)"
LIGHT_BG_COLOR = "rgb(242, 237, 231)"

# Icon colors
WHITE_HEX = "ffffff"
WHITE_HEX_SHORT = "fff"

# Animation/transition timing (ms)
ANIMATION_TIMEOUT = 400

# =============================================================================
# Performance Test Constants
# =============================================================================

# Performance thresholds (milliseconds) - based on Core Web Vitals research
# Stricter for local testing since no network latency
PERF_THRESHOLDS = {
    "ttfb_avg": 100,
    "ttfb_p90": 200,
    "dom_content_loaded_avg": 500,
    "dom_content_loaded_p90": 800,
    "load_complete_avg": 1000,
    "load_complete_p90": 1500,
}

# Pages to test - representative sample of site
PERF_TEST_PAGES = [
    "/",
    "/about/",
    "/contact/",
    "/essays/",
    "/2025/01/01/post1/",
]

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
    "pagination_info": ".pagination-info",
    "pagination_prev": ".pagination-prev",
    "pagination_next": ".pagination-next",
    "search_container": ".search-container",
    "search_input": ".search-input",
    "search_results": ".search-results",
}

# Test page URL path
TEST_PAGE_PATH = "/2020/04/12/post1/"
