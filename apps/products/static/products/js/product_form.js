// static/products/js/product_form.js

document.addEventListener('DOMContentLoaded', function() {
    const titleInput = document.getElementById('id_title');
    const slugInput = document.getElementById('id_slug');
    
    if (titleInput && slugInput) {
        titleInput.addEventListener('input', function() {
            // Если slug пустой или равен старому значению из title
            if (!slugInput.value || slugInput.dataset.auto === 'true') {
                const slug = generateSlug(this.value);
                slugInput.value = slug;
                slugInput.dataset.auto = 'true';
            }
        });
        
        // Если пользователь начал редактировать slug вручную
        slugInput.addEventListener('input', function() {
            this.dataset.auto = 'false';
        });
    }
    
    function generateSlug(text) {
        return text
            .toLowerCase()
            .replace(/[^a-zа-яё0-9\s-]/g, '')  // убираем спецсимволы
            .replace(/\s+/g, '-')               // пробелы на дефисы
            .replace(/-+/g, '-')                // убираем повторяющиеся дефисы
            .replace(/^-+/, '')                 // убираем дефис в начале
            .replace(/-+$/, '');                // убираем дефис в конце
    }
});