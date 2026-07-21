# apps/size_helper/models.py

from django.db import models


class SizeTable(models.Model):
    """
    Таблица размеров.
    """
    size = models.CharField(max_length=10, verbose_name='Размер (RU)')
    chest = models.PositiveSmallIntegerField(verbose_name='Обхват груди, см')
    waist = models.PositiveSmallIntegerField(verbose_name='Обхват талии, см')
    hips = models.PositiveSmallIntegerField(verbose_name='Обхват бёдер, см')
    height_min = models.PositiveSmallIntegerField(verbose_name='Рост (от), см')
    height_max = models.PositiveSmallIntegerField(verbose_name='Рост (до), см')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['sort_order', 'size']
        verbose_name = 'Размер'
        verbose_name_plural = 'Таблица размеров'

    def __str__(self):
        return f'{self.size} (Г:{self.chest}, Т:{self.waist}, Б:{self.hips}, Р:{self.height_min}-{self.height_max})'


class SizeRecommendation(models.Model):
    # Параметры
    height_min = models.PositiveIntegerField(verbose_name='Рост от (см)')
    height_max = models.PositiveIntegerField(verbose_name='Рост до (см)')
    bust_min = models.PositiveIntegerField(verbose_name='Обхват груди от (см)')
    bust_max = models.PositiveIntegerField(verbose_name='Обхват груди до (см)')
    waist_min = models.PositiveIntegerField(verbose_name='Талия от (см)')
    waist_max = models.PositiveIntegerField(verbose_name='Талия до (см)')
    hips_min = models.PositiveIntegerField(verbose_name='Бёдра от (см)')
    hips_max = models.PositiveIntegerField(verbose_name='Бёдра до (см)')
    
    size = models.CharField(max_length=10, verbose_name='Рекомендуемый размер')
    description = models.TextField(blank=True, verbose_name='Примечание')

    class Meta:
        ordering = ['size']
        verbose_name = 'Размерная рекомендация'
        verbose_name_plural = 'Размерные рекомендации'

    def __str__(self):
        return f'Размер {self.size} (рост {self.height_min}-{self.height_max}, грудь {self.bust_min}-{self.bust_max}...)'
