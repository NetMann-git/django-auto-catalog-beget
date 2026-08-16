// apps/products/static/products/js/catalog.js
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('catalog-products-container');
    if (!container) return;

    const sentinel = document.getElementById('catalog-load-sentinel');
    const loader = document.getElementById('catalog-loader');
    const paginationNav = document.querySelector('.pagination');
    const loadMoreBtn = document.getElementById('load-more-btn');

    // Скрываем пагинацию (она остаётся в DOM для SEO)
    if (paginationNav) {
        paginationNav.style.display = 'none';
    }

    let nextPage = parseInt(container.dataset.nextPage, 10) || 2;
    let hasNext = container.dataset.hasNext === 'true';
    let isLoading = false;

    let previousCardCount = 0;
    const params = new URLSearchParams(window.location.search);

    function loadMore() {
        if (!hasNext || isLoading) return;

        isLoading = true;
        if (loader) loader.style.display = 'block';

        params.set('page', nextPage);
        const fetchUrl = `${window.location.pathname}?${params.toString()}`;

        fetch(fetchUrl, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.html) {
                const grid = container.querySelector('.dress-grid');
                if (grid) {
                    // Запоминаем, сколько карточек уже было
                    previousCardCount = grid.children.length;
                    grid.insertAdjacentHTML('beforeend', data.html);
                } else {
                    // Если сетки нет, создаём её и анимируем все карточки
                    const newGrid = document.createElement('div');
                    newGrid.className = 'dress-grid';
                    newGrid.innerHTML = data.html;
                    container.appendChild(newGrid);
                    previousCardCount = 0;
                    grid = newGrid;
                }

                // Анимируем только новые карточки
                const newCards = Array.from(grid.children).slice(previousCardCount);
                newCards.forEach((card, index) => {
                    card.classList.add('catalog-card-animate');
                    card.style.animationDelay = `${index * 0.1}s`;
                });

                hasNext = data.has_next;
                nextPage = data.next_page || nextPage + 1;
                container.dataset.hasNext = hasNext ? 'true' : 'false';
                container.dataset.nextPage = nextPage;

                // Если товары закончились, скрываем кнопку (если она есть)
                if (!hasNext && loadMoreBtn) {
                    loadMoreBtn.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Ошибка подгрузки товаров:', error))
        .finally(() => {
            isLoading = false;
            if (loader) loader.style.display = 'none';
        });
    }

    if ('IntersectionObserver' in window) {
        // Современные браузеры: бесконечная прокрутка, кнопка не нужна
        if (loadMoreBtn) loadMoreBtn.style.display = 'none';

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    loadMore();
                }
            });
        }, { rootMargin: '200px' });

        if (sentinel) observer.observe(sentinel);
    } else {
        // Fallback для старых браузеров: показываем кнопку «Показать ещё»
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'inline-block';
            loadMoreBtn.addEventListener('click', loadMore);
        }
        // Сентинел не нужен
        if (sentinel) sentinel.style.display = 'none';
    }
});