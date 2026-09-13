from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.users.constants import ROLE_CUSTOMER, ROLE_MANAGER

from .models import ClientShowcase


class ClientShowcaseTests(TestCase):
    def create_user(self, username, role):
        user = get_user_model().objects.create_user(username=username, password="testpass123")
        user.profile.role = role
        user.profile.save(update_fields=("role",))
        return user

    def test_home_shows_only_published_clients(self):
        ClientShowcase.objects.create(name="Виден", vehicle="KIA", legacy_image="x.webp", is_published=True)
        ClientShowcase.objects.create(name="Скрыт", vehicle="BMW", legacy_image="y.webp", is_published=False)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Виден")
        self.assertNotContains(response, "Скрыт")

    def test_manager_can_open_client_management(self):
        user = self.create_user("manager_clients", ROLE_MANAGER)
        self.client.force_login(user)
        response = self.client.get(reverse("home:client_list_manage"))
        self.assertEqual(response.status_code, 200)

    def test_customer_cannot_open_client_management(self):
        user = self.create_user("customer_clients", ROLE_CUSTOMER)
        self.client.force_login(user)
        response = self.client.get(reverse("home:client_list_manage"))
        self.assertEqual(response.status_code, 302)

    def test_manager_can_reorder_all_clients(self):
        first = ClientShowcase.objects.create(name="Первый", vehicle="KIA", sort_order=10)
        second = ClientShowcase.objects.create(name="Второй", vehicle="BMW", sort_order=20)
        third = ClientShowcase.objects.create(name="Третий", vehicle="Audi", sort_order=30)

        user = self.create_user("manager_reorder", ROLE_MANAGER)
        self.client.force_login(user)
        response = self.client.post(
            reverse("home:client_reorder"),
            {"ordered_ids": f"{third.id},{first.id},{second.id}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(ClientShowcase.objects.values_list("id", flat=True)),
            [third.id, first.id, second.id],
        )

    def test_reorder_rejects_partial_list(self):
        first = ClientShowcase.objects.create(name="Первый", vehicle="KIA", sort_order=10)
        ClientShowcase.objects.create(name="Второй", vehicle="BMW", sort_order=20)

        user = self.create_user("manager_partial_reorder", ROLE_MANAGER)
        self.client.force_login(user)
        response = self.client.post(reverse("home:client_reorder"), {"ordered_ids": str(first.id)})

        self.assertEqual(response.status_code, 409)

    def test_manager_can_delete_client(self):
        client = ClientShowcase.objects.create(name="Удалить", vehicle="Volvo", sort_order=10)
        user = self.create_user("manager_delete", ROLE_MANAGER)
        self.client.force_login(user)

        response = self.client.post(reverse("home:client_delete", args=[client.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ClientShowcase.objects.filter(pk=client.id).exists())

    def test_superuser_can_open_client_management_without_admin_profile_role(self):
        user = get_user_model().objects.create_superuser(
            username="root_clients",
            email="root@example.com",
            password="testpass123",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("home:client_list_manage"))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_move_client_down_without_javascript(self):
        first = ClientShowcase.objects.create(name="Первый", vehicle="KIA", sort_order=10)
        second = ClientShowcase.objects.create(name="Второй", vehicle="BMW", sort_order=20)
        third = ClientShowcase.objects.create(name="Третий", vehicle="Audi", sort_order=30)

        user = self.create_user("manager_move", ROLE_MANAGER)
        self.client.force_login(user)
        response = self.client.post(
            reverse("home:client_move", args=[first.id]),
            {"direction": "down"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(ClientShowcase.objects.values_list("id", flat=True)),
            [second.id, first.id, third.id],
        )
