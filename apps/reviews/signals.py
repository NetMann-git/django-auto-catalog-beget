# apps/reviews/signals.py

from django.db.models import Avg, Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Review


def update_product_rating(product):
    """Пересчитывает средний рейтинг и количество отзывов для товара."""
    reviews = product.reviews.filter(is_published=True)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    count = reviews.count()

    product.rating = round(avg_rating, 2)
    product.reviews_count = count
    product.save(update_fields=['rating', 'reviews_count'])


@receiver(post_save, sender=Review)
def review_post_save(sender, instance, created, **kwargs):
    """Обновляет рейтинг при сохранении отзыва."""
    update_product_rating(instance.product)


@receiver(post_delete, sender=Review)
def review_post_delete(sender, instance, **kwargs):
    """Обновляет рейтинг при удалении отзыва."""
    update_product_rating(instance.product)