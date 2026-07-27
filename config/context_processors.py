# config/context_processors.py

from django.conf import settings

def theme_context(request):
    """Добавляет в контекст шаблонов информацию о текущей теме."""
    return {
        'current_theme': getattr(settings, 'CURRENT_THEME', 'default'),
        'site_name': getattr(settings, 'SITE_NAME', 'Каталог'),
    }