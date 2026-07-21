# apps/products/tests/test_models.py
from django.test import TestCase

from apps.products.models import Product


class ProductModelTest(TestCase):

    def test_create_product(self):
        product = Product.objects.create(
            title="Василиса",
            slug="vasilisa",
            article="A001",
            price=100000,
            is_active=True,
        )

        self.assertEqual(product.title, "Василиса")
        self.assertEqual(product.slug, "vasilisa")
        self.assertTrue(product.is_active)

    def test_product_absolute_url(self):
        product = Product.objects.create(
            title="Тест",
            slug="test-slug",
            price=100,
            is_active=True,
        )
        url = product.get_absolute_url()
        self.assertEqual(url, "/catalog/test-slug/")  # проверяем формат URL