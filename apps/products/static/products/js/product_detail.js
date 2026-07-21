// apps/products/static/products/js/product_detail.js

document.addEventListener('DOMContentLoaded', function() {

    // ========================================
    // 1. Открытие модалки с таблицей размеров
    // ========================================
    const sizeTableBtn = document.getElementById('open-size-table-modal');
    if (sizeTableBtn) {
        sizeTableBtn.addEventListener('click', function() {
            const modal = document.getElementById('size-table-modal');
            const body = document.getElementById('size-table-modal-body');

            if (!modal || !body) return;

            modal.style.display = 'flex';
            body.innerHTML = '<div class="modal-loader">Загрузка...</div>';
            document.body.style.overflow = 'hidden';

            fetch('/size-helper/table/')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Ошибка загрузки таблицы');
                    }
                    return response.text();
                })
                .then(html => {
                    body.innerHTML = html;
                })
                .catch(error => {
                    body.innerHTML = '<p style="color:red;">Ошибка загрузки таблицы. Попробуйте позже.</p>';
                    console.error('Ошибка:', error);
                });
        });
    }


    // ========================================
    // 2. Открытие модалки с размерным помощником
    // ========================================
    const sizeHelperBtn = document.getElementById('open-size-helper-modal');
    if (sizeHelperBtn) {
        sizeHelperBtn.addEventListener('click', function() {
            const modal = document.getElementById('size-helper-modal');
            const body = document.getElementById('size-helper-modal-body');

            if (!modal || !body) return;

            modal.style.display = 'flex';
            body.innerHTML = '<div class="modal-loader">Загрузка...</div>';
            document.body.style.overflow = 'hidden';

            fetch('/size-helper/helper/')
                .then(response => response.text())
                .then(html => {
                    body.innerHTML = html;

                    // ========================================
                    // ПРИВЯЗКА ОБРАБОТЧИКА ПОСЛЕ ЗАГРУЗКИ ФОРМЫ
                    // ========================================
                    const form = body.querySelector('#size-helper-form-modal');
                    if (form) {
                        form.addEventListener('submit', function(e) {
                            e.preventDefault(); // ← отключаем перезагрузку

                            const result = document.getElementById('result-modal');
                            const sizeDisplay = document.getElementById('size-display-modal');
                            const descriptionDisplay = document.getElementById('description-display-modal');
                            const errorMessage = document.getElementById('error-message-modal');

                            result.style.display = 'none';
                            errorMessage.style.display = 'none';

                            const formData = new FormData(form);
                            const params = new URLSearchParams(formData);

                            fetch('/size-helper/recommend/?' + params.toString())
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
                    }
                })
                .catch(error => {
                    body.innerHTML = '<p style="color:red;">Ошибка загрузки формы. Попробуйте позже.</p>';
                    console.error('Ошибка:', error);
                });
        });
    }

    // ========================================
    // 3. Закрытие модальных окон (общий обработчик)
    // ========================================
    // Закрытие по крестику
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.dataset.modal;
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'none';
                document.body.style.overflow = '';
            }
        });
    });

    // Закрытие по клику на фон (вне контента)
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = '';
            }
        });
    });

    // Закрытие по клавише Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                if (modal.style.display === 'flex') {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                }
            });
        }
    });

});