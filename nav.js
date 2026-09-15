/* Only the mobile menu needs enhancement; every page remains usable without JS. */
(function () {
  'use strict';
  const button = document.querySelector('.nav-toggle');
  const nav = document.getElementById('site-nav');
  if (!button || !nav) return;
  const mobile = window.matchMedia('(max-width: 760px)');
  let lastFocusedNav = false;

  function setOpen(open) {
    button.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  }
  button.addEventListener('click', function () {
    setOpen(button.getAttribute('aria-expanded') !== 'true');
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') {
      setOpen(false);
      button.focus();
    }
  });
  nav.addEventListener('click', function (event) {
    const link = event.target.closest('a');
    if (!link || !mobile.matches) return;
    const destination = new URL(link.href, window.location.href);
    setOpen(false);
    if (destination.origin === location.origin && destination.pathname === location.pathname && destination.hash) {
      const target = document.getElementById(decodeURIComponent(destination.hash.slice(1)));
      if (target) {
        if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
    }
  });
  document.addEventListener('focusin', function (event) {
    lastFocusedNav = nav.contains(event.target);
  });
  function breakpointChanged() {
    const nowMobile = mobile.matches;
    if (nowMobile === lastMobile) return;
    lastMobile = nowMobile;
    const willHideFocusedLink = nowMobile && (nav.contains(document.activeElement) || lastFocusedNav);
    const wasButtonFocused = document.activeElement === button;
    setOpen(false);
    if (willHideFocusedLink) button.focus();
    if (!mobile.matches && wasButtonFocused) nav.querySelector('a').focus();
  }
  let lastMobile = mobile.matches;
  if (mobile.addEventListener) mobile.addEventListener('change', breakpointChanged);
  else mobile.addListener(breakpointChanged);
  window.addEventListener('resize', breakpointChanged);
  // Hide the menu only after its controls are installed successfully.
  document.documentElement.classList.add('nav-ready');
})();
