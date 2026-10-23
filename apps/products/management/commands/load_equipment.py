"""Seed only the supplied options.standard dictionary, preserving edits."""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.products.models import EquipmentGroup, EquipmentOption


class Command(BaseCommand):
    help = 'Добавить отсутствующие группы и опции комплектации Encar standard.'

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        path = Path(__file__).resolve().parents[2] / 'fixtures/equipment_standard.json'
        groups = json.loads(path.read_text(encoding='utf-8'))
        created = 0
        for index, data in enumerate(groups):
            group, _ = EquipmentGroup.objects.get_or_create(
                slug=data['slug'], defaults={'name': data['name'], 'sort_order': index},
            )
            for position, item in enumerate(data['options']):
                _, added = EquipmentOption.objects.get_or_create(
                    encar_standard_code=item['code'], defaults={
                        'name': item['name'], 'group': group, 'sort_order': position,
                    },
                )
                created += added
        self.stdout.write(self.style.SUCCESS(f'Добавлено опций: {created}.'))
