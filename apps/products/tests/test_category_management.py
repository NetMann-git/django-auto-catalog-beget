"""Manager category lifecycle and access protection."""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from apps.products.models import Category, Product


class CategoryManagementTests(TestCase):
    """Exercise validation, authorization and safe deletion."""

    def setUp(self):
        self.manager = get_user_model().objects.create_user('manager')
        self.manager.profile.role = 'manager'
        self.manager.profile.save()
        self.client.force_login(self.manager)
        self.category = Category.objects.create(title='Седаны', slug='sedany')

    def test_create_and_edit(self):
        response = self.client.post(reverse('catalog:category_create'), {
            'title': 'Внедорожники', 'slug': '',
        })
        self.assertEqual(response.status_code, 302)
        category = Category.objects.get(title='Внедорожники')
        self.assertEqual(category.slug, 'vnedorozhniki')
        response = self.client.post(reverse('catalog:category_edit', args=[category.pk]), {
            'title': 'Кроссоверы', 'slug': category.slug,
        })
        self.assertEqual(response.status_code, 302)
        category.refresh_from_db()
        self.assertEqual(category.title, 'Кроссоверы')

    def test_duplicate_rejected(self):
        response = self.client.post(reverse('catalog:category_create'), {
            'title': 'Седаны', 'slug': 'another',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Category.objects.count(), 1)

    def test_delete_requires_post_and_empty_category(self):
        url = reverse('catalog:category_delete', args=[self.category.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        car = Product.objects.create(title='Авто', slug='auto', category=self.category, price=1000000)
        self.client.post(url)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        self.assertTrue(Product.objects.filter(pk=car.pk).exists())
        car.delete()
        self.client.post(url)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_access_and_csrf(self):
        customer = get_user_model().objects.create_user('customer')
        for user in (None, customer):
            self.client.logout()
            if user:
                self.client.force_login(user)
            for name, args in (
                ('category_list_manage', []), ('category_create', []),
                ('category_edit', [self.category.pk]),
                ('category_delete', [self.category.pk]),
            ):
                self.assertEqual(self.client.get(reverse('catalog:' + name, args=args)).status_code, 302)
            self.client.post(reverse('catalog:category_delete', args=[self.category.pk]))
            self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.manager)
        self.assertEqual(strict.post(reverse('catalog:category_create'), {'title': 'Test'}).status_code, 403)

    def test_pages_render(self):
        for name, args in (
            ('category_list_manage', []), ('category_create', []),
            ('category_edit', [self.category.pk]),
        ):
            self.assertEqual(self.client.get(reverse('catalog:' + name, args=args)).status_code, 200)
