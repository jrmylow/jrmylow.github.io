/**
 * Site Search
 *
 * Redirect-based search implementation:
 * - Sidebar: redirects to /search/?q= on Enter
 * - Search page: displays results, re-searches on Enter
 *
 * The search engine (Fuse.js) can be swapped by replacing the SearchEngine class.
 *
 * Enhancements over the original:
 * - `tags` is indexed and searchable, and rendered as chips on each result.
 * - Matched substrings are wrapped in <mark> (Fuse `includeMatches`).
 */

(function () {
  'use strict';

  /* ==========================================================================
     Search Engine (Fuse.js implementation - swap this to change engines)
     ========================================================================== */

  class FuseSearchEngine {
    constructor(options = {}) {
      this.fuse = null;
      this.options = Object.assign({
        keys: ['title', 'tags', 'content'],
        threshold: 0.4,
        ignoreLocation: true,
        minMatchCharLength: 2,
        includeMatches: true,
      }, options);
    }

    async init(indexUrl) {
      const response = await fetch(indexUrl);
      const data = await response.json();
      this.fuse = new Fuse(data, this.options);
    }

    search(query) {
      if (!this.fuse || !query.trim()) {
        return [];
      }
      // Keep the match metadata so the page can highlight hits.
      return this.fuse.search(query).map(result => ({
        item: result.item,
        matches: result.matches || [],
      }));
    }
  }

  /* ==========================================================================
     Highlighting helpers
     ========================================================================== */

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  // Wrap the given [start, end] (inclusive) index ranges of `text` in <mark>,
  // escaping everything so result content can never inject markup.
  function highlight(text, ranges) {
    if (text == null) return '';
    const src = String(text);
    if (!ranges || ranges.length === 0) return escapeHtml(src);

    const sorted = ranges.slice().sort((a, b) => a[0] - b[0]);
    let out = '';
    let cursor = 0;
    sorted.forEach(([start, end]) => {
      if (start < cursor) return; // skip overlaps
      out += escapeHtml(src.slice(cursor, start));
      out += '<mark>' + escapeHtml(src.slice(start, end + 1)) + '</mark>';
      cursor = end + 1;
    });
    out += escapeHtml(src.slice(cursor));
    return out;
  }

  function matchFor(matches, key) {
    return matches.find(m => m.key === key);
  }

  /* ==========================================================================
     Sidebar Search (redirect only)
     ========================================================================== */

  function initSidebarSearch() {
    const input = document.querySelector('.sidebar .search-input');
    if (!input) return;

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        const query = input.value.trim();
        if (query) {
          window.location.href = '/search/?q=' + encodeURIComponent(query);
        }
      }
    });
  }

  /* ==========================================================================
     Search Page
     ========================================================================== */

  class SearchPage {
    constructor(engine) {
      this.engine = engine;
      this.input = null;
      this.resultsContainer = null;
    }

    init() {
      this.input = document.querySelector('.search-page-input');
      this.resultsContainer = document.querySelector('.search-page-results');

      if (!this.input || !this.resultsContainer) {
        return;
      }

      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const query = this.input.value.trim();
          if (query) {
            window.location.href = '/search/?q=' + encodeURIComponent(query);
          }
        }
      });

      const urlParams = new URLSearchParams(window.location.search);
      const query = urlParams.get('q');

      if (query) {
        this.input.value = query;
        this.performSearch(query);
      }
    }

    performSearch(query) {
      const results = this.engine.search(query);
      this.renderResults(results);
    }

    renderResults(results) {
      this.resultsContainer.innerHTML = '';

      if (results.length === 0) {
        this.resultsContainer.innerHTML = '<div class="search-no-results">No results found</div>';
        return;
      }

      results.forEach(({ item, matches }) => {
        const link = document.createElement('a');
        link.href = item.url;
        link.className = 'search-result-item';

        const title = document.createElement('span');
        title.className = 'search-result-title';
        title.innerHTML = highlight(item.title, (matchFor(matches, 'title') || {}).indices);

        link.appendChild(title);

        if (item.date) {
          const date = document.createElement('span');
          date.className = 'search-result-date';
          date.textContent = item.date;
          link.appendChild(date);
        }

        if (item.tags && item.tags.length) {
          const tagWrap = document.createElement('span');
          tagWrap.className = 'search-result-tags';
          item.tags.forEach(t => {
            const chip = document.createElement('span');
            chip.className = 'search-result-tag';
            chip.textContent = t;
            tagWrap.appendChild(chip);
          });
          link.appendChild(tagWrap);
        }

        const excerpt = document.createElement('span');
        excerpt.className = 'search-result-excerpt';
        const contentMatch = matchFor(matches, 'content');
        if (contentMatch) {
          excerpt.innerHTML = this.excerptAround(item.content, contentMatch.indices, 150);
        } else {
          excerpt.textContent = this.truncate(item.content, 150);
        }
        link.appendChild(excerpt);

        this.resultsContainer.appendChild(link);
      });
    }

    // Build a ~`length`-char window centred on the first match and highlight
    // every match that falls inside the window.
    excerptAround(text, ranges, length) {
      if (!text) return '';
      const src = String(text);
      if (!ranges || ranges.length === 0) return this.truncate(src, length);

      const first = ranges.slice().sort((a, b) => a[0] - b[0])[0][0];
      const half = Math.floor(length / 2);
      let start = Math.max(0, first - half);
      let end = Math.min(src.length, start + length);
      start = Math.max(0, end - length);

      const shifted = ranges
        .filter(([s, e]) => e >= start && s < end)
        .map(([s, e]) => [Math.max(s, start) - start, Math.min(e, end - 1) - start]);

      let out = highlight(src.slice(start, end), shifted);
      if (start > 0) out = '...' + out;
      if (end < src.length) out = out + '...';
      return out;
    }

    truncate(text, length) {
      if (!text) return '';
      if (text.length <= length) return text;
      return text.substring(0, length).trim() + '...';
    }
  }

  /* ==========================================================================
     Initialize
     ========================================================================== */

  async function init() {
    initSidebarSearch();

    const isSearchPage = document.querySelector('.search-page-input');
    if (!isSearchPage) return;

    const engine = new FuseSearchEngine();

    try {
      await engine.init('/search-index.json');
    } catch (error) {
      console.error('Search: Failed to load index', error);
      return;
    }

    const searchPage = new SearchPage(engine);
    searchPage.init();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
