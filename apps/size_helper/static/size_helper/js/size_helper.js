
// apps/size_helper/static/size_helper/js/size_helper.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('size-helper-form');
    const result = document.getElementById('result');
    const sizeDisplay = document.getElementById('size-display');
    const descriptionDisplay = document.getElementById('description-display');
    const errorMessage = document.getElementById('error-message');

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // Скрываем предыдущие результаты и ошибки
        result.style.display = 'none';
        errorMessage.style.display = 'none';

        const formData = new FormData(form);
        const params = new URLSearchParams(formData);

        fetch('/size-helper/recommend/?' + params.toString())
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    sizeDisplay.textContent = data.size;
                    if (data.description) {
                        descriptionDisplay.textContent = data.description;
                    } else {
                        descriptionDisplay.textContent = '';
                    }
                    result.style.display = 'block';
                } else {
                    errorMessage.textContent = data.message || 'Не удалось подобрать размер. Попробуйте другие параметры.';
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