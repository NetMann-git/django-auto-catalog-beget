from apps.products.models import Product, Category

class RecommendationService:
    """Сервис для получения рекомендаций товаров."""

    @staticmethod
    def get_similar_products(viewed_products, limit=4):
        """
        Возвращает товары, похожие на просмотренные (по категориям).
        Исключает уже просмотренные товары.
        Если просмотренных нет — возвращает featured-товары.
        """
        if not viewed_products:
            return Product.objects.filter(
                is_active=True,
                is_featured=True
            )[:limit]

        # Собираем категории просмотренных товаров
        category_ids = viewed_products.values_list('category_id', flat=True).distinct()

        # Ищем товары из тех же категорий, исключая просмотренные
        similar = Product.objects.filter(
            is_active=True,
            category_id__in=category_ids
        ).exclude(
            id__in=viewed_products.values_list('id', flat=True)
        ).distinct()[:limit]

        # Если похожих не хватило — добиваем featured
        if similar.count() < limit:
            featured = Product.objects.filter(
                is_active=True,
                is_featured=True
            ).exclude(
                id__in=viewed_products.values_list('id', flat=True)
            ).exclude(
                id__in=similar.values_list('id', flat=True)
            )[:limit - similar.count()]

            return list(similar) + list(featured)

        return similar