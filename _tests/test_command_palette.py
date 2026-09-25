"""Tests for the command palette (Cmd/Ctrl-K)."""

from playwright.sync_api import Page, expect


def _first_title_word(page: Page, jekyll_server: str) -> str:
    """A real query term drawn from the live index, so results are deterministic."""
    page.goto(f"{jekyll_server}/search-index.json")
    return page.evaluate(
        """() => {
            const data = JSON.parse(document.body.innerText);
            const title = (data[0] && data[0].title) || '';
            return (title.split(/\\s+/).find(w => w.length >= 3) || '').toLowerCase();
        }"""
    )


class TestCommandPalette:
    """The palette opens on shortcut, searches the index, and navigates."""

    def test_shortcut_opens_palette(self, page: Page, jekyll_server: str):
        """Ctrl/Cmd-K opens the overlay and focuses the input."""
        page.goto(jekyll_server)
        page.keyboard.press("Control+k")

        expect(page.locator(".command-palette")).to_be_visible()
        expect(page.locator(".command-palette-input")).to_be_focused()

    def test_escape_closes_palette(self, page: Page, jekyll_server: str):
        """Escape hides the overlay."""
        page.goto(jekyll_server)
        page.keyboard.press("Control+k")
        expect(page.locator(".command-palette")).to_be_visible()

        page.keyboard.press("Escape")
        expect(page.locator(".command-palette")).to_be_hidden()

    def test_query_renders_results(self, page: Page, jekyll_server: str):
        """Typing a real term shows at least one result."""
        word = _first_title_word(page, jekyll_server)
        if not word:
            import pytest

            pytest.skip("no indexable post titles")

        page.goto(jekyll_server)
        page.keyboard.press("Control+k")
        page.locator(".command-palette-input").fill(word)

        expect(page.locator(".command-palette-results li").first).to_be_visible()

    def test_enter_navigates_away_from_home(self, page: Page, jekyll_server: str):
        """Enter on a selected result navigates to it."""
        word = _first_title_word(page, jekyll_server)
        if not word:
            import pytest

            pytest.skip("no indexable post titles")

        page.goto(jekyll_server)
        home = page.url
        page.keyboard.press("Control+k")
        palette_input = page.locator(".command-palette-input")
        palette_input.fill(word)
        expect(page.locator(".command-palette-results li").first).to_be_visible()
        palette_input.press("Enter")

        expect(page).not_to_have_url(home)
