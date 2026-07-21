# apps/products/models/attribute_value.py

from django.db import models
from .attribute_type import AttributeType


class AttributeValue(models.Model):
    attribute_type = models.ForeignKey(
        AttributeType,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name="Тип характеристики"
    )
    value = models.CharField(
        max_length=255,
        verbose_name="Значение"
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["sort_order", "value"]
        unique_together = ("attribute_type", "value")
        verbose_name = "Значение характеристики"
        verbose_name_plural = "Значения характеристик"

    def __str__(self):
        return self.value