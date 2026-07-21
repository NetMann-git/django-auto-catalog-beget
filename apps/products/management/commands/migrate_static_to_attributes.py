# apps/products/management/commands/migrate_static_to_attributes.py

from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductAttribute, AttributeType


class Command(BaseCommand):
    help = "Переносит данные из статических полей (silhouette, collection, ...) в ProductAttribute"

    def handle(self, *args, **options):
        # Сопоставление названий полей и слагов типов
        field_mapping = {
            'silhouette': 'silhouette',
            'collection': 'collection',
            'color': 'color',
            'fabric': 'fabric',
            'sizes': 'sizes',
        }

        # Проходим по всем товарам
        for product in Product.objects.all():
            for field, slug in field_mapping.items():
                value = getattr(product, field, None)
                if value:  # если поле не пустое
                    try:
                        attr_type = AttributeType.objects.get(slug=slug)
                    except AttributeType.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Тип {slug} не найден, пропускаем"
                        ))
                        continue

                    # Создаём или обновляем запись характеристики
                    obj, created = ProductAttribute.objects.get_or_create(
                        product=product,
                        attribute_type=attr_type,
                        defaults={'value': value}
                    )
                    if created:
                        self.stdout.write(f"Добавлена характеристика {attr_type.name} = {value} для {product.title}")
                    else:
                        if obj.value != value:
                            obj.value = value
                            obj.save()
                            self.stdout.write(f"Обновлена характеристика {attr_type.name} = {value} для {product.title}")

        self.stdout.write(self.style.SUCCESS("Перенос завершён"))