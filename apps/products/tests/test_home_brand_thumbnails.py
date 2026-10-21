"""Check actual bytes served by the home brand section."""
import re
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote

from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from PIL import Image

from apps.products.models import Brand


class HomeBrandThumbnailTests(TestCase):
    """Large transparent logos must render as cached small images."""

    def test_large_png_uses_transparent_thumbnail_in_all_layouts(self):
        with TemporaryDirectory() as directory, override_settings(
            MEDIA_ROOT=directory, MEDIA_URL='/media/', THUMBNAIL_DEBUG=True,
        ):
            content = BytesIO()
            Image.new('RGBA', (2400, 1200), (20, 40, 60, 128)).save(content, 'PNG')
            brand = Brand.objects.create(
                name='Проверка', slug='test-brand',
                logo=SimpleUploadedFile('large.png', content.getvalue(), 'image/png'),
            )
            html = render_to_string('home/sections/brands.html', {
                'featured_brands': [brand],
            })
            sources = re.findall(r'src="([^"]+)"', html)
            self.assertEqual(len(sources), 3)
            self.assertEqual(len(set(sources)), 1)
            self.assertNotIn(brand.logo.url, sources)
            thumbnail = Path(directory) / unquote(sources[0]).removeprefix('/media/')
            with Image.open(thumbnail) as image:
                self.assertEqual(image.size, (200, 100))
                self.assertEqual(image.mode, 'RGBA')
                self.assertEqual(image.getpixel((0, 0))[3], 128)
            with Image.open(brand.logo.path) as original:
                self.assertEqual(original.size, (2400, 1200))
            second = render_to_string('home/sections/brands.html', {
                'featured_brands': [brand],
            })
            self.assertEqual(sources, re.findall(r'src="([^"]+)"', second))
