"""Gallery integration: originals, permissions, deduplication and partial failures."""
import hashlib
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.products.gallery_upload import prepare_hashes
from apps.products.models import Product, ProductGalleryImage


def image_bytes(format='JPEG', color='red'):
    output = io.BytesIO()
    Image.new('RGB', (32, 24), color).save(output, format=format)
    return output.getvalue()


class GalleryUploadTests(TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.settings = override_settings(MEDIA_ROOT=self.folder.name)
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.user = get_user_model().objects.create_user('gallery-manager')
        self.user.profile.role = 'manager'
        self.user.profile.save()
        self.client.force_login(self.user)
        self.product = Product.objects.create(title='Автомобиль', slug='gallery-car', price=12345, is_active=False)

    def url(self, action, pk=None):
        return reverse('catalog:gallery_' + action, args=[pk or self.product.pk])

    def token(self, data):
        response = self.client.post(self.url('prepare'), {'files': json.dumps([
            {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)},
        ])})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()['token']

    def upload(self, data=None, name='photo_001.jpg'):
        data = data if data is not None else image_bytes()
        while not prepare_hashes(self.product.pk):
            pass
        return self.client.post(self.url('add'), {
            'token': self.token(data), 'index': '0',
            'image': SimpleUploadedFile(name, data),
        })

    def test_first_photo_cover_original_and_duplicate_renamed(self):
        raw = image_bytes()
        self.assertEqual(self.upload(raw).json()['status'], 'added')
        photo = self.product.gallery.get()
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, photo.image.name)
        self.assertEqual(photo.image.read(), raw)
        photo.image.close()
        self.assertEqual(photo.image_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.upload(raw, 'renamed.png').json()['status'], 'duplicate')
        self.assertEqual(self.upload(raw).json()['status'], 'duplicate')
        self.assertEqual(self.product.gallery.count(), 1)
        self.assertFalse(self.product.is_active)
        self.assertEqual(self.product.price, 12345)

    def test_formats_real_extension_and_same_filename_different_bytes(self):
        for fmt, suffix in [('JPEG', '.jpg'), ('PNG', '.png'), ('WEBP', '.webp')]:
            raw = image_bytes(fmt)
            self.assertEqual(self.upload(raw, 'same.jpg').json()['status'], 'added')
            photo = self.product.gallery.last()
            self.assertTrue(photo.image.name.endswith(suffix))
            self.assertEqual(photo.image.read(), raw)
            photo.image.close()
        self.assertEqual(self.product.gallery.count(), 3)

    def test_legacy_hashes_cached_in_bounded_batches(self):
        for number in range(7):
            photo = ProductGalleryImage(product=self.product, sort_order=number)
            photo.image.save(f'old_{number}.jpg', ContentFile(image_bytes(color=(number, 0, 0))))
        self.assertFalse(prepare_hashes(self.product.pk))
        self.assertEqual(self.product.gallery.exclude(image_sha256='').count(), 5)
        self.assertTrue(prepare_hashes(self.product.pk))
        with patch('apps.products.gallery_upload.digest_file', side_effect=AssertionError('should be cached')):
            self.assertTrue(prepare_hashes(self.product.pk))
        self.assertEqual(self.upload(image_bytes(color=(0, 0, 0))).json()['status'], 'duplicate')

    def test_legacy_cover_preserved_and_new_images_appended(self):
        self.product.image.save('old.jpg', ContentFile(image_bytes(color='blue')))
        old_name = self.product.image.name
        old = ProductGalleryImage(product=self.product, sort_order=12)
        old.image.save('old_gallery.jpg', ContentFile(image_bytes(color='green')))
        self.upload()
        added = self.product.gallery.last()
        self.assertEqual(added.sort_order, 13)
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, old_name)
        self.client.post(self.url('cover', added.pk))
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, added.image.name)
        self.assertTrue(self.product.gallery.filter(image=old_name).exists())
        self.assertTrue(Path(self.folder.name, old_name).exists())

    def test_reorder_delete_and_public_cover_not_duplicated(self):
        self.upload()
        self.upload(image_bytes(color='blue'))
        first, second = list(self.product.gallery.all())
        self.client.post(self.url('order'), {f'order_{first.pk}': '20', f'order_{second.pk}': '10'})
        self.assertEqual(list(self.product.gallery.values_list('pk', flat=True)), [second.pk, first.pk])
        self.product.is_active = True
        self.product.save(update_fields=['is_active'])
        response = self.client.get(reverse('catalog:product_detail', args=[self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['gallery_images']), [second])
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url('delete', first.pk))
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, second.image.name)
        self.assertFalse(Path(self.folder.name, first.image.name).exists())
        self.assertTrue(Path(self.folder.name, second.image.name).exists())

    def test_corrupt_file_partial_success_and_retry(self):
        self.assertEqual(self.upload().json()['status'], 'added')
        response = self.upload(b'not an image')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.product.gallery.count(), 1)
        self.assertEqual(self.upload(image_bytes(color='blue')).json()['status'], 'added')
        self.assertEqual(self.upload(image_bytes(color='blue')).json()['status'], 'duplicate')

    def test_storage_cleanup_if_database_save_fails(self):
        with patch('apps.products.gallery_upload.ProductGalleryImage.objects.create', side_effect=IntegrityError):
            response = self.upload()
        self.assertEqual(response.status_code, 409)
        self.assertFalse(self.product.gallery.exists())
        self.assertEqual([p for p in Path(self.folder.name).rglob('*') if p.is_file()], [])

    def test_changed_original_invalidates_hash(self):
        self.upload()
        photo = self.product.gallery.get()
        photo.image.save('replacement.png', ContentFile(image_bytes('PNG')))
        photo.refresh_from_db()
        self.assertEqual(photo.image_sha256, '')
        self.assertEqual(self.upload(image_bytes('PNG')).json()['status'], 'duplicate')

    def test_limits_and_manifest_tampering(self):
        with override_settings(GALLERY_UPLOAD_MAX_FILE_BYTES=10):
            response = self.client.post(self.url('prepare'), {'files': json.dumps([{'sha256': '0' * 64, 'size': 11}])})
            self.assertEqual(response.status_code, 400)
        with override_settings(GALLERY_UPLOAD_MAX_TOTAL_BYTES=10):
            response = self.client.post(self.url('prepare'), {'files': json.dumps([{'sha256': '0' * 64, 'size': 6}] * 2)})
            self.assertEqual(response.status_code, 400)
        token = self.token(image_bytes())
        response = self.client.post(self.url('add'), {'token': token, 'index': 0, 'image': SimpleUploadedFile('x.jpg', image_bytes(color='blue'))})
        self.assertEqual(response.status_code, 400)
        with override_settings(GALLERY_UPLOAD_MAX_PIXELS=10):
            self.assertEqual(self.upload().status_code, 400)
        self.assertFalse(self.product.gallery.exists())

    def test_permissions_csrf_post_only_and_other_product_token(self):
        self.upload()
        photo = self.product.gallery.get()
        actions = [('add', self.product.pk), ('prepare', self.product.pk), ('order', self.product.pk), ('cover', photo.pk), ('delete', photo.pk)]
        for action, pk in actions:
            self.assertEqual(self.client.get(self.url(action, pk)).status_code, 405)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        for action, pk in actions:
            self.assertEqual(csrf_client.post(self.url(action, pk)).status_code, 403)
        other = Product.objects.create(title='Другой', slug='other', price=1)
        token = self.token(image_bytes())
        self.assertEqual(self.client.post(self.url('add', other.pk), {'token': token, 'index': 0, 'image': SimpleUploadedFile('x.jpg', image_bytes())}).status_code, 400)
        self.user.profile.role = 'customer'
        self.user.profile.save()
        for action, pk in actions:
            self.assertEqual(self.client.post(self.url(action, pk)).status_code, 302)
        self.assertEqual(self.product.gallery.count(), 1)

    def test_manager_editor_contains_queue_and_existing_equipment(self):
        response = self.client.get(reverse('catalog:product_edit', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-queue')
        self.assertContains(response, 'Добавить фотографии')
        self.assertContains(response, 'car-equipment-compact')
