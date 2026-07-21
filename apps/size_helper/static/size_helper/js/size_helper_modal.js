// apps/size_helper/static/size_helper/js/size_helper_modal.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('size-helper-form-modal');
    if (!form) return;

    const result = document.getElementById('result-modal');
    const sizeDisplay = document.getElementById('size-display-modal');
    const descriptionDisplay = document.getElementById('description-display-modal');
    const errorMessage = document.getElementById('error-message-modal');

    // Функция для получения CSRF-токена из cookie
    function getCookie(name) {
        let value = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    value = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return value;
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        result.style.display = 'none';
        errorMessage.style.display = 'none';

        const formData = new FormData(form);
        const params = new URLSearchParams(formData);

        fetch('/size-helper/recommend/?' + params.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                sizeDisplay.textContent = data.size;
                descriptionDisplay.textContent = data.description || '';
                result.style.display = 'block';
            } else {
                errorMessage.textContent = data.message || 'Не удалось подобрать размер.';
                errorMessage.style.display = 'block';
            }
        })
        .catch(error => {
            errorMessage.textContent = 'Ошибка сервера. Попробуйте позже.';
            errorMessage.style.display = 'block';
            console.error('Ошибка:', error);
        });
    });
});