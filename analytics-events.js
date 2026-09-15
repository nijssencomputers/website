/* A contact click is an intention, not evidence of a received enquiry or a sale. */
(function () {
  'use strict';
  document.addEventListener('click', function (event) {
    const link = event.target.closest && event.target.closest('a[href]');
    if (!link || typeof window.gtag !== 'function') return;
    const href = link.getAttribute('href') || '';
    let method;
    if (href.startsWith('tel:')) method = 'phone';
    else if (href.startsWith('mailto:')) method = 'email';
    else if (href.startsWith('https://wa.me/')) method = 'whatsapp';
    else return;
    window.gtag('event', 'contact_click', {
      event_category: 'contact',
      method: method,
      page_path: window.location.pathname,
      transport_type: 'beacon'
    });
  });
})();
