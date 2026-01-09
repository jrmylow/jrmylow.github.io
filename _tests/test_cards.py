"""Tests for card component styles and functionality."""

from playwright.sync_api import Page

from constants import SELECTORS


class TestCardStyles:
    """Tests for the consolidated card system."""

    def test_index_page_has_post_cards(self, page: Page, jekyll_server: str):
        """Index page should display post cards."""
        page.goto(jekyll_server)

        # Should have card grid container
        card_grid = page.locator(SELECTORS["card_grid"])
        assert card_grid.count() >= 1, "Index page should have a card grid"

    def test_card_grid_has_cards(self, page: Page, jekyll_server: str):
        """Card grid should contain card elements."""
        page.goto(jekyll_server)

        cards = page.locator(f"{SELECTORS['card_grid']} {SELECTORS['card']}")
        assert cards.count() >= 1, "Card grid should contain cards"

    def test_cards_have_required_elements(self, page: Page, jekyll_server: str):
        """Each card should have title, date, and body."""
        page.goto(jekyll_server)

        first_card = page.locator(SELECTORS["card"]).first

        # Check for title
        title = first_card.locator(SELECTORS["card_title"])
        assert title.count() == 1, "Card should have a title"

        # Check for meta (date)
        meta = first_card.locator(SELECTORS["card_meta"])
        assert meta.count() == 1, "Card should have meta info"

        # Check for body
        body = first_card.locator(SELECTORS["card_body"])
        assert body.count() == 1, "Card should have a body"

    def test_cards_are_clickable_links(self, page: Page, jekyll_server: str):
        """Cards should be wrapped in links."""
        page.goto(jekyll_server)

        card_links = page.locator(SELECTORS["card_link"])
        assert card_links.count() >= 1, "Cards should be wrapped in links"

        # First link should have href
        first_link = card_links.first
        href = first_link.get_attribute("href")
        assert href is not None and len(href) > 0, "Card link should have href"

    def test_card_hover_changes_style(self, page: Page, jekyll_server: str):
        """Card should change background on hover."""
        page.goto(jekyll_server)

        card = page.locator(SELECTORS["card"]).first

        # Get initial background
        initial_bg = card.evaluate("el => getComputedStyle(el).backgroundColor")

        # Hover over card
        card.hover()

        # Get hover background
        hover_bg = card.evaluate("el => getComputedStyle(el).backgroundColor")

        assert initial_bg != hover_bg, "Card background should change on hover"

    def test_view_all_link_exists(self, page: Page, jekyll_server: str):
        """Index page should have 'view all' link to essays."""
        page.goto(jekyll_server)

        view_all = page.locator(SELECTORS["view_all_link"])
        assert view_all.count() == 1, "Should have view all link"

        href = view_all.get_attribute("href")
        assert "/essays" in href, "View all should link to essays page"

    def test_responsive_grid_columns(self, page: Page, jekyll_server: str):
        """Card grid should be responsive."""
        page.goto(jekyll_server)

        card_grid = page.locator(SELECTORS["card_grid"]).first

        # At desktop width (1280px from fixture), should have multiple columns
        grid_template = card_grid.evaluate(
            "el => getComputedStyle(el).gridTemplateColumns"
        )

        # Should have more than one column value (not just "1fr" or similar)
        assert grid_template != "none", "Grid should have column template"
