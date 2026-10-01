"""Find unused logos only inside the brands media directory."""

from apps.products.image_cleanup import delete_unused_image
from apps.products.management.commands.cleanup_product_images import (
    Command as ProductImageCleanupCommand,
)
from apps.products.models import Brand


class Command(ProductImageCleanupCommand):
    """Reuse preview, reference checks and error reporting for brand logos."""

    help = 'Поиск неиспользуемых логотипов в media/brands; удаление с --delete.'
    media_directory = 'brands'
    extra_extensions = {'.svg'}

    def delete_candidate(self, name: str) -> bool:
        """Remove an unused logo and its registered thumbnails."""
        return delete_unused_image(Brand(), name, field_name='logo')
