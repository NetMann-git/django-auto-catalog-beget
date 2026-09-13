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
