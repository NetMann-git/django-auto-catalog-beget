(function () {
    'use strict';

    const button = document.querySelector('.scroll-to-top');
    const cookies = document.getElementById('cookie-settings');
    const modal = document.getElementById('appointment-modal');
    if (!button) return;

    function updateVisibility() {
        const hasOverlay = (cookies && !cookies.hidden) ||
            (modal && getComputedStyle(modal).display !== 'none');
        button.hidden = window.scrollY < window.innerHeight || hasOverlay;
    }

    button.addEventListener('click', function () {
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
    window.addEventListener('scroll', updateVisibility, { passive: true });
    window.addEventListener('resize', updateVisibility);
    if (cookies) new MutationObserver(updateVisibility).observe(cookies, { attributes: true, attributeFilter: ['hidden'] });
    if (modal) new MutationObserver(updateVisibility).observe(modal, { attributes: true, attributeFilter: ['style', 'class'] });
    updateVisibility();
})();
