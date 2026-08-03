# apps/products/cache.py

from django.core.cache import cache


class CatalogCache:
    """
    Работа с кэшем каталога.
    """

    @staticmethod
    def clear_catalog():
        """
        Очищает кэш каталога и фильтров.
        """
        cache.delete("catalog_queryset")
        cache.delete("catalog_filters")