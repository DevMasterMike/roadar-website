/* Roadar site — scroll-reveal (Apple-style: sections ease in as they enter the viewport).
   Progressive enhancement: with no JS, or with reduced-motion, everything is simply visible. */
(function () {
  var root = document.documentElement;

  // Respect the user's motion preference — no reveal animation, content stays visible.
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Add this synchronously (script is in <head>, before paint) so the hidden start-state applies
  // without a flash of un-revealed content.
  root.classList.add('js');

  function start() {
    var els = document.querySelectorAll('.fade-up');
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    // Light stagger for grouped items so rows cascade instead of popping together.
    els.forEach(function (el, i) {
      var siblings = el.parentElement ? el.parentElement.children.length : 1;
      if (siblings > 1) el.style.transitionDelay = ((i % 6) * 60) + 'ms';
      io.observe(el);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
