"""Matching is identical for previews and submissions, on either DB backend."""
import json
from pathlib import Path

from django.http import QueryDict
from django.test import TestCase

from apps.products.encar_import.forms import ImportForm
from apps.products.encar_import.parser import parse
from apps.products.models import AttributeType, AttributeValue, Product


class EncarMatchingTests(TestCase):
    def setUp(self):
        raw = json.loads((Path(__file__).parent / 'fixtures/encar_car_info.json').read_text(encoding='utf-8-sig'))
        self.proposal = parse(raw)
        self.product = Product.objects.create(title='Ручная', slug='manual', price=1)

    def form(self, data_type='choice', value='SUV', selected='', text='', apply=True):
        kind, _ = AttributeType.objects.get_or_create(
            slug='body_type', defaults={'name': 'Тип кузова', 'data_type': data_type},
        )
        self.proposal['specs'] = [{'label': kind.name, 'value': value, 'slugs': [kind.slug]}]
        data = QueryDict('', mutable=True)
        data.update(token='test', equipment_mode='keep', attr_0_type=str(kind.pk),
                    attr_0_choice=selected, attr_0_text=text)
        if apply:
            data['attr_0_apply'] = 'on'
        data._mutable = False
        form = ImportForm(data=data, proposal=self.proposal, product=self.product)
        return form, kind, data

    def test_empty_choice_filled_and_post_not_modified(self):
        kind = AttributeType.objects.create(name='Тип кузова', slug='body_type', data_type='choice')
        value = AttributeValue.objects.create(attribute_type=kind, value='SUV')
        form, _, post = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['attr_0_choice'], value)
        self.assertEqual(post['attr_0_choice'], '')
        self.assertEqual(form['attr_0_choice'].value(), str(value.pk))

    def test_manual_choice_has_priority(self):
        kind = AttributeType.objects.create(name='Тип кузова', slug='body_type', data_type='choice')
        AttributeValue.objects.create(attribute_type=kind, value='SUV')
        manual = AttributeValue.objects.create(attribute_type=kind, value='RV')
        form, _, _ = self.form(selected=str(manual.pk))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['attr_0_choice'], manual)

    def test_unicode_case_and_spaces(self):
        kind = AttributeType.objects.create(name='Тип кузова', slug='body_type', data_type='choice')
        value = AttributeValue.objects.create(attribute_type=kind, value='Средний класс')
        form, _, _ = self.form(value='  СРЕДНИЙ\u00a0  КЛАСС ')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['attr_0_choice'], value)

    def test_ambiguous_match_requires_choice(self):
        kind = AttributeType.objects.create(name='Тип кузова', slug='body_type', data_type='choice')
        for text in ('SUV', ' SUV '):
            AttributeValue.objects.create(attribute_type=kind, value=text)
        form, _, _ = self.form()
        self.assertFalse(form.is_valid())
        self.assertIn('attr_0_choice', form.errors)

    def test_numeric_value_filled_and_saved_without_duplicate(self):
        for _ in range(2):
            form, kind, _ = self.form(data_type='number', value='125,5')
            self.assertTrue(form.is_valid(), form.errors)
            attr = form.attribute_forms[0].save(commit=False)
            attr.product = self.product
            attr.save()
        self.assertEqual(self.product.attributes.count(), 1)
        self.assertEqual(AttributeValue.objects.filter(attribute_type=kind).count(), 1)
        self.assertEqual(self.product.attributes.get().attribute_value.value, '125.5')

    def test_text_filled_and_manual_text_preserved(self):
        form, _, _ = self.form(data_type='text', value='Из файла')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.attribute_forms[0].cleaned_data['free_value'], 'Из файла')
        form, _, _ = self.form(data_type='text', value='Из файла', text='Ручной текст')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.attribute_forms[0].cleaned_data['free_value'], 'Ручной текст')

    def test_invalid_number_is_not_guessed(self):
        form, _, _ = self.form(data_type='number', value='неизвестно')
        self.assertFalse(form.is_valid())
        self.assertIn('attr_0_text', form.errors)

    def test_unchecked_attribute_not_applied(self):
        form, _, _ = self.form(data_type='text', value='Из файла', apply=False)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.attribute_forms, [])
        self.assertFalse(self.product.attributes.exists())
