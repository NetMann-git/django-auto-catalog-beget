// Предпросмотр латинского URL-кода в формах кабинета менеджера.
document.addEventListener('DOMContentLoaded', () => {
    const source = document.querySelector('[data-slug-source]');
    const target = document.querySelector('[data-slug-target]');
    if (!source || !target) return;

    const letters = {
        а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'yo',
        ж: 'zh', з: 'z', и: 'i', й: 'y', к: 'k', л: 'l', м: 'm',
        н: 'n', о: 'o', п: 'p', р: 'r', с: 's', т: 't', у: 'u',
        ф: 'f', х: 'kh', ц: 'ts', ч: 'ch', ш: 'sh', щ: 'shch',
        ъ: '', ы: 'y', ь: '', э: 'e', ю: 'yu', я: 'ya',
        і: 'i', ї: 'yi', є: 'ye', ґ: 'g'
    };
    let automatic = !target.value.trim();

    function latinSlug(value) {
        return Array.from(value.toLowerCase(), (letter) =>
            Object.prototype.hasOwnProperty.call(letters, letter) ? letters[letter] : letter
        ).join('')
            .normalize('NFKD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9_\s-]/g, '')
            .trim()
            .replace(/[\s-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    source.addEventListener('input', () => {
        if (automatic) target.value = latinSlug(source.value);
    });
    target.addEventListener('input', () => {
        automatic = false;
    });
});
