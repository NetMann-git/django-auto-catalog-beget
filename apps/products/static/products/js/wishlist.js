// apps/products/static/products/js/wishlist.js
document.addEventListener('DOMContentLoaded', function() {
    const wishlistGrid = document.getElementById('wishlist-grid');
    const recommendedGrid = document.querySelector('.recommended-section .products-grid');
    const wishlistProducts = document.getElementById('wishlist-products');
    const emptyWishlist = document.getElementById('empty-wishlist');

    const buttons = document.querySelectorAll('.wishlist-btn');

    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.tagName === 'A') return;
            e.preventDefault();

            const url = this.dataset.url;
            const card = this.closest('.dress-card, .product-card');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                // Обновляем состояние кнопки
                if (data.is_favorite) {
                    this.classList.add('active');
                    this.querySelector('.heart').textContent = '❤️';
                    this.querySelector('.label').textContent = 'В избранном';
                } else {
                    this.classList.remove('active');
                    this.querySelector('.heart').textContent = '🤍';
                    this.querySelector('.label').textContent = 'В избранное';
                }

                // Логика перемещения карточки только на странице избранного
                if (window.location.pathname.includes('/wishlist/')) {
                    if (!card) return;

                    if (data.is_favorite) {
                        // Добавление в избранное: перемещаем карточку из рекомендаций в список
                        if (recommendedGrid && recommendedGrid.contains(card)) {
                            if (wishlistGrid) {
                                wishlistGrid.prepend(card);
                            }
                            // Показываем блок с товарами, если он был скрыт
                            if (wishlistProducts) wishlistProducts.style.display = 'block';
                            if (emptyWishlist) emptyWishlist.style.display = 'none';
                        }
                    } else {
                        // Удаление из избранного: перемещаем карточку из списка в рекомендации
                        if (wishlistGrid && wishlistGrid.contains(card)) {
                            if (recommendedGrid) {
                                recommendedGrid.appendChild(card);
                            } else {
                                card.remove();
                            }
                            // Проверяем, остались ли карточки в списке
                            const remainingCards = wishlistGrid.querySelectorAll('.product-card, .dress-card').length;
                            if (remainingCards === 0 && wishlistProducts && emptyWishlist) {
                                wishlistProducts.style.display = 'none';
                                emptyWishlist.style.display = 'block';
                            }
                        }
                    }
                }

                // Обновляем счётчик
                const counter = document.getElementById('wishlist-count');
                if (counter) counter.textContent = data.count;
            })
            .catch(error => console.error('Ошибка:', error));
        });
    });

    // Обработчик кнопки «✕ Очистить избранное»
    const clearBtn = document.getElementById('clear-wishlist');
    if (clearBtn) {
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Скрываем блок с товарами
                    const productsBlock = document.getElementById('wishlist-products');
                    const emptyBlock = document.getElementById('empty-wishlist');
                    if (productsBlock) productsBlock.style.display = 'none';
                    if (emptyBlock) emptyBlock.style.display = 'block';

                    // Очищаем контейнер с карточками (на случай, если они ещё в DOM)
                    const grid = document.getElementById('wishlist-grid');
                    if (grid) grid.innerHTML = '';

                    // Обновляем счётчик в шапке
                    const counter = document.getElementById('wishlist-count');
                    if (counter) counter.textContent = '0';
                }
            })
            .catch(error => console.error('Ошибка очистки избранного:', error));
        });
    }
});