"""Remove expired private ZIP previews (safe to run from cron)."""
from django.core.management.base import BaseCommand
from apps.products.encar_import.package import cleanup_expired


class Command(BaseCommand):
    help = 'Удалить временные предпросмотры пакетов Encar старше 30 минут.'

    def handle(self, *args, **options):
        self.stdout.write(f'Удалено предпросмотров: {cleanup_expired()}')
