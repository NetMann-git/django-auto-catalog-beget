"""Латинские URL-коды для объектов, создаваемых менеджером."""

import unicodedata

from django import forms
from django.utils.text import slugify


_TRANSLITERATION = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
    "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
    "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya", "і": "i", "ї": "yi", "є": "ye",
    "ґ": "g",
})


def latin_slug(value: str) -> str:
    """Превратить русское название в допустимый ASCII slug."""
    transliterated = str(value).lower().translate(_TRANSLITERATION)
    ascii_text = unicodedata.normalize("NFKD", transliterated).encode(
        "ascii", "ignore",
    ).decode("ascii")
    return slugify(ascii_text)


def unique_slug(model, title: str) -> str:
    """Подобрать свободный URL-код с учётом длины поля модели."""
    maximum = model._meta.get_field("slug").max_length
    base = latin_slug(title)[:maximum].strip("-")
    if not base:
        raise forms.ValidationError(
            "Не удалось создать URL из названия. Введите URL латиницей.",
        )
    candidate = base
    counter = 2
    while model.objects.filter(slug=candidate).exists():
        suffix = f"-{counter}"
        candidate = base[:maximum - len(suffix)].rstrip("-") + suffix
        counter += 1
    return candidate


class AutoSlugMixin:
    """Создавать URL-код при сохранении, даже если JavaScript отключён."""

    slug_source: str

    def clean_slug(self) -> str:
        """Сохранить введённый код либо сформировать уникальный автоматически."""
        slug = (self.cleaned_data.get("slug") or "").strip()
        if self.instance.pk:
            return slug
        name = self.cleaned_data.get(self.slug_source, "")
        base = latin_slug(name)
        if not slug or slug == base:
            return unique_slug(self._meta.model, name)
        return slug
