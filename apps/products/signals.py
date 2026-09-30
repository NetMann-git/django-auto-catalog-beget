# apps/products/signals.py
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.products.models import Product, ProductGalleryImage
from apps.products.image_cleanup import delete_after_commit


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_catalog_cache(**kwargs):
    cache.delete("catalog_queryset")
    cache.delete("catalog_filters")


@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=ProductGalleryImage)
def remove_deleted_product_image(sender, instance, using, **kwargs) -> None:
    """Delete physical files only after the database transaction commits."""
    name = instance.image.name
    if name:
        transaction.on_commit(
            lambda: delete_after_commit(instance, name, using), using=using,
        )
