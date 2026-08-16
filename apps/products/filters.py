# apps/products/filters.py
"""
Фильтры каталога.
"""
from django.db.models import Q
from django.db.models.functions import Lower
from apps.products.models import Product

from apps.products.constants import AVAILABILITY_CHOICES

class CatalogFilter:
    """
    Хранит выбранные пользователем параметры фильтрации.
    """

    def __init__(self, request_get):
        self.query = request_get.get("q", "").strip()
        self.silhouette = request_get.get("silhouette")
        self.collection = request_get.get("collection")
        self.brand = request_get.get("brand")
        self.category = request_get.get("category")
        self.color = request_get.get("color")
        self.price_min = request_get.get("price_min")
        self.price_max = request_get.get("price_max")
        self.sort = request_get.get("sort")
        self.availability = request_get.get("availability")

    def apply(self, queryset):
        # Сначала применяем все фильтры, кроме поиска
        if self.silhouette:
            queryset = queryset.filter(
                attributes__attribute_type__slug='silhouette',
                attributes__attribute_value__value=self.silhouette
            )

        if self.brand:
            queryset = queryset.filter(brand_id=self.brand)   

        if self.collection:
            queryset = queryset.filter(
                attributes__attribute_type__slug='collection',
                attributes__attribute_value__value=self.collection
            )

        if self.color:
            queryset = queryset.filter(
                attributes__attribute_type__slug='color',
                attributes__attribute_value__value=self.color
            )

        if self.availability:
            queryset = queryset.filter(availability_status=self.availability)

        if self.price_min:
            queryset = queryset.filter(price__gte=self.price_min)

        if self.price_max:
            queryset = queryset.filter(price__lte=self.price_max)

        if self.category:
            queryset = queryset.filter(
                category_id=self.category
            )

        # Поиск выполняется в Python (регистронезависимо для кириллицы)
        if self.query:
            query = self.query.casefold()
            ids = []
            for product in queryset:
                if (
                    query in (product.title or "").casefold()
                    or query in (product.article or "").casefold()
                    or query in (product.short_description or "").casefold()
                    or query in (product.description or "").casefold()
                ):
                    ids.append(product.id)
            queryset = queryset.filter(id__in=ids)

        # Сортировка
        if self.sort == "price_asc":
            queryset = queryset.order_by("price")
        elif self.sort == "price_desc":
            queryset = queryset.order_by("-price")
        elif self.sort == "title_asc":
            queryset = queryset.order_by(Lower("title"))
        elif self.sort == "title_desc":
            queryset = queryset.order_by(Lower("title").desc())

        return queryset

    def get_brand_name(self):
        if self.brand:
            from apps.products.models import Brand
            try:
                return Brand.objects.get(pk=self.brand).name
            except Brand.DoesNotExist:
                return None
        return None
    
    def context(self):
        """
        Возвращает выбранные значения фильтров для передачи в шаблон.
        """
        return {
            "search_query": self.query,
            "selected_silhouette": self.silhouette,
            "selected_brand": self.brand,
            "selected_brand_name": self.get_brand_name(),
            "selected_collection": self.collection,
            "selected_category": self.category,
            "selected_color": self.color,
            "selected_sort": self.sort,
            "selected_availability": self.availability,
            "selected_availability_label": dict(AVAILABILITY_CHOICES).get(self.availability, self.availability),
<<<<<<< HEAD
            "selected_price_min": self.price_min,
            "selected_price_max": self.price_max,
=======
            "selected_price_min": self.price_min or "",
            "selected_price_max": self.price_max or "",
>>>>>>> dev
        }