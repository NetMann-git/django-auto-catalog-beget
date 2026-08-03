# apps/products/repository.py
from django.core.cache import cache
from apps.products.querysets import CatalogQuerySet
from apps.products.models import Brand


class CatalogRepository:

    @staticmethod
    def catalog():
        cache_key = "catalog_queryset"
        queryset = cache.get(cache_key)
        if queryset is None:
            queryset = CatalogQuerySet.catalog_queryset()
            cache.set(cache_key, queryset, 600)
        return queryset

    @staticmethod
    def filters():
        cache_key = "catalog_filters"
        data = cache.get(cache_key)
        if data is None:
            from apps.products.models import Category
            from apps.products.models import Product
            data = {
                "silhouettes": CatalogRepository.distinct("silhouette"),
                "brands": Brand.objects.order_by("name"),
                "collections": CatalogRepository.distinct("collection"),
                "colors": CatalogRepository.distinct("color"),
                "categories": Category.objects.order_by("title"),
                "availabilities": Product.AVAILABILITY_CHOICES,
            }
            cache.set(cache_key, data, 600)
        return data

    @staticmethod
    def distinct(field):
        return CatalogQuerySet.distinct_values(field)

    @staticmethod
    def related(product):
        return CatalogQuerySet.base_product_queryset(product)

    @staticmethod
    def featured(limit=8):
        return CatalogQuerySet.featured(limit)

    @staticmethod
    def by_brand(brand):
        """
        Возвращает активные товары указанного бренда.
        """
        return CatalogQuerySet._with_related(
            CatalogQuerySet._base_queryset().filter(brand=brand)
        )