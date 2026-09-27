"""Латинские адреса объектов, создаваемых через кабинет менеджера."""

from django.test import TestCase

from apps.products.attribute_forms import AttributeTypeForm
from apps.products.forms import BrandForm, ProductForm
from apps.products.manager_slugs import latin_slug
from apps.products.models import AttributeType, Brand, Product


class ManagerSlugsTests(TestCase):
    """Генерация без JavaScript, сохранение ручных и существующих адресов."""

    def test_transliteration_is_ascii_and_human_readable(self):
        self.assertEqual(latin_slug("Объём двигателя, л"), "obyom-dvigatelya-l")
        self.assertEqual(latin_slug("Чери Тигго 8 2022"), "cheri-tiggo-8-2022")

    def test_attribute_type_auto_slug_and_no_duplicate_url(self):
        form = AttributeTypeForm(data={
            "name": "Тип двигателя", "slug": "", "data_type": "choice",
        })
        self.assertTrue(form.is_valid(), form.errors)
        kind = form.save()
        self.assertEqual(kind.slug, "tip-dvigatelya")

        second = AttributeTypeForm(data={
            "name": "Тип-двигателя", "slug": "tip-dvigatelya",
            "data_type": "choice",
        })
        self.assertTrue(second.is_valid(), second.errors)
        self.assertEqual(second.save().slug, "tip-dvigatelya-2")

    def test_brand_auto_slug_or_manual_url(self):
        form = BrandForm(data={"name": "Чанган", "slug": "", "sort_order": 0})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().slug, "changan")
        manual = BrandForm(data={
            "name": "Чери", "slug": "chery-auto", "sort_order": 0,
        })
        self.assertTrue(manual.is_valid(), manual.errors)
        self.assertEqual(manual.save().slug, "chery-auto")

    def test_product_auto_slug_preserves_existing_address_on_edit(self):
        form = ProductForm(data={
            "title": "Чери Тигго 8 2022", "slug": "", "price": "2900000",
            "currency": "RUB", "availability_status": "in_stock",
        })
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save()
        self.assertEqual(product.slug, "cheri-tiggo-8-2022")

        updated = ProductForm(data={
            "title": "Чери Тигго 8 2022 рестайлинг", "slug": product.slug,
            "price": "2900000", "currency": "RUB",
            "availability_status": "in_stock",
        }, instance=product)
        self.assertTrue(updated.is_valid(), updated.errors)
        self.assertEqual(updated.save().slug, "cheri-tiggo-8-2022")

    def test_existing_type_slug_is_not_edited(self):
        kind = AttributeType.objects.create(
            name="Пробег", slug="mileage", data_type="number",
        )
        form = AttributeTypeForm(data={
            "name": "Пробег автомобиля", "data_type": "number",
        }, instance=kind)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().slug, "mileage")
