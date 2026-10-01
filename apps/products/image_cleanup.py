"""Remove unused product images through Django's storage backend."""

import logging

from django.apps import apps
from django.db.models import FileField
from easy_thumbnails.files import ThumbnailerFieldFile

logger = logging.getLogger(__name__)


def referenced_files(using: str = 'default') -> set[str]:
    """Collect file references, including those outside the products app."""
    names: set[str] = set()
    for model in apps.get_models():
        for field in model._meta.concrete_fields:
            if isinstance(field, FileField):
                names.update(
                    name for name in model._base_manager.using(using)
                    .values_list(field.name, flat=True) if name
                )
    return names


def delete_unused_image(
    instance, name: str, using: str = 'default', field_name: str = 'image',
) -> bool:
    """Delete an image and its registered thumbnails unless still referenced."""
    if not name or name in referenced_files(using):
        return False
    # FieldFile.delete also clears the field on its instance. Use a detached
    # instance so deleting an old file never clears the newly assigned image.
    instance = type(instance)()
    image = ThumbnailerFieldFile(
        instance, instance._meta.get_field(field_name), name,
    )
    image.delete(save=False)
    return True


def delete_after_commit(
    instance, name: str, using: str, field_name: str = 'image',
) -> None:
    """Log storage failures without failing an already committed deletion."""
    try:
        delete_unused_image(instance, name, using, field_name=field_name)
    except Exception:
        logger.exception('Не удалось удалить файл изображения %s', name)
