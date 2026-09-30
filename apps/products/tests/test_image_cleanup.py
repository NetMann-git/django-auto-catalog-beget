"""Deletion and dry-run cleanup must preserve images that are still in use."""

from io import BytesIO, StringIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase
from easy_thumbnails.files import get_thumbnailer

from apps.products.models import Product, ProductGalleryImage


class ImageCleanupTests(TestCase):
    """Check committed deletion, shared references and orphan cleanup."""

    def setUp(self) -> None:
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = self.settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.product = Product.objects.create(
            title='Автомобиль', slug='cleanup-car', price=1000000,
        )

    def photo(self) -> ProductGalleryImage:
        """Create a real gallery image in temporary storage."""
        content = BytesIO()
        Image.new('RGB', (20, 20)).save(content, format='PNG')
        return ProductGalleryImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('photo.png', content.getvalue(), 'image/png'),
        )

    def test_committed_gallery_deletion_removes_original_and_thumbnail(self) -> None:
        photo = self.photo()
        name = photo.image.name
        thumbnail = get_thumbnailer(photo.image).get_thumbnail({'size': (10, 10)})
        with self.captureOnCommitCallbacks(execute=True):
            photo.delete()
            self.assertTrue(default_storage.exists(name))
        self.assertFalse(default_storage.exists(name))
        self.assertFalse(thumbnail.storage.exists(thumbnail.name))

    def test_product_cascade_removes_gallery_files(self) -> None:
        name = self.photo().image.name
        with self.captureOnCommitCallbacks(execute=True):
            self.product.delete()
        self.assertFalse(default_storage.exists(name))

    def test_rollback_keeps_photo(self) -> None:
        photo = self.photo()
        name = photo.image.name
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    photo.delete()
                    raise ValueError('rollback')
            except ValueError:
                pass
        self.assertTrue(default_storage.exists(name))
        self.assertEqual(self.product.gallery.count(), 1)

    def test_shared_photo_is_kept(self) -> None:
        photo = self.photo()
        name = photo.image.name
        ProductGalleryImage.objects.create(product=self.product, image=name)
        with self.captureOnCommitCallbacks(execute=True):
            photo.delete()
        self.assertTrue(default_storage.exists(name))

    def test_cleanup_dry_run_and_explicit_deletion(self) -> None:
        live_name = self.photo().image.name
        orphan = default_storage.save('products/gallery/orphan.png', ContentFile(b'old'))
        outside = default_storage.save('brands/logo.png', ContentFile(b'logo'))
        call_command('cleanup_product_images', stdout=StringIO())
        self.assertTrue(default_storage.exists(orphan))
        call_command('cleanup_product_images', delete=True, stdout=StringIO())
        self.assertFalse(default_storage.exists(orphan))
        self.assertTrue(default_storage.exists(live_name))
        self.assertTrue(default_storage.exists(outside))
