// apps/products/static/products/js/wishlist.js
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.wishlist-btn');

    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.tagName === 'A') return;
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
                if (data.is_favorite) {
                    this.classList.add('active');
                    this.querySelector('.heart').textContent = '❤️';
                    this.querySelector('.label').textContent = 'В избранном';
                } else {
                    this.classList.remove('active');
                    this.querySelector('.heart').textContent = '🤍';
                    this.querySelector('.label').textContent = 'В избранное';

                    if (window.location.pathname.includes('/wishlist/')) {
                        const card = this.closest('.dress-card, .product-card');
                        if (card) {
                            card.remove();
                            const grid = document.getElementById('wishlist-grid');
                            const remainingCards = grid ? grid.querySelectorAll('.dress-card, .product-card').length : 0;
                            if (remainingCards === 0) {
                                const productsBlock = document.getElementById('wishlist-products');
                                const emptyBlock = document.getElementById('empty-wishlist');
                                if (productsBlock) productsBlock.style.display = 'none';
                                if (emptyBlock) emptyBlock.style.display = 'block';
                            }
                        }
                    }
                }
                const counter = document.getElementById('wishlist-count');
                if (counter) counter.textContent = data.count;
            })
            .catch(error => console.error('Ошибка:', error));
        });
    });
});