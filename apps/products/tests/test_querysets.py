from django.test import TestCase

from apps.products.models import Product
from apps.products.querysets import CatalogQuerySet

from apps.products.models import AttributeType, AttributeValue

class CatalogQuerySetBaseTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.active_product = Product.objects.create(
            title="Активное платье",
            slug="active-dress",
            price=100000,
            is_active=True,
        )

        cls.inactive_product = Product.objects.create(
            title="Неактивное платье",
            slug="inactive-dress",
            price=100000,
            is_active=False,
        )

    def test_base_queryset_returns_only_active_products(self):
        result = CatalogQuerySet._base_queryset()

        self.assertIn(self.active_product, result)
        self.assertNotIn(self.inactive_product, result)


class CatalogQuerySetBaseProductTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Текущее платье",
            slug="current-dress",
            price=100000,
            is_active=True,
        )

        cls.similar_product = Product.objects.create(
            title="Похожее платье",
            slug="similar-dress",
            price=120000,
            is_active=True,
        )

        cls.inactive_product = Product.objects.create(
            title="Неактивное платье",
            slug="inactive-similar-dress",
            price=110000,
            is_active=False,
        )

    def test_excludes_current_product(self):
        result = CatalogQuerySet.base_product_queryset(
            self.product
        )

        self.assertNotIn(self.product, result)

    def test_returns_active_products(self):
        result = CatalogQuerySet.base_product_queryset(
            self.product
        )

        self.assertIn(self.similar_product, result)
        self.assertNotIn(self.inactive_product, result)


class CatalogQuerySetFeaturedTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.featured_1 = Product.objects.create(
            title="Featured 1",
            slug="featured-1",
            price=100000,
            is_active=True,
            is_featured=True,
        )

        cls.featured_2 = Product.objects.create(
            title="Featured 2",
            slug="featured-2",
            price=110000,
            is_active=True,
            is_featured=True,
        )

        cls.featured_3 = Product.objects.create(
            title="Featured 3",
            slug="featured-3",
            price=120000,
            is_active=True,
            is_featured=True,
        )

        cls.not_featured = Product.objects.create(
            title="Not Featured",
            slug="not-featured",
            price=130000,
            is_active=True,
            is_featured=False,
        )

        cls.inactive_featured = Product.objects.create(
            title="Inactive Featured",
            slug="inactive-featured",
            price=140000,
            is_active=False,
            is_featured=True,
        )

    def test_returns_only_active_featured_products(self):
        result = CatalogQuerySet.featured()

        self.assertIn(self.featured_1, result)
        self.assertIn(self.featured_2, result)
        self.assertIn(self.featured_3, result)

        self.assertNotIn(self.not_featured, result)
        self.assertNotIn(self.inactive_featured, result)

    def test_respects_limit(self):
        result = CatalogQuerySet.featured(limit=2)

        self.assertEqual(len(result), 2)

class CatalogQuerySetDistinctValuesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.color_type = AttributeType.objects.create(
            name="Цвет",
            slug="color",
        )

        cls.silhouette_type = AttributeType.objects.create(
            name="Силуэт",
            slug="silhouette",
        )

        AttributeValue.objects.create(
            attribute_type=cls.color_type,
            value="Белый",
        )

        AttributeValue.objects.create(
            attribute_type=cls.color_type,
            value="Красный",
        )

        AttributeValue.objects.create(
            attribute_type=cls.silhouette_type,
            value="A-line",
        )

    def test_returns_values_for_requested_attribute(self):
        result = list(
            CatalogQuerySet.distinct_values("color")
        )

        self.assertEqual(
            result,
            ["Белый", "Красный"],
        )

    def test_does_not_return_values_from_other_attribute_types(self):
        result = list(
            CatalogQuerySet.distinct_values("color")
        )

        self.assertNotIn("A-line", result)