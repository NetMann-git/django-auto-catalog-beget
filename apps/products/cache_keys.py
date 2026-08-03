# apps/products/cache_keys.py

"""
Ключи кэша приложения products.

Все ключи и префиксы хранятся здесь, чтобы не использовать
магические строки в разных частях проекта.
"""

CATALOG_QUERYSET_KEY = "catalog_queryset"
CATALOG_FILTERS_KEY = "catalog_filters"

SIMILAR_PRODUCTS_PREFIX = "similar_"

CACHE_TIMEOUT = 600