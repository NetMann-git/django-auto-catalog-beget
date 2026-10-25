"""Build v1 packages from the real parser JSON; exercise security and rollback."""
import copy
import hashlib
import io
import json
import os
import stat
import tempfile
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.products.encar_import import package
from apps.products.models import Product, ProductGalleryImage, VehicleImportSource


def picture(color='red', fmt='JPEG'):
    buffer = io.BytesIO()
    Image.new('RGB', (32, 24), color).save(buffer, fmt)
    return buffer.getvalue()


class EncarPackageTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = override_settings(
            MEDIA_ROOT=self.tmp.name + '/media', ENCAR_PACKAGE_TEMP_ROOT=self.tmp.name + '/private',
        )
        self.config.enable()
        self.addCleanup(self.config.disable)
        self.user = get_user_model().objects.create_user('package-manager')
        self.user.profile.role = 'manager'
        self.user.profile.save()
        self.client.force_login(self.user)
        self.url = reverse('catalog:import_encar')
        self.raw = json.loads((Path(__file__).parent / 'fixtures/encar_car_info.json').read_text(encoding='utf-8-sig'))
        self.listing_id = self.raw['source']['listing_id']

    def archive(self, photos=None, edit=None, extra=None, compression=zipfile.ZIP_STORED):
        photos = photos if photos is not None else [picture(), picture('blue', 'WEBP')]
        raw = json.dumps(self.raw, ensure_ascii=False).encode('utf-8')
        manifest = {
            'format': 'encar-car-package', 'schema_version': 1,
            'created_at': '2026-10-24T12:00:00Z',
            'producer': {'name': 'EncarPhotosApp', 'version': '1.13'},
            'source': copy.deepcopy(self.raw['source']),
            'data': {'path': 'car_info.json', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
            'photos': [], 'cover_path': None, 'warnings': ['Проверьте состав'],
        }
        bodies = {}
        for index, content in enumerate(photos):
            with Image.open(io.BytesIO(content)) as image:
                ext, mime = {'JPEG': ('jpg', 'image/jpeg'), 'PNG': ('png', 'image/png'), 'WEBP': ('webp', 'image/webp')}[image.format]
                path = f'photos/photo_{index + 1:03}.{ext}'
                manifest['photos'].append({
                    'path': path, 'order': index + 1, 'original_filename': f'original-{index}.jpg',
                    'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(),
                    'width': image.width, 'height': image.height, 'mime_type': mime,
                })
                bodies[path] = content
        if photos:
            manifest['cover_path'] = manifest['photos'][-1]['path']
        if edit:
            edit(manifest, bodies)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=compression) as archive:
            archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False))
            archive.writestr('car_info.json', raw)
            for name, body in bodies.items():
                archive.writestr(name, body)
            if extra:
                extra(archive)
        return SimpleUploadedFile(f'encar_{self.listing_id}.zip', buffer.getvalue(), 'application/zip')

    def preview(self, **kwargs):
        return self.client.post(self.url, {'action': 'upload', 'file': self.archive(**kwargs)})

    def submission(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertIn('package_token', response.context)
        form = response.context['form']
        data = {}
        for name in form.fields:
            value = form[name].value()
            if value is True:
                data[name] = 'on'
            elif value not in (None, False, ''):
                data[name] = value
        data.update(action='save_package', package_token=response.context['package_token'],
                    review_token=response.context['review_token'])
        if not response.context['product']:
            data.update(price='2500000', availability='under_order')
        return data

    def save(self, response):
        result = self.client.post(self.url, self.submission(response))
        self.assertEqual(result.status_code, 302, getattr(result, 'context', None) and str(result.context['form'].errors))
        return result

    def test_create_repeat_cover_originals_and_empty_photos(self):
        preview = self.preview()
        self.assertFalse(Product.objects.exists())
        token = preview.context['package_token']
        thumb = self.client.get(reverse('catalog:package_thumbnail', args=[token, 0]))
        self.assertEqual(thumb.status_code, 200)
        thumb.close()
        self.save(preview)
        product = Product.objects.get()
        self.assertFalse(product.is_active)
        self.assertEqual(product.article, self.listing_id)
        self.assertEqual(product.gallery.count(), 2)
        self.assertEqual(product.image.name, product.gallery.last().image.name)
        self.assertFalse(list(package.storage_root().iterdir()))
        self.save(self.preview())
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(ProductGalleryImage.objects.count(), 2)
        self.assertEqual(VehicleImportSource.objects.count(), 1)
        first = product.gallery.first()
        self.assertEqual(first.image.read(), picture())
        first.image.close()
        self.save(self.preview(photos=[]))
        self.assertEqual(ProductGalleryImage.objects.count(), 2)

    def test_manual_preservation_and_selective_photos(self):
        product = Product.objects.create(title='Ручное название', slug='manual', article=self.listing_id,
                                         description='Ручной текст', price=777, is_active=True)
        product.image.save('old.png', ContentFile(picture('green', 'PNG')))
        old_cover = product.image.name
        preview = self.preview()
        self.assertEqual(preview.context['product'], product)
        data = self.submission(preview)
        data.update(photo_selection=['0'], package_cover='')
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.image.name, old_cover)
        self.assertEqual(product.title, 'Ручное название')
        self.assertEqual(product.description, 'Ручной текст')
        self.assertEqual(product.price, 777)
        self.assertTrue(product.is_active)
        self.assertEqual(product.gallery.count(), 1)
        self.assertTrue(Path(self.tmp.name, 'media', old_cover).is_file())

    def test_manual_ambiguity_explicit_selection(self):
        for i in range(2):
            Product.objects.create(title=str(i), slug=str(i), article=self.listing_id, price=1)
        response = self.preview()
        self.assertContains(response, 'Уточните автомобиль')
        product = Product.objects.last()
        response = self.client.post(self.url, {'package_token': response.context['package_token'],
                                              'action': 'choose_product', 'product_id': product.pk})
        self.save(response)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(VehicleImportSource.objects.get().product_id, product.pk)
        self.save(self.preview())
        self.assertEqual(VehicleImportSource.objects.count(), 1)

    def test_cancel_expire_owner_and_csrf(self):
        response = self.preview()
        token = response.context['package_token']
        folder = package.locate(token, self.user.pk)
        other = get_user_model().objects.create_user('other-manager')
        other.profile.role = 'manager'
        other.profile.save()
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('catalog:package_thumbnail', args=[token, 0])).status_code, 404)
        self.client.force_login(self.user)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.user)
        self.assertEqual(csrf.post(self.url, {'action': 'cancel_package', 'package_token': token}).status_code, 403)
        self.client.post(self.url, {'action': 'cancel_package', 'package_token': token})
        self.assertFalse(folder.exists())
        self.assertFalse(Product.objects.exists())
        response = self.preview()
        folder = package.locate(response.context['package_token'], self.user.pk)
        old = time.time() - package.TTL - 2
        os.utime(folder, (old, old))
        self.assertEqual(package.cleanup_expired(), 1)
        self.assertFalse(folder.exists())

    def test_bad_hash_id_version_metadata_and_limits(self):
        mutations = [
            lambda m, b: m['data'].update(sha256='0' * 64),
            lambda m, b: m['source'].update(listing_id='123'),
            lambda m, b: m.update(schema_version=2),
            lambda m, b: m.update(schema_version=True),
            lambda m, b: m['photos'][0].update(width=999),
            lambda m, b: m['photos'][0].update(mime_type='image/png'),
            lambda m, b: m['photos'][1].update(order=1),
            lambda m, b: m['photos'][0].update(sha256='0' * 64),
            lambda m, b: m.update(cover_path='photos/missing.jpg'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValidationError):
                    package.validate_package(self.archive(edit=mutation))
        with override_settings(ENCAR_PACKAGE_MAX_BYTES=10):
            with self.assertRaises(ValidationError):
                package.validate_package(self.archive())
        with override_settings(GALLERY_UPLOAD_MAX_FILES=1):
            with self.assertRaises(ValidationError):
                package.validate_package(self.archive())
        with override_settings(ENCAR_PACKAGE_MAX_PIXELS=10):
            with self.assertRaises(ValidationError):
                package.validate_package(self.archive())
        self.assertFalse(Product.objects.exists())

    def test_dangerous_zip_entries_compression_duplicates_and_symlinks(self):
        for name in ['../escape', '/absolute.jpg', 'photos/../x.jpg', 'photos\\x.jpg',
                     'nested.zip', 'photos/deeper/a.jpg', 'random.txt', 'car_info.json']:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    package.validate_package(self.archive(extra=lambda z: z.writestr(name, b'x')))
        def symlink(z):
            info = zipfile.ZipInfo('photos/link.jpg')
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, b'/etc/passwd')
        with self.assertRaises(ValidationError):
            package.validate_package(self.archive(extra=symlink))
        with self.assertRaises(ValidationError):
            package.validate_package(self.archive(compression=zipfile.ZIP_DEFLATED))
        with self.assertRaises(ValidationError):
            package.validate_package(self.archive(photos=[picture(), picture()]))

    def test_failure_after_first_photo_rolls_back_database_and_files(self):
        response = self.preview()
        original = ProductGalleryImage.objects.create
        calls = 0
        def create(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise IntegrityError('forced second photo failure')
            return original(**kwargs)
        with patch('apps.products.gallery_upload.ProductGalleryImage.objects.create', side_effect=create):
            result = self.client.post(self.url, self.submission(response))
        self.assertContains(result, 'Не удалось завершить импорт')
        self.assertFalse(Product.objects.exists())
        self.assertFalse(VehicleImportSource.objects.exists())
        media = Path(self.tmp.name, 'media')
        self.assertEqual([p for p in media.rglob('*') if p.is_file()], [])

    def test_invalid_upload_is_rendered_as_error(self):
        response = self.client.post(self.url, {'action': 'upload', 'file': SimpleUploadedFile('encar_1.zip', b'broken')})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Не удалось прочитать ZIP')
        self.assertFalse(Product.objects.exists())

    def test_encryption_flag_corrupt_image_and_json_limit(self):
        archive = self.archive()
        content = bytearray(archive.read())
        # Encryption is rejected from the central directory before opening files.
        marker = content.index(b'PK\x01\x02')
        content[marker + 8] |= 1
        with self.assertRaises(ValidationError):
            package.validate_package(SimpleUploadedFile(archive.name, bytes(content)))
        def corrupt(manifest, bodies):
            path = manifest['photos'][0]['path']
            bodies[path] = b'not an image'
            manifest['photos'][0].update(bytes=len(bodies[path]), sha256=hashlib.sha256(bodies[path]).hexdigest())
        with self.assertRaises(ValidationError):
            package.validate_package(self.archive(edit=corrupt))
        with override_settings(GALLERY_UPLOAD_MAX_FILE_BYTES=10):
            with self.assertRaises(ValidationError):
                package.validate_package(self.archive())
        self.raw['description_original'] = 'a' * (1024 * 1024 + 1)
        with self.assertRaises(ValidationError):
            package.validate_package(self.archive(photos=[]))

    def test_png_and_unselected_cover_validation(self):
        preview = self.preview(photos=[picture('green', 'PNG')])
        data = self.submission(preview)
        data['photo_selection'] = []
        response = self.client.post(self.url, data)
        self.assertContains(response, 'Для обложки отметьте эту фотографию')
        self.assertFalse(Product.objects.exists())
        data['package_cover'] = ''
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertFalse(ProductGalleryImage.objects.exists())

    def test_customer_denied_for_zip_and_thumbnail(self):
        preview = self.preview()
        token = preview.context['package_token']
        self.user.profile.role = 'customer'
        self.user.profile.save()
        self.assertEqual(self.preview().status_code, 302)
        self.assertEqual(self.client.get(reverse('catalog:package_thumbnail', args=[token, 0])).status_code, 302)
        self.assertFalse(Product.objects.exists())

    def test_replace_gallery_commits_files_only_after_success(self):
        self.save(self.preview())
        product = Product.objects.get()
        old_names = list(product.gallery.values_list('image', flat=True))
        storage = product.image.storage
        preview = self.preview(photos=[picture('green', 'PNG')])
        data = self.submission(preview)
        data['replace_photos'] = 'on'
        data['package_cover'] = ''
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.gallery.count(), 1)
        self.assertEqual(product.image.name, product.gallery.get().image.name)
        self.assertTrue(product.image.name.endswith('.png'))
        self.assertTrue(storage.exists(product.image.name))
        self.assertTrue(all(not storage.exists(name) for name in old_names))

    def test_replace_gallery_failure_keeps_old_cover_and_files(self):
        self.save(self.preview())
        product = Product.objects.get()
        cover = product.image.name
        old_names = list(product.gallery.values_list('image', flat=True))
        preview = self.preview(photos=[picture('green'), picture('yellow')])
        data = self.submission(preview)
        data['replace_photos'] = 'on'
        original = ProductGalleryImage.objects.create
        calls = 0

        def fail_second(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise IntegrityError('replacement failed')
            return original(**kwargs)

        with self.captureOnCommitCallbacks(execute=True):
            with patch.object(ProductGalleryImage.objects, 'create', side_effect=fail_second):
                response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.image.name, cover)
        self.assertEqual(list(product.gallery.values_list('image', flat=True)), old_names)
        self.assertTrue(all(product.image.storage.exists(name) for name in old_names))
        actual = [p for p in Path(self.tmp.name, 'media').rglob('*') if p.is_file()]
        self.assertEqual(len(actual), len(set(old_names)))

    def test_replace_requires_selected_photo_and_preview_is_read_only(self):
        self.save(self.preview())
        product = Product.objects.get()
        old_names = list(product.gallery.values_list('image', flat=True))
        preview = self.preview()
        data = self.submission(preview)
        data.update(replace_photos='on', photo_selection=[], package_cover='')
        response = self.client.post(self.url, data)
        self.assertContains(response, 'Для замены выберите хотя бы одну фотографию.')
        self.assertEqual(list(product.gallery.values_list('image', flat=True)), old_names)

    def test_import_slug_requires_separate_approval(self):
        product = Product.objects.create(
            title='Ручное название', slug='manual-url',
            article=self.listing_id, price=1,
        )
        self.save(self.preview(photos=[]))
        product.refresh_from_db()
        self.assertEqual(product.slug, 'manual-url')
        preview = self.preview(photos=[])
        data = self.submission(preview)
        data.update(apply_title='on', title='Новый автомобиль')
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.slug, 'manual-url')
        preview = self.preview(photos=[])
        data = self.submission(preview)
        data['regenerate_slug'] = 'on'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.slug, 'novyy-avtomobil')

    def test_gallery_changes_invalidate_replace_preview(self):
        self.save(self.preview())
        product = Product.objects.get()
        preview = self.preview()
        data = self.submission(preview)
        data['replace_photos'] = 'on'
        product.gallery.update(sort_order=100)
        response = self.client.post(self.url, data)
        self.assertContains(response, 'Карточка изменилась после предпросмотра.')
        self.assertEqual(product.gallery.filter(sort_order=100).count(), 2)
