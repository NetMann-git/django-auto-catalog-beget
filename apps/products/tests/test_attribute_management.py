"""Права менеджера и сохранность справочника характеристик."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.users.constants import ROLE_MANAGER

from apps.products.models import (
    AttributeType, AttributeValue, Product, ProductAttribute,
)


class AttributeManagementTests(TestCase):
    """Менеджер без Django Admin управляет типами и значениями."""

    def setUp(self):
        self.manager = get_user_model().objects.create_user(
            username="attribute-manager", password="test-pass",
        )
        self.manager.profile.role = ROLE_MANAGER
        self.manager.profile.save()
        self.assertFalse(self.manager.is_staff)
        self.list_url = reverse("catalog:attribute_type_list_manage")

    def test_manager_can_open_list_from_dashboard(self):
        self.client.force_login(self.manager)
        dashboard = self.client.get(reverse("users:manager_dashboard"))
        self.assertContains(dashboard, self.list_url)
        self.assertNotContains(dashboard, "/admin/products/attributetype/")
        self.assertEqual(self.client.get(self.list_url).status_code, 200)

    def test_customer_cannot_open_or_create_types(self):
        customer = get_user_model().objects.create_user(
            username="customer", password="test-pass",
        )
        self.client.force_login(customer)
        self.assertRedirects(
            self.client.get(self.list_url), reverse("users:dashboard"),
        )
        self.client.post(reverse("catalog:attribute_type_create"), {
            "name": "Год выпуска", "slug": "year", "data_type": "choice",
        })
        self.assertFalse(AttributeType.objects.exists())

    def test_manager_creates_type_and_values_and_edits_value(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("catalog:attribute_type_create"), {
            "name": "Тип двигателя", "slug": "engine_type",
            "data_type": "choice",
        })
        attribute_type = AttributeType.objects.get(slug="engine_type")
        self.assertRedirects(response, reverse(
            "catalog:attribute_type_edit", args=[attribute_type.pk],
        ))
        self.client.post(reverse(
            "catalog:attribute_value_create", args=[attribute_type.pk],
        ), {"value": "Бензин", "sort_order": 1})
        value = AttributeValue.objects.get(attribute_type=attribute_type)
        self.assertEqual(value.value, "Бензин")
        self.client.post(reverse(
            "catalog:attribute_value_edit", args=[attribute_type.pk, value.pk],
        ), {"value": "Дизель", "sort_order": 2})
        value.refresh_from_db()
        self.assertEqual(value.value, "Дизель")

    def test_slug_cannot_change_after_creation(self):
        self.client.force_login(self.manager)
        kind = AttributeType.objects.create(
            name="Пробег", slug="mileage", data_type="number",
        )
        self.client.post(reverse("catalog:attribute_type_edit", args=[kind.pk]), {
            "name": "Пробег, км", "slug": "changed", "data_type": "number",
        })
        kind.refresh_from_db()
        self.assertEqual(kind.name, "Пробег, км")
        self.assertEqual(kind.slug, "mileage")

    def test_used_value_and_type_cannot_be_deleted(self):
        self.client.force_login(self.manager)
        kind = AttributeType.objects.create(name="Пробег", slug="mileage")
        value = AttributeValue.objects.create(
            attribute_type=kind, value="50000",
        )
        product = Product.objects.create(
            title="Автомобиль", slug="sample-auto", price=100000,
        )
        ProductAttribute.objects.create(
            product=product, attribute_type=kind, attribute_value=value,
        )
        self.client.post(reverse(
            "catalog:attribute_value_delete", args=[kind.pk, value.pk],
        ))
        self.client.post(reverse("catalog:attribute_type_delete", args=[kind.pk]))
        self.assertTrue(AttributeValue.objects.filter(pk=value.pk).exists())
        self.assertTrue(AttributeType.objects.filter(pk=kind.pk).exists())
