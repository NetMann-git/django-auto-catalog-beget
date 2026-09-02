"""Контекст главной страницы автомобильного каталога."""

from apps.products.models import Brand
from apps.products.repository import CatalogRepository
from apps.reviews.models import Review


class HomeContextBuilder:
    """Собирает данные главной страницы из существующих приложений проекта."""

    @staticmethod
    def build(request):
        featured_products = CatalogRepository.featured(limit=8)

        featured_brands = (
            Brand.objects
            .filter(products__is_active=True)
            .distinct()
            .prefetch_related("products")
            .order_by("name")[:12]
        )

        reviews = (
            Review.objects
            .filter(is_published=True)
            .select_related("product", "user")
            .prefetch_related("images")
            .order_by("-created_at")[:4]
        )

        if request.user.is_authenticated:
            wishlist_ids = list(
                request.user.favorites.values_list("product_id", flat=True)
            )
        else:
            wishlist_ids = request.session.get("wishlist", [])

        return {
            "featured_products": featured_products,
            "featured_brands": featured_brands,
            "reviews": reviews,
            "wishlist_ids": wishlist_ids,
        }
