# apps\recommendations\models.py

from django.db import models
from apps.products.models import Product

class PromotedProduct(models.Model):
    """Ручные рекомендации товаров, управляемые менеджером."""

    PAGE_CHOICES = [
        ('recently_viewed', 'История просмотров'),
        ('wishlist', 'Избранное'),
        ('home', 'Главная страница'),
        ('comparison', 'Сравнение'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='promotions',
        verbose_name='Товар'
    )
    page = models.CharField(
        max_length=50,
        choices=PAGE_CHOICES,
        default='recently_viewed',
        verbose_name='Страница показа'
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text='Чем выше число, тем ближе к началу списка.',
        verbose_name='Приоритет'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    start_date = models.DateTimeField(
        blank=True, null=True,
        verbose_name='Начало показа'
    )
    end_date = models.DateTimeField(
        blank=True, null=True,
        verbose_name='Окончание показа'
    )

    class Meta:
        ordering = ['-priority', '-id']
        verbose_name = 'Продвигаемый товар'
        verbose_name_plural = 'Продвигаемые товары'

    def __str__(self):
        return f'{self.product.title} (приоритет {self.priority})'