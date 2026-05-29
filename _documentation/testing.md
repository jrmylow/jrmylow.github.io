# Test commands for UX

```bash
# Install dependencies
uv add pytest pytest-playwright

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_theme_toggle.py

# Run with headed browser (visible)
uv run pytest --headed

# Run all tests with Firefox
uv run pytest --browser firefox

# Run with visible browser
uv run pytest --browser firefox --headed

# Run single test file
uv run pytest tests/test_theme_toggle.py --browser firefox

# Run single test
uv run pytest tests/test_theme_toggle.py::TestThemeToggle::test_default_theme_is_dark --browser firefox
```
