document.addEventListener('DOMContentLoaded', () => {
    const triggers = document.querySelectorAll('.car-inquiry__trigger');
    const modal = document.getElementById('car-inquiry-modal');
    const content = document.getElementById('car-inquiry-content');
    if (!triggers.length || !modal || !content) return;

    const closeButton = modal.querySelector('.car-inquiry__close');
    const headers = { 'X-Requested-With': 'XMLHttpRequest' };
    let activeTrigger = null;
    let closeTimer;
    let generation = 0;
    let previousOverflow = '';
    const isCurrent = (id) => id === generation && !modal.hidden;

    function close() {
        clearTimeout(closeTimer);
        generation += 1;
        modal.hidden = true;
        document.body.style.overflow = previousOverflow;
        activeTrigger?.focus();
    }

    triggers.forEach((trigger) => {
        trigger.addEventListener('click', async (event) => {
            event.preventDefault();
            clearTimeout(closeTimer);
            const requestId = ++generation;
            if (modal.hidden) previousOverflow = document.body.style.overflow;
            activeTrigger = trigger;
            modal.hidden = false;
            document.body.style.overflow = 'hidden';
            content.textContent = 'Загружаем форму…';
            closeButton.focus();
            try {
                const response = await fetch(trigger.href, { headers });
                if (!response.ok) throw new Error('Не удалось загрузить форму');
                const html = await response.text();
                if (!isCurrent(requestId)) return;
                content.innerHTML = html;
                content.querySelector('input:not([type="hidden"])')?.focus();
            } catch (error) {
                if (!isCurrent(requestId)) return;
                content.textContent = 'Форма временно недоступна. Попробуйте открыть её отдельно.';
                const link = document.createElement('a');
                link.href = trigger.href;
                link.textContent = 'Открыть форму';
                content.append(link);
            }
        });
    });

    closeButton.addEventListener('click', close);
    document.addEventListener('keydown', (event) => {
        if (modal.hidden) return;
        if (event.key === 'Escape') close();
        if (event.key === 'Tab') {
            const items = Array.from(modal.querySelectorAll('a[href], button, input:not([type="hidden"]), textarea, select, [tabindex="0"]'))
                .filter(el => !el.disabled && el.tabIndex >= 0 && !el.closest('.car-inquiry__honeypot') && el.getClientRects().length);
            const first = items[0];
            const last = items[items.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        }
    });

    content.addEventListener('submit', async (event) => {
        if (!event.target.matches('.car-inquiry__form')) return;
        event.preventDefault();
        const requestId = generation;
        const form = event.target;
        const button = form.querySelector('[type="submit"]');
        if (button.disabled) return;
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
            if (!isCurrent(requestId)) return;
            if (response.status === 400 || response.status === 429) {
                const html = await response.text();
                if (!isCurrent(requestId)) return;
                content.innerHTML = html;
                return;
            }
            if (!response.ok) throw new Error('Не удалось отправить запрос');
            const result = await response.json();
            if (!isCurrent(requestId)) return;
            if (!result.success) throw new Error('Не удалось отправить запрос');
            content.innerHTML = '';
            const title = document.createElement('h2');
            title.id = 'car-inquiry-title';
            title.textContent = 'Спасибо!';
            const message = document.createElement('p');
            message.textContent = result.message || 'Заявка получена. Менеджер свяжется с вами.';
            content.append(title, message);
            closeButton.focus();
            closeTimer = setTimeout(close, 3000);
        } catch (error) {
            if (!isCurrent(requestId)) return;
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
