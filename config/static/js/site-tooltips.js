/* Delegated events also cover AJAX cards and dynamically opened forms. */
(() => {
    'use strict';
    if (window.carstarTooltipsReady) return;
    window.carstarTooltipsReady = true;
    const selector = 'a[href], button, input[type="submit"], input[type="button"], input[type="reset"], [role="button"]';
    const titles = new WeakMap();
    const tip = document.createElement('div');
    tip.id = 'carstar-site-tooltip';
    tip.className = 'carstar-tooltip';
    tip.setAttribute('role', 'tooltip');
    tip.hidden = true;
    document.body.append(tip);
    let current = null;
    let timer;
    let leaveTimer;
    const clean = value => (value || '').replace(/\s+/g, ' ').trim();
    function label(el) {
        const explicit = el.getAttribute('data-tooltip');
        if (explicit !== null) return clean(explicit);
        if (el.matches('.compare-btn')) {
            return el.classList.contains('active') ? 'Убрать автомобиль из сравнения' : 'Добавить автомобиль к сравнению';
        }
        if (el.matches('.wishlist-btn')) {
            return el.classList.contains('active') ? 'Убрать автомобиль из избранного' : 'Сохранить автомобиль в избранном';
        }
        const title = el.getAttribute('title');
        if (title) titles.set(el, title);
        const labelled = (el.getAttribute('aria-labelledby') || '').split(/\s+/)
            .map(id => document.getElementById(id)?.textContent || '').join(' ');
        const text = clean(el.getAttribute('aria-label') || labelled || title || titles.get(el)
            || el.innerText || el.value || el.querySelector('img')?.alt);
        const href = el.getAttribute('href') || '';
        if (href.startsWith('tel:')) return 'Позвонить: ' + href.slice(4);
        if (href.startsWith('mailto:')) return 'Написать на ' + href.slice(7).split('?')[0];
        const hints = {
            'Связаться с нами': 'Открыть форму обратной связи',
            'Узнать стоимость под ключ': 'Оставить заявку на расчёт стоимости автомобиля с доставкой',
            'Заказать это авто': 'Оставить заявку на покупку этого автомобиля',
            'В избранное': 'Сохранить автомобиль в избранном',
            'Наверх': 'Вернуться к началу страницы',
            'Управление cookies': 'Выбрать настройки использования cookies',
            'Показать автомобили': 'Применить выбранные фильтры каталога'
        };
        return hints[text] || text || (el.matches('a') ? 'Перейти по ссылке' : 'Выполнить действие');
    }
    function hide() {
        clearTimeout(timer);
        clearTimeout(leaveTimer);
        if (current) {
            const ids = (current.getAttribute('aria-describedby') || '').split(/\s+/)
                .filter(id => id && id !== tip.id);
            if (ids.length) current.setAttribute('aria-describedby', ids.join(' '));
            else current.removeAttribute('aria-describedby');
        }
        current = null;
        tip.hidden = true;
    }
    function show(el) {
        if (!el.isConnected || el.getClientRects().length === 0) return hide();
        const text = label(el);
        if (!text) return hide();
        // Put the tooltip inside native dialogs to keep it above their top layer.
        (el.closest('dialog[open]') || document.body).append(tip);
        tip.textContent = text;
        tip.hidden = false;
        const ids = new Set((el.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean));
        ids.add(tip.id);
        el.setAttribute('aria-describedby', [...ids].join(' '));
        const box = el.getBoundingClientRect();
        const bounds = tip.getBoundingClientRect();
        tip.style.left = Math.max(12, Math.min(innerWidth - bounds.width - 12,
            box.left + (box.width - bounds.width) / 2)) + 'px';
        const top = box.top - bounds.height - 9;
        tip.style.top = Math.max(8, Math.min(innerHeight - bounds.height - 8,
            top >= 8 ? top : box.bottom + 9)) + 'px';
    }
    function schedule(el) {
        if (!el || el.closest('[data-tooltips="off"]')) return;
        if (current === el) { clearTimeout(leaveTimer); return; }
        hide();
        if (!label(el)) return;
        // Avoid a second, native browser tooltip. Keep its text in memory.
        if (el.hasAttribute('title')) {
            titles.set(el, el.getAttribute('title'));
            if (!el.getAttribute('aria-label') && !clean(el.textContent)
                && !el.querySelector('img[alt]')) el.setAttribute('aria-label', el.title);
            el.removeAttribute('title');
        }
        current = el;
        timer = setTimeout(() => show(el), 450);
    }
    document.addEventListener('pointerover', event => {
        if (event.pointerType === 'touch') return;
        if (tip.contains(event.target)) { clearTimeout(leaveTimer); return; }
        schedule(event.target.closest?.(selector));
    });
    document.addEventListener('pointerout', event => {
        if (!current) return;
        if (current.contains(event.relatedTarget) || tip.contains(event.relatedTarget)) return;
        leaveTimer = setTimeout(hide, 180);
    });
    document.addEventListener('focusin', event => {
        if (event.target.matches?.(':focus-visible')) schedule(event.target.closest(selector));
    });
    document.addEventListener('focusout', hide);
    document.addEventListener('pointerdown', hide, true);
    document.addEventListener('click', hide, true);
    document.addEventListener('keydown', event => { if (event.key === 'Escape') hide(); });
    document.addEventListener('scroll', hide, true);
    window.addEventListener('resize', hide);
})();
