/**
 * Sidenotes
 *
 * kramdown renders footnotes as a `.footnotes` list at the end of the post with
 * `sup[id^="fnref:"] > a` references in the body. This clones each footnote's
 * content into an `<aside class="sidenote">` placed right after its reference.
 *
 * CSS (features.css) does the rest: at >= 64em the asides float into the right
 * margin and the original `.footnotes` list is hidden; below 64em the asides are
 * hidden and the normal footnotes list is shown. So this script only builds the
 * asides; visibility is entirely CSS, which keeps the two breakpoints testable.
 *
 * Idempotent and a no-op on posts with no footnotes.
 */

(function () {
  'use strict';

  function build() {
    const footnotes = document.querySelector('.footnotes');
    if (!footnotes) return;

    const refs = document.querySelectorAll('sup[id^="fnref"]');
    refs.forEach((sup) => {
      const link = sup.querySelector('a[href^="#fn"]');
      if (!link) return;

      const id = link.getAttribute('href').slice(1); // e.g. "fn:1"
      const note = document.getElementById(id);
      if (!note) return;

      const aside = document.createElement('aside');
      aside.className = 'sidenote';
      // Clone so the original footnote (shown on narrow screens) is untouched;
      // drop the return-arrow backlink kramdown appends.
      const clone = note.cloneNode(true);
      clone.querySelectorAll('a.reversefootnote, a[href^="#fnref"]').forEach(a => a.remove());
      aside.innerHTML = clone.innerHTML;

      sup.insertAdjacentElement('afterend', aside);
    });

    document.documentElement.classList.add('has-sidenotes');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
