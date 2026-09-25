/**
 * Webmentions loader
 *
 * Fetches webmentions for the current page from webmention.io and renders them.
 * No plugin, no build step: the display is entirely client-side.
 *
 * Target resolution: the canonical <link> if present, else window.location.href.
 * With `url:` unset in _config.yml the canonical resolves to the dev origin,
 * which is fine locally and under test; set `url:` for production.
 *
 * Contract (kept stable for tests):
 *   #webmentions              section, `hidden` until at least one mention loads
 *   .webmentions-list         <ul> of <li class="webmention">
 */

(function () {
  'use strict';

  const API = 'https://webmention.io/api/mentions.jf2';

  function target() {
    const canonical = document.querySelector('link[rel="canonical"]');
    return (canonical && canonical.href) || window.location.href;
  }

  function render(children) {
    const section = document.getElementById('webmentions');
    const list = section && section.querySelector('.webmentions-list');
    if (!section || !list) return;

    if (!children || children.length === 0) {
      section.hidden = true;
      return;
    }

    list.innerHTML = '';
    children.forEach((wm) => {
      const li = document.createElement('li');
      li.className = 'webmention';

      const author = wm.author || {};
      if (author.photo) {
        const img = document.createElement('img');
        img.className = 'webmention-avatar';
        img.src = author.photo;
        img.alt = '';
        img.loading = 'lazy';
        li.appendChild(img);
      }

      const body = document.createElement('div');
      body.className = 'webmention-body';

      const name = document.createElement('a');
      name.className = 'webmention-author';
      name.href = author.url || wm.url || '#';
      name.textContent = author.name || 'Someone';
      body.appendChild(name);

      const content = (wm.content && (wm.content.text || wm.content.value)) || '';
      if (content) {
        const p = document.createElement('p');
        p.className = 'webmention-content';
        p.textContent = content;
        body.appendChild(p);
      }

      li.appendChild(body);
      list.appendChild(li);
    });

    section.hidden = false;
  }

  async function load() {
    const url = API + '?target=' + encodeURIComponent(target()) + '&per-page=50';
    try {
      const res = await fetch(url);
      if (!res.ok) return;
      const data = await res.json();
      render(data.children || []);
    } catch (err) {
      console.error('Webmentions: load failed', err);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
