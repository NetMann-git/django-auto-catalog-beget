"""Regression tests for free-entry attributes and choice validation."""

from django.forms import inlineformset_factory
from django.test import TestCase

from apps.products.models import (
    AttributeType, AttributeValue, Product, ProductAttribute,
)
from apps.products.product_attribute_forms import ProductAttributeForm


class TypedAttributeTests(TestCase):
    """Values remain compatible with existing catalog relations."""

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(title='Авто', slug='auto', price=1)
        cls.number = AttributeType.objects.create(
            name='Пробег', slug='mileage', data_type='number',
        )
        cls.choice = AttributeType.objects.create(
            name='Топливо', slug='fuel', data_type='choice',
        )
        cls.text = AttributeType.objects.create(
            name='Описание', slug='description', data_type='string',
        )

    def make_form(self, kind, value='', **extra):
        """Construct the same form used by manager and admin."""
        return ProductAttributeForm(
            {'attribute_type': kind.pk, 'free_value': value, **extra},
            instance=ProductAttribute(product=self.product),
        )

    def test_arbitrary_mileage(self):
        form = self.make_form(self.number, '45001')
        self.assertTrue(form.is_valid(), form.errors)
        result = form.save()
        self.assertEqual(result.attribute_value.value, '45001')

    def test_invalid_mileage(self):
        for raw in ('-1', '1.5', 'abc', '', 'NaN', 'Infinity'):
            with self.subTest(raw=raw):
                form = self.make_form(self.number, raw)
                self.assertFalse(form.is_valid())
                self.assertIn('free_value', form.errors)

    def test_zero(self):
        form = self.make_form(self.number, '0')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().attribute_value.value, '0')

    def test_decimal_number(self):
        self.number.slug = 'engine_volume'
        self.number.save()
        form = self.make_form(self.number, '1,50')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().attribute_value.value, '1.5')

    def test_free_text(self):
        form = self.make_form(self.text, 'Любой текст')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().attribute_value.value, 'Любой текст')

    def test_choice_validation(self):
        value = AttributeValue.objects.create(attribute_type=self.choice, value='Бензин')
        form = self.make_form(self.choice, attribute_value=value.pk)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().attribute_value, value)
        wrong = self.make_form(self.text, 'Текст', attribute_value=value.pk)
        self.assertTrue(wrong.is_valid(), wrong.errors)
        other = AttributeType.objects.create(name='Другой', slug='other', data_type='choice')
        self.assertFalse(self.make_form(other, attribute_value=value.pk).is_valid())
        self.assertFalse(self.make_form(other).is_valid())

    def test_edit_preserves_shared_value(self):
        old = AttributeValue.objects.create(attribute_type=self.number, value='100')
        instance = ProductAttribute.objects.create(
            product=self.product, attribute_type=self.number, attribute_value=old,
        )
        form = ProductAttributeForm(
            {'attribute_type': self.number.pk, 'free_value': '200'}, instance=instance,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().attribute_value.value, '200')
        old.refresh_from_db()
        self.assertEqual(old.value, '100')

    def test_admin_inline_and_widget(self):
        formset_class = inlineformset_factory(
            Product, ProductAttribute, form=ProductAttributeForm, extra=1,
        )
        formset = formset_class({
            'attributes-TOTAL_FORMS': '1', 'attributes-INITIAL_FORMS': '0',
            'attributes-0-attribute_type': str(self.number.pk),
            'attributes-0-free_value': '12345',
        }, instance=self.product, prefix='attributes')
        self.assertTrue(formset.is_valid(), formset.errors)
        self.assertEqual(formset.save()[0].attribute_value.value, '12345')
        rendered = ProductAttributeForm().as_p()
        self.assertIn('data-kind="number"', rendered)
        self.assertIn('data-attribute-input', rendered)

    def test_manager_creates_and_updates_number(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory
        from apps.products.views import product_attributes

        for raw in ('123', '456'):
            request = RequestFactory().post('/', {
                'attributes-TOTAL_FORMS': '1',
                'attributes-INITIAL_FORMS': str(self.product.attributes.count()),
                'attributes-0-id': str(self.product.attributes.first().pk)
                if self.product.attributes.exists() else '',
                'attributes-0-attribute_type': str(self.number.pk),
                'attributes-0-free_value': raw,
            })
            request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)
            request.session = {}
            request._messages = FallbackStorage(request)
            with patch('apps.products.views.redirect') as redirect:
                product_attributes(request, self.product.pk)
                redirect.assert_called_once()
            self.assertEqual(self.product.attributes.count(), 1)
            self.assertEqual(self.product.attributes.get().attribute_value.value, raw)

    def test_admin_uses_shared_form(self):
        from django.contrib.admin.sites import AdminSite
        from apps.products.admin import ProductAttributeInline, AttributeTypeAdmin

        self.assertIs(ProductAttributeInline.form, ProductAttributeForm)
        admin = AttributeTypeAdmin(AttributeType, AdminSite())
        self.assertEqual(admin.get_inlines(None, self.number), [])
        self.assertTrue(admin.get_inlines(None, self.choice))
