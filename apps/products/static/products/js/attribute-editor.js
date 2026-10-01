/* Add manager inline rows using the same initialization event as Django admin. */
(() => {
    'use strict';
    function setup() {
        const button = document.getElementById('attribute-editor-add');
        const rows = document.getElementById('attribute-editor-rows');
        const total = document.getElementById('id_attributes-TOTAL_FORMS');
        const template = document.getElementById('attribute-editor-empty');
        if (!button || !rows || !total || !template) return;
        button.addEventListener('click', () => {
            const index = Number(total.value);
            const content = template.innerHTML.replace(/__prefix__/g, String(index));
            rows.insertAdjacentHTML('beforeend', content);
            total.value = String(index + 1);
            const row = rows.lastElementChild;
            row.dispatchEvent(new CustomEvent('formset:added', {bubbles: true}));
            row.querySelector('select').focus();
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup);
    else setup();
})();
