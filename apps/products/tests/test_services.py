# apps/products/tests/test_services.py
from django.test import TestCase

from apps.products.models import Product
from apps.products.services import ProductService


class ProductServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Платье 1",
            slug="dress-1",
            article="A001",
            collection="Premium",
            silhouette="A-line",
            price=100,
            is_active=True,
        )

        Product.objects.create(
            title="Платье 2",
            slug="dress-2",
            article="A002",
            collection="Premium",
            silhouette="A-line",
            price=200,
            is_active=True,
        )

        Product.objects.create(
            title="Платье 3",
            slug="dress-3",
            article="A003",
            collection="Classic",
            silhouette="A-line",
            price=300,
            is_active=True,
        )

    def test_similar_products_length(self):
        products = ProductService.get_similar_products(self.product)
        # Должен вернуть хотя бы 1 товар (Платье 2)
        self.assertGreaterEqual(len(products), 1)

    def test_similar_products_not_include_self(self):
        products = ProductService.get_similar_products(self.product)
        self.assertNotIn(self.product, products)