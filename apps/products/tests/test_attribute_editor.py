"""Editing existing manager attribute rows, ordering and ownership checks."""

from django.test import TestCase

from apps.products.attribute_formsets import ManagerAttributeFormSet
from apps.products.models import (
    AttributeType, AttributeValue, Product, ProductAttribute,
)


class AttributeEditorTests(TestCase):
    """Check database effects rather than only form presentation."""

    def setUp(self) -> None:
        self.product = Product.objects.create(title='Авто', slug='auto', price=1)
        self.kind = AttributeType.objects.create(
            name='Пробег', slug='mileage', data_type='number',
        )
        value = AttributeValue.objects.create(attribute_type=self.kind, value='100')
        self.attribute = ProductAttribute.objects.create(
            product=self.product, attribute_type=self.kind,
            attribute_value=value, sort_order=5,
        )

    def data(self, **changes) -> dict:
        """Build a normal submitted existing row."""
        data = {
            'attributes-TOTAL_FORMS': '1', 'attributes-INITIAL_FORMS': '1',
            'attributes-0-id': str(self.attribute.pk),
            'attributes-0-attribute_type': str(self.kind.pk),
            'attributes-0-free_value': '25000',
            'attributes-0-sort_order': '2',
        }
        data.update(changes)
        return data

    def test_updates_value_and_order_without_recreating_row(self):
        formset = ManagerAttributeFormSet(self.data(), instance=self.product)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        self.attribute.refresh_from_db()
        self.assertEqual(self.attribute.attribute_value.value, '25000')
        self.assertEqual(self.attribute.sort_order, 2)
        self.assertEqual(self.product.attributes.count(), 1)

    def test_change_type_to_choice(self):
        kind = AttributeType.objects.create(name='Топливо', slug='fuel', data_type='choice')
        value = AttributeValue.objects.create(attribute_type=kind, value='Бензин')
        formset = ManagerAttributeFormSet(self.data(**{
            'attributes-0-attribute_type': str(kind.pk),
            'attributes-0-attribute_value': str(value.pk),
        }), instance=self.product)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        self.attribute.refresh_from_db()
        self.assertEqual(self.attribute.attribute_type, kind)
        self.assertEqual(self.attribute.attribute_value, value)

    def test_delete_and_add(self):
        kind = AttributeType.objects.create(
            name='Описание', slug='description', data_type='string',
        )
        formset = ManagerAttributeFormSet(self.data(**{
            'attributes-TOTAL_FORMS': '2', 'attributes-0-DELETE': 'on',
            'attributes-1-attribute_type': str(kind.pk),
            'attributes-1-free_value': '500', 'attributes-1-sort_order': '0',
        }), instance=self.product)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        self.assertFalse(ProductAttribute.objects.filter(pk=self.attribute.pk).exists())
        self.assertEqual(self.product.attributes.get().attribute_value.value, '500')

    def test_invalid_order_and_duplicate_type(self):
        for changes in (
            {'attributes-0-sort_order': '-1'},
            {'attributes-TOTAL_FORMS': '2',
             'attributes-1-attribute_type': str(self.kind.pk),
             'attributes-1-free_value': '500'},
        ):
            formset = ManagerAttributeFormSet(self.data(**changes), instance=self.product)
            self.assertFalse(formset.is_valid())
            self.attribute.refresh_from_db()
            self.assertEqual(self.attribute.attribute_value.value, '100')

    def test_reject_foreign_row_even_when_marked_for_deletion(self):
        other = Product.objects.create(title='Другой', slug='other', price=2)
        foreign = ProductAttribute.objects.create(
            product=other, attribute_type=self.kind,
            attribute_value=self.attribute.attribute_value,
        )
        formset = ManagerAttributeFormSet(self.data(**{
            'attributes-0-id': str(foreign.pk), 'attributes-0-DELETE': 'on',
        }), instance=self.product)
        self.assertFalse(formset.is_valid())
        self.assertTrue(ProductAttribute.objects.filter(pk=foreign.pk).exists())

    def test_blank_extra_row_is_ignored(self):
        formset = ManagerAttributeFormSet(self.data(**{
            'attributes-TOTAL_FORMS': '2', 'attributes-1-sort_order': '0',
        }), instance=self.product)
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        self.assertEqual(self.product.attributes.count(), 1)
