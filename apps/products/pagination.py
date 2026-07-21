# apps/products/pagination.py
"""
Пагинация каталога.
"""

from django.core.paginator import Paginator

from apps.products.constants import ITEMS_PER_PAGE


class CatalogPaginator:
    """
    Пагинация каталога.
    """

    def __init__(self, queryset, request):
        paginator = Paginator(queryset, ITEMS_PER_PAGE)

        self.page_obj = paginator.get_page(
            request.GET.get("page")
        )

        query_params = request.GET.copy()
        query_params.pop("page", None)

        self.query_params = query_params.urlencode()

    def context(self):
        return {
            "products": self.page_obj,
            "page_obj": self.page_obj,
            "query_params": self.query_params,
        }