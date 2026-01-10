/**
 * Site Search
 *
 * Redirect-based search implementation:
 * - Sidebar: redirects to /search/?q= on Enter
 * - Search page: displays results, re-searches on Enter
 *
 * The search engine (Fuse.js) can be swapped by replacing the SearchEngine class.
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
        keys: ['title', 'content'],
        threshold: 0.4,
        ignoreLocation: true,
        minMatchCharLength: 2,
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
      return this.fuse.search(query).map(result => result.item);
    }
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

      // Handle Enter key for new search
      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const query = this.input.value.trim();
          if (query) {
            window.location.href = '/search/?q=' + encodeURIComponent(query);
          }
        }
      });

      // Get query from URL and perform search
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

      results.forEach(item => {
        const link = document.createElement('a');
        link.href = item.url;
        link.className = 'search-result-item';

        const title = document.createElement('span');
        title.className = 'search-result-title';
        title.textContent = item.title;

        const date = document.createElement('span');
        date.className = 'search-result-date';
        date.textContent = item.date || '';

        const excerpt = document.createElement('span');
        excerpt.className = 'search-result-excerpt';
        excerpt.textContent = this.truncate(item.content, 150);

        link.appendChild(title);
        if (item.date) {
          link.appendChild(date);
        }
        link.appendChild(excerpt);
        this.resultsContainer.appendChild(link);
      });
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
    // Always init sidebar search (redirect behavior)
    initSidebarSearch();

    // Check if we're on the search page
    const isSearchPage = document.querySelector('.search-page-input');
    if (!isSearchPage) return;

    // Initialize search engine for search page
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

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
