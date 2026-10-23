"""Equipment persistence, dictionary safety and public rendering."""
from io import StringIO

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.template import Context, Template
from django.test import RequestFactory, TestCase

from apps.products.admin import ProductAdmin
from apps.products.car_model_forms import ProductModelForm
from apps.products.forms import ProductForm
from apps.products.models import (
    AttributeType, AttributeValue, EquipmentGroup, EquipmentOption,
    Product, ProductAttribute,
)


class EquipmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('load_equipment', stdout=StringIO())
        cls.product = Product.objects.create(title='Авто', slug='auto', price=100)

    def data(self, selected=()):
        return {
            'title': 'Авто', 'slug': 'auto', 'price': '100', 'currency': 'RUB',
            'availability_status': 'in_stock', 'rating': '0', 'reviews_count': '0',
            'equipment': list(selected),
        }

    def render_product(self):
        return Template('{% load equipment_tags %}{% vehicle_equipment product %}').render(
            Context({'product': self.product}),
        )

    def test_seed_preserves_edits_selections_and_attributes(self):
        option = EquipmentOption.objects.get(encar_standard_code='010')
        self.product.equipment.add(option)
        option.name = 'Переименовано'
        option.is_active = False
        option.sort_order = 500
        option.save()
        kind = AttributeType.objects.create(name='Топливо', slug='fuel', data_type='choice')
        value = AttributeValue.objects.create(attribute_type=kind, value='Бензин')
        attr = ProductAttribute.objects.create(product=self.product, attribute_type=kind, attribute_value=value)
        call_command('load_equipment', stdout=StringIO())
        option.refresh_from_db()
        self.assertEqual(EquipmentOption.objects.count(), 61)
        self.assertEqual(EquipmentGroup.objects.count(), 4)
        self.assertEqual(option.name, 'Переименовано')
        self.assertFalse(option.is_active)
        self.assertEqual(option.sort_order, 500)
        self.assertEqual(list(self.product.equipment.all()), [option])
        attr.refresh_from_db()
        self.assertEqual(attr.attribute_value_id, value.pk)
        self.assertFalse(EquipmentOption.objects.filter(encar_standard_code__in=['002', '003']).exists())

    def test_both_forms_save_reopen_and_remove(self):
        kind = AttributeType.objects.create(name='Год', slug='year', data_type='choice')
        value = AttributeValue.objects.create(attribute_type=kind, value='2024')
        attr = ProductAttribute.objects.create(
            product=self.product, attribute_type=kind, attribute_value=value,
        )
        ids = list(EquipmentOption.objects.filter(encar_standard_code__in=['010', '034']).values_list('pk', flat=True))
        for form_type in (ProductForm, ProductModelForm):
            form = form_type(data=self.data(ids), instance=self.product)
            self.assertTrue(form.is_valid(), form.errors)
            form.save()
            reopened = form_type(instance=self.product)
            self.assertEqual(set(reopened['equipment'].value()), set(ids))
            self.assertIn('Экстерьер и интерьер', str(reopened['equipment']))
            self.assertIn('type="checkbox"', str(reopened['equipment']))
            form = form_type(data=self.data(), instance=self.product)
            self.assertTrue(form.is_valid(), form.errors)
            saved = form.save(commit=False)
            saved.save()
            form.save_m2m()
            self.assertFalse(self.product.equipment.exists())
            attr.refresh_from_db()
            self.assertEqual(attr.attribute_value_id, value.pk)

    def test_public_selected_only_empty_hidden_and_no_inferences(self):
        self.assertEqual(self.render_product().strip(), '')
        option = EquipmentOption.objects.get(encar_standard_code='034')
        self.product.equipment.add(option)
        html = self.render_product()
        self.assertIn('Комплектация', html)
        self.assertIn('Сиденья', html)
        self.assertIn(option.name, html)
        self.assertNotIn('Безопасность', html)
        self.assertNotIn('Вентиляция сиденья переднего пассажира', html)
        self.assertNotIn('Вентиляция сидений<', html)
        option.is_active = False
        option.save()
        self.assertEqual(self.render_product().strip(), '')

    def test_inactive_selections_retained_but_not_newly_assignable(self):
        option = EquipmentOption.objects.get(encar_standard_code='010')
        option.is_active = False
        option.save()
        form = ProductForm(data=self.data([option.pk]), instance=self.product)
        self.assertFalse(form.is_valid())
        self.product.equipment.add(option)
        form = ProductForm(data=self.data([option.pk]), instance=self.product)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertIn('(отключена)', str(ProductForm(instance=self.product)['equipment']))
        form = ProductForm(data=self.data(), instance=self.product)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(self.product.equipment.exists())

    def test_admin_form_and_manual_options(self):
        group = EquipmentGroup.objects.first()
        for name in ('Ручная 1', 'Ручная 2'):
            EquipmentOption.objects.create(group=group, name=name)
        request = RequestFactory().get('/')
        request.user = get_user_model().objects.create_superuser('admin', password='test')
        form_class = ProductAdmin(Product, admin.site).get_form(request, self.product)
        form = form_class(data=self.data(), instance=self.product)
        self.assertIn('equipment', form.fields)
        self.assertIn('Ручная 1', str(form['equipment']))

    def test_initial_seed_does_not_assign_any_options(self):
        self.assertFalse(self.product.equipment.exists())
