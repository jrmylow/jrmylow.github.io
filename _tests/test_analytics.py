"""Tests for GoatCounter analytics integration."""

from playwright.sync_api import Page


class TestGoatCounterIntegration:
    """Tests for GoatCounter analytics setup."""

    def test_goatcounter_script_present(self, page: Page, jekyll_server: str):
        """GoatCounter script should be present on pages."""
        page.goto(jekyll_server)

        script = page.locator("script[data-goatcounter]")
        assert script.count() == 1, "Should have GoatCounter script"

        src = script.get_attribute("src")
        assert "gc.zgo.at/count.js" in src, "Should load GoatCounter script"

    def test_goatcounter_uses_correct_site(self, page: Page, jekyll_server: str):
        """GoatCounter should use the correct site identifier."""
        page.goto(jekyll_server)

        script = page.locator("script[data-goatcounter]")
        data_gc = script.get_attribute("data-goatcounter")

        assert "jrmylow-gc.goatcounter.com" in data_gc, "Should use correct GoatCounter site"

    def test_noscript_fallback_exists(self, page: Page, jekyll_server: str):
        """Noscript fallback should exist for non-JS browsers."""
        page.goto(jekyll_server)

        html = page.content()
        assert "<noscript>" in html, "Should have noscript fallback"
        assert "jrmylow-gc.goatcounter.com/count" in html, "Noscript should have GoatCounter pixel"

    def test_noscript_fallback_has_dynamic_page_url(self, page: Page, jekyll_server: str):
        """Noscript fallback should use actual page URL, not placeholder."""
        page.goto(jekyll_server)

        html = page.content()

        # Should NOT have the placeholder text
        assert "INSERT-PAGE-HERE" not in html, "Should not have placeholder in noscript"

    def test_noscript_fallback_reflects_current_page(self, page: Page, jekyll_server: str):
        """Noscript fallback URL should match the current page."""
        page.goto(f"{jekyll_server}/about/")

        html = page.content()

        # The noscript img src should contain the page path
        assert "p=/about" in html or "p=%2Fabout" in html, "Noscript should contain page path"

    def test_noscript_fallback_on_post_page(self, page: Page, jekyll_server: str, any_post_url: str):
        page.goto(f"{jekyll_server}{any_post_url}")
        html = page.content()
        escaped = any_post_url.replace("/", "%2F")
        assert (
            f"p={any_post_url}" in html or f"p={escaped}" in html
        ), f"Noscript should contain post path {any_post_url}"
