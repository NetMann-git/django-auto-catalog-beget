# apps/products/tests/test_views.py
from django.test import TestCase
from django.urls import reverse

from apps.products.models import Product


class CatalogViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Василиса",
            slug="vasilisa",
            article="A001",
            price=100000,
            is_active=True,
        )

    def test_catalog_page_status(self):
        response = self.client.get(reverse("catalog:catalog"))
        self.assertEqual(response.status_code, 200)

    def test_catalog_page_contains_product(self):
        response = self.client.get(reverse("catalog:catalog"))
        self.assertContains(response, "Василиса")


class ProductDetailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            title="Василиса",
            slug="vasilisa",
            article="A001",
            price=100000,
            is_active=True,
        )

    def test_product_page_status(self):
        response = self.client.get(
            reverse("catalog:product_detail", kwargs={"slug": "vasilisa"})
        )
        self.assertEqual(response.status_code, 200)

    def test_product_page_contains_title(self):
        response = self.client.get(
            reverse("catalog:product_detail", kwargs={"slug": "vasilisa"})
        )
        self.assertContains(response, "Василиса")


class SearchTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Product.objects.create(
            title="Василиса",
            slug="vasilisa",
            article="A001",
            price=100000,
            is_active=True,
        )

    def test_search_icontains(self):
        response = self.client.get(
            reverse("catalog:catalog"),
            {"q": "василиса"},
        )
        self.assertContains(response, "Василиса")