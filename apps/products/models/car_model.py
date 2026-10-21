"""Vehicle models grouped by their manufacturer."""

from django.core.exceptions import ValidationError
from django.db import models


class CarModel(models.Model):
    """A model family, such as Audi A3, independent of year and trim."""

    brand = models.ForeignKey(
        'products.Brand', on_delete=models.PROTECT,
        related_name='car_models', verbose_name='Марка',
    )
    name = models.CharField(max_length=100, verbose_name='Название модели')
    slug = models.SlugField(unique=True, verbose_name='Код модели')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['brand__name', 'sort_order', 'name']
        verbose_name = 'Модель автомобиля'
        verbose_name_plural = 'Модели автомобилей'
        constraints = [
            models.UniqueConstraint(
                fields=['brand', 'name'], name='products_unique_brand_model',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.brand} {self.name}'

    def clean(self) -> None:
        """Do not move an assigned model to a different manufacturer."""
        super().clean()
        if self.pk and self.products.exclude(brand_id=self.brand_id).exists():
            raise ValidationError({
                'brand': 'Нельзя менять марку модели, используемой в товарах.',
            })
