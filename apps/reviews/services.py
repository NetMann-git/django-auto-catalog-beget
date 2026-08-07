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
            rating_value = int(rating_filter)

            if rating_value == 5:
                queryset = queryset.filter(rating=5)

            elif rating_value == 4:
                queryset = queryset.filter(rating__gte=4)

            elif rating_value == 3:
                queryset = queryset.filter(rating__gte=3)

            else:
                queryset = queryset.filter(rating=rating_value)

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
            "-helpful_count,-created_at",
        )

        sort_fields = (
            sort_by.split(",")
            if "," in sort_by
            else [sort_by]
        )

        ordered = False

        for field in sort_fields:

            if field == "-created_at":
                queryset = queryset.order_by("-created_at")
                ordered = True

            elif field == "-rating":
                queryset = queryset.order_by("-rating")
                ordered = True

            elif field == "rating":
                queryset = queryset.order_by("rating")
                ordered = True

            elif field == "-helpful_count":
                queryset = queryset.order_by("-helpful_count")
                ordered = True

        if not ordered or sort_by == "-helpful_count,-created_at":
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