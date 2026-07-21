# apps/products/signals.py
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.products.models import Product


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_catalog_cache(**kwargs):
    cache.delete("catalog_queryset")
    cache.delete("catalog_filters")