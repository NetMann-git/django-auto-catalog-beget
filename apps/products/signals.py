# apps/products/signals.py
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.products.models import Product, ProductGalleryImage
from apps.products.image_cleanup import delete_after_commit


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_catalog_cache(**kwargs):
    cache.delete("catalog_queryset")
    cache.delete("catalog_filters")


@receiver(pre_save, sender=Product)
@receiver(pre_save, sender=ProductGalleryImage)
def remember_previous_image(
    sender, instance, using, raw=False, update_fields=None, **kwargs
) -> None:
    """Remember the stored image before saving a replacement or clearing it."""
    instance._previous_image_name = None
    if raw or not instance.pk:
        return
    if update_fields is not None and "image" not in update_fields:
        return
    instance._previous_image_name = (
        sender._base_manager.using(using)
        .filter(pk=instance.pk)
        .values_list("image", flat=True)
        .first()
    )


@receiver(post_save, sender=Product)
@receiver(post_save, sender=ProductGalleryImage)
def remove_replaced_image(
    sender, instance, using, raw=False, **kwargs
) -> None:
    """Remove the former image only after the new database state commits."""
    if raw:
        return
    previous_name = getattr(instance, "_previous_image_name", None)
    if previous_name and previous_name != instance.image.name:
        transaction.on_commit(
            lambda: delete_after_commit(instance, previous_name, using),
            using=using,
        )
    instance._previous_image_name = None


@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=ProductGalleryImage)
def remove_deleted_product_image(sender, instance, using, **kwargs) -> None:
    """Delete physical files only after the database transaction commits."""
    name = instance.image.name
    if name:
        transaction.on_commit(
            lambda: delete_after_commit(instance, name, using), using=using,
        )
