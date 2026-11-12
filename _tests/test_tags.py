"""Tests for tags: the links on a post, and the tags page's cloud and filter.

Expectations are the designed corpus's tag cases (corpus.py). Alpha is on four posts and
beta on two, so their counts can't be confused; one post has both, so every way of combining
the two selects a different set; and "alphabet" is a separate tag that contains "alpha".
"""

import urllib.parse

import corpus
import pytest
from playwright.sync_api import Page

# The designed tags as the cloud shows them: in alphabetical order, each with its post count.
CLOUD = ["alpha (4)", "alphabet (1)", "beta (2)", "quokka (1)"]

# The posts shown for each selection, newest first.
SHOWN = [
    (("alpha",), [corpus.ALPHA, corpus.ALPHA_TWO, corpus.ALPHA_THREE, corpus.ALPHA_BETA]),
    (("beta",), [corpus.BETA, corpus.ALPHA_BETA]),
    (("alpha", "beta"), [corpus.ALPHA_BETA]),  # all of the selected tags, not any of them
    (("alphabet",), [corpus.UNSHARED_TAGS]),
    (("alphabet", "quokka"), [corpus.UNSHARED_TAGS]),
    (("alpha", "quokka"), []),  # tags are selected, but no post has both
]


def _ids(selection: tuple[str, ...]) -> str:
    return "+".join(selection)


def _shown(page: Page) -> list[str]:
    """Titles of the posts the filter is showing, in page order."""
    return page.locator(".tag-post-item:visible a").all_inner_texts()


def _selected(page: Page) -> list[str]:
    """The tags marked as selected, in cloud order; the pressed state and the highlight must agree."""
    pressed = page.locator(".tag-cloud-item[aria-pressed='true']").evaluate_all("els => els.map(e => e.dataset.tag)")
    highlighted = page.locator(".tag-cloud-item.selected").evaluate_all("els => els.map(e => e.dataset.tag)")
    assert pressed == highlighted, "aria-pressed and the .selected highlight disagree"
    return pressed


def _tags_in_url(page: Page) -> list[str]:
    """The tags named in the address bar's ?t=, or [] if there is no ?t=."""
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)
    return query["t"][0].split(",") if "t" in query else []


def _click_tag(page: Page, tag: str) -> None:
    page.locator(f".tag-cloud-item[data-tag='{tag}']").click()


class TestPostTags:
    """A post lists its tags, each linking to the tags page filtered to that tag."""

    def test_post_lists_its_tags_as_links_to_the_filtered_tags_page(self, page: Page, designed_site):
        page.goto(designed_site.page_url(corpus.UNSHARED_TAGS.filename))
        tags = page.locator(".post-tags .post-tag")
        assert tags.all_inner_texts() == ["alphabet", "quokka"]
        hrefs = tags.evaluate_all("els => els.map(a => a.getAttribute('href'))")
        assert hrefs == ["/tags/?t=alphabet", "/tags/?t=quokka"]

    def test_untagged_post_has_no_tags_block(self, page: Page, designed_site):
        page.goto(designed_site.page_url(corpus.LINKED.filename))
        assert page.locator(".post-tags").count() == 0

    def test_following_a_tag_shows_that_tags_posts(self, page: Page, designed_site):
        """From a post with two tags, the second tag's link selects that tag and no other."""
        page.goto(designed_site.page_url(corpus.ALPHA_BETA.filename))
        with page.expect_navigation():
            page.locator(".post-tag", has_text="beta").click()
        assert _tags_in_url(page) == ["beta"]
        assert _selected(page) == ["beta"]
        assert _shown(page) == [corpus.BETA.title, corpus.ALPHA_BETA.title]

    def test_post_tag_is_not_underlined(self, page: Page, designed_site):
        page.goto(designed_site.page_url(corpus.ALPHA.filename))
        tag = page.locator(".post-tag")
        assert "underline" not in tag.evaluate("el => getComputedStyle(el).textDecoration")
        tag.hover()
        assert "underline" not in tag.evaluate("el => getComputedStyle(el).textDecoration")


class TestTagsPage:
    """The tags page as it loads: the cloud, the full list, and nothing selected."""

    def test_cloud_lists_each_tag_once_in_order_with_its_post_count(self, page: Page, designed_site):
        """Filtered to the designed tags, so the test also holds with --scale-posts filler."""
        page.goto(f"{designed_site.url}/tags/")
        labels = page.locator(".tag-cloud-item").all_inner_texts()
        designed = {label.split(" (")[0] for label in CLOUD}
        assert [label for label in labels if label.split(" (")[0] in designed] == CLOUD

    def test_every_post_is_in_the_list_once_newest_first(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}/tags/")
        hrefs = page.locator(".tag-post-item a").evaluate_all("els => els.map(a => a.getAttribute('href'))")
        assert hrefs == [post["url"] for post in designed_site.manifest["posts"]]

    def test_nothing_is_selected_or_shown_at_first(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}/tags/")
        assert _selected(page) == []
        assert _shown(page) == []

    def test_intro_prose_is_rendered(self, page: Page, jekyll_server: str):
        """The real page's Markdown body (how to use the filter) appears above the cloud."""
        page.goto(f"{jekyll_server}/tags/")
        assert "select tags" in page.locator(".page").inner_text().lower()

    def test_cloud_tag_changes_colour_on_hover_without_an_underline(self, page: Page, designed_site):
        page.add_init_script("localStorage.setItem('theme', 'light')")
        page.goto(f"{designed_site.url}/tags/")
        page.add_style_tag(content="*, *::before, *::after { transition: none !important; }")
        tag = page.locator(".tag-cloud-item").first
        before = tag.evaluate("el => getComputedStyle(el).color")
        tag.hover()
        assert tag.evaluate("el => getComputedStyle(el).color") != before
        assert "underline" not in tag.evaluate("el => getComputedStyle(el).textDecoration")


class TestTagFilter:
    """Selecting tags shows the posts that have every selected tag, and the address follows."""

    @pytest.mark.parametrize("selection, posts", SHOWN, ids=[_ids(selection) for selection, _ in SHOWN])
    def test_clicking_tags_shows_the_posts_with_all_of_them(self, page: Page, designed_site, selection, posts):
        page.goto(f"{designed_site.url}/tags/")
        for tag in selection:
            _click_tag(page, tag)
        assert _shown(page) == [post.title for post in posts]
        assert _selected(page) == list(selection)
        assert _tags_in_url(page) == list(selection)

    @pytest.mark.parametrize("selection, posts", SHOWN, ids=[_ids(selection) for selection, _ in SHOWN])
    def test_address_naming_tags_selects_them(self, page: Page, designed_site, selection, posts):
        page.goto(f"{designed_site.url}/tags/?t={','.join(selection)}")
        assert _selected(page) == list(selection)
        assert _shown(page) == [post.title for post in posts]

    def test_address_naming_an_unknown_tag_ignores_it(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}/tags/?t=beta,no-such-tag")
        assert _selected(page) == ["beta"]
        assert _shown(page) == [corpus.BETA.title, corpus.ALPHA_BETA.title]

    def test_deselecting_widens_the_filter_then_empties_it(self, page: Page, designed_site):
        page.goto(f"{designed_site.url}/tags/")
        _click_tag(page, "alpha")
        _click_tag(page, "beta")
        assert _shown(page) == [corpus.ALPHA_BETA.title]

        _click_tag(page, "alpha")
        assert _selected(page) == ["beta"]
        assert _shown(page) == [corpus.BETA.title, corpus.ALPHA_BETA.title]
        assert _tags_in_url(page) == ["beta"]

        _click_tag(page, "beta")
        assert _selected(page) == []
        assert _shown(page) == []
        assert "t=" not in page.url, "with nothing selected the address has no ?t="
