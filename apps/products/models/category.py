# Категории товаров.
# apps/products/models/category.py
from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title