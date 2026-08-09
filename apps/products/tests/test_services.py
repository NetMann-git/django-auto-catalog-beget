# apps/products/tests/test_services.py
from django.test import TestCase

from apps.products.models import (
    Product,
    AttributeType,
    AttributeValue,
    ProductAttribute,
)
from apps.products.services import ProductService

from django.core.cache import cache


class ProductServiceTest(TestCase):

    def setUp(self):
        cache.clear()

    @classmethod
    def setUpTestData(cls):
        cls.collection_type = AttributeType.objects.create(
            name="Коллекция",
            slug="collection",
            data_type="string",
        )

        cls.silhouette_type = AttributeType.objects.create(
            name="Силуэт",
            slug="silhouette",
            data_type="string",
        )

        cls.premium = AttributeValue.objects.create(
            attribute_type=cls.collection_type,
            value="Premium",
        )

        cls.classic = AttributeValue.objects.create(
            attribute_type=cls.collection_type,
            value="Classic",
        )

        cls.a_line = AttributeValue.objects.create(
            attribute_type=cls.silhouette_type,
            value="A-line",
        )

        cls.mermaid = AttributeValue.objects.create(
            attribute_type=cls.silhouette_type,
            value="Mermaid",
        )

        cls.product = Product.objects.create(
            title="Платье 1",
            slug="dress-1",
            article="A001",
            price=100,
            is_active=True,
        )

        cls.similar_product = Product.objects.create(
            title="Платье 2",
            slug="dress-2",
            article="A002",
            price=200,
            is_active=True,
        )

        cls.different_collection = Product.objects.create(
            title="Платье 3",
            slug="dress-3",
            article="A003",
            price=300,
            is_active=True,
        )

        cls.different_silhouette = Product.objects.create(
            title="Платье 4",
            slug="dress-4",
            article="A004",
            price=400,
            is_active=True,
        )

        ProductAttribute.objects.create(
            product=cls.product,
            attribute_type=cls.collection_type,
            attribute_value=cls.premium,
        )

        ProductAttribute.objects.create(
            product=cls.product,
            attribute_type=cls.silhouette_type,
            attribute_value=cls.a_line,
        )

        ProductAttribute.objects.create(
            product=cls.similar_product,
            attribute_type=cls.collection_type,
            attribute_value=cls.premium,
        )

        ProductAttribute.objects.create(
            product=cls.similar_product,
            attribute_type=cls.silhouette_type,
            attribute_value=cls.a_line,
        )

        ProductAttribute.objects.create(
            product=cls.different_collection,
            attribute_type=cls.collection_type,
            attribute_value=cls.classic,
        )

        ProductAttribute.objects.create(
            product=cls.different_collection,
            attribute_type=cls.silhouette_type,
            attribute_value=cls.a_line,
        )

        ProductAttribute.objects.create(
            product=cls.different_silhouette,
            attribute_type=cls.collection_type,
            attribute_value=cls.premium,
        )

        ProductAttribute.objects.create(
            product=cls.different_silhouette,
            attribute_type=cls.silhouette_type,
            attribute_value=cls.mermaid,
        )

    def test_similar_products_returns_matching_product(self):
        products = ProductService.get_similar_products(self.product)

        self.assertIn(self.similar_product, products)


    def test_similar_products_not_include_self(self):
        products = ProductService.get_similar_products(self.product)

        self.assertNotIn(self.product, products)


    def test_similar_products_includes_same_collection(self):
        products = ProductService.get_similar_products(self.product)

        self.assertIn(self.different_silhouette, products)


    def test_similar_products_includes_same_silhouette(self):
        products = ProductService.get_similar_products(self.product)

        self.assertIn(self.different_collection, products)


    def test_similar_products_respects_limit(self):
        products = ProductService.get_similar_products(
            self.product,
            limit=1,
        )

        self.assertLessEqual(len(products), 1)
        