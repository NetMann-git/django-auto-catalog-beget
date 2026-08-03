# apps/products/services.py
from django.core.cache import cache

from .cache_keys import (
    CACHE_TIMEOUT,
    SIMILAR_PRODUCTS_PREFIX,
)
from .repository import CatalogRepository


class ProductService:

    

    @staticmethod
    def get_similar_products(product, limit=4):
        cache_key = f"{SIMILAR_PRODUCTS_PREFIX}{product.pk}"
        similar = cache.get(cache_key)
        if similar is None:
            queryset = CatalogRepository.related(product)
            similar = []

            # Получаем коллекцию и силуэт через ProductAttribute
            
            collection_value = ProductService._get_attribute_value(
                product,
                "collection",
            )
            
            silhouette_value = ProductService._get_attribute_value(
                product,
                "silhouette",
            )

            # 1. Та же коллекция + тот же силуэт
            if collection_value and silhouette_value:
                similar = list(
                    queryset.filter(
                        attributes__attribute_type__slug='collection',
                        attributes__attribute_value__value=collection_value,
                    ).filter(
                        attributes__attribute_type__slug='silhouette',
                        attributes__attribute_value__value=silhouette_value,
                    ).distinct()[:limit]
                )

            # 2. Та же коллекция
            if len(similar) < limit and collection_value:
                ids = [obj.id for obj in similar]
                similar.extend(
                    queryset
                    .filter(
                        attributes__attribute_type__slug='collection',
                        attributes__attribute_value__value=collection_value,
                    )
                    .exclude(id__in=ids)
                    .distinct()[:limit - len(similar)]
                )

            # 3. Тот же силуэт
            if len(similar) < limit and silhouette_value:
                ids = [obj.id for obj in similar]
                similar.extend(
                    queryset
                    .filter(
                        attributes__attribute_type__slug='silhouette',
                        attributes__attribute_value__value=silhouette_value,
                    )
                    .exclude(id__in=ids)
                    .distinct()[:limit - len(similar)]
                )

            # 4. Любые товары (запасной вариант)
            if len(similar) < limit:
                ids = [obj.id for obj in similar]
                similar.extend(
                    queryset
                    .exclude(id__in=ids)
                    .distinct()[:limit - len(similar)]
                )

            cache.set(cache_key, similar, CACHE_TIMEOUT)
        return similar

    @staticmethod
    def context(product):
        return {
            "similar_products": ProductService.get_similar_products(product),
        }

    @staticmethod
    def _get_attribute_value(product, slug):
        """
        Возвращает значение характеристики товара по slug.
        """
        attribute = (
            product.attributes
            .filter(attribute_type__slug=slug)
            .select_related("attribute_value")
            .first()
        )
        return attribute.attribute_value.value if attribute else None