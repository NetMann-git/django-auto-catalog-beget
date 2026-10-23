"""Shared equipment dictionary; Encar codes refer only to options.standard."""
from django.core.validators import RegexValidator
from django.db import models


class EquipmentGroup(models.Model):
    """Ordered equipment section shared by all vehicles."""

    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('Код группы', unique=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ('sort_order', 'pk')
        verbose_name = 'Группа комплектации'
        verbose_name_plural = 'Группы комплектации'

    def __str__(self) -> str:
        return self.name


class EquipmentOption(models.Model):
    """Optional source code never implies equipment presence on a vehicle."""

    name = models.CharField('Название', max_length=255)
    group = models.ForeignKey(
        EquipmentGroup, on_delete=models.PROTECT,
        related_name='options', verbose_name='Группа',
    )
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)
    encar_standard_code = models.CharField(
        'Код Encar options.standard', max_length=3, unique=True,
        null=True, blank=True,
        validators=[RegexValidator(r'^[0-9]{3}$', 'Введите три цифры, например 010.')],
        help_text='Только options.standard; для ручной опции оставьте пустым.',
    )

    class Meta:
        ordering = ('group__sort_order', 'group_id', 'sort_order', 'pk')
        verbose_name = 'Опция комплектации'
        verbose_name_plural = 'Опции комплектации'

    def save(self, *args, **kwargs) -> None:
        self.encar_standard_code = self.encar_standard_code or None
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
