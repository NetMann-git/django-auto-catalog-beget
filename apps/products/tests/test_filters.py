from django.test import RequestFactory, TestCase

from apps.products.filters import CatalogFilter
from apps.products.models import Category, Product


class CatalogFilterCategoryTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category_a = Category.objects.create(
            title="Свадебные платья",
            slug="wedding-dresses",
        )

        cls.category_b = Category.objects.create(
            title="Вечерние платья",
            slug="evening-dresses",
        )

        cls.product_a = Product.objects.create(
            title="Платье А",
            slug="dress-a",
            price=100000,
            category=cls.category_a,
        )

        cls.product_b = Product.objects.create(
            title="Платье Б",
            slug="dress-b",
            price=200000,
            category=cls.category_b,
        )

    def test_category_filter_returns_only_selected_category(self):
        request = RequestFactory().get(
            "/catalog/",
            {"category": str(self.category_a.pk)},
        )

        catalog_filter = CatalogFilter(request.GET)

        queryset = Product.objects.all()
        result = catalog_filter.apply(queryset)

        self.assertIn(self.product_a, result)
        self.assertNotIn(self.product_b, result)