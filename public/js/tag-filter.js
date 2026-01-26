/**
 * Tag Filter
 *
 * Multi-tag filtering with AND logic.
 * - Click tag to select/deselect
 * - Multiple tags show posts matching ALL selected tags
 * - URL updates with selected tags (?t=tag1,tag2)
 * - Loading with URL params pre-selects tags
 */

(function() {
  'use strict';

  const PARAM_NAME = 't';

  class TagFilter {
    constructor() {
      this.selectedTags = new Set();
      this.tagButtons = [];
      this.postItems = [];
    }

    init() {
      this.tagButtons = Array.from(document.querySelectorAll('.tag-cloud-item'));
      this.postItems = Array.from(document.querySelectorAll('.tag-post-item'));

      if (this.tagButtons.length === 0) return;

      // Bind click handlers
      this.tagButtons.forEach(btn => {
        btn.addEventListener('click', (e) => this.handleTagClick(e));
      });

      // Check URL for pre-selected tags
      this.loadFromURL();

      // Apply initial filter
      this.applyFilter();
    }

    handleTagClick(e) {
      const btn = e.target;
      const tag = btn.getAttribute('data-tag');

      if (this.selectedTags.has(tag)) {
        this.selectedTags.delete(tag);
        btn.classList.remove('selected');
      } else {
        this.selectedTags.add(tag);
        btn.classList.add('selected');
      }

      this.applyFilter();
      this.updateURL();
    }

    applyFilter() {
      const selected = Array.from(this.selectedTags);

      this.postItems.forEach(post => {
        if (selected.length === 0) {
          // No tags selected - hide all posts
          post.style.display = 'none';
        } else {
          // Check if post has ALL selected tags (AND logic)
          const postTags = (post.getAttribute('data-tags') || '').split(',');
          const hasAllTags = selected.every(tag => postTags.includes(tag));
          post.style.display = hasAllTags ? 'block' : 'none';
        }
      });
    }

    updateURL() {
      const selected = Array.from(this.selectedTags);
      const url = new URL(window.location);

      if (selected.length > 0) {
        url.searchParams.set(PARAM_NAME, selected.join(','));
      } else {
        url.searchParams.delete(PARAM_NAME);
      }

      history.replaceState(null, '', url);
    }

    loadFromURL() {
      const url = new URL(window.location);
      const param = url.searchParams.get(PARAM_NAME);

      if (param) {
        const tags = param.split(',').map(t => t.trim()).filter(t => t);

        tags.forEach(tag => {
          const btn = this.tagButtons.find(b => b.getAttribute('data-tag') === tag);
          if (btn) {
            this.selectedTags.add(tag);
            btn.classList.add('selected');
          }
        });
      }
    }
  }

  // Initialize when DOM is ready
  function init() {
    const filter = new TagFilter();
    filter.init();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
