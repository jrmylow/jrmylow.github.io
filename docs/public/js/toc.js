/**
 * Table of contents (_includes/post_toc.html)
 *
 * The TOC is one <details>: open in the right margin from 80em, a closed box
 * above the post below that. An inline script sets the initial state before
 * first paint; this keeps it in step when the viewport crosses the breakpoint.
 *
 * It also marks the section being read with aria-current="location": the last
 * heading whose top has scrolled past the masthead, or the last heading once
 * the page is scrolled to the bottom (a short final section can't reach the
 * top). Following a link to a heading inside a closed collapsible box opens the
 * box first, so the jump has somewhere to land.
 *
 * A no-op on pages without a TOC.
 */

(function () {
  'use strict';

  var WIDE = '(min-width: 80em)';

  function init() {
    var toc = document.querySelector('.toc');
    if (!toc) return;
    var details = toc.querySelector('.toc-details');

    var wide = window.matchMedia(WIDE);
    wide.addEventListener('change', function (e) { details.open = e.matches; });

    var entries = [];
    toc.querySelectorAll('a[href^="#"]').forEach(function (link) {
      var heading = document.getElementById(decodeURIComponent(link.hash.slice(1)));
      if (heading) entries.push({ link: link, heading: heading });
    });
    if (!entries.length) return;

    // Open any collapsible box hiding the target before the browser jumps.
    toc.addEventListener('click', function (e) {
      var link = e.target.closest('a[href^="#"]');
      if (!link) return;
      var target = document.getElementById(decodeURIComponent(link.hash.slice(1)));
      for (var box = target && target.closest('details:not([open])'); box;
           box = box.parentElement.closest('details:not([open])')) {
        box.open = true;
      }
    });

    var current = null;

    function setCurrent(entry) {
      if (entry === current) return;
      if (current) current.link.removeAttribute('aria-current');
      current = entry;
      if (!entry) return;
      entry.link.setAttribute('aria-current', 'location');
      // Keep the marked entry visible when the TOC is taller than its box.
      // Only the TOC scrolls: scrollIntoView would move the page as well.
      if (toc.scrollHeight > toc.clientHeight) {
        var top = entry.link.offsetTop - toc.clientHeight / 2;
        toc.scrollTop = Math.max(0, top);
      }
    }

    function update() {
      // Below the masthead: scroll-padding-top is where anchor jumps land.
      var line = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
      line += 8;
      var atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      var found = null;
      for (var i = 0; i < entries.length; i++) {
        var h = entries[i].heading;
        if (!h.getClientRects().length) continue; // inside a closed box
        if (atBottom || h.getBoundingClientRect().top <= line) found = entries[i];
        else break;
      }
      setCurrent(found);
    }

    var queued = false;
    function schedule() {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () { queued = false; update(); });
    }

    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    document.addEventListener('toggle', schedule, true); // a box opening moves what follows
    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
