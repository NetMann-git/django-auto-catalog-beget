"""Home brand counts must match public catalog eligibility."""
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.template.loader import render_to_string

from apps.home.context import HomeContextBuilder
from apps.products.models import Brand, Product


class HomeBrandCountTests(TestCase):
    def test_count_excludes_unpublished_and_hides_empty_brands(self):
        visible = Brand.objects.create(name='Audi', slug='audi')
        hidden = Brand.objects.create(name='BMW', slug='bmw')
        Brand.objects.create(name='Empty', slug='empty')
        for index, (brand, active) in enumerate([
            (visible, True), (visible, True), (visible, False), (hidden, False),
        ]):
            Product.objects.create(
                title=f'Auto {index}', slug=f'auto-{index}', price=100,
                brand=brand, is_active=active,
            )
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        request.session = {}
        brands = list(HomeContextBuilder.build(request)['featured_brands'])
        self.assertEqual([(item.pk, item.catalog_count) for item in brands], [(visible.pk, 2)])
        # A logo-less brand must not leave a broken card in the section.
        html = render_to_string('home/sections/brands.html', {'featured_brands': brands})
        self.assertNotIn('class="home-brand-link"', html)
