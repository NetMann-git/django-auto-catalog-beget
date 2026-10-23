"""Make a consistent SQLite backup before schema changes."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Сохранить SQLite в patch-backups перед миграциями.'
    requires_system_checks = []

    def handle(self, *args, **options) -> None:
        config = settings.DATABASES['default']
        if config['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('Команда предназначена только для SQLite.')
        source = Path(config['NAME']).resolve()
        if not source.is_file():
            raise CommandError('Файл SQLite не найден; миграции не запускайте.')
        folder = Path(settings.BASE_DIR) / 'patch-backups'
        folder.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        target = folder / f'before-82-45-{stamp}.sqlite3'
        try:
            with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as original:
                with sqlite3.connect(target) as backup:
                    original.backup(backup)
        except sqlite3.Error as error:
            raise CommandError('Не удалось создать резервную копию SQLite.') from error
        self.stdout.write(self.style.SUCCESS(f'Резервная копия: {target}'))
