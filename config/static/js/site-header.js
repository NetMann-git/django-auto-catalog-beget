(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const header = document.querySelector('[data-site-header]');
        const toggle = document.querySelector('[data-mobile-menu-toggle]');
        if (!header || !toggle) return;

        toggle.addEventListener('click', function () {
            const open = header.classList.toggle('mobile-open');
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            toggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
        });

        header.querySelectorAll('.mobile-nav a').forEach(function (link) {
            link.addEventListener('click', function () {
                header.classList.remove('mobile-open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.setAttribute('aria-label', 'Открыть меню');
            });
        });
    });
}());
