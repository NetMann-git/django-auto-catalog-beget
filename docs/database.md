
```markdown
# Схема базы данных

## Основные модели

### Product (товар)

- `title` – CharField (название)
- `slug` – SlugField (уникальный URL)
- `image` – ImageField (главное фото)
- `price` – DecimalField (цена)
- `currency` – CharField (валюта, по умолчанию "₽")
- `article` – CharField (артикул)
- `product_type` – CharField (тип товара)
- `short_description` – TextField (краткое описание)
- `description` – TextField (полное описание)
- `is_active` – BooleanField (активен/скрыт)
- `is_featured` – BooleanField (показывать на главной)
- `rating` – DecimalField (средний рейтинг, автоматически пересчитывается)
- `reviews_count` – PositiveIntegerField (количество отзывов)
- `meta_title` – CharField (SEO-заголовок)
- `meta_description` – TextField (SEO-описание)
- `category` – ForeignKey → Category
- `brand` – ForeignKey → Brand
- `badges` – ManyToManyField → Badge
- `availability_status` – CharField (выбор: in_stock, under_order, last_size, out_of_stock)

---

### Category (категория)

- `title` – CharField
- `slug` – SlugField

---

### Badge (бейдж)

- `title` – CharField
- `slug` – SlugField

---

### Brand (бренд)

- `name` – CharField
- `slug` – SlugField
- `logo` – ImageField
- `description` – TextField
- `country` – CharField
- `meta_title` – CharField
- `meta_description` – TextField

---

### AttributeType (тип характеристики)

- `name` – CharField
- `slug` – SlugField
- `data_type` – CharField (string / number / choice)

---

### AttributeValue (значение характеристики)

- `attribute_type` – ForeignKey → AttributeType
- `value` – CharField
- `sort_order` – PositiveIntegerField

---

### ProductAttribute (связь товара с характеристикой)

- `product` – ForeignKey → Product
- `attribute_type` – ForeignKey → AttributeType
- `attribute_value` – ForeignKey → AttributeValue
- `sort_order` – PositiveIntegerField

---

### ProductGalleryImage (галерея товара)

- `product` – ForeignKey → Product
- `image` – ImageField
- `alt` – CharField
- `sort_order` – PositiveIntegerField

---

### Favorite (избранное)

- `user` – ForeignKey → User
- `product` – ForeignKey → Product
- `created_at` – DateTimeField
- Уникальность: (user, product)

---

### Review (отзыв)

- `product` – ForeignKey → Product
- `user` – ForeignKey → User (может быть null)
- `guest_name` – CharField (имя гостя, если без регистрации)
- `rating` – PositiveSmallIntegerField (1–5)
- `title` – CharField (заголовок)
- `text` – TextField
- `created_at` – DateTimeField
- `updated_at` – DateTimeField
- `is_published` – BooleanField
- `is_verified` – BooleanField (подтверждённая покупка)

---

### ReviewReply (ответ на отзыв)

- `review` – OneToOneField → Review
- `text` – TextField
- `created_at` – DateTimeField
- `updated_at` – DateTimeField

---

### ReviewImage (фото в отзыве)

- `review` – ForeignKey → Review
- `image` – ImageField
- `sort_order` – PositiveIntegerField

---

## Связи между моделями

- Product → Category (ForeignKey)
- Product → Brand (ForeignKey)
- Product → Badge (ManyToMany)
- Product → AttributeType (через ProductAttribute)
- Product → ProductGalleryImage (OneToMany)
- Product → Review (OneToMany)
- Product → Favorite (OneToMany)
- Review → ReviewReply (OneToOne)
- Review → ReviewImage (OneToMany)
- User → Favorite (OneToMany)
- User → Review (OneToMany)

---

## Особенности

- Все текстовые поля поддерживают кириллицу.
- Рейтинг товара пересчитывается автоматически при добавлении/изменении/удалении отзыва (сигналы).
- Избранное хранится в сессии для гостей и в БД для авторизованных.
- Характеристики универсальны и не привязаны к конкретным полям.
- SEO-поля (meta_title, meta_description) есть у Product и Brand.

---

### ReviewVote (голос за отзыв)

- `review` – ForeignKey → Review
- `user` – ForeignKey → User (может быть null)
- `session_key` – CharField (для гостей)
- `is_helpful` – BooleanField (полезно/не полезно)
- Уникальность: (review, user, session_key)

---

### Appointment (запись на примерку)

- `product` – ForeignKey → Product (может быть null)
- `name` – CharField
- `phone` – CharField
- `email` – EmailField (blank)
- `date` – DateField
- `time` – TimeField
- `comment` – TextField (blank)
- `status` – CharField (pending / confirmed / completed / cancelled)
- `created_at` – DateTimeField
- `updated_at` – DateTimeField

---

### WorkingHours (рабочее время салона)

- `day_of_week` – IntegerField (0–6)
- `start_time` – TimeField
- `end_time` – TimeField
- `is_active` – BooleanField

---

### SizeRecommendation (размерная рекомендация)
- `height_min` – PositiveIntegerField (рост от)
- `height_max` – PositiveIntegerField (рост до)
- `bust_min` – PositiveIntegerField (грудь от)
- `bust_max` – PositiveIntegerField (грудь до)
- `waist_min` – PositiveIntegerField (талия от)
- `waist_max` – PositiveIntegerField (талия до)
- `hips_min` – PositiveIntegerField (бёдра от)
- `hips_max` – PositiveIntegerField (бёдра до)
- `size` – CharField (размер)
- `description` – TextField (примечание)

---

### SizeTable (таблица размеров)
- `size` – CharField (размер RU)
- `chest` – PositiveSmallIntegerField (грудь)
- `waist` – PositiveSmallIntegerField (талия)
- `hips` – PositiveSmallIntegerField (бёдра)
- `height_min` – PositiveSmallIntegerField (рост от)
- `height_max` – PositiveSmallIntegerField (рост до)
- `sort_order` – PositiveSmallIntegerField (порядок)


### Profile (профиль пользователя)

Расширяет стандартную модель User.

| Поле | Тип | Описание |
|------|-----|----------|
| user | OneToOneField(User) | Связь с пользователем |
| phone | CharField(20) | Номер телефона |
| role | CharField(20) | Роль: customer, consultant, manager, admin |
| avatar | ImageField | Аватар пользователя |
| created_at | DateTimeField | Дата создания |
| updated_at | DateTimeField | Дата обновления |


```
