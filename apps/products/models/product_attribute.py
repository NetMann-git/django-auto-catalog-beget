# apps/products/models/product_attribute.py
from django.db import models
from .product_model import Product
from .attribute_type import AttributeType
from .attribute_value import AttributeValue
from smart_selects.db_fields import ChainedForeignKey


class ProductAttribute(models.Model):
    """
    Значение характеристики для конкретного товара.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name="Товар",
    )
    attribute_type = models.ForeignKey(
        AttributeType,
        on_delete=models.PROTECT,
        related_name="product_attributes",
        verbose_name="Тип характеристики",
        null=False,   # временно разрешаем NULL
        blank=False,  # временно разрешаем пустое значение        
    )
    attribute_value = ChainedForeignKey(
        AttributeValue,
        chained_field="attribute_type",
        chained_model_field="attribute_type",
        show_all=False,
        auto_choose=True,
        on_delete=models.PROTECT,
        related_name="product_attributes",
        verbose_name="Значение",
        null=True,
        blank=True,
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )


    class Meta:
        ordering = ["sort_order", "attribute_type__name"]
        unique_together = ("product", "attribute_type")  # один тип на товар – одно значение
        verbose_name = "Характеристика товара"
        verbose_name_plural = "Характеристики товаров"

def __str__(self):
    value = getattr(self.attribute_value, 'value', 'не указано')
    return f"{self.attribute_type.name}: {value}"