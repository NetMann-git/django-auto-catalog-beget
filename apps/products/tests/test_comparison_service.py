# apps/products/tests/test_comparison_service.py

from unittest.mock import Mock, patch

from django.test import TestCase

from apps.products.comparison_service import ComparisonService
from apps.products.models import Product


class ComparisonServiceGetProductsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product_a = Product.objects.create(
            title="Платье A",
            slug="dress-a",
            price=10000,
            is_active=True,
        )

        cls.product_b = Product.objects.create(
            title="Платье B",
            slug="dress-b",
            price=20000,
            is_active=True,
        )

        cls.product_c = Product.objects.create(
            title="Платье C",
            slug="dress-c",
            price=30000,
            is_active=True,
        )

        cls.inactive_product = Product.objects.create(
            title="Неактивное платье",
            slug="inactive-dress",
            price=40000,
            is_active=False,
        )

    def setUp(self):
        self.request = Mock()

    @patch(
        "apps.products.comparison_service.SessionService.get_comparison"
    )
    def test_returns_products_from_comparison(self, mock_get_comparison):
        mock_get_comparison.return_value = [
            self.product_a.id,
            self.product_b.id,
        ]

        result = ComparisonService.get_products(self.request)

        self.assertEqual(
            list(result),
            [
                self.product_a,
                self.product_b,
            ],
        )

    @patch(
        "apps.products.comparison_service.SessionService.get_comparison"
    )
    def test_preserves_comparison_order(self, mock_get_comparison):
        mock_get_comparison.return_value = [
            self.product_c.id,
            self.product_a.id,
            self.product_b.id,
        ]

        result = ComparisonService.get_products(self.request)

        self.assertEqual(
            list(result),
            [
                self.product_c,
                self.product_a,
                self.product_b,
            ],
        )

    @patch(
        "apps.products.comparison_service.SessionService.get_comparison"
    )
    def test_excludes_inactive_products(self, mock_get_comparison):
        mock_get_comparison.return_value = [
            self.product_a.id,
            self.inactive_product.id,
            self.product_b.id,
        ]

        result = ComparisonService.get_products(self.request)

        self.assertEqual(
            list(result),
            [
                self.product_a,
                self.product_b,
            ],
        )

    @patch(
        "apps.products.comparison_service.SessionService.get_comparison"
    )
    def test_ignores_missing_products(self, mock_get_comparison):
        missing_product_id = 999999

        mock_get_comparison.return_value = [
            self.product_a.id,
            missing_product_id,
            self.product_b.id,
        ]

        result = ComparisonService.get_products(self.request)

        self.assertEqual(
            list(result),
            [
                self.product_a,
                self.product_b,
            ],
        )

    @patch(
        "apps.products.comparison_service.SessionService.get_comparison"
    )
    def test_returns_empty_list_for_empty_comparison(
        self,
        mock_get_comparison,
    ):
        mock_get_comparison.return_value = []

        result = ComparisonService.get_products(self.request)

        self.assertEqual(list(result), [])

class ComparisonServiceGetAttributesRowsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        from apps.products.models import (
            AttributeType,
            AttributeValue,
            ProductAttribute,
        )

        cls.product_a = Product.objects.create(
            title="Платье A",
            slug="attributes-dress-a",
            price=10000,
            is_active=True,
        )

        cls.product_b = Product.objects.create(
            title="Платье B",
            slug="attributes-dress-b",
            price=20000,
            is_active=True,
        )

        cls.silhouette_type = AttributeType.objects.create(
            name="Силуэт",
            slug="silhouette-test",
        )

        cls.color_type = AttributeType.objects.create(
            name="Цвет",
            slug="color-test",
        )

        cls.a_line = AttributeValue.objects.create(
            attribute_type=cls.silhouette_type,
            value="А-силуэт",
        )

        cls.mermaid = AttributeValue.objects.create(
            attribute_type=cls.silhouette_type,
            value="Русалка",
        )

        cls.white = AttributeValue.objects.create(
            attribute_type=cls.color_type,
            value="Белый",
        )

        cls.ivory = AttributeValue.objects.create(
            attribute_type=cls.color_type,
            value="Айвори",
        )

        ProductAttribute.objects.create(
            product=cls.product_a,
            attribute_type=cls.silhouette_type,
            attribute_value=cls.a_line,
        )

        ProductAttribute.objects.create(
            product=cls.product_a,
            attribute_type=cls.color_type,
            attribute_value=cls.white,
        )

        ProductAttribute.objects.create(
            product=cls.product_b,
            attribute_type=cls.silhouette_type,
            attribute_value=cls.mermaid,
        )

        ProductAttribute.objects.create(
            product=cls.product_b,
            attribute_type=cls.color_type,
            attribute_value=cls.ivory,
        )

    def test_returns_attribute_rows_for_products(self):
        rows = ComparisonService.get_attributes_rows(
            [
                self.product_a,
                self.product_b,
            ]
        )

        self.assertEqual(len(rows), 2)

        rows_by_name = {
            row["name"]: row
            for row in rows
        }

        self.assertIn("Силуэт", rows_by_name)
        self.assertIn("Цвет", rows_by_name)

        self.assertEqual(
            rows_by_name["Силуэт"][self.product_a.id],
            "А-силуэт",
        )

        self.assertEqual(
            rows_by_name["Силуэт"][self.product_b.id],
            "Русалка",
        )

        self.assertEqual(
            rows_by_name["Цвет"][self.product_a.id],
            "Белый",
        )

        self.assertEqual(
            rows_by_name["Цвет"][self.product_b.id],
            "Айвори",
        )

    def test_missing_attribute_is_displayed_as_dash(self):
        from apps.products.models import ProductAttribute

        ProductAttribute.objects.filter(
            product=self.product_b,
            attribute_type=self.color_type,
        ).delete()

        self.product_b.refresh_from_db()

        rows = ComparisonService.get_attributes_rows(
            [
                self.product_a,
                self.product_b,
            ]
        )

        rows_by_name = {
            row["name"]: row
            for row in rows
        }

        self.assertEqual(
            rows_by_name["Цвет"][self.product_a.id],
            "Белый",
        )

        self.assertEqual(
            rows_by_name["Цвет"][self.product_b.id],
            "—",
        )

    def test_empty_products_returns_empty_list(self):
        result = ComparisonService.get_attributes_rows([])

        self.assertEqual(result, [])