/**
 * Command palette
 *
 * Cmd/Ctrl-K opens a keyboard-first overlay to jump-search posts. Reuses the
 * existing /search-index.json and Fuse.js (already loaded globally), so it adds
 * no new data or search dependency, only this module.
 *
 * Contract (kept stable for tests):
 *   .command-palette            overlay, `hidden` when closed
 *   .command-palette-input      text input, focused on open
 *   .command-palette-results    <ul> of <li><a> results
 *   [aria-selected="true"]      the active result
 */

(function () {
  'use strict';

  const MAX_RESULTS = 8;
  let overlay, input, list, fuse, results = [], selected = 0, loaded = false;

  function build() {
    overlay = document.createElement('div');
    overlay.className = 'command-palette';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Search essays');
    overlay.hidden = true;
    overlay.innerHTML =
      '<div class="command-palette-panel">' +
      '  <input class="command-palette-input" type="text"' +
      '         placeholder="Search essays..." aria-label="Search essays"' +
      '         autocomplete="off" spellcheck="false">' +
      '  <ul class="command-palette-results" role="listbox"></ul>' +
      '</div>';
    document.body.appendChild(overlay);

    input = overlay.querySelector('.command-palette-input');
    list = overlay.querySelector('.command-palette-results');

    input.addEventListener('input', () => run(input.value));
    input.addEventListener('keydown', onKeydown);
    overlay.addEventListener('mousedown', (e) => {
      if (e.target === overlay) close();
    });
  }

  async function ensureIndex() {
    if (loaded) return;
    const res = await fetch('/search-index.json');
    const data = await res.json();
    fuse = new Fuse(data, {
      keys: ['title', 'tags'],
      threshold: 0.4,
      ignoreLocation: true,
      minMatchCharLength: 2,
    });
    loaded = true;
  }

  function run(query) {
    if (!fuse || !query.trim()) {
      results = [];
      render();
      return;
    }
    results = fuse.search(query).slice(0, MAX_RESULTS).map(r => r.item);
    selected = 0;
    render();
  }

  function render() {
    list.innerHTML = '';
    results.forEach((item, i) => {
      const li = document.createElement('li');
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', i === selected ? 'true' : 'false');

      const a = document.createElement('a');
      a.href = item.url;
      a.className = 'command-palette-result';
      a.textContent = item.title;
      li.appendChild(a);

      li.addEventListener('mouseenter', () => { selected = i; paint(); });
      li.addEventListener('click', () => go(item.url));
      list.appendChild(li);
    });
  }

  function paint() {
    Array.from(list.children).forEach((li, i) =>
      li.setAttribute('aria-selected', i === selected ? 'true' : 'false'));
  }

  function onKeydown(e) {
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (results.length) { selected = (selected + 1) % results.length; paint(); }
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (results.length) { selected = (selected - 1 + results.length) % results.length; paint(); }
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const item = results[selected];
      if (item) go(item.url);
      else if (input.value.trim()) go('/search/?q=' + encodeURIComponent(input.value.trim()));
    }
  }

  function go(url) { window.location.href = url; }

  async function open() {
    if (!overlay) build();
    overlay.hidden = false;
    document.documentElement.classList.add('command-palette-open');
    input.value = '';
    results = [];
    render();
    input.focus();
    try {
      await ensureIndex();
      run(input.value); // in case the user typed before the index finished loading
    } catch (err) {
      console.error('Command palette: index load failed', err);
    }
  }

  function close() {
    if (!overlay) return;
    overlay.hidden = true;
    document.documentElement.classList.remove('command-palette-open');
  }

  function isOpen() { return overlay && !overlay.hidden; }

  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
      e.preventDefault();
      isOpen() ? close() : open();
    }
  });
})();
