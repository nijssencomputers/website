(function () {
  document.documentElement.classList.add("js-nav");

  function setupNavigation() {
    var toggle = document.querySelector(".nav-toggle");
    if (!toggle) return;

    var navId = toggle.getAttribute("aria-controls");
    var nav = document.getElementById(navId);
    if (!nav) return;

    function setOpen(open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
    }

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) setOpen(false);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape" || toggle.getAttribute("aria-expanded") !== "true") return;
      setOpen(false);
      toggle.focus();
    });

    window.matchMedia("(min-width: 701px)").addEventListener("change", function (event) {
      if (event.matches) setOpen(false);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupNavigation);
  } else {
    setupNavigation();
  }
})();
