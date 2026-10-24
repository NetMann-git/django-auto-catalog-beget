"""Exercise a real parser file through the manager upload/preview workflow."""
import copy
import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from apps.products.models import (
    AttributeType, AttributeValue, Brand, CarModel, EquipmentOption,
    Product, ProductAttribute, VehicleImportSource,
)


class EncarImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.raw = json.loads((Path(__file__).parent / 'fixtures/encar_car_info.json').read_text(encoding='utf-8-sig'))
        call_command('load_equipment', stdout=StringIO())
        cls.manager = get_user_model().objects.create_user('manager')
        cls.manager.profile.role = 'manager'
        cls.manager.profile.save()
        cls.brand = Brand.objects.create(name='Kia', slug='kia')
        cls.model = CarModel.objects.create(brand=cls.brand, name='Sportage', slug='sportage')
        cls.year = AttributeType.objects.create(name='Год', slug='year', data_type='choice')
        AttributeValue.objects.create(attribute_type=cls.year, value='2022')
        AttributeType.objects.create(name='Пробег', slug='mileage', data_type='number')
        AttributeType.objects.create(name='Объём, л', slug='engine_volume', data_type='number')

    def setUp(self):
        self.client.force_login(self.manager)
        self.url = reverse('catalog:import_encar')

    def preview(self, raw=None):
        data = self.raw if raw is None else raw
        return self.client.post(self.url, {'action': 'upload', 'file': SimpleUploadedFile('car_info.json', json.dumps(data).encode(), 'application/json')})

    def submission(self, response):
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        data = {}
        for name in form.fields:
            value = form[name].value()
            if value is True:
                data[name] = 'on'
            elif value not in (None, False, ''):
                data[name] = value
        data.update(action='save')
        if not response.context['product']:
            data.update(price='2500000', availability='under_order')
        return data

    def create(self):
        response = self.client.post(self.url, self.submission(self.preview()))
        self.assertEqual(response.status_code, 302, getattr(response, 'context', None) and response.context['form'].errors)
        product = Product.objects.get()
        self.assertEqual(product.article, product.import_sources.get(source='encar').listing_id)
        return product

    def test_real_file_preview_cancel_create_and_repeat(self):
        preview = self.preview()
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(VehicleImportSource.objects.count(), 0)
        self.client.get(self.url)
        self.assertEqual(Product.objects.count(), 0)
        product = self.create()
        self.assertFalse(product.is_active)
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 404)
        self.assertEqual(product.brand, self.brand)
        self.assertEqual(product.car_model, self.model)
        self.assertEqual(product.equipment.count(), 38)
        self.assertEqual(product.attributes.count(), 3)
        source = VehicleImportSource.objects.get()
        self.assertEqual(source.listing_id, '42764770')
        self.assertEqual(source.internal_vehicle_id, '42761908')
        self.assertEqual(source.source_price, 18900000)
        self.assertEqual(source.source_currency, 'KRW')
        self.assertEqual(source.raw_json, self.raw)
        self.assertIsNotNone(source.retrieved_at)
        result = self.client.post(self.url, self.submission(self.preview()))
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(VehicleImportSource.objects.count(), 1)
        self.assertEqual(ProductAttribute.objects.count(), 3)
        self.assertEqual(AttributeValue.objects.count(), 3)

    def test_update_preserves_manual_data_and_adds_equipment(self):
        product = self.create()
        product.title, product.description, product.price = 'Ручное название', 'Ручной перевод', 3333333
        product.is_active, product.slug = True, 'manual-url'
        product.image = 'products/manual.jpg'
        product.save()
        extra = EquipmentOption.objects.get(encar_standard_code='010')
        product.equipment.add(extra)
        response = self.client.post(self.url, self.submission(self.preview()))
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual((product.title, product.description, product.price, product.slug, product.is_active), ('Ручное название', 'Ручной перевод', 3333333, 'manual-url', True))
        self.assertEqual(product.image.name, 'products/manual.jpg')
        self.assertIn(extra, product.equipment.all())
        data = self.submission(self.preview())
        data.update(apply_title='on', title='Новое выбранное название')
        self.client.post(self.url, data)
        product.refresh_from_db()
        self.assertEqual(product.title, 'Новое выбранное название')
        self.assertEqual(product.description, 'Ручной перевод')

    def test_empty_fields_unknown_codes_and_replace_confirmation(self):
        product = self.create()
        original_description = product.description
        raw = copy.deepcopy(self.raw)
        raw['translation'] = {}
        raw['vehicle'] = {}
        raw['description_original'] = ''
        raw['equipment']['standard_codes'] = ['001', '002', '999']
        raw['equipment']['standard_items'] = []
        preview = self.preview(raw)
        self.assertContains(preview, '999')
        data = self.submission(preview)
        data.update(equipment_mode='replace')
        failed = self.client.post(self.url, data)
        self.assertEqual(failed.status_code, 200)
        self.assertEqual(product.equipment.count(), 38)
        data['confirm_replace'] = 'on'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.description, original_description)
        self.assertEqual(list(product.equipment.values_list('encar_standard_code', flat=True)), ['001'])
        self.assertEqual(VehicleImportSource.objects.get().raw_json['equipment']['standard_codes'], ['001', '002', '999'])

    def test_different_listing_with_same_internal_id_stays_separate(self):
        self.create()
        raw = copy.deepcopy(self.raw)
        raw['source'].update(listing_id='42764771', url='https://fem.encar.com/cars/detail/42764771')
        self.client.post(self.url, self.submission(self.preview(raw)))
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(VehicleImportSource.objects.count(), 2)

    def test_stale_preview_and_database_uniqueness(self):
        data = self.submission(self.preview())
        self.create()
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)
        source = VehicleImportSource.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            VehicleImportSource.objects.create(product=source.product, source='encar', listing_id=source.listing_id, raw_json={})

    def test_rollback_on_save_failure(self):
        data = self.submission(self.preview())
        with patch.object(VehicleImportSource, 'save', side_effect=IntegrityError):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(ProductAttribute.objects.count(), 0)
        self.assertEqual(AttributeValue.objects.count(), 1)

    def test_invalid_json_size_and_structure(self):
        for content in (b'{broken', b'[]', b'x' * (1024 * 1024 + 1)):
            response = self.client.post(self.url, {'action': 'upload', 'file': SimpleUploadedFile('bad.json', content)})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        raw = copy.deepcopy(self.raw)
        raw['equipment']['standard_codes'] = [1]
        self.assertTrue(self.preview(raw).context['form'].errors)
        raw['source']['url'] = 'https://example.com/attack'
        self.assertTrue(self.preview(raw).context['form'].errors)
        self.assertEqual(Product.objects.count(), 0)

    def test_permissions_csrf_and_user_bound_confirmation(self):
        data = self.submission(self.preview())
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        customer = get_user_model().objects.create_user('customer')
        self.client.force_login(customer)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        customer.profile.role = 'manager'
        customer.profile.save()
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(Product.objects.count(), 0)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.manager)
        self.assertEqual(strict.post(self.url, data).status_code, 403)

    def test_untrusted_description_is_escaped(self):
        raw = copy.deepcopy(self.raw)
        raw['translation']['seller_text_ru'] = '<script>alert(1)</script>'
        response = self.preview(raw)
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_selected_attribute_updates_without_creating_values_twice(self):
        product = self.create()
        raw = copy.deepcopy(self.raw)
        raw['vehicle']['mileage_km'] = 120000
        preview = self.preview(raw)
        data = self.submission(preview)
        index = next(i for i, spec in enumerate(preview.context['proposal']['specs']) if spec['key'] == 'mileage_km')
        data[f'attr_{index}_apply'] = 'on'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        attribute = product.attributes.get(attribute_type__slug='mileage')
        self.assertEqual(attribute.attribute_value.value, '120000')
        data = self.submission(self.preview(raw))
        data[f'attr_{index}_apply'] = 'on'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(AttributeValue.objects.filter(attribute_type__slug='mileage', value='120000').count(), 1)
        self.assertEqual(product.attributes.count(), 3)

    def test_editor_change_after_preview_is_not_overwritten(self):
        product = self.create()
        data = self.submission(self.preview())
        data.update(apply_description='on')
        product.description = 'Изменено другим менеджером'
        product.save()
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.description, 'Изменено другим менеджером')

    def test_missing_translation_is_not_replaced_by_korean_text(self):
        raw = copy.deepcopy(self.raw)
        raw.pop('translation')
        preview = self.preview(raw)
        self.assertEqual(preview.context['form']['description'].value(), '')
        data = self.submission(preview)
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(Product.objects.get().description, '')
        self.assertEqual(VehicleImportSource.objects.get().original_description, raw['description_original'])
