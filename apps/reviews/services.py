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

    @staticmethod
    def apply_sorting(queryset, request):
        """
        Применяет сортировку отзывов.
        """

        sort_by = request.GET.get(
            "sort",
            "-helpful_count",
        )

        if sort_by == "created_at":
            queryset = queryset.order_by("-created_at")

        elif sort_by == "rating":
            queryset = queryset.order_by("-rating")

        elif sort_by == "helpful_count":
            queryset = queryset.order_by("-helpful_count")

        else:
            queryset = queryset.order_by(
                "-helpful_count",
                "-created_at",
            )

        return queryset

    @staticmethod
    def get_reviews(product, request):
        """
        Возвращает опубликованные отзывы
        с учётом фильтрации и сортировки.
        """

        queryset = ReviewService.queryset(product)

        queryset = ReviewService.apply_filters(
            queryset,
            request,
        )

        queryset = ReviewService.apply_sorting(
            queryset,
            request,
        )

        return queryset