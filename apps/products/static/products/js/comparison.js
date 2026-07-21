// static/products/js/comparison.js

document.addEventListener('DOMContentLoaded', function() {
    const comparisonButtons = document.querySelectorAll('.compare-btn[data-url^="/catalog/comparison/toggle/"]');
    const comparisonCount = document.getElementById('comparison-count');
    const emptyMessage = document.getElementById('empty-message');
    const tableWrapper = document.getElementById('comparison-table-wrapper');
    const backLink = document.querySelector('.comparison-back-link');

    function updateComparisonUI(productId, isAdded, count, message) {
        // Обновляем счётчик в шапке
        if (comparisonCount) {
            comparisonCount.textContent = count;
        }

        // Обновляем кнопку на карточке
        const btn = document.querySelector(`.compare-btn[data-product-id="${productId}"]`);
        if (btn) {
            if (isAdded) {
                btn.classList.add('active');
                btn.textContent = 'Убрать из сравнения';
            } else {
                btn.classList.remove('active');
                btn.textContent = 'Сравнить';
            }
        }

        // Если мы на странице сравнения — обновляем её
        if (window.location.pathname === '/catalog/comparison/') {
            if (count === 0) {
                // Показываем сообщение о пустом списке
                if (emptyMessage) emptyMessage.style.display = 'block';
                if (tableWrapper) tableWrapper.style.display = 'none';
                if (backLink) backLink.style.display = 'none';
            } else {
                if (emptyMessage) emptyMessage.style.display = 'none';
                if (tableWrapper) tableWrapper.style.display = 'block';
                if (backLink) backLink.style.display = 'block';
                // Обновляем таблицу (перезагружаем страницу для простоты)
                location.reload();
            }
        }

        // Показываем сообщение
        if (message) {
            showMessage(message);
        }
    }

    function showMessage(message) {
        const existing = document.querySelector('.comparison-message');
        if (existing) existing.remove();

        const div = document.createElement('div');
        div.className = 'comparison-message';
        div.style.cssText = 'position:fixed; bottom:20px; right:20px; background:#333; color:#fff; padding:12px 24px; border-radius:8px; z-index:999;';
        div.textContent = message;
        document.body.appendChild(div);

        setTimeout(() => div.remove(), 3000);
    }

    comparisonButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url;
            const productId = this.dataset.productId;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showMessage(data.message || 'Ошибка');
                    return;
                }
                updateComparisonUI(productId, data.is_added, data.count, data.message);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});