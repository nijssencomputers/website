(function () {
  function getContactMethod(href) {
    if (href.indexOf("tel:") === 0) return "phone";
    if (href.indexOf("mailto:") === 0) return "email";
    if (href.indexOf("https://wa.me/") === 0 || href.indexOf("https://api.whatsapp.com/") === 0) return "whatsapp";
    return "contact";
  }

  function trackContactClick(link) {
    if (typeof window.gtag !== "function") return;

    var href = link.getAttribute("href") || "";
    var method = getContactMethod(href);
    var linkText = (link.textContent || "").trim();

    window.gtag("event", "generate_lead", {
      event_category: "contact",
      method: method,
      link_url: href,
      link_text: linkText,
      transport_type: "beacon"
    });

    window.gtag("event", "contact_click", {
      event_category: "contact",
      method: method,
      link_url: href,
      link_text: linkText,
      transport_type: "beacon"
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var links = document.querySelectorAll('a[href^="tel:"], a[href^="mailto:"], a[href^="https://wa.me/"], a[href^="https://api.whatsapp.com/"]');

    links.forEach(function (link) {
      link.addEventListener("click", function () {
        trackContactClick(link);
      });
    });
  });
})();
