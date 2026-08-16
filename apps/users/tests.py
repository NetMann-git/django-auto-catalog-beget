from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .constants import (
    ROLE_ADMIN,
    ROLE_CONSULTANT,
    ROLE_CUSTOMER,
    ROLE_MANAGER,
)
from .decorators import role_required
from .models import Profile

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

class ProfileTests(TestCase):

    def test_profile_created_automatically_for_new_user(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.assertTrue(
            Profile.objects.filter(user=user).exists()
        )

    def test_new_profile_has_customer_role(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.assertEqual(
            user.profile.role,
            ROLE_CUSTOMER,
        )


class RoleRequiredTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        def test_view(request):
            from django.http import HttpResponse
            return HttpResponse("OK")

        self.test_view = test_view

    def create_user(self, username, role=None):
        user = User.objects.create_user(
            username=username,
            password="testpass123",
        )

        if role is not None:
            user.profile.role = role
            user.profile.save()

        return user

    def test_anonymous_user_redirected_to_login(self):
        request = self.factory.get("/test/")
        request = self.prepare_request(
            request,
            AnonymousUser(),
        )

        protected_view = role_required(ROLE_ADMIN)(
            self.test_view
        )

        response = protected_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("users:login"),
        )

    def test_customer_denied_from_admin_view(self):
        user = self.create_user(
            "customer",
            ROLE_CUSTOMER,
        )

        request = self.factory.get("/test/")
        request = self.prepare_request(
            request,
            user,
        )

        protected_view = role_required(ROLE_ADMIN)(
            self.test_view
        )

        response = protected_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("users:dashboard"),
        )

    def test_allowed_role_can_access_view(self):
        user = self.create_user(
            "admin",
            ROLE_ADMIN,
        )

        request = self.factory.get("/test/")
        request = self.prepare_request(
            request,
            user,
        )

        protected_view = role_required(ROLE_ADMIN)(
            self.test_view
        )

        response = protected_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")


    def prepare_request(self, request, user):
        request.user = user

        session_middleware = SessionMiddleware(lambda request: None)
        session_middleware.process_request(request)
        request.session.save()

        message_middleware = MessageMiddleware(lambda request: None)
        message_middleware.process_request(request)

        return request



class DashboardAccessTests(TestCase):

    def create_user(self, username, role):
        user = User.objects.create_user(
            username=username,
            password="testpass123",
        )

        user.profile.role = role
        user.profile.save()

        return user

    def login_as(self, username):
        self.client.login(
            username=username,
            password="testpass123",
        )

    def test_customer_can_access_dashboard(self):
        self.create_user("customer", ROLE_CUSTOMER)
        self.login_as("customer")

        response = self.client.get(
            reverse("users:dashboard")
        )

        self.assertEqual(response.status_code, 200)

    def test_customer_cannot_access_consultant_dashboard(self):
        self.create_user("customer", ROLE_CUSTOMER)
        self.login_as("customer")

        response = self.client.get(
            reverse("users:consultant_dashboard")
        )

        self.assertRedirects(
            response,
            reverse("users:dashboard"),
        )

    def test_customer_cannot_access_manager_dashboard(self):
        self.create_user("customer", ROLE_CUSTOMER)
        self.login_as("customer")

        response = self.client.get(
            reverse("users:manager_dashboard")
        )

        self.assertRedirects(
            response,
            reverse("users:dashboard"),
        )

    def test_consultant_can_access_consultant_dashboard(self):
        self.create_user("consultant", ROLE_CONSULTANT)
        self.login_as("consultant")

        response = self.client.get(
            reverse("users:consultant_dashboard")
        )

        self.assertEqual(response.status_code, 200)

    def test_consultant_cannot_access_manager_dashboard(self):
        self.create_user("consultant", ROLE_CONSULTANT)
        self.login_as("consultant")

        response = self.client.get(
            reverse("users:manager_dashboard")
        )

        self.assertRedirects(
            response,
            reverse("users:dashboard"),
        )

    def test_manager_can_access_consultant_dashboard(self):
        self.create_user("manager", ROLE_MANAGER)
        self.login_as("manager")

        response = self.client.get(
            reverse("users:consultant_dashboard")
        )

        self.assertEqual(response.status_code, 200)

    def test_manager_can_access_manager_dashboard(self):
        self.create_user("manager", ROLE_MANAGER)
        self.login_as("manager")

        response = self.client.get(
            reverse("users:manager_dashboard")
        )

        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_consultant_dashboard(self):
        self.create_user("admin", ROLE_ADMIN)
        self.login_as("admin")

        response = self.client.get(
            reverse("users:consultant_dashboard")
        )

        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_manager_dashboard(self):
        self.create_user("admin", ROLE_ADMIN)
        self.login_as("admin")

        response = self.client.get(
            reverse("users:manager_dashboard")
        )

        self.assertEqual(response.status_code, 200)