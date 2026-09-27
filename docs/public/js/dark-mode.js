// Theme. An explicit choice (localStorage 'theme') wins; with nothing stored the
// site follows the OS preference live. Only a toggle stores a choice, so a first
// visit never pins the OS theme.
//
// The inline script in _includes/head.html sets the initial theme before first
// paint. This file keeps the toggle checkbox in sync and handles toggles and OS
// changes. Tests: _tests/test_theme_matrix.py, _tests/test_theme_flash.py.

const osPrefersLight = window.matchMedia('(prefers-color-scheme: light)');

function storedTheme() {
  return localStorage.getItem('theme');
}

function osTheme() {
  return osPrefersLight.matches ? 'light' : 'dark';
}

// Show a theme without storing it.
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const toggleInput = document.querySelector('.theme-toggle input');
  if (toggleInput) {
    toggleInput.checked = theme === 'light';
  }
}

// Called by the sidebar checkbox. Flips the theme shown, which came from the OS
// when nothing is stored, and stores the result as the user's choice.
function toggleTheme() {
  const shown = document.documentElement.getAttribute('data-theme') || storedTheme() || osTheme();
  const next = shown === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', next);
  applyTheme(next);
}

document.addEventListener('DOMContentLoaded', () => {
  applyTheme(storedTheme() || osTheme());
});

osPrefersLight.addEventListener('change', () => {
  if (!storedTheme()) {
    applyTheme(osTheme());
  }
});
