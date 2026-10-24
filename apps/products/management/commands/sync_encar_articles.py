"""Preview or synchronize articles from existing, authoritative Encar links."""
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from apps.products.cache import CatalogCache
from apps.products.models import Product, VehicleImportSource


class Command(BaseCommand):
    help = 'Сопоставить артикулы с ID исходных объявлений Encar; без --apply только отчёт.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options) -> None:
        if options['apply'] and settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            call_command('backup_catalog_sqlite', stdout=self.stdout)
        with transaction.atomic():
            if options['apply']:
                # Acquire the SQLite write lock before inspecting identities.
                Product.objects.filter(import_sources__source='encar').update(id=F('id'))
            sources = list(VehicleImportSource.objects.filter(source='encar').select_related('product'))
            product_ids = [source.product_id for source in sources]
            changes = []
            conflicts = []
            for source in sources:
                product = source.product
                if product_ids.count(product.pk) != 1:
                    conflicts.append(f'Карточка {product.pk}: несколько ID Encar.')
                    continue
                if Product.objects.filter(article=source.listing_id).exclude(pk=product.pk).exists():
                    conflicts.append(f'Карточка {product.pk}: артикул {source.listing_id} занят другой карточкой.')
                    continue
                if product.article != source.listing_id:
                    changes.append((product, source.listing_id))
                    self.stdout.write(f'{product.pk}: {product.article or "(пусто)"} → {source.listing_id}')
            for message in conflicts:
                self.stderr.write(message)
            self.stdout.write(f'Изменений: {len(changes)}. Конфликтов: {len(conflicts)}.')
            if conflicts and options['apply']:
                raise CommandError('Изменения отменены. Сначала устраните конфликты артикулов/связей.')
            if options['apply']:
                for product, article in changes:
                    Product.objects.filter(pk=product.pk).update(article=article)
                transaction.on_commit(CatalogCache.clear_catalog)
                self.stdout.write(self.style.SUCCESS('Артикулы синхронизированы.'))
            else:
                self.stdout.write('Данные не изменены. Для применения: --apply.')
