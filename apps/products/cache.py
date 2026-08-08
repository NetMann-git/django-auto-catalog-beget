# apps/products/cache.py

from django.core.cache import cache

from .cache_keys import (
    CATALOG_QUERYSET_KEY,
    CATALOG_FILTERS_KEY,
)


class CatalogCache:
    """
    Работа с кэшем каталога.
    """

    @staticmethod
    def clear_catalog():
        """
        Очищает кэш каталога и фильтров.
        """
        cache.delete(CATALOG_QUERYSET_KEY)
        cache.delete(CATALOG_FILTERS_KEY)