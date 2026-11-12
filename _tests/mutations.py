"""Known bugs the suite must catch. Run by mutate.py; see there for how.

Each entry is a bug someone could plausibly write, not a syntax error: the site still
builds, and something a reader would notice is wrong. Add one when a bug gets past the
suite, alongside the test that now catches it.

`old` must occur exactly once in its file (test_mutate.py checks, without a build), so a
mutation that the source has moved away from fails loudly instead of quietly testing nothing.
"""

from mutate import Mutation

TAG_FILTER = "docs/public/js/tag-filter.js"
TAGS_PAGE = "docs/_layouts/tags.html"
RELATED = "docs/_includes/related.html"
BACKLINKS = "docs/_includes/backlinks.html"
SERIES = "docs/_includes/series.html"
SEARCH = "docs/public/js/search.js"
SEARCH_INDEX = "docs/search-index.json"
PALETTE = "docs/public/js/command-palette.js"
POST_CARD = "docs/_includes/post_card.html"

TAGS_TESTS = ("_tests/test_tags.py",)
RELATED_TESTS = ("_tests/test_related.py",)
BACKLINKS_TESTS = ("_tests/test_backlinks.py",)
SERIES_TESTS = ("_tests/test_series.py",)
SEARCH_TESTS = ("_tests/test_search.py",)
PALETTE_TESTS = ("_tests/test_command_palette.py",)
CARD_TESTS = ("_tests/test_cards.py",)

MUTATIONS = [
    # --- Tags page: the filter ---
    Mutation(
        "tag filter shows every post once any tag is selected",
        TAG_FILTER,
        "const hasAllTags = selected.every(tag => postTags.includes(tag));",
        "const hasAllTags = true;",
        TAGS_TESTS,
    ),
    Mutation(
        "tag filter shows posts with any selected tag, not all of them",
        TAG_FILTER,
        "selected.every(tag => postTags.includes(tag))",
        "selected.some(tag => postTags.includes(tag))",
        TAGS_TESTS,
    ),
    Mutation(
        "tag filter matches a tag inside a longer tag",
        TAG_FILTER,
        "const postTags = (post.getAttribute('data-tags') || '').split(',');",
        "const postTags = (post.getAttribute('data-tags') || '');",
        TAGS_TESTS,
    ),
    Mutation(
        "tags page URL keeps only the first selected tag",
        TAG_FILTER,
        "url.searchParams.set(PARAM_NAME, selected.join(','));",
        "url.searchParams.set(PARAM_NAME, selected[0]);",
        TAGS_TESTS,
    ),
    Mutation(
        "tags page URL naming two tags selects neither",
        TAG_FILTER,
        "const tags = param.split(',').map(t => t.trim()).filter(t => t);",
        "const tags = [param];",
        TAGS_TESTS,
    ),
    # --- Tags page: the cloud and the list ---
    Mutation(
        "tag cloud counts are one too many",
        TAGS_PAGE,
        "{{ tag }} ({{ count }})",
        "{{ tag }} ({{ count | plus: 1 }})",
        TAGS_TESTS,
    ),
    Mutation(
        "tag cloud is in first-seen order, not sorted",
        TAGS_PAGE,
        "all_tags | uniq | sort_natural",
        "all_tags | uniq",
        TAGS_TESTS,
    ),
    Mutation(
        "tags page lists posts oldest first",
        TAGS_PAGE,
        "{% for post in site.posts %}\n    {% assign post_tags",
        "{% for post in site.posts reversed %}\n    {% assign post_tags",
        TAGS_TESTS,
    ),
    Mutation(
        "a post's tag links go to the tags page with no tag selected",
        "docs/_includes/tags.html",
        "'/tags/?t=' | append: tag | relative_url",
        "'/tags/' | relative_url",
        TAGS_TESTS,
    ),
    # --- Related ---
    Mutation(
        "related lists four posts",
        RELATED,
        "{% assign max_related = 3 %}",
        "{% assign max_related = 4 %}",
        RELATED_TESTS,
    ),
    Mutation(
        "related lists the post itself",
        RELATED,
        "{% if post.url != page.url and shown < max_related %}",
        "{% if shown < max_related %}",
        RELATED_TESTS,
    ),
    Mutation(
        "related lists posts that share no tag",
        RELATED,
        "{% if shared > 0 %}",
        "{% if shared >= 0 %}",
        RELATED_TESTS,
    ),
    Mutation(
        "related lists the oldest matches, not the newest",
        RELATED,
        "{% for post in site.posts %}",
        "{% for post in site.posts reversed %}",
        RELATED_TESTS,
    ),
    # --- Backlinks ---
    Mutation(
        "every other post is listed as a reference",
        BACKLINKS,
        "{% if post.url != page.url and post.content contains page.url %}",
        "{% if post.url != page.url %}",
        BACKLINKS_TESTS,
    ),
    Mutation(
        "a post that links to itself is its own reference",
        BACKLINKS,
        "{% if post.url != page.url and post.content contains page.url %}",
        "{% if post.content contains page.url %}",
        BACKLINKS_TESTS,
    ),
    # --- Series ---
    Mutation(
        "series parts are in date order, not series order",
        SERIES,
        '| where: "series", page.series | sort: "series_order" %}',
        '| where: "series", page.series %}',
        SERIES_TESTS,
    ),
    Mutation(
        "a series of one gets series navigation",
        SERIES,
        "{% if parts.size > 1 %}",
        "{% if parts.size > 0 %}",
        SERIES_TESTS,
    ),
    Mutation(
        "no series part is marked as the current one",
        SERIES,
        "{% if part.url == page.url %}",
        "{% if false %}",
        SERIES_TESTS,
    ),
    # --- Search ---
    Mutation(
        "search doesn't look at tags",
        SEARCH,
        "keys: ['title', 'tags', 'content'],",
        "keys: ['title', 'content'],",
        SEARCH_TESTS,
    ),
    Mutation(
        "search results render a title's markup instead of showing it",
        SEARCH,
        "    return div.innerHTML;",
        "    return String(text == null ? '' : text);",
        SEARCH_TESTS,
    ),
    Mutation(
        "search matches exact text only, so a typo finds nothing",
        SEARCH,
        "threshold: 0.4,",
        "threshold: 0.0,",
        SEARCH_TESTS,
    ),
    Mutation(
        "search excerpts don't highlight the match",
        SEARCH,
        "excerpt.innerHTML = this.excerptAround(item.content, contentMatch.indices, 150);",
        "excerpt.textContent = this.truncate(item.content, 150);",
        SEARCH_TESTS,
    ),
    Mutation(
        "search index has no tags",
        SEARCH_INDEX,
        '"tags": {{ post.tags | jsonify }},',
        '"tags": [],',
        SEARCH_TESTS,
    ),
    Mutation(
        "search results all link to the home page",
        SEARCH_INDEX,
        '"url": {{ post.url | jsonify }},',
        '"url": "/",',
        SEARCH_TESTS,
    ),
    Mutation(
        "search index holds only the newest post",
        SEARCH_INDEX,
        "{% for post in site.posts %}",
        "{% for post in site.posts limit:1 %}",
        SEARCH_TESTS,
    ),
    # --- Command palette ---
    Mutation(
        "palette shows nine results",
        PALETTE,
        "const MAX_RESULTS = 8;",
        "const MAX_RESULTS = 9;",
        PALETTE_TESTS,
    ),
    Mutation(
        "palette Enter opens the search page, not the selected result",
        PALETTE,
        "if (item) go(item.url);",
        "if (false) go(item.url);",
        PALETTE_TESTS,
    ),
    Mutation(
        "palette down arrow doesn't move the selection",
        PALETTE,
        "if (results.length) { selected = (selected + 1) % results.length; paint(); }",
        "if (results.length) { paint(); }",
        PALETTE_TESTS,
    ),
    # --- The suite's own helpers ---
    Mutation(
        "accessibility scan judges colours part-way through a fade",
        "_tests/test_a11y.py",
        "    page.add_style_tag(content=SETTLED)\n    options =",
        "    options =",
        ("_tests/test_a11y.py::test_scan_judges_colours_once_transitions_have_finished",),
    ),
    # --- Cards on the home and essays pages ---
    Mutation(
        "home shows seven posts",
        "docs/_layouts/index.html",
        "{% for post in recent_posts limit: 6 %}",
        "{% for post in recent_posts limit: 7 %}",
        CARD_TESTS,
    ),
    Mutation(
        "home lists oldest posts first",
        "docs/_layouts/index.html",
        "{% assign recent_posts = site.posts | sort: 'date' | reverse %}",
        "{% assign recent_posts = site.posts | sort: 'date' %}",
        CARD_TESTS,
    ),
    Mutation(
        "essays landing shows six posts",
        "docs/_layouts/essays.html",
        "{% for post in sorted_posts limit:5 %}",
        "{% for post in sorted_posts limit:6 %}",
        CARD_TESTS,
    ),
    Mutation(
        "cards ignore a post's summary",
        POST_CARD,
        "{% if post.summary %}{% for paragraph in post.summary limit:1 %}<p>{{ paragraph.p }}</p>{% endfor %}"
        "{% else %}{{ post.excerpt }}{% endif %}",
        "{{ post.excerpt }}",
        CARD_TESTS,
    ),
    Mutation(
        "cards link to the home page",
        POST_CARD,
        '<a href="{{ post.url | relative_url }}" class="card-link">',
        '<a href="{{ \'/\' | relative_url }}" class="card-link">',
        CARD_TESTS,
    ),
]
