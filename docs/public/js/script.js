(function(document) {
  var toggle = document.querySelector('.sidebar-toggle');
  var sidebar = document.querySelector('#sidebar');
  var checkbox = document.querySelector('#sidebar-checkbox');

  document.addEventListener('click', function(e) {
    var target = e.target;

    if(!checkbox.checked ||
       sidebar.contains(target) ||
       (target === checkbox || target === toggle)) return;

    checkbox.checked = false;
  }, false);

  // Escape closes the open menu. Focus goes back to the menu control, since the
  // control it was on (inside the menu) is about to be hidden. Keys another
  // handler already used (the command palette's Escape) are left alone.
  document.addEventListener('keydown', function(e) {
    if (e.key !== 'Escape' || e.defaultPrevented || !checkbox.checked) return;
    checkbox.checked = false;
    checkbox.focus();
  });
})(document);
