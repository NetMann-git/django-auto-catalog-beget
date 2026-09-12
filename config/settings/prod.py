# config/settings/prod.py

from .base import *

DEBUG = False

# Разрешённые хосты берём из .env, значения разделяются запятыми.
ALLOWED_HOSTS = [
    host.strip()
    for host in config('ALLOWED_HOSTS', default='localhost').split(',')
    if host.strip()
]

# -----------------------------------------------------------------------------
# База данных MySQL
# Все параметры подключения хранятся в .env и не попадают в Git.
# -----------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
