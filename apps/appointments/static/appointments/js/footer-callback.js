(function () {
    'use strict';
    const dialog = document.getElementById('footer-callback-dialog');
    if (!dialog || !dialog.showModal || !window.fetch) return;
    const form = dialog.querySelector('form');
    const submit = form.querySelector('[type="submit"]');
    const status = dialog.querySelector('[role="status"]');
    let opener;
    let busy = false;
    let closeTimer;
    let previousOverflow = '';
    document.querySelectorAll('[data-footer-callback]').forEach(function (link) {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            clearTimeout(closeTimer);
            if (form.hidden) {
                form.hidden = false;
                status.textContent = '';
                status.classList.remove('is-success');
            }
            opener = link;
            previousOverflow = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
            dialog.showModal();
        });
    });
    dialog.querySelector('.footer-callback__close').addEventListener('click', () => dialog.close());
    // Native Escape closes the dialog; backdrop clicks do not.
    dialog.addEventListener('close', function () {
        clearTimeout(closeTimer);
        document.body.style.overflow = previousOverflow;
        if (opener) opener.focus();
    });
    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (busy) return;
        busy = true;
        submit.disabled = true;
        status.textContent = 'Отправляем заявку…';
        status.classList.remove('is-success');
        form.querySelectorAll('[data-error]').forEach(el => { el.textContent = ''; });
        form.querySelectorAll('[aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
        try {
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });
            if (response.status === 403) {
                status.textContent = 'Сессия обновилась. Обновите страницу и отправьте форму ещё раз.';
                return;
            }
            const data = await response.json();
            if (!response.ok || !data.success) {
                status.textContent = data.message || 'Не удалось отправить заявку. Попробуйте ещё раз.';
                ['name', 'phone'].forEach(function (name) {
                    if (data.errors && data.errors[name]) {
                        form.querySelector('[data-error="' + name + '"]').textContent = data.errors[name].join(' ');
                        form.elements[name].setAttribute('aria-invalid', 'true');
                    }
                });
                const invalid = form.querySelector('[aria-invalid="true"]');
                if (invalid) invalid.focus();
                return;
            }
            form.reset();
            form.hidden = true;
            status.textContent = 'Спасибо! Заявка получена. Менеджер свяжется с вами.';
            status.classList.add('is-success');
            if (dialog.open) {
                status.focus();
                closeTimer = setTimeout(() => dialog.close(), 3000);
            }
        } catch (error) {
            status.textContent = 'Не удалось подтвердить отправку. Проверьте соединение и попробуйте ещё раз.';
        } finally {
            busy = false;
            submit.disabled = false;
        }
    });
}());
