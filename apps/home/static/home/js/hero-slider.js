(function () {
    'use strict';

    function initHeroSlider() {
        const root = document.querySelector('[data-home-hero]');
        if (!root) return;

        const slides = Array.from(root.querySelectorAll('[data-hero-slide]'));
        const dots = Array.from(root.querySelectorAll('[data-hero-dot]'));
        if (slides.length <= 1) return;

        let current = 0;
        let timer = null;
        const interval = 5000;

        function show(index) {
            current = (index + slides.length) % slides.length;
            slides.forEach((slide, i) => {
                slide.classList.toggle('is-active', i === current);
                slide.setAttribute('aria-hidden', i === current ? 'false' : 'true');
            });
            dots.forEach((dot, i) => {
                dot.classList.toggle('is-active', i === current);
                dot.setAttribute('aria-selected', i === current ? 'true' : 'false');
            });
        }

        function restart() {
            window.clearInterval(timer);
            timer = window.setInterval(() => show(current + 1), interval);
        }

        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                show(index);
                restart();
            });
        });

        root.addEventListener('mouseenter', () => window.clearInterval(timer));
        root.addEventListener('mouseleave', restart);

        show(0);
        restart();
    }

    document.addEventListener('DOMContentLoaded', initHeroSlider);
}());
