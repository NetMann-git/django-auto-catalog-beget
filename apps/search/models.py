# apps/search/models.py

from django.db import models
from django.conf import settings


class SearchQuery(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_queries',
        verbose_name='Пользователь',
    )
    query = models.CharField(max_length=255, verbose_name='Запрос')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    count = models.PositiveIntegerField(default=1, verbose_name='Количество')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Поисковый запрос'
        verbose_name_plural = 'Поисковые запросы'

    def __str__(self):
        return self.query