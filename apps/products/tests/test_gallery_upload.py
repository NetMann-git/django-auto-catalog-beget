"""Batch gallery uploads preserve existing photos and validate each file."""

from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.products.models import Product, ProductGalleryImage
from apps.users.constants import ROLE_MANAGER


class GalleryUploadTests(TestCase):
    """Check batch uploads through the manager's existing endpoint."""

    def setUp(self) -> None:
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = self.settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        manager = get_user_model().objects.create_user(username='gallery-manager')
        manager.profile.role = ROLE_MANAGER
        manager.profile.save()
        self.client.force_login(manager)
        self.product = Product.objects.create(
            title='Автомобиль', slug='gallery-car', price=1000000,
        )
        self.url = reverse('catalog:gallery_add', args=[self.product.pk])

    @staticmethod
    def photo(name: str) -> SimpleUploadedFile:
        """Return a real image for Django's image validation."""
        content = BytesIO()
        Image.new('RGB', (10, 10)).save(content, format='PNG')
        return SimpleUploadedFile(name, content.getvalue(), 'image/png')

    def test_batch_appends_after_existing_photo(self) -> None:
        existing = ProductGalleryImage.objects.create(
            product=self.product, image=self.photo('existing.png'), sort_order=7,
        )
        response = self.client.post(self.url, {
            'image': [self.photo('first.png'), self.photo('second.png')],
            'alt': 'Фото автомобиля',
        })
        self.assertEqual(response.status_code, 302)
        photos = list(self.product.gallery.all())
        self.assertEqual(photos[0].pk, existing.pk)
        self.assertEqual([photo.sort_order for photo in photos], [7, 8, 9])
        self.assertEqual([photo.alt for photo in photos[1:]],
                         ['Фото автомобиля', 'Фото автомобиля'])

    def test_invalid_file_prevents_partial_upload(self) -> None:
        self.client.post(self.url, {
            'image': [self.photo('valid.png'), SimpleUploadedFile(
                'invalid.png', b'not an image', 'image/png',
            )],
        })
        self.assertFalse(self.product.gallery.exists())

    def test_single_image_still_works(self) -> None:
        self.client.post(self.url, {'image': self.photo('single.png')})
        self.assertEqual(self.product.gallery.count(), 1)
