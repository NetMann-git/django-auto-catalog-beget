"""List orphaned product images, or delete them when explicitly requested."""

import os
from pathlib import PurePosixPath

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from easy_thumbnails.models import Thumbnail

from apps.products.image_cleanup import delete_unused_image, referenced_files
from apps.products.models import ProductGalleryImage


class Command(BaseCommand):
    """Keep active images and their thumbnails while cleaning product media."""

    help = 'Поиск неиспользуемых фото в media/products; удаление только с --delete.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--delete', action='store_true', help='Удалить найденные файлы.')

    def handle(self, *args, **options) -> None:
        references = referenced_files()
        protected = references | set(Thumbnail.objects.filter(
            source__name__in=references,
        ).values_list('name', flat=True))
        candidates = []
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif',
                      '.bmp', '.tif', '.tiff', '.heic', '.heif', '.ico'}

        def scan(directory: str) -> None:
            """Inspect only product media, without following local symlinks."""
            try:
                if os.path.islink(default_storage.path(directory)):
                    return
            except NotImplementedError:
                pass
            try:
                directories, files = default_storage.listdir(directory)
            except FileNotFoundError:
                return
            for filename in files:
                name = f'{directory}/{filename}'
                if PurePosixPath(name).suffix.lower() not in extensions:
                    continue
                if name in protected:
                    continue
                # Keep old-style thumbnails even when their cache entry is absent.
                if any(name.startswith(original + '.') for original in references):
                    continue
                candidates.append(name)
            for child in directories:
                scan(f'{directory}/{child}')

        scan('products')
        for name in sorted(candidates):
            self.stdout.write(name)
        self.stdout.write(f'Найдено неиспользуемых файлов: {len(candidates)}.')
        if not options['delete']:
            self.stdout.write('Файлы не удалены. Для удаления добавьте --delete.')
            return
        deleted = 0
        for name in candidates:
            # Recheck current references before deleting each file.
            if default_storage.exists(name) and delete_unused_image(
                ProductGalleryImage(), name,
            ):
                deleted += 1
        self.stdout.write(self.style.SUCCESS(f'Удалено файлов: {deleted}.'))
