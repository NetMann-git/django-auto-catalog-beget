# apps/products/models/product_model.py
from django.db import models

class Product(models.Model):
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Слаг', unique=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name



# from django.urls import reverse

# from .badge import Badge
# from .category import Category
# from .brand import Brand

# CURRENCY_CHOICES = [
#     ('USD', 'USD $'),
#     ('EUR', 'EUR €'),
#     ('RUB', 'RUB ₽'),
# ]


# class Product(models.Model):
#     """
#     Обычная Django-модель товара (без Wagtail).
#     """

#     # Основная информация
#     title = models.CharField(max_length=255, verbose_name="Название")
#     slug = models.SlugField(unique=True, verbose_name="URL")

#     image = models.ImageField(
#         upload_to="products/",
#         blank=True,
#         null=True,
#         verbose_name="Изображение",
#     )

#     badges = models.ManyToManyField(
#         Badge,
#         blank=True,
#         related_name="products",
#         verbose_name="Бейджи",
#     )

#     category = models.ForeignKey(
#         Category,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="product_items",
#         verbose_name="Категория",
#     )
    
#     article = models.CharField(
#         max_length=100,
#         blank=True,
#         verbose_name="Артикул"
#     )
#     product_type = models.CharField(
#         max_length=100,
#         blank=True,
#         verbose_name="Тип товара"
#     )

#     # Цена
#     price = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         verbose_name="Цена"
#     )
#     currency = models.CharField(
#         max_length=3,
#         choices=CURRENCY_CHOICES,
#         default='RUB',
#         verbose_name="Валюта"
#     )

#     # Статусы
#     is_active = models.BooleanField(
#         default=True,
#         verbose_name="Активен"
#     )
#     is_featured = models.BooleanField(
#         default=False,
#         verbose_name="Показывать на главной"
#     )

#     AVAILABILITY_CHOICES = [
#         ('in_stock', 'В наличии'),
#         ('under_order', 'Под заказ'),
#         ('last_size', 'Последний размер'),
#         ('out_of_stock', 'Нет в наличии'),
#     ]

#     availability_status = models.CharField(
#         max_length=20,
#         choices=AVAILABILITY_CHOICES,
#         default='in_stock',
#         verbose_name='Наличие',
#     )

#     short_description = models.TextField(
#         blank=True,
#         verbose_name="Краткое описание"
#     )

#     description = models.TextField(
#         blank=True,
#         verbose_name="Описание"
#     )

#     brand = models.ForeignKey(
#         Brand,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="products",
#         verbose_name="Бренд",
#     )

#     meta_title = models.CharField(
#         max_length=255,
#         blank=True,
#         verbose_name="SEO Title",
#         help_text="Если не заполнено, будет использоваться название товара."
#     )

#     meta_description = models.TextField(
#         blank=True,
#         verbose_name="SEO Description",
#         help_text="Описание страницы для поисковых систем."
#     )

#     rating = models.DecimalField(
#         max_digits=3,
#         decimal_places=2,
#         default=0,
#         verbose_name="Рейтинг",
#     )

#     reviews_count = models.PositiveIntegerField(
#         default=0,
#         verbose_name="Количество отзывов",
#     )

#     class Meta:
#         ordering = ["title"]
#         verbose_name = "Товар"
#         verbose_name_plural = "Товары"

#     def __str__(self):
#         return self.title

#     def get_absolute_url(self):
#         return reverse("catalog:product_detail", kwargs={"slug": self.slug})

#     @property
#     def seo_title(self):
#         return self.meta_title or self.title

#     @property
#     def search_description(self):
#         if self.meta_description:
#             return self.meta_description
#         if self.short_description:
#             return self.short_description
#         if self.description:
#             return self.description[:160]
#         return ""