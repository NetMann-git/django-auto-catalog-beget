# apps/products/querysets/catalog.py
"""
Запросы для каталога товаров.
"""


class CatalogQuerySet:
    """Класс-контейнер для запросов каталога."""

    @staticmethod
    def _base_queryset():
        """Базовый запрос для всех методов."""
        from apps.products.config import PRODUCT_MODEL

        return PRODUCT_MODEL.objects.filter(is_active=True)

    @staticmethod
    def _with_related(queryset):
        """
        Подгружает связанные объекты для отображения товаров.
        """
        return queryset.select_related("category").prefetch_related(
            "badges",
            "gallery",
        )

    @staticmethod
    def catalog_queryset():
        """
        QuerySet каталога с подгрузкой связанных данных.
        """
        return CatalogQuerySet._with_related(
            CatalogQuerySet._base_queryset()
        )

    @staticmethod
    def base_product_queryset(product):
        """
        Базовый queryset для поиска похожих товаров (исключая текущий).
        """
        return (
            CatalogQuerySet._with_related(
                CatalogQuerySet._base_queryset()
            )
            .exclude(id=product.id)
        )

    @staticmethod
    def distinct_values(attribute_slug):
        """
        Возвращает уникальные значения для указанного типа характеристики.
        Например, для 'silhouette' вернёт список силуэтов.
        """
        from apps.products.models import AttributeValue

        return (
            AttributeValue.objects
            .filter(attribute_type__slug=attribute_slug)
            .values_list("value", flat=True)
            .distinct()
            .order_by("value")
        )

    @staticmethod
    def featured(limit=8):
        """
        Возвращает избранные товары для главной страницы.
        """
        from apps.products.models import Product

        return (
            CatalogQuerySet._with_related(
                Product.objects.filter(
                    is_active=True,
                    is_featured=True,
                )
            )[:limit]
        )

    @staticmethod
    def by_brand(brand):
        """
        Возвращает активные товары указанного бренда.
        """
        return CatalogQuerySet._with_related(
            CatalogQuerySet._base_queryset().filter(brand=brand)
        )