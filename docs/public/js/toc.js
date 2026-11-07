/**
 * Table of contents (_includes/post_toc.html)
 *
 * A panel that drops down from the header bar, toggled by .toc-toggle. The
 * state is data-toc="open|closed" on <html>; an inline script sets it before
 * first paint. It is one state at every width: resizing across 80em leaves it
 * as the reader left it, and only the layout changes (CSS). The stored choice
 * decides how a page loads, never what a resize does.
 *
 * - From 80em the panel hangs in the right margin and covers nothing, so it
 *   stays open while the reader scrolls and clicks the page. Opening or closing
 *   it there is remembered (localStorage key `toc`) and applied on the next post.
 * - Below 80em it covers the screen under the header: it starts closed, and a
 *   click outside it, Escape, or following one of its links closes it.
 *
 * Its height runs to the bottom of the window, so this keeps
 * --masthead-height on <html> set to the header's height (CSS has a fallback).
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
  var KEY = 'toc';
  var root = document.documentElement;

  function remember(value) {
    try { localStorage.setItem(KEY, value); } catch (e) { /* private mode: not remembered */ }
  }

  function targetOf(link) {
    return document.getElementById(decodeURIComponent(link.hash.slice(1)));
  }

  function init() {
    var toc = document.getElementById('toc');
    var button = document.querySelector('.toc-toggle');
    if (!toc || !button) return;

    var wide = window.matchMedia(WIDE);
    var masthead = toc.closest('.masthead');

    function measure() {
      if (masthead) root.style.setProperty('--masthead-height', masthead.getBoundingClientRect().height + 'px');
    }
    measure();
    window.addEventListener('resize', measure);

    function isOpen() { return root.getAttribute('data-toc') === 'open'; }

    function setOpen(open) {
      root.setAttribute('data-toc', open ? 'open' : 'closed');
      button.setAttribute('aria-expanded', String(open));
    }

    function choose(open) {
      setOpen(open);
      if (wide.matches) remember(open ? 'open' : 'closed');
    }

    // Slide only on changes after load, never into the initial state.
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () { root.classList.add('toc-ready'); });
    });

    button.addEventListener('click', function () { choose(!isOpen()); });

    // Over the page (narrow), a click outside closes it, as the menu does.
    document.addEventListener('click', function (e) {
      if (wide.matches || !isOpen()) return;
      if (toc.contains(e.target) || button.contains(e.target)) return;
      setOpen(false);
    });

    // Escape closes it when it covers the page, or when focus is inside it.
    // Keys another handler already used (the command palette's) are left alone.
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape' || e.defaultPrevented || !isOpen()) return;
      var focusInside = toc.contains(document.activeElement);
      if (wide.matches && !focusInside) return;
      e.preventDefault();
      choose(false);
      if (focusInside || document.activeElement === document.body) button.focus();
    });

    toc.addEventListener('click', function (e) {
      var link = e.target.closest('a[href^="#"]');
      if (!link) return;
      // Open any collapsible box hiding the target before the browser jumps.
      var target = targetOf(link);
      for (var box = target && target.closest('details:not([open])'); box;
           box = box.parentElement.closest('details:not([open])')) {
        box.open = true;
      }
      if (!wide.matches) setOpen(false);
    });

    var entries = [];
    toc.querySelectorAll('a[href^="#"]').forEach(function (link) {
      var heading = targetOf(link);
      if (heading) entries.push({ link: link, heading: heading });
    });
    if (!entries.length) return;

    var current = null;

    function setCurrent(entry) {
      if (entry === current) return;
      if (current) current.link.removeAttribute('aria-current');
      current = entry;
      if (!entry) return;
      entry.link.setAttribute('aria-current', 'location');
      // Keep the marked entry in view when the list is taller than the panel.
      // Only the panel scrolls: scrollIntoView would move the page as well.
      if (toc.scrollHeight > toc.clientHeight) {
        toc.scrollTop = Math.max(0, entry.link.offsetTop - toc.clientHeight / 2);
      }
    }

    function update() {
      // Below the masthead: scroll-padding-top is where anchor jumps land.
      var line = (parseFloat(getComputedStyle(root).scrollPaddingTop) || 0) + 8;
      var atBottom = window.innerHeight + window.scrollY >= root.scrollHeight - 2;
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
