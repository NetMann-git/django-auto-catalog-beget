document.addEventListener('DOMContentLoaded', () => {
    const trigger = document.getElementById('open-car-inquiry-modal');
    const modal = document.getElementById('car-inquiry-modal');
    const content = document.getElementById('car-inquiry-content');
    if (!trigger || !modal || !content) return;

    const closeButton = modal.querySelector('.car-inquiry__close');
    const headers = { 'X-Requested-With': 'XMLHttpRequest' };

    function close() {
        modal.hidden = true;
        document.body.style.overflow = '';
        trigger.focus();
    }

    trigger.addEventListener('click', async (event) => {
        event.preventDefault();
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
        content.textContent = 'Загружаем форму…';
        closeButton.focus();
        try {
            const response = await fetch(trigger.href, { headers });
            if (!response.ok) throw new Error('Не удалось загрузить форму');
            content.innerHTML = await response.text();
            content.querySelector('input:not([type="hidden"])')?.focus();
        } catch (error) {
            content.textContent = 'Форма временно недоступна. Попробуйте открыть её отдельно.';
            const link = document.createElement('a');
            link.href = trigger.href;
            link.textContent = 'Открыть форму';
            content.append(link);
        }
    });

    closeButton.addEventListener('click', close);
    modal.addEventListener('click', (event) => {
        if (event.target === modal) close();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.hidden) close();
    });

    content.addEventListener('submit', async (event) => {
        if (!event.target.matches('.car-inquiry__form')) return;
        event.preventDefault();
        const form = event.target;
        const button = form.querySelector('[type="submit"]');
        button.disabled = true;
        try {
            const data = new FormData(form);
            const currentToken = typeof getCookie === 'function' ? getCookie('csrftoken') : null;
            if (currentToken) data.set('csrfmiddlewaretoken', currentToken);
            const response = await fetch(form.action, {
                method: 'POST',
                headers,
                body: data,
            });
            if (response.status === 400) {
                content.innerHTML = await response.text();
                return;
            }
            if (!response.ok) throw new Error('Не удалось отправить запрос');
            const result = await response.json();
            if (!result.success) throw new Error('Не удалось отправить запрос');
            content.innerHTML = '';
            const title = document.createElement('h2');
            title.id = 'car-inquiry-title';
            title.textContent = 'Спасибо!';
            const message = document.createElement('p');
            message.textContent = result.message || 'Заявка получена. Менеджер свяжется с вами.';
            content.append(title, message);
            closeButton.focus();
        } catch (error) {
            button.disabled = false;
            let errorText = form.querySelector('.car-inquiry__error--submit');
            if (!errorText) {
                errorText = document.createElement('p');
                errorText.className = 'car-inquiry__error car-inquiry__error--submit';
                form.append(errorText);
            }
            errorText.textContent = 'Не удалось отправить запрос. Попробуйте ещё раз.';
        }
    });
});
