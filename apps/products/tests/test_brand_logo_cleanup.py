"""Brand logo cleanup must preserve live references and other media."""

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

from apps.products.models import Brand, Product


class BrandLogoCleanupTests(TestCase):
    """Exercise logo replacement, deletion, rollback and orphan discovery."""

    def setUp(self) -> None:
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        override = self.settings(MEDIA_ROOT=media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.brand = Brand.objects.create(name='Test brand', slug='test-brand')

    def save_logo(self, name: str) -> str:
        """Store a real PNG and return its storage name."""
        content = BytesIO()
        Image.new('RGB', (20, 20)).save(content, format='PNG')
        self.brand.logo = SimpleUploadedFile(name, content.getvalue(), 'image/png')
        self.brand.save(update_fields=['logo'])
        return self.brand.logo.name

    def test_replace_and_clear_logo(self) -> None:
        old = self.save_logo('old.png')
        thumbnail = get_thumbnailer(self.brand.logo).get_thumbnail({'size': (10, 10)})
        with self.captureOnCommitCallbacks(execute=True):
            new = self.save_logo('new.png')
            self.assertTrue(default_storage.exists(old))
        self.assertFalse(default_storage.exists(old))
        self.assertFalse(thumbnail.storage.exists(thumbnail.name))
        self.assertEqual(self.brand.logo.name, new)
        self.assertTrue(default_storage.exists(new))
        with self.captureOnCommitCallbacks(execute=True):
            self.brand.logo = ''
            self.brand.save(update_fields=['logo'])
        self.assertFalse(default_storage.exists(new))

    def test_brand_deletion_keeps_product(self) -> None:
        logo = self.save_logo('delete.png')
        product = Product.objects.create(
            title='Car', slug='car', price=1000000, brand=self.brand,
        )
        with self.captureOnCommitCallbacks(execute=True):
            self.brand.delete()
        self.assertFalse(default_storage.exists(logo))
        product.refresh_from_db()
        self.assertIsNone(product.brand_id)

    def test_shared_logo_is_preserved(self) -> None:
        logo = self.save_logo('shared.png')
        Brand.objects.create(name='Second', slug='second', logo=logo)
        with self.captureOnCommitCallbacks(execute=True):
            self.brand.delete()
        self.assertTrue(default_storage.exists(logo))

    def test_rollback_preserves_logo(self) -> None:
        logo = self.save_logo('rollback.png')
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    self.brand.logo = ''
                    self.brand.save(update_fields=['logo'])
                    raise ValueError('rollback')
            except ValueError:
                pass
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.logo.name, logo)
        self.assertTrue(default_storage.exists(logo))

    def test_command_preview_and_scope(self) -> None:
        logo = self.save_logo('used.png')
        thumbnail = get_thumbnailer(self.brand.logo).get_thumbnail({'size': (10, 10)})
        orphan = default_storage.save('brands/orphan.JFIF', ContentFile(b'old'))
        outside = default_storage.save('products/keep.png', ContentFile(b'keep'))
        output = StringIO()
        call_command('cleanup_brand_logos', stdout=output)
        self.assertIn(orphan, output.getvalue())
        self.assertTrue(default_storage.exists(orphan))
        call_command('cleanup_brand_logos', delete=True, stdout=StringIO())
        self.assertFalse(default_storage.exists(orphan))
        self.assertTrue(default_storage.exists(outside))
        self.assertTrue(default_storage.exists(logo))
        self.assertTrue(thumbnail.storage.exists(thumbnail.name))
