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

    def set_main_photo(self, name: str) -> str:
        """Save a real main image and return its storage name."""
        content = BytesIO()
        Image.new('RGB', (20, 20)).save(content, format='PNG')
        self.product.image = SimpleUploadedFile(
            name, content.getvalue(), 'image/png',
        )
        self.product.save(update_fields=['image'])
        return self.product.image.name

    def test_replacing_main_photo_removes_old_file_and_thumbnail(self) -> None:
        old = self.set_main_photo('old.png')
        thumbnail = get_thumbnailer(self.product.image).get_thumbnail(
            {'size': (10, 10)},
        )
        with self.captureOnCommitCallbacks(execute=True):
            new = self.set_main_photo('new.png')
            self.assertTrue(default_storage.exists(old))
        self.assertFalse(default_storage.exists(old))
        self.assertFalse(thumbnail.storage.exists(thumbnail.name))
        self.assertEqual(self.product.image.name, new)
        self.assertTrue(default_storage.exists(new))
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, new)

    def test_clearing_main_photo_removes_old_file(self) -> None:
        old = self.set_main_photo('clear.png')
        with self.captureOnCommitCallbacks(execute=True):
            self.product.image = ''
            self.product.save(update_fields=['image'])
        self.assertFalse(default_storage.exists(old))

    def test_rolled_back_clear_preserves_main_photo(self) -> None:
        old = self.set_main_photo('rollback.png')
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    self.product.image = ''
                    self.product.save(update_fields=['image'])
                    raise ValueError('rollback')
            except ValueError:
                pass
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, old)
        self.assertTrue(default_storage.exists(old))
