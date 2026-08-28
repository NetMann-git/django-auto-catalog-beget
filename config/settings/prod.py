# config\settings\prod.py

from .base import *

DEBUG = False
# Разрешённые хосты (берём из переменной окружения, разделённые запятыми)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# Настройки базы данных MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'link23yu_django',
        'USER': 'link23yu_django',
        'PASSWORD': 'J7777777d',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}