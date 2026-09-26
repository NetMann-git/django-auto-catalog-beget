# apps/products/context.py
"""
Контекст-билдеры для страниц товаров и каталога.
"""

from apps.products.querysets import CatalogQuerySet
from apps.products.filters import CatalogFilter
from apps.products.pagination import CatalogPaginator

from apps.products.repository import CatalogRepository


class CatalogContextBuilder:
    @staticmethod
    def build(request):
        # 1. Базовый запрос
        products = CatalogRepository.catalog()

        # 2. Фильтры
        filters = CatalogFilter(request.GET)
        products = filters.apply(products)

        # 3. Пагинация
        pagination = CatalogPaginator(products, request)

        # 4. Сборка контекста
        context = CatalogRepository.filters()
        context.update(filters.context())
        context.update(pagination.context())

        # Списки ограничены значениями опубликованных автомобилей.
        from apps.products.models import AttributeValue, ProductAttribute
        from apps.products.filters import FUEL_SLUGS, parse_number

        active_attributes = ProductAttribute.objects.filter(
            product__is_active=True,
        )
        years = AttributeValue.objects.filter(
            product_attributes__in=active_attributes.filter(
                attribute_type__slug="year",
            ),
        ).values_list("value", flat=True).distinct()
        context["catalog_years"] = sorted(
            {int(number) for value in years
             if (number := parse_number(value)) is not None
             and number == int(number)},
            reverse=True,
        )
        context["fuel_values"] = AttributeValue.objects.filter(
            product_attributes__in=active_attributes.filter(
                attribute_type__slug__in=FUEL_SLUGS,
            ),
        ).distinct().order_by("value")

        # 5. Избранное (wishlist)
        if request.user.is_authenticated:
            wishlist_ids = list(request.user.favorites.values_list("product_id", flat=True))
        else:
            wishlist_ids = request.session.get('wishlist', [])
        context["wishlist_ids"] = wishlist_ids

        return context


class ProductContextBuilder:
    @staticmethod
    def build(product_page, request):
        from apps.products.services import ProductService
        context = ProductService.context(product_page)  # содержит similar_products

        # Избранное (wishlist)
        if request.user.is_authenticated:
            wishlist_ids = list(request.user.favorites.values_list("product_id", flat=True))
        else:
            wishlist_ids = request.session.get('wishlist', [])
        context["wishlist_ids"] = wishlist_ids

        return context


class HomeContextBuilder:
    """
    Формирует контекст главной страницы.
    """

    @staticmethod
    def build(request):
        context = {
            "featured_products": CatalogRepository.featured(),
        }
        # Можно также добавить wishlist_ids для главной, если там есть кнопки избранного (пока не нужно)
        return context