// apps/reviews/static/reviews/js/review_filters.js
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('reviews-container');
    if (!container) return;

    const filters = document.querySelectorAll('.review-filter');
    let timeout = null;

    function updateReviews() {
        const params = new URLSearchParams();  // ← объявляем params до использования


        filters.forEach(el => {
            if (el.type === 'checkbox') {
                if (el.checked) {
                    params.set(el.dataset.param, el.value);
                } else {
                    params.delete(el.dataset.param);
                }
            } else {
                const val = el.value;
                if (val && val !== '') {
                    params.set(el.dataset.param, val);
                } else {
                    params.delete(el.dataset.param);
                }
            }
        });

        const productId = container.dataset.productId;
        if (!productId) {
            console.error('productId не найден');
            return;
        }

        fetch(`/reviews/filter/${productId}/?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                container.innerHTML = data.html;

                // Переинициализируем голосование (review_vote.js)
                if (typeof initVoteButtons === 'function') {
                    initVoteButtons();
                }

                // Переинициализируем лайтбокс (review_lightbox.js)
                if (typeof initReviewLightbox === 'function') {
                    initReviewLightbox();
                }
            })
            .catch(error => console.error('Ошибка обновления отзывов:', error));
    }

    // Навешиваем обработчики на фильтры
    filters.forEach(el => {
        el.addEventListener('change', function() {
            clearTimeout(timeout);
            timeout = setTimeout(updateReviews, 200);
        });
    });
});