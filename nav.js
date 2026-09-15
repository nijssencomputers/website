(function () {
  var items = document.querySelectorAll(".nav-item.has-dropdown");
  if (!items.length) return;

  function fineHover() {
    return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  }

  function openMenu(toggle, menu) {
    toggle.setAttribute("aria-expanded", "true");
    menu.removeAttribute("hidden");
  }

  function closeMenu(toggle, menu) {
    toggle.setAttribute("aria-expanded", "false");
    menu.setAttribute("hidden", "");
  }

  function isOpen(toggle) {
    return toggle.getAttribute("aria-expanded") === "true";
  }

  function closeAll() {
    items.forEach(function (item) {
      var toggle = item.querySelector(".nav-dropdown-toggle");
      var menu = item.querySelector(".nav-dropdown");
      if (toggle && menu) closeMenu(toggle, menu);
    });
  }

  items.forEach(function (item) {
    var toggle = item.querySelector(".nav-dropdown-toggle");
    var menu = item.querySelector(".nav-dropdown");
    if (!toggle || !menu) return;

    toggle.addEventListener("click", function (event) {
      event.stopPropagation();
      if (isOpen(toggle)) {
        closeMenu(toggle, menu);
      } else {
        closeAll();
        openMenu(toggle, menu);
      }
    });

    item.addEventListener("mouseenter", function () {
      if (fineHover()) openMenu(toggle, menu);
    });

    item.addEventListener("mouseleave", function () {
      if (fineHover()) closeMenu(toggle, menu);
    });

    item.addEventListener("focusout", function (event) {
      if (!item.contains(event.relatedTarget)) closeMenu(toggle, menu);
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest(".nav-item.has-dropdown")) closeAll();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    var openToggle = document.querySelector('.nav-dropdown-toggle[aria-expanded="true"]');
    closeAll();
    if (openToggle) openToggle.focus();
  });
})();
