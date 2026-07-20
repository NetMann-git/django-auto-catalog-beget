# config/settings/dev.py

from .base import *

# -----------------------------------------------------------------------------
# Настройки для разработки (локально)
# -----------------------------------------------------------------------------

# Отключаем ManifestStaticFilesStorage для разработки (удобнее работать со статикой)
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Настройки кэширования (файловый кэш)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / "cache",
        "TIMEOUT": 60 * 10,   # 10 минут
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    }
}

# Разрешённые хосты
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

# URL сайта для разработки
SITE_URL = 'http://127.0.0.1:8000'

# Доверенные источники для CSRF
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

# Отправка писем в консоль (для отладки)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Попытка импортировать локальные настройки (для секретных ключей)
try:
    from .local import *
except ImportError:
    pass