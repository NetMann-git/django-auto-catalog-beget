/* Shared dependent selector. Server validation remains authoritative. */
(() => {
    'use strict';
    function initialize() {
        document.querySelectorAll('[data-car-model-select]').forEach(select => {
            const prefix = select.name.slice(0, -'car_model'.length);
            const brand = select.form && select.form.elements.namedItem(prefix + 'brand');
            if (!brand) return;
            const options = Array.from(select.options, item => item.cloneNode(true));
            function update() {
                const previous = select.value;
                select.replaceChildren(...options.filter(option =>
                    !option.value || option.dataset.brand === brand.value
                ).map(option => option.cloneNode(true)));
                select.value = Array.from(select.options).some(option => option.value === previous)
                    ? previous : '';
                select.disabled = !brand.value;
                if (select.options[0]) select.options[0].textContent = brand.value
                    ? 'Модель не указана' : 'Сначала выберите марку';
            }
            brand.addEventListener('change', update);
            update();
        });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
    else initialize();
})();
