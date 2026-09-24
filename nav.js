/* Progressive enhancement for the mobile menu and the Regio groups. Usable without JS. */
(function () {
  'use strict';
  const menuButton = document.querySelector('.nav-toggle');
  const nav = document.getElementById('site-nav');
  if (!menuButton || !nav) return;
  const mobile = window.matchMedia('(max-width: 760px)');
  const regioItem = nav.querySelector('.nav-regio');
  const regioToggle = nav.querySelector('.nav-regio-toggle');
  const regioFallback = nav.querySelector('.nav-regio-fallback');
  const townToggles = Array.from(nav.querySelectorAll('.nav-town-toggle'));
  let lastFocusedNav = false;
  let lastMobile = mobile.matches;

  if (regioToggle) regioToggle.hidden = false;
  if (regioFallback) regioFallback.hidden = true;
  townToggles.forEach(function (toggle) { toggle.hidden = false; });

  function setMenuOpen(open) {
    menuButton.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
    if (!open) {
      setRegioOpen(false);
      setAllTownsOpen(false);
    }
  }

  function setRegioOpen(open) {
    if (!regioToggle || !regioItem) return;
    regioToggle.setAttribute('aria-expanded', String(open));
    regioItem.classList.toggle('is-open', open);
  }

  function setTownOpen(toggle, open) {
    const group = toggle.closest('.nav-regio-group');
    toggle.setAttribute('aria-expanded', String(open));
    if (group) group.classList.toggle('is-open', open);
  }

  function setAllTownsOpen(open) {
    townToggles.forEach(function (toggle) { setTownOpen(toggle, open); });
  }

  menuButton.addEventListener('click', function () {
    setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
  });

  if (regioToggle) {
    regioToggle.addEventListener('click', function (event) {
      event.stopPropagation();
      setRegioOpen(regioToggle.getAttribute('aria-expanded') !== 'true');
    });
  }

  townToggles.forEach(function (toggle) {
    toggle.addEventListener('click', function (event) {
      event.stopPropagation();
      const willOpen = toggle.getAttribute('aria-expanded') !== 'true';
      townToggles.forEach(function (other) {
        setTownOpen(other, willOpen && other === toggle);
      });
    });
  });

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') return;
    if (regioToggle && regioToggle.getAttribute('aria-expanded') === 'true') {
      setRegioOpen(false);
      regioToggle.focus();
      return;
    }
    if (menuButton.getAttribute('aria-expanded') === 'true') {
      setMenuOpen(false);
      menuButton.focus();
    }
  });

  document.addEventListener('click', function (event) {
    if (regioItem && !regioItem.contains(event.target)) setRegioOpen(false);
  });

  nav.addEventListener('click', function (event) {
    const link = event.target.closest('a');
    if (!link || !mobile.matches) return;
    const destination = new URL(link.href, window.location.href);
    setMenuOpen(false);
    if (destination.origin === location.origin && destination.pathname === location.pathname && destination.hash) {
      const target = document.getElementById(decodeURIComponent(destination.hash.slice(1)));
      if (target) {
        if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
    }
  });

  document.addEventListener('focusin', function (event) {
    if (nav.contains(event.target)) lastFocusedNav = true;
    else if (event.target !== document.body && event.target !== document.documentElement) lastFocusedNav = false;
    if (regioItem && !regioItem.contains(event.target) && !mobile.matches) setRegioOpen(false);
  });

  function breakpointChanged() {
    const nowMobile = mobile.matches;
    if (nowMobile === lastMobile) return;
    lastMobile = nowMobile;
    const willHideFocusedLink = nowMobile && (nav.contains(document.activeElement) || lastFocusedNav);
    const wasButtonFocused = document.activeElement === menuButton;
    setMenuOpen(false);
    if (willHideFocusedLink) menuButton.focus();
    if (!nowMobile && wasButtonFocused) {
      const first = nav.querySelector('a:not([hidden])');
      if (first) first.focus();
    }
  }

  if (mobile.addEventListener) mobile.addEventListener('change', breakpointChanged);
  else mobile.addListener(breakpointChanged);
  window.addEventListener('resize', breakpointChanged);
  document.documentElement.classList.add('nav-ready');
})();
