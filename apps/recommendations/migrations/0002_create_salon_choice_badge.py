# apps/recommendations/migrations/0002_create_salon_choice_badge.py
from django.db import migrations


def create_badge(apps, schema_editor):
    Badge = apps.get_model('products', 'Badge')
    Badge.objects.get_or_create(
        slug='salon-choice',
        defaults={'title': 'Выбор салона'},
    )


def remove_badge(apps, schema_editor):
    Badge = apps.get_model('products', 'Badge')
    Badge.objects.filter(slug='salon-choice').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('recommendations', '0001_initial'),  # замените на вашу предыдущую миграцию
    ]

    operations = [
        migrations.RunPython(create_badge, remove_badge),
    ]