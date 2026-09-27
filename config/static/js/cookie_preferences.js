(function () {
    'use strict';

    const cookieName = 'carstar_cookie_preferences';
    const consentVersion = 1;
    const panel = document.getElementById('cookie-settings');
    if (!panel) return;

    const options = panel.querySelector('[data-cookie-options]');
    const analytics = panel.querySelector('[data-cookie-analytics]');
    const external = panel.querySelector('[data-cookie-external]');
    const saveButton = panel.querySelector('[data-cookie-save]');

    function readPreferences() {
        const match = document.cookie.split('; ').find(function (item) {
            return item.startsWith(cookieName + '=');
        });
        if (!match) return null;
        try {
            const value = JSON.parse(decodeURIComponent(match.slice(cookieName.length + 1)));
            if (value.version !== consentVersion ||
                typeof value.analytics !== 'boolean' ||
                typeof value.external !== 'boolean') return null;
            return value;
        } catch (error) {
            return null;
        }
    }

    let preferences = readPreferences();

    function refreshEmbeds() {
        document.querySelectorAll('iframe[data-consent-src]').forEach(function (iframe) {
            let wrapper = iframe.closest('.cookie-embed');
            if (!wrapper) {
                wrapper = document.createElement('div');
                wrapper.className = 'cookie-embed';
                iframe.parentNode.insertBefore(wrapper, iframe);
                wrapper.appendChild(iframe);
                const placeholder = document.createElement('div');
                placeholder.className = 'cookie-embed__placeholder';
                const text = document.createElement('span');
                text.textContent = 'Для показа карты или видео разрешите загрузку внешнего содержимого.';
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'cookie-embed__button';
                button.textContent = 'Показать содержимое';
                button.addEventListener('click', function () {
                    persist({ analytics: preferences ? preferences.analytics : false, external: true });
                });
                placeholder.append(text, button);
                wrapper.appendChild(placeholder);
            }
            const allowed = Boolean(preferences && preferences.external);
            iframe.hidden = !allowed;
            wrapper.querySelector('.cookie-embed__placeholder').hidden = allowed;
            if (allowed && !iframe.src) iframe.src = iframe.dataset.consentSrc;
            if (!allowed && iframe.hasAttribute('src')) iframe.removeAttribute('src');
        });
    }

    function persist(choice) {
        preferences = { version: consentVersion, analytics: choice.analytics, external: choice.external };
        const secure = location.protocol === 'https:' ? '; Secure' : '';
        document.cookie = cookieName + '=' + encodeURIComponent(JSON.stringify(preferences)) +
            '; Path=/; Max-Age=15552000; SameSite=Lax' + secure;
        panel.hidden = true;
        refreshEmbeds();
        document.dispatchEvent(new CustomEvent('carstar:cookie-preferences', {
            detail: { analytics: preferences.analytics, external: preferences.external }
        }));
    }

    document.querySelectorAll('[data-cookie-settings]').forEach(function (link) {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            analytics.checked = Boolean(preferences && preferences.analytics);
            external.checked = Boolean(preferences && preferences.external);
            options.hidden = false;
            saveButton.hidden = false;
            panel.hidden = false;
            panel.querySelector('h2').focus();
        });
    });
    panel.querySelector('h2').tabIndex = -1;
    panel.querySelector('[data-cookie-necessary]').addEventListener('click', function () {
        persist({ analytics: false, external: false });
    });
    panel.querySelector('[data-cookie-accept]').addEventListener('click', function () {
        persist({ analytics: true, external: true });
    });
    panel.querySelector('[data-cookie-customize]').addEventListener('click', function () {
        options.hidden = false;
        saveButton.hidden = false;
        analytics.focus();
    });
    saveButton.addEventListener('click', function () {
        persist({ analytics: analytics.checked, external: external.checked });
    });

    panel.hidden = Boolean(preferences);
    refreshEmbeds();
})();
