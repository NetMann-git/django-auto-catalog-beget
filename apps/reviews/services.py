# apps/reviews/services.py

from django.db.models import QuerySet
from apps.products.models import Product

class ReviewService:
    """
    Сервис для работы с отзывами.
    """

    @staticmethod
    def queryset(product: Product) -> QuerySet:
        """
        Возвращает опубликованные отзывы товара.
        """
        return product.reviews.filter(is_published=True)

    @staticmethod
    def apply_filters(
        queryset,
        request,
    ):
        """
        Применяет фильтры к списку отзывов.
        """

        rating_filter = request.GET.get("rating")

        if rating_filter and rating_filter.isdigit():
            queryset = queryset.filter(
                rating=int(rating_filter)
            )

        with_photos = request.GET.get("with_photos")

        if with_photos == "1":
            queryset = queryset.filter(
                images__isnull=False
            ).distinct()

        verified = request.GET.get("verified")

        if verified == "1":
            queryset = queryset.filter(
                is_verified=True
            )

        return queryset