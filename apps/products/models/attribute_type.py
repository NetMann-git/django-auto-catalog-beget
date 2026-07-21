# apps/products/models/attribute_type.py
from django.db import models


class AttributeType(models.Model):
    """
    Тип характеристики (например, "Силуэт", "Коллекция", "Цвет").
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    
    DATA_TYPES = (
        ('string', 'Строка'),
        ('number', 'Число'),
        ('choice', 'Выбор из списка'),
    )
    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPES,
        default='string',
        verbose_name="Тип данных"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Тип характеристики"
        verbose_name_plural = "Типы характеристик"

    def __str__(self):
        return self.name