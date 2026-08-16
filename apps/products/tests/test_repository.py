from django.test import TestCase

from apps.products.models import Brand, Product
from apps.products.repository import CatalogRepository
from apps.products.constants import AVAILABILITY_CHOICES

from django.core.cache import cache
from unittest.mock import patch

class CatalogRepositoryByBrandTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.brand_a = Brand.objects.create(
            name="Brand A",
            slug="brand-a",
        )

        cls.brand_b = Brand.objects.create(
            name="Brand B",
            slug="brand-b",
        )

        cls.product_a = Product.objects.create(
            title="Платье A",
            slug="dress-a",
            price=100000,
            is_active=True,
            brand=cls.brand_a,
        )

        cls.product_b = Product.objects.create(
            title="Платье B",
            slug="dress-b",
            price=120000,
            is_active=True,
            brand=cls.brand_b,
        )

        cls.inactive_product_a = Product.objects.create(
            title="Неактивное платье A",
            slug="inactive-dress-a",
            price=110000,
            is_active=False,
            brand=cls.brand_a,
        )

    def test_returns_products_of_selected_brand_only(self):
        result = CatalogRepository.by_brand(self.brand_a)

        self.assertIn(self.product_a, result)
        self.assertNotIn(self.product_b, result)

    def test_does_not_return_inactive_products(self):
        result = CatalogRepository.by_brand(self.brand_a)

        self.assertNotIn(self.inactive_product_a, result)

class CatalogRepositoryRelatedTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Текущее платье",
            slug="current-dress",
            price=100000,
            is_active=True,
        )

        cls.related_product = Product.objects.create(
            title="Похожее платье",
            slug="related-dress",
            price=120000,
            is_active=True,
        )

    def test_related_excludes_current_product(self):
        result = CatalogRepository.related(self.product)

        self.assertNotIn(self.product, result)

    def test_related_returns_other_active_products(self):
        result = CatalogRepository.related(self.product)

        self.assertIn(self.related_product, result)


class CatalogRepositoryFiltersTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(
            name="Brand A",
            slug="brand-a",
        )

        from apps.products.models import Category

        cls.category = Category.objects.create(
            title="Свадебные платья",
            slug="wedding-dresses",
        )

    def test_returns_expected_filter_keys(self):
        result = CatalogRepository.filters()

        expected_keys = {
            "silhouettes",
            "brands",
            "collections",
            "colors",
            "categories",
            "availabilities",
        }

        self.assertEqual(set(result.keys()), expected_keys)

    def test_contains_brands_and_categories(self):
        result = CatalogRepository.filters()

        self.assertIn(self.brand, result["brands"])
        self.assertIn(self.category, result["categories"])

    def test_contains_availabilities(self):
        result = CatalogRepository.filters()

        self.assertEqual(
            result["availabilities"],
            AVAILABILITY_CHOICES,
        )

class CatalogRepositoryFeaturedTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.featured_product = Product.objects.create(
            title="Избранное платье",
            slug="featured-dress",
            price=100000,
            is_active=True,
            is_featured=True,
        )

        cls.regular_product = Product.objects.create(
            title="Обычное платье",
            slug="regular-dress",
            price=120000,
            is_active=True,
            is_featured=False,
        )

    def test_returns_featured_products(self):
        result = CatalogRepository.featured()

        self.assertIn(self.featured_product, result)
        self.assertNotIn(self.regular_product, result)

    def test_respects_limit(self):
        result = CatalogRepository.featured(limit=1)

        self.assertEqual(len(result), 1)

class CatalogRepositoryCatalogCacheTest(TestCase):

    def setUp(self):
        cache.clear()

    def test_catalog_result_is_cached(self):
        with patch(
            "apps.products.repository.CatalogQuerySet.catalog_queryset"
        ) as mock_catalog:
            mock_catalog.return_value = Product.objects.none()

            CatalogRepository.catalog()
            CatalogRepository.catalog()

            mock_catalog.assert_called_once()       