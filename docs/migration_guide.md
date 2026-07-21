# 📋 Инструкция по переносу данных между проектами Django

## Содержание

1. [Подготовка](#1-подготовка)
2. [Перенос категорий](#2-перенос-категорий)
3. [Перенос брендов](#3-перенос-брендов)
4. [Перенос бейджей](#4-перенос-бейджей)
5. [Перенос типов характеристик](#5-перенос-типов-характеристик)
6. [Перенос значений характеристик](#6-перенос-значений-характеристик)
7. [Перенос товаров](#7-перенос-товаров)
8. [Перенос галереи товаров](#8-перенос-галереи-товаров)
9. [Перенос характеристик товаров](#9-перенос-характеристик-товаров)
10. [Перенос отзывов](#10-перенос-отзывов)
11. [Перенос фото отзывов](#11-перенос-фото-отзывов)
12. [Перенос записей на примерку](#12-перенос-записей-на-примерку)
13. [Перенос пользователей](#13-перенос-пользователей)
14. [Копирование медиа-файлов](#14-копирование-медиа-файлов)
15. [Полный скрипт для одной команды](#15-полный-скрипт-для-одной-команды)

---

## 1. Подготовка

### 1.1 Убедитесь, что оба проекта имеют одинаковые модели

Перед переносом убедитесь, что модели в целевом проекте совпадают с исходным.

### 1.2 Создайте папку для фикстур (опционально)

```bash
mkdir F:\Projects\fixtures
```

---

## 2. Перенос категорий

### Выгрузка (в исходном проекте)

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import Category

data = serialize('json', Category.objects.all(), indent=2)
with open('categories.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Category.objects.count()} категорий")
exit()
```

### Копирование

```bash
copy categories.json F:\Projects\catalog-clean\
```

### Загрузка (в целевом проекте)

```bash
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata categories.json
```

---

## 3. Перенос брендов

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import Brand

data = serialize('json', Brand.objects.all(), indent=2)
with open('brands.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Brand.objects.count()} брендов")
exit()
```

### Копирование и загрузка

```bash
copy brands.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata brands.json
```

---

## 4. Перенос бейджей

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import Badge

data = serialize('json', Badge.objects.all(), indent=2)
with open('badges.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Badge.objects.count()} бейджей")
exit()
```

### Копирование и загрузка

```bash
copy badges.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata badges.json
```

---

## 5. Перенос типов характеристик

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import AttributeType

data = serialize('json', AttributeType.objects.all(), indent=2)
with open('attribute_types.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {AttributeType.objects.count()} типов характеристик")
exit()
```

### Копирование и загрузка

```bash
copy attribute_types.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata attribute_types.json
```

---

## 6. Перенос значений характеристик

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import AttributeValue

data = serialize('json', AttributeValue.objects.all(), indent=2)
with open('attribute_values.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {AttributeValue.objects.count()} значений характеристик")
exit()
```

### Копирование и загрузка

```bash
copy attribute_values.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata attribute_values.json
```

---

## 7. Перенос товаров

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import Product

data = serialize('json', Product.objects.all(), indent=2)
with open('products.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {Product.objects.count()} товаров")
exit()
```

### Копирование и загрузка

```bash
copy products.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata products.json
```

---

## 8. Перенос галереи товаров

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import ProductGalleryImage

data = serialize('json', ProductGalleryImage.objects.all(), indent=2)
with open('gallery.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {ProductGalleryImage.objects.count()} изображений галереи")
exit()
```

### Копирование и загрузка

```bash
copy gallery.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata gallery.json
```

---

## 9. Перенос характеристик товаров

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.products.models import ProductAttribute

data = serialize('json', ProductAttribute.objects.all(), indent=2)
with open('product_attributes.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {ProductAttribute.objects.count()} характеристик товаров")
exit()
```

### Копирование и загрузка

```bash
copy product_attributes.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata product_attributes.json
```

---

## 10. Перенос отзывов

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.reviews.models import Review, ReviewReply, ReviewVote

# Отзывы
data = serialize('json', Review.objects.all(), indent=2)
with open('reviews.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Ответы на отзывы
data = serialize('json', ReviewReply.objects.all(), indent=2)
with open('review_replies.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Голоса
data = serialize('json', ReviewVote.objects.all(), indent=2)
with open('review_votes.json', 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Отзывов: {Review.objects.count()}, Ответов: {ReviewReply.objects.count()}, Голосов: {ReviewVote.objects.count()}")
exit()
```

### Копирование и загрузка

```bash
copy reviews.json F:\Projects\catalog-clean\
copy review_replies.json F:\Projects\catalog-clean\
copy review_votes.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata reviews.json
python manage.py loaddata review_replies.json
python manage.py loaddata review_votes.json
```

---

## 11. Перенос фото отзывов

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.reviews.models import ReviewImage

data = serialize('json', ReviewImage.objects.all(), indent=2)
with open('review_images.json', 'w', encoding='utf-8') as f:
    f.write(data)
print(f"Сохранено {ReviewImage.objects.count()} фото отзывов")
exit()
```

### Копирование и загрузка

```bash
copy review_images.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata review_images.json
```

---

## 12. Перенос записей на примерку

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from apps.appointments.models import Appointment, WorkingHours

# Записи
data = serialize('json', Appointment.objects.all(), indent=2)
with open('appointments.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Рабочее время
data = serialize('json', WorkingHours.objects.all(), indent=2)
with open('working_hours.json', 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Записей: {Appointment.objects.count()}, Рабочих часов: {WorkingHours.objects.count()}")
exit()
```

### Копирование и загрузка

```bash
copy appointments.json F:\Projects\catalog-clean\
copy working_hours.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata appointments.json
python manage.py loaddata working_hours.json
```

---

## 13. Перенос пользователей

### ⚠️ ВНИМАНИЕ: При переносе пользователей могут быть конфликты с уже существующими

### Выгрузка

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python manage.py shell
```

```python
import json
from django.core.serializers import serialize
from django.contrib.auth.models import User
from apps.users.models import Profile

# Пользователи
data = serialize('json', User.objects.all(), indent=2)
with open('users.json', 'w', encoding='utf-8') as f:
    f.write(data)

# Профили
data = serialize('json', Profile.objects.all(), indent=2)
with open('profiles.json', 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Пользователей: {User.objects.count()}, Профилей: {Profile.objects.count()}")
exit()
```

### Копирование и загрузка

```bash
copy users.json F:\Projects\catalog-clean\
copy profiles.json F:\Projects\catalog-clean\
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py loaddata users.json
python manage.py loaddata profiles.json
```

---

## 14. Копирование медиа-файлов

### Копирование всех медиа-файлов

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

## 15. Полный скрипт для одной команды

Создайте файл `export_all.py` в корне старого проекта:

```python
# export_all.py
import json
from django.core.serializers import serialize
from django.contrib.auth.models import User
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
    data = serialize('json', model.objects.all(), indent=2)
    with open(f'{name}.json', 'w', encoding='utf-8') as f:
        f.write(data)
    print(f'Exported {name}: {model.objects.count()} records')
```

### Запуск:

```bash
cd F:\Projects\wedding-catalog
.venv\Scripts\activate
python export_all.py
```

---

## 16. Проверка после переноса

```bash
cd F:\Projects\catalog-clean
.venv\Scripts\activate
python manage.py runserver
```

Проверьте:
- [ ] Каталог товаров
- [ ] Страницы товаров
- [ ] Галерея
- [ ] Характеристики
- [ ] Отзывы с фото
- [ ] Записи на примерку
- [ ] Рабочее время
- [ ] Пользователи и роли

---

## ⚠️ Возможные проблемы и решения

### 1. Ошибка `UnicodeDecodeError` при загрузке
**Решение:** Используйте Python shell для выгрузки (как в инструкции) вместо команды `dumpdata` с перенаправлением.

### 2. Ошибка `IntegrityError` при загрузке
**Решение:** Загружайте данные в правильном порядке (сначала зависимые модели, потом те, которые на них ссылаются).

### 3. Ошибка `DoesNotExist` при загрузке
**Решение:** Убедитесь, что все связанные модели загружены.

### 4. Фото не отображаются
**Решение:** Проверьте, что папка `media/` скопирована правильно и пути в БД совпадают с фактическими путями файлов.

---

## 📁 Файлы фикстур (итоговый список)

| Файл | Модель | Количество |
|------|--------|------------|
| `categories.json` | Category | ... |
| `brands.json` | Brand | ... |
| `badges.json` | Badge | ... |
| `attribute_types.json` | AttributeType | ... |
| `attribute_values.json` | AttributeValue | ... |
| `products.json` | Product | ... |
| `gallery.json` | ProductGalleryImage | ... |
| `product_attributes.json` | ProductAttribute | ... |
| `reviews.json` | Review | ... |
| `review_images.json` | ReviewImage | ... |
| `review_votes.json` | ReviewVote | ... |
| `review_replies.json` | ReviewReply | ... |
| `appointments.json` | Appointment | ... |
| `working_hours.json` | WorkingHours | ... |
| `users.json` | User | ... |
| `profiles.json` | Profile | ... |

---
