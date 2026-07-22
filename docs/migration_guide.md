---

# 📋 Инструкция по переносу данных между проектами Django

## Содержание

1. [Подготовка](#1-подготовка)
2. [Экспорт данных (скрипт export_all.py)](#2-экспорт-данных-скрипт-export_allpy)
3. [Экспорт данных (вручную, по одному)](#3-экспорт-данных-вручную-по-одному)
4. [Копирование файлов в новый проект](#4-копирование-файлов-в-новый-проект)
5. [Импорт данных (скрипт import_all.py)](#5-импорт-данных-скрипт-import_allpy)
6. [Импорт данных (вручную, по одному)](#6-импорт-данных-вручную-по-одному)
7. [Копирование медиа-файлов](#7-копирование-медиа-файлов)
8. [Проверка после переноса](#8-проверка-после-переноса)
9. [Возможные проблемы и решения](#9-возможные-проблемы-и-решения)
10. [Специальный скрипт для загрузки пользователей](#10-специальный-скрипт-для-загрузки-пользователей)
11. [Деплой на хостинг Beget](#11-деплой-на-хостинг-beget)

---

## 1. Подготовка

### 1.1 Убедитесь, что оба проекта имеют одинаковые модели
Перед переносом убедитесь, что модели в целевом проекте совпадают с исходным (одинаковые поля, связи, имена).

### 1.2 Убедитесь, что виртуальное окружение активировано

**В старом проекте:**
```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
```

**В новом проекте:**
```bash
cd F:\Projects\catalog-clean
venv\Scripts\activate
```

### 1.3 Создайте папку для фикстур (опционально)
```bash
mkdir F:\Projects\fixtures
```

---

## 2. Экспорт данных (скрипт export_all.py)

### Создайте файл `export_all.py` в корне старого проекта:

```python
# export_all.py
import os
import django

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

import json
from django.core.serializers import serialize
from django.contrib.auth.models import User

# Импорты моделей с указанием папки apps/
from apps.products.models import Category, Brand, Badge, AttributeType, AttributeValue, Product, ProductGalleryImage, ProductAttribute
from apps.reviews.models import Review, ReviewImage, ReviewVote, ReviewReply
from apps.appointments.models import Appointment, WorkingHours
from apps.users.models import Profile

models_to_export = [
    ('categories', Category),
    ('brands', Brand),
    ('badges', Badge),
    ('attribute_types', AttributeType),
    ('attribute_values', AttributeValue),
    ('products', Product),
    ('gallery', ProductGalleryImage),
    ('product_attributes', ProductAttribute),
    ('reviews', Review),
    ('review_images', ReviewImage),
    ('review_votes', ReviewVote),
    ('review_replies', ReviewReply),
    ('appointments', Appointment),
    ('working_hours', WorkingHours),
    ('users', User),
    ('profiles', Profile),
]

for name, model in models_to_export:
    data = serialize('json', model.objects.all(), indent=2, use_natural_foreign_keys=True)
    with open(f'{name}.json', 'w', encoding='utf-8') as f:
        f.write(data)
    print(f'Exported {name}: {model.objects.count()} records')
```

### Запуск экспорта:
```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python export_all.py
```

---

## 3. Экспорт данных (вручную, по одному)

Если вы хотите экспортировать каждую модель отдельно, используйте Django shell.

### Запустите Django shell:
```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

### 3.1 Экспорт категорий
```python
import json
from django.core.serializers import serialize
from apps.products.models import Category

data = serialize('json', Category.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('categories.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Category.objects.count()} категорий")
```

### 3.2 Экспорт брендов
```python
from apps.products.models import Brand

data = serialize('json', Brand.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('brands.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Brand.objects.count()} брендов")
```

### 3.3 Экспорт бейджей
```python
from apps.products.models import Badge

data = serialize('json', Badge.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('badges.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Badge.objects.count()} бейджей")
```

### 3.4 Экспорт типов характеристик
```python
from apps.products.models import AttributeType

data = serialize('json', AttributeType.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('attribute_types.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {AttributeType.objects.count()} типов характеристик")
```

### 3.5 Экспорт значений характеристик
```python
from apps.products.models import AttributeValue

data = serialize('json', AttributeValue.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('attribute_values.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {AttributeValue.objects.count()} значений характеристик")
```

### 3.6 Экспорт товаров
```python
from apps.products.models import Product

data = serialize('json', Product.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('products.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Product.objects.count()} товаров")
```

### 3.7 Экспорт галереи товаров
```python
from apps.products.models import ProductGalleryImage

data = serialize('json', ProductGalleryImage.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('gallery.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {ProductGalleryImage.objects.count()} изображений галереи")
```

### 3.8 Экспорт характеристик товаров
```python
from apps.products.models import ProductAttribute

data = serialize('json', ProductAttribute.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('product_attributes.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {ProductAttribute.objects.count()} характеристик товаров")
```

### 3.9 Экспорт отзывов
```python
from apps.reviews.models import Review, ReviewReply, ReviewVote

# Отзывы
data = serialize('json', Review.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('reviews.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Ответы на отзывы
data = serialize('json', ReviewReply.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('review_replies.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Голоса
data = serialize('json', ReviewVote.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('review_votes.json', 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Отзывов: {Review.objects.count()}, Ответов: {ReviewReply.objects.count()}, Голосов: {ReviewVote.objects.count()}")
```

### 3.10 Экспорт фото отзывов
```python
from apps.reviews.models import ReviewImage

data = serialize('json', ReviewImage.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('review_images.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {ReviewImage.objects.count()} фото отзывов")
```

### 3.11 Экспорт записей на примерку
```python
from apps.appointments.models import Appointment, WorkingHours

# Записи
data = serialize('json', Appointment.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('appointments.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Рабочее время
data = serialize('json', WorkingHours.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('working_hours.json', 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Записей: {Appointment.objects.count()}, Рабочих часов: {WorkingHours.objects.count()}")
```

### 3.12 Экспорт пользователей
```python
from django.contrib.auth.models import User
from apps.users.models import Profile

# Пользователи
data = serialize('json', User.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('users.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Профили
data = serialize('json', Profile.objects.all(), indent=2, use_natural_foreign_keys=True)
with open('profiles.json', 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Пользователей: {User.objects.count()}, Профилей: {Profile.objects.count()}")
```

### Выход из shell
```python
exit()
```

---

## 4. Копирование файлов в новый проект

```bash
copy *.json F:\Projects\catalog-clean\
```

---

## 5. Импорт данных (скрипт import_all.py)

### Создайте файл `import_all.py` в корне нового проекта:

```python
# import_all.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

import json
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Отключаем сигналы для пользователей (чтобы избежать ошибок)
from apps.users.signals import save_user_profile
post_save.disconnect(save_user_profile, sender=User)

# Загрузка моделей с правильным порядком
def load_fixture(filename):
    if not os.path.exists(filename):
        print(f'Файл {filename} не найден, пропускаем')
        return
    print(f'Загрузка {filename}...')
    os.system(f'python manage.py loaddata {filename}')

# Порядок загрузки важен!
fixtures_order = [
    'categories.json',      # 1. Независимые модели
    'brands.json',
    'badges.json',
    'attribute_types.json',
    'attribute_values.json', # 2. Зависят от attribute_types
    'products.json',         # 3. Зависят от categories, brands, badges
    'gallery.json',          # 4. Зависят от products
    'product_attributes.json',
    'reviews.json',          # 5. Зависят от products, users
    'review_images.json',
    'review_votes.json',
    'review_replies.json',
    'appointments.json',     # 6. Зависят от users
    'working_hours.json',
    'users.json',            # 7. Пользователи и профили (последними)
    'profiles.json',
]

for fixture in fixtures_order:
    load_fixture(fixture)

print('\n✅ Импорт завершён!')
```

### Запуск импорта:
```bash
cd F:\Projects\catalog-clean
venv\Scripts\activate
python import_all.py
```

---

## 6. Импорт данных (вручную, по одному)

Если вы хотите импортировать каждую модель отдельно, используйте команду `loaddata`.

### Важно: соблюдайте порядок загрузки!

```bash
cd F:\Projects\catalog-clean
venv\Scripts\activate

# 1. Сначала независимые модели
python manage.py loaddata categories.json
python manage.py loaddata brands.json
python manage.py loaddata badges.json
python manage.py loaddata attribute_types.json

# 2. Потом те, что зависят от них
python manage.py loaddata attribute_values.json

# 3. Товары и связанные с ними
python manage.py loaddata products.json
python manage.py loaddata gallery.json
python manage.py loaddata product_attributes.json

# 4. Отзывы
python manage.py loaddata reviews.json
python manage.py loaddata review_images.json
python manage.py loaddata review_votes.json
python manage.py loaddata review_replies.json

# 5. Записи на примерку
python manage.py loaddata appointments.json
python manage.py loaddata working_hours.json

# 6. Пользователи и профили (последними)
python manage.py loaddata users.json
python manage.py loaddata profiles.json
```

### Если какой-то файл пустой
```bash
# Проверьте содержимое
cat reviews.json

# Если там [], пропустите загрузку этого файла
```

---

## 7. Копирование медиа-файлов

```bash
# Товары
xcopy F:\Projects\wedding-catalog\media\products\* F:\Projects\catalog-clean\media\products\ /E /I /Y

# Бренды
xcopy F:\Projects\wedding-catalog\media\brands\* F:\Projects\catalog-clean\media\brands\ /E /I /Y

# Отзывы
xcopy F:\Projects\wedding-catalog\media\reviews\* F:\Projects\catalog-clean\media\reviews\ /E /I /Y

# Если есть другие папки:
xcopy F:\Projects\wedding-catalog\media\* F:\Projects\catalog-clean\media\ /E /I /Y
```

---

## 8. Проверка после переноса

### 8.1 Примените миграции (если нужно)
```bash
python manage.py migrate
```

### 8.2 Создайте суперпользователя
```bash
python manage.py createsuperuser
```

### 8.3 Запустите сервер и проверьте
```bash
python manage.py runserver
```

Откройте `http://127.0.0.1:8000` и проверьте:
- [ ] Каталог товаров
- [ ] Страницы товаров
- [ ] Галерея
- [ ] Характеристики
- [ ] Отзывы с фото
- [ ] Записи на примерку
- [ ] Рабочее время
- [ ] Пользователи и роли

---

## 9. Возможные проблемы и решения

### 9.1 Ошибка: `ModuleNotFoundError: No module named 'products'`
**Причина:** Django не находит приложение, потому что оно в папке `apps/`.
**Решение:** В скриптах используйте импорты `from apps.products.models import ...`

### 9.2 Ошибка: `User has no profile`
**Причина:** Сигнал пытается сохранить профиль, которого ещё нет.
**Решение:** Отключите сигналы перед загрузкой пользователей:
```python
from apps.users.signals import save_user_profile
post_save.disconnect(save_user_profile, sender=User)
```

### 9.3 Ошибка: `Direct assignment to the forward side of a many-to-many set is prohibited`
**Причина:** В фикстуре `users.json` есть ManyToMany поля (`groups`, `user_permissions`).
**Решение:** Используйте скрипт `load_users_without_signals.py` (см. раздел 10).

### 9.4 Ошибка: `File format may be invalid`
**Причина:** Файл пустой или содержит `[]`.
**Решение:** Это нормально, если в старом проекте не было данных. Просто пропустите этот файл.

### 9.5 Ошибка: `No fixture data found`
**Причина:** В файле нет данных.
**Решение:** Проверьте содержимое файла — если там `[]`, пропустите загрузку.

### 9.6 Фото не отображаются
**Причина:** Папка `media/` не скопирована или пути в БД не совпадают.
**Решение:** Проверьте, что папка `media/` скопирована правильно и пути в БД совпадают с фактическими путями файлов.

---

## 10. Специальный скрипт для загрузки пользователей (если стандартный способ не работает)

Создайте файл `load_users_without_signals.py` в корне нового проекта:

```python
# load_users_without_signals.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

import json
from django.contrib.auth.models import User

with open('users.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Отключаем сигналы на время загрузки
from django.db.models.signals import post_save
from apps.users.signals import save_user_profile

post_save.disconnect(save_user_profile, sender=User)

# Загружаем пользователей
for obj in data:
    fields = obj['fields']
    pk = obj['pk']
    
    # Извлекаем ManyToMany поля (их нужно добавлять отдельно)
    groups = fields.pop('groups', [])
    user_permissions = fields.pop('user_permissions', [])
    
    # Создаём пользователя
    user = User(**fields)
    user.pk = pk
    user.save()
    
    # Добавляем ManyToMany связи
    if groups:
        user.groups.set(groups)
    if user_permissions:
        user.user_permissions.set(user_permissions)

print(f"Загружено {len(data)} пользователей")
```

### Запуск:
```bash
python load_users_without_signals.py
```

---

## 11. Список файлов фикстур (итоговый)

| Файл | Модель | Порядок загрузки |
|------|--------|------------------|
| `categories.json` | Category | 1 |
| `brands.json` | Brand | 1 |
| `badges.json` | Badge | 1 |
| `attribute_types.json` | AttributeType | 1 |
| `attribute_values.json` | AttributeValue | 2 |
| `products.json` | Product | 3 |
| `gallery.json` | ProductGalleryImage | 4 |
| `product_attributes.json` | ProductAttribute | 4 |
| `reviews.json` | Review | 5 |
| `review_images.json` | ReviewImage | 5 |
| `review_votes.json` | ReviewVote | 5 |
| `review_replies.json` | ReviewReply | 5 |
| `appointments.json` | Appointment | 6 |
| `working_hours.json` | WorkingHours | 6 |
| `users.json` | User | 7 |
| `profiles.json` | Profile | 7 |

---

## 11. Деплой на хостинг Beget

### 11.1 Подготовка на сервере

**Подключитесь к серверу:**
```bash
ssh ваше_имя_пользователя@moreug.beget.tech
```

**Перейдите в папку проекта:**
```bash
cd ~/moreug.beget.tech/public_html/catalog-clean
```

**Переключитесь на ветку `prod` и обновите код:**
```bash
git checkout prod
git pull origin prod
```

---

### 11.2 Установка зависимостей и миграции

**Активируйте виртуальное окружение:**
```bash
source ~/moreug.beget.tech/public_html/venv/bin/activate
```

**Установите зависимости:**
```bash
pip install -r requirements.txt
```

**Примените миграции:**
```bash
python manage.py migrate --settings=config.settings.prod
```

**Создайте суперпользователя:**
```bash
python manage.py createsuperuser --settings=config.settings.prod
```

---

### 11.3 Загрузка фикстур (демо-данных)

**Скопируйте файлы `.json` на сервер (локально):**
```bash
scp *.json ваше_имя_пользователя@moreug.beget.tech:~/moreug.beget.tech/public_html/catalog-clean/
```

**На сервере загрузите фикстуры в правильном порядке:**
```bash
# 1. Независимые модели
python manage.py loaddata categories.json --settings=config.settings.prod
python manage.py loaddata brands.json --settings=config.settings.prod
python manage.py loaddata badges.json --settings=config.settings.prod
python manage.py loaddata attribute_types.json --settings=config.settings.prod

# 2. Зависят от предыдущих
python manage.py loaddata attribute_values.json --settings=config.settings.prod

# 3. Товары и связанные данные
python manage.py loaddata products.json --settings=config.settings.prod
python manage.py loaddata gallery.json --settings=config.settings.prod
python manage.py loaddata product_attributes.json --settings=config.settings.prod

# 4. Отзывы (после пользователей!)
python manage.py loaddata users.json --settings=config.settings.prod
python manage.py loaddata profiles.json --settings=config.settings.prod
python manage.py loaddata reviews.json --settings=config.settings.prod
python manage.py loaddata review_images.json --settings=config.settings.prod
python manage.py loaddata review_votes.json --settings=config.settings.prod
python manage.py loaddata review_replies.json --settings=config.settings.prod

# 5. Записи на примерку
python manage.py loaddata appointments.json --settings=config.settings.prod
python manage.py loaddata working_hours.json --settings=config.settings.prod
```

---

### 11.4 Копирование медиа-файлов и симлинк

**Скопируйте папку `media/` на сервер (локально):**
```bash
scp -r F:\Projects\moreug.beget.tech\public_html\catalog-clean\media\* ваше_имя_пользователя@moreug.beget.tech:~/moreug.beget.tech/public_html/catalog-clean/media/
```

**Создайте симлинк для медиа (на сервере):**
```bash
cd ~/moreug.beget.tech/public_html/
rm -rf media/                      # удаляем старую папку, если есть
ln -s catalog-clean/media media    # создаём симлинк
```

**Проверьте:**
```bash
ls -la media/
# должно показывать: media -> catalog-clean/media/
```

**Права на папку `media/`:**
```bash
chmod -R 755 ~/moreug.beget.tech/public_html/catalog-clean/media/
```

---

### 11.5 Сборка статики и перезапуск

**Соберите статику:**
```bash
python manage.py collectstatic --settings=config.settings.prod --noinput
```

**Перезапустите приложение:**
```bash
touch ~/moreug.beget.tech/public_html/catalog-clean/config/tmp/restart.txt
```

---

### 11.6 Проверка

Откройте в браузере:
```
https://moreug.beget.tech
```

Проверьте:
- [ ] Главная страница
- [ ] Каталог товаров
- [ ] Страницы товаров (фото должны отображаться)
- [ ] Админка

---

## 12. Быстрый чек-лист перед переносом

- [ ] В старом проекте выполнены все миграции
- [ ] В новом проекте созданы все модели
- [ ] Скрипт `export_all.py` создан и настроен
- [ ] Или готовы экспортировать каждую модель вручную через shell
- [ ] Скрипт `import_all.py` создан и настроен
- [ ] Или готовы импортировать каждую модель вручную через `loaddata`
- [ ] Сигналы отключены перед загрузкой пользователей
- [ ] Медиа-файлы скопированы после загрузки данных
- [ ] Симлинк для `media/` создан на сервере
- [ ] Суперпользователь создан в новом проекте

---

✅ **Инструкция готова к использованию!**