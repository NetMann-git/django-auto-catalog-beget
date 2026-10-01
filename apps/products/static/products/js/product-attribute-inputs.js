/* Typed attribute controls shared by manager forms and Django admin inlines. */
(() => {
    'use strict';
    const initialized = new WeakSet();
    function initialize(root) {
        root.querySelectorAll('[data-attribute-type]').forEach((type) => {
            if (initialized.has(type) || type.closest('.empty-form')) return;
            const row = type.closest('[data-product-attribute-row], tr');
            if (!row) return;
            const choice = row.querySelector('[data-attribute-choice]');
            const input = row.querySelector('[data-attribute-input]');
            if (!choice || !input) return;
            initialized.add(type);
            const options = Array.from(choice.options, option => option.cloneNode(true));
            function update() {
                const option = type.selectedOptions[0];
                const kind = option ? option.dataset.kind : '';
                const isChoice = kind === 'choice';
                const selected = choice.value;
                choice.replaceChildren(...options.filter(item =>
                    !item.value || item.dataset.owner === type.value
                ).map(item => item.cloneNode(true)));
                choice.value = selected;
                choice.disabled = !isChoice;
                choice.required = isChoice;
                input.disabled = !kind || isChoice;
                input.required = !!kind && !isChoice;
                input.type = kind === 'number' ? 'number' : 'text';
                input.removeAttribute('min');
                input.removeAttribute('step');
                if (kind === 'number') {
                    const mileage = option.dataset.slug === 'mileage';
                    input.step = mileage ? '1' : 'any';
                    if (mileage) input.min = '0';
                }
                const choiceContainer = row.querySelector('[data-attribute-choice-container]');
                const inputContainer = row.querySelector('[data-attribute-input-container]');
                (choiceContainer || choice).hidden = !isChoice;
                (inputContainer || input).hidden = !kind || isChoice;
            }
            type.addEventListener('change', update);
            update();
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => initialize(document));
    } else {
        initialize(document);
    }
    document.addEventListener('formset:added', event => initialize(event.target));
})();
