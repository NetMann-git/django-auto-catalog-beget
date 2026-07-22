
---

```markdown
# 🛍️ Django Catalog — каталог товаров на Django

Полнофункциональный каталог товаров с фильтрацией, избранным, сравнением, отзывами и админ-панелью.  
Проект оптимизирован для деплоя на виртуальный хостинг **Beget.com**.

---

## 📦 Основной функционал

- Товары с категориями, брендами, бейджами, галереей изображений и характеристиками
- Фильтрация по категории, бренду, цене, наличию
- Поиск по названию, артикулу и описанию
- Избранное (для авторизованных и гостей)
- Сравнение товаров (до 4 шт.)
- История просмотров (в сессии)
- Отзывы с рейтингом, фотографиями и голосованием
- Размерный помощник
- Запись на примерку
- Личный кабинет, панель продавца и менеджера
- Готовые фикстуры для загрузки демо-данных

---

## 🚀 Быстрый старт (локально)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/NetMann-git/django-catalog-beget.git
cd django-catalog-beget

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать .env (или использовать готовый)
# SECRET_KEY=...
# DEBUG=True
# ALLOWED_HOSTS=127.0.0.1,localhost

# 5. Выполнить миграции
python manage.py migrate

# 6. Загрузить демо-данные (опционально)
python manage.py loaddata categories.json
python manage.py loaddata brands.json
python manage.py loaddata products.json
# ... остальные фикстуры (см. docs/migration_guide.md)

# 7. Собрать статику
python manage.py collectstatic --noinput

# 8. Создать суперпользователя
python manage.py createsuperuser

# 9. Запустить сервер
python manage.py runserver
```

---

## 🌐 Деплой на Beget.com

### 1. Подготовка на сервере

```bash
# Подключиться по SSH
ssh ваше_имя_пользователя@moreug.beget.tech

# Перейти в public_html
cd ~/moreug.beget.tech/public_html
```

### 2. Клонирование и настройка

```bash
# Клонировать проект
git clone https://github.com/NetMann-git/django-catalog-beget.git catalog-clean
cd catalog-clean

# Переключиться на ветку prod
git checkout prod

# Создать и активировать виртуальное окружение (если ещё нет)
python3 -m venv ../venv
source ../venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### 3. Настройка Passenger (WSGI)

На Beget используется **Passenger** для запуска Django-приложений.  
Файл `config/passenger_wsgi.py` уже настроен:

```python
# config/passenger_wsgi.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Файл `.htaccess` в корне `public_html/` должен указывать на него:

```apache
PassengerEnabled On
PassengerAppType wsgi
PassengerStartupFile catalog-clean/config/passenger_wsgi.py
PassengerPython /home/ваше_имя_пользователя/moreug.beget.tech/public_html/venv/bin/python
```

### 4. Применение миграций

```bash
python manage.py migrate --settings=config.settings.prod
python manage.py createsuperuser --settings=config.settings.prod
```

### 5. Загрузка демо-данных (если есть фикстуры)

```bash
# Сначала пользователи, потом всё остальное
python manage.py loaddata users.json --settings=config.settings.prod
python manage.py loaddata profiles.json --settings=config.settings.prod
python manage.py loaddata categories.json --settings=config.settings.prod
python manage.py loaddata brands.json --settings=config.settings.prod
python manage.py loaddata products.json --settings=config.settings.prod
# ... остальные (см. docs/migration_guide.md)
```

### 6. Симлинки для медиа и статики

**Важно:** Apache на Beget отдаёт файлы напрямую из `public_html/`, поэтому нужно создать симлинки на папки `media/` и `static/`.

```bash
cd ~/moreug.beget.tech/public_html

# Удаляем старые папки, если есть
rm -rf media static

# Создаём симлинк для медиа
ln -s catalog-clean/media media

# Создаём симлинк для глобальной статики (из config/static)
ln -s catalog-clean/config/static static

# Права на папки
chmod -R 755 catalog-clean/media/
chmod -R 755 catalog-clean/config/static/
```

После этого:
- `https://moreug.beget.tech/media/...` → `public_html/catalog-clean/media/...`
- `https://moreug.beget.tech/static/...` → `public_html/catalog-clean/config/static/...`

### 7. Сборка статики

```bash
cd ~/moreug.beget.tech/public_html/catalog-clean
python manage.py collectstatic --settings=config.settings.prod --noinput
```

### 8. Перезапуск приложения

```bash
touch ~/moreug.beget.tech/public_html/catalog-clean/config/tmp/restart.txt
```

### 9. Проверка

Открыть в браузере:  
👉 `https://moreug.beget.tech`

---

## 🗂️ Структура проекта

```
catalog-clean/
├── apps/                         # Все приложения
│   ├── appointments/             # Запись на примерку
│   ├── home/                     # Главная страница
│   ├── products/                 # Каталог товаров (ядро)
│   ├── reviews/                  # Отзывы
│   ├── search/                   # Поиск
│   ├── size_helper/              # Размерный помощник
│   ├── users/                    # Пользователи
│   └── wishlist/                 # Избранное
├── config/                       # Настройки Django
│   ├── settings/
│   │   ├── base.py               # Общие настройки
│   │   ├── dev.py                # Для разработки
│   │   └── prod.py               # Для продакшена
│   ├── static/                   # Глобальная статика (CSS, JS)
│   │   ├── css/
│   │   └── js/
│   ├── templates/                # Глобальные шаблоны
│   │   ├── base.html
│   │   ├── 404.html
│   │   └── 500.html
│   ├── passenger_wsgi.py         # WSGI-вход для Passenger (Beget)
│   ├── urls.py
│   └── wsgi.py
├── staticfiles/                  # Собранная статика (collectstatic)
├── media/                        # Загруженные пользователем файлы
├── docs/                         # Документация
├── logs/                         # Логи
├── .env                          # Переменные окружения
├── requirements.txt
└── manage.py
```

---

## 🔗 Симлинки на Beget (важно для продакшена)

В папке `public_html/` должны быть созданы симлинки:

```bash
~/moreug.beget.tech/public_html/
├── media -> catalog-clean/media/          # для медиа-файлов
├── static -> catalog-clean/config/static/ # для глобальной статики
└── catalog-clean/                         # сам проект
```

Это позволяет Apache отдавать файлы напрямую, без участия Django, что ускоряет работу сайта.

---

## ⚙️ Passenger (Beget)

**Файл `.htaccess`** в `~/moreug.beget.tech/public_html/.htaccess`:

```apache
PassengerEnabled On
PassengerAppType wsgi
PassengerStartupFile catalog-clean/config/passenger_wsgi.py
PassengerPython /home/ваше_имя_пользователя/moreug.beget.tech/public_html/venv/bin/python

<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ /catalog-clean/config/passenger_wsgi.py/$1 [QSA,PT,L]
</IfModule>
```

**Файл `config/passenger_wsgi.py`** — точка входа для Passenger:

```python
# config/passenger_wsgi.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

---

## 🧪 Технологии

- Python 3.11+
- Django 5.2.8
- SQLite (локально) / SQLite (на Beget)
- HTML5 / CSS3 / JavaScript (vanilla)

---

## 📄 Лицензия

MIT
```
---
