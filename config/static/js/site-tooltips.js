/* Delegated events also cover AJAX cards and dynamically opened forms. */
(() => {
    'use strict';
    if (window.carstarTooltipsReady) return;
    window.carstarTooltipsReady = true;
    const selector = 'a[href], button, input[type="submit"], input[type="button"], input[type="reset"] , [role="button"], [role="tab"]';
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
    // Curated explanations: never use a control's caption as its tooltip.
    function label(el) {
        const explicit = el.getAttribute('data-tooltip');
        if (explicit !== null) return clean(explicit);
        const rules = [
            ['.compare-btn', el.classList.contains('active')
                ? 'Исключить этот автомобиль из списка сравнения. Карточка останется в каталоге.'
                : 'Добавить этот автомобиль в список для сопоставления характеристик с другими машинами.'],
            ['.wishlist-btn', el.classList.contains('active')
                ? 'Убрать этот автомобиль из сохранённого списка. Из каталога он не удаляется.'
                : 'Сохранить автомобиль в избранном, чтобы позже быстро вернуться к нему.'],
            ['[data-footer-callback]', 'Открыть форму: оставьте имя и телефон, чтобы менеджер связался с вами.'],
            ['.car-inquiry__trigger', (el.getAttribute('href') || '').includes('type=order')
                ? 'Отправить менеджеру заявку на покупку именно этого автомобиля. Нажатие не оформляет оплату.'
                : 'Запросить у менеджера стоимость этого автомобиля с доставкой и оформлением.'],
            ['.car-inquiry__submit, .footer-callback__submit, .home-callback__submit', 'Передать указанные контакты и заявку менеджеру. Дождитесь сообщения об успешной отправке.'],
            ['.car-inquiry__close, .footer-callback__close, .modal-close', 'Закрыть окно без отправки заявки.'],
            ['.scroll-to-top', 'Прокрутить страницу к началу, не перезагружая её.'],
            ['[data-mobile-menu-toggle], #offcanvas-toggler', 'Показать или скрыть разделы сайта в мобильном меню.'],
            ['[data-cookie-settings], [data-cookie-customize]', 'Открыть настройки и выбрать разрешённые категории cookies.'],
            ['[data-cookie-necessary]', 'Оставить только cookies, необходимые для работы сайта.'],
            ['[data-cookie-accept]', 'Разрешить все категории cookies, перечисленные в настройках.'],
            ['[data-cookie-save]', 'Применить выбранные категории cookies.'],
            ['#prev-image-btn, .prev-image', 'Показать предыдущую фотографию этого автомобиля.'],
            ['#next-image-btn, .next-image', 'Показать следующую фотографию этого автомобиля.'],
            ['.home-inspection__panel-heading', 'Развернуть или свернуть описание этого этапа проверки автомобиля.'],
            ['.home-korea-facts__tab', 'Показать пояснение выбранного преимущества автомобилей из Кореи.'],
            ['[data-delete-photo]', 'Удалить выбранную фотографию из галереи автомобиля.'],
            ['[data-start]', 'Загрузить выбранные фотографии в галерею; одинаковые файлы будут пропущены.'],
            ['[data-retry]', 'Повторить загрузку файлов, которые не удалось добавить.'],
            ['#attribute-editor-add', 'Добавить строку характеристики. Выберите её тип и укажите значение перед сохранением.'],
            ['.util-sbor__submit', 'Рассчитать утилизационный сбор по указанным параметрам и дате расчёта.']
        ];
        for (const [selector, explanation] of rules) if (el.matches(selector)) return explanation;
        const text = clean(el.innerText || el.value || el.getAttribute('aria-label'))
            .replace(/^[^А-Яа-яA-Za-z0-9]+/u, '').trim();
        const actions = {
            'Сохранить': 'Записать введённые значения. Если форма содержит ошибки, исправьте отмеченные поля.',
            'Сохранить изменения': 'Записать изменения этой формы. Проверьте заполненные поля перед отправкой.',
            'Сохранить товар': 'Записать данные автомобиля и выбранный статус публикации.',
            'Сохранить бренд': 'Записать название и настройки марки в общий справочник каталога.',
            'Сохранить выбранные изменения': 'Применить отмеченные данные импорта к выбранной карточке автомобиля.',
            'Отмена': 'Вернуться без отправки изменений текущей формы.',
            'Выйти': 'Завершить текущий сеанс. Для доступа к кабинету потребуется войти снова.',
            'Войти': 'Проверить введённые данные и открыть доступ к вашему кабинету.',
            'Зарегистрироваться': 'Создать учётную запись с указанными данными.',
            'Изменить пароль': 'Сохранить новый пароль для последующих входов в аккаунт.',
            'Показать автомобили': 'Обновить список автомобилей с учётом выбранных фильтров.',
            'Сбросить': 'Убрать выбранные условия фильтрации и снова показать список.',
            'Рассчитать': 'Выполнить расчёт по заполненным параметрам. Проверьте дату и исходные значения.',
            'Рассчитать стоимость': 'Рассчитать платежи по указанным данным автомобиля; результат носит информационный характер.',
            'Отправить отзыв': 'Передать заполненный отзыв на обработку сайтом.',
            'Подтвердить удаление': 'Подтвердить удаление записи, указанной на этой странице.',
            'Жду звонка': 'Отправить имя и телефон менеджеру для обратного звонка.',
            'Отправить заявку': 'Передать заполненную заявку менеджеру и дождаться подтверждения отправки.',
            'Отправить запрос': 'Передать заполненный запрос менеджеру и дождаться подтверждения отправки.'
        };
        if (!el.matches('a[href]')) return actions[text] || '';
        const raw = el.getAttribute('href') || '';
        if (raw.startsWith('tel:')) return 'Открыть приложение для звонка по номеру ' + raw.slice(4);
        if (raw.startsWith('mailto:')) return 'Создать письмо в почтовом приложении на адрес ' + raw.slice(7).split('?')[0];
        let url;
        try { url = new URL(raw, location.href); } catch (_) { return ''; }
        if (url.origin !== location.origin) {
            if (/^(t\.me|telegram\.me)$/.test(url.hostname)) return 'Открыть указанный Telegram-контакт или канал в новой вкладке или приложении.';
            if (/(^|\.)vk\.com$/.test(url.hostname)) return 'Открыть страницу ВКонтакте для знакомства с публикациями и связи.';
            if (url.hostname === 'max.ru') return 'Открыть указанный контакт в мессенджере MAX.';
            if (url.protocol === 'https:' || url.protocol === 'http:') return 'Открыть внешний ресурс: ' + url.hostname + (el.target === '_blank' ? '. Ссылка откроется в новой вкладке.' : '.');
            return '';
        }
        const anchors = {
            '#contacts': 'Перейти к телефонам, адресу и способам связи с нашей командой.',
            '#callback': 'Перейти к форме, где можно оставить телефон для обратного звонка.',
            '#o-nas': 'Узнать, как наша команда помогает подобрать и доставить автомобиль.',
            '#kak-kupit': 'Посмотреть этапы покупки автомобиля: от подбора до получения.',
            '#osmotry': 'Узнать, что проверяется при осмотре автомобиля перед покупкой.',
            '#sroki': 'Посмотреть информацию об этапах и сроках доставки.',
            '#klienty': 'Посмотреть примеры автомобилей, подобранных для наших клиентов.',
            '#product-gallery': 'Перейти к загрузке фотографий, выбору обложки и порядку изображений.'
        };
        if (anchors[url.hash]) return anchors[url.hash];
        if (url.searchParams.has('page')) return 'Открыть страницу ' + url.searchParams.get('page') + ' текущего списка.';
        const path = url.pathname.replace(/\/?$/, '/');
        const routes = {
            '/': 'Перейти на главную: услуги подбора, этапы покупки, автомобили и контакты.',
            '/catalog/': url.searchParams.has('brand')
                ? 'Показать в каталоге только автомобили этой марки. Другие фильтры можно уточнить на странице каталога.'
                : 'Открыть все предложения и подобрать автомобиль по марке, модели, цене и характеристикам.',
            '/catalog/comparison/': 'Сопоставить характеристики автомобилей, которые вы добавили к сравнению.',
            '/wishlist/': 'Вернуться к автомобилям, которые вы сохранили для дальнейшего выбора.',
            '/catalog/recently-viewed/': 'Снова открыть автомобили, карточки которых вы недавно просматривали.',
            '/calculator/util-sbor/': 'Оценить утилизационный сбор с учётом типа автомобиля, возраста и параметров двигателя.',
            '/calculator/rastamozhka/': 'Оценить пошлину, таможенный сбор и утильсбор по данным автомобиля.',
            '/account/login/': 'Войти в свою учётную запись для работы с личным кабинетом.',
            '/account/dashboard/': 'Открыть доступные вашей учётной записи разделы и настройки.',
            '/account/manager/': 'Перейти к управлению автомобилями, справочниками и обращениями клиентов.',
            '/account/register/': 'Открыть форму создания учётной записи.',
            '/account/password-reset/': 'Запросить письмо со ссылкой для восстановления доступа.',
            '/catalog/manage/': 'Открыть список автомобилей для добавления и редактирования карточек.',
            '/catalog/create/': 'Создать новую карточку автомобиля и заполнить её данные.',
            '/catalog/manage/import-encar/': 'Загрузить JSON или ZIP из EncarPhotosApp, проверить данные и выбрать изменения перед сохранением.',
            '/catalog/manage/brands/': 'Добавлять и редактировать марки автомобилей и их логотипы.',
            '/catalog/manage/car-models/': 'Настроить модели автомобилей и их связь с марками.',
            '/catalog/manage/categories/': 'Настроить категории, по которым распределены автомобили каталога.',
            '/catalog/manage/attribute-types/': 'Настроить характеристики, типы полей и доступные значения справочников.',
            '/appointments/callbacks/': 'Просмотреть обращения клиентов и обновить статус их обработки.',
            '/recommendations/manage/': 'Выбрать автомобили для рекомендательных блоков и настроить сроки показа.',
            '/account/profile/edit/': 'Изменить личные данные вашей учётной записи.',
            '/account/reviews/': 'Просмотреть отзывы, оставленные с вашей учётной записи.',
            '/terms/': 'Ознакомиться с условиями публичной оферты перед обращением за услугой.',
            '/privacy/': 'Узнать, какие персональные данные обрабатываются и для каких целей.',
            '/consent/': 'Прочитать условия согласия на обработку персональных данных.'
        };
        if (routes[path]) return routes[path];
        if (/^\/catalog\/brand\//.test(path)) return 'Посмотреть информацию о марке и автомобили этого бренда.';
        if (/^\/catalog\/attributes\/\d+\/$/.test(path)) return 'Изменить значения и порядок характеристик этого автомобиля.';
        if (/^\/catalog\/edit\/\d+\/$/.test(path)) return 'Открыть редактор данных, комплектации и фотографий этого автомобиля.';
        if (/^\/catalog\/[^/]+\/$/.test(path)) return 'Открыть фотографии, общие данные и комплектацию этого автомобиля; при необходимости отправить заявку менеджеру.';
        if (/\/edit\/$/.test(path)) return 'Открыть форму изменения выбранной записи справочника.';
        if (/\/create\/$/.test(path)) return 'Открыть форму добавления новой записи в этот справочник.';
        if (/\/delete\//.test(path) || /\/delete\/$/.test(path)) return 'Перейти к удалению выбранной записи. Проверьте её название перед подтверждением.';
        if (actions[text] && text !== 'Войти') return actions[text];
        return '';
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
