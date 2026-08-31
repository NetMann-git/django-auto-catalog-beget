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

        # Добавляем списки для фильтров-атрибутов
        from apps.products.models import AttributeType, AttributeValue

        # Уникальные значения для коробки передач
        transmission_values = AttributeValue.objects.filter(
            attribute_type__slug='transmission'
        ).values_list('value', flat=True).distinct().order_by('value')
        context['transmissions'] = transmission_values

        # Уникальные значения для привода
        drive_values = AttributeValue.objects.filter(
            attribute_type__slug='drive'
        ).values_list('value', flat=True).distinct().order_by('value')
        context['drives'] = drive_values

        # Уникальные значения для состояния
        condition_values = AttributeValue.objects.filter(
            attribute_type__slug='condition'
        ).values_list('value', flat=True).distinct().order_by('value')
        context['conditions'] = condition_values

        # Для года и пробега можно вычислить минимальное/максимальное значение
        # (но пока оставляем как диапазон)       
        
        
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