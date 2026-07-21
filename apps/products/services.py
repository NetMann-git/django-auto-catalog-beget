# apps/products/services.py
from django.core.cache import cache

from apps.products.repository import CatalogRepository


class ProductService:

    

    @staticmethod
    def get_similar_products(product, limit=4):
        cache_key = f"similar_{product.pk}"
        similar = cache.get(cache_key)
        if similar is None:
            queryset = CatalogRepository.related(product)
            similar = []

            # Получаем коллекцию и силуэт через ProductAttribute
            collection_attr = product.attributes.filter(attribute_type__slug='collection').first()
            silhouette_attr = product.attributes.filter(attribute_type__slug='silhouette').first()

            collection_value = collection_attr.attribute_value.value if collection_attr else None
            silhouette_value = silhouette_attr.attribute_value.value if silhouette_attr else None

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

            cache.set(cache_key, similar, 600)
        return similar

    @staticmethod
    def context(product):
        return {
            "similar_products": ProductService.get_similar_products(product),
        }