"""Article identity, manager lookup and category rendering regressions."""
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.urls import reverse

from apps.products.forms import ProductForm
from apps.products.models import Category, Product, VehicleImportSource


class EncarArticlesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('articles-manager')
        self.user.profile.role = 'manager'
        self.user.profile.save()
        self.client.force_login(self.user)
        self.category = Category.objects.create(title='Авто из Кореи', slug='korea')
        self.product = Product.objects.create(
            title='Моя машина', slug='my-car', category=self.category,
            price=1234567, article='old', is_active=False,
        )
        self.source = VehicleImportSource.objects.create(
            product=self.product, listing_id='42510470', internal_vehicle_id='999',
            raw_json={}, source_url='https://fem.encar.com/cars/detail/42510470',
        )

    def test_category_and_manager_search(self):
        url = reverse('catalog:product_list_manage')
        self.assertContains(self.client.get(url), self.category.title)
        self.assertContains(self.client.get(url, {'search': self.category.title}), self.product.title)

    def test_lookup_uses_listing_id_and_offers_existing_gallery(self):
        url = reverse('catalog:import_encar')
        response = self.client.get(url, {'listing_id': '42510470'})
        self.assertContains(response, 'Добавить фотографии')
        self.assertContains(response, reverse('catalog:product_edit', args=[self.product.pk]) + '#product-gallery')
        self.assertIsNone(self.client.get(url, {'listing_id': '999'}).context['lookup_source'])
        self.assertEqual(Product.objects.count(), 1)
        self.client.logout()
        self.assertEqual(self.client.get(url, {'listing_id': '42510470'}).status_code, 302)

    def test_article_field_is_bound_to_source(self):
        form = ProductForm(instance=self.product)
        self.assertTrue(form.fields['article'].disabled)
        self.assertEqual(form['article'].value(), '42510470')
        self.product.refresh_from_db()
        self.assertEqual(self.product.article, 'old')  # GET is read-only.

    def test_sync_preview_apply_idempotence_and_backup(self):
        call_command('sync_encar_articles', stdout=StringIO())
        self.product.refresh_from_db()
        self.assertEqual(self.product.article, 'old')
        with patch('apps.products.management.commands.sync_encar_articles.call_command') as backup:
            call_command('sync_encar_articles', apply=True, stdout=StringIO())
            self.assertEqual(backup.call_args.args[0], 'backup_catalog_sqlite')
            call_command('sync_encar_articles', apply=True, stdout=StringIO())
        self.product.refresh_from_db()
        self.assertEqual(self.product.article, '42510470')
        self.assertEqual(self.product.price, 1234567)
        self.assertFalse(self.product.is_active)
        self.assertEqual(VehicleImportSource.objects.count(), 1)

    def test_conflict_does_not_merge_or_overwrite(self):
        Product.objects.create(title='Другая', slug='another', price=1, article='42510470')
        with patch('apps.products.management.commands.sync_encar_articles.call_command'):
            with self.assertRaises(CommandError):
                call_command('sync_encar_articles', apply=True, stdout=StringIO(), stderr=StringIO())
        self.product.refresh_from_db()
        self.assertEqual(self.product.article, 'old')
