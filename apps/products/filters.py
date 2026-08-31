# apps/products/filters.py
"""
Фильтры каталога (адаптировано под автомобили).
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
        self.category = request_get.get("category")
        self.brand = request_get.get("brand")
        self.price_min = request_get.get("price_min")
        self.price_max = request_get.get("price_max")
        self.sort = request_get.get("sort")
        self.availability = request_get.get("availability")

        # Диапазоны
        self.year_min = request_get.get("year_min")
        self.year_max = request_get.get("year_max")
        self.mileage_min = request_get.get("mileage_min")
        self.mileage_max = request_get.get("mileage_max")

        # Выбор из списка
        self.transmission = request_get.get("transmission")
        self.drive = request_get.get("drive")
        self.condition = request_get.get("condition")

    def apply(self, queryset):
        # Фильтр по категории (тип кузова)
        if self.category:
            queryset = queryset.filter(category_id=self.category)

        # Фильтр по бренду
        if self.brand:
            queryset = queryset.filter(brand_id=self.brand)

        # Фильтр по наличию
        if self.availability:
            queryset = queryset.filter(availability_status=self.availability)

        # Цена
        if self.price_min:
            queryset = queryset.filter(price__gte=self.price_min)
        if self.price_max:
            queryset = queryset.filter(price__lte=self.price_max)

        # --- Фильтры по атрибутам через поле `attributes` ---
        # Год выпуска (диапазон)
        if self.year_min:
            queryset = queryset.filter(
                attributes__attribute_type__slug='year',
                attributes__attribute_value__value__gte=self.year_min
            )
        if self.year_max:
            queryset = queryset.filter(
                attributes__attribute_type__slug='year',
                attributes__attribute_value__value__lte=self.year_max
            )

        # Пробег (диапазон)
        if self.mileage_min:
            queryset = queryset.filter(
                attributes__attribute_type__slug='mileage',
                attributes__attribute_value__value__gte=self.mileage_min
            )
        if self.mileage_max:
            queryset = queryset.filter(
                attributes__attribute_type__slug='mileage',
                attributes__attribute_value__value__lte=self.mileage_max
            )

        # Коробка передач
        if self.transmission:
            queryset = queryset.filter(
                attributes__attribute_type__slug='transmission',
                attributes__attribute_value__value=self.transmission
            )

        # Привод
        if self.drive:
            queryset = queryset.filter(
                attributes__attribute_type__slug='drive',
                attributes__attribute_value__value=self.drive
            )

        # Состояние (новый / с пробегом)
        if self.condition:
            queryset = queryset.filter(
                attributes__attribute_type__slug='condition',
                attributes__attribute_value__value=self.condition
            )

        # Поиск (регистронезависимый)
        if self.query:
            query = self.query.casefold()
            ids = []
            for product in queryset:
                if (query in (product.title or "").casefold() or
                    query in (product.description or "").casefold()):
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
        elif self.sort == "year_desc":
            # Сортировка по году (новые сначала)
            queryset = queryset.order_by("-attributes__attribute_value__value")
            # Примечание: может дать неоднозначный результат, если товар имеет несколько атрибутов года.
            # Для точности лучше использовать аннотации, но для демо-целей допустимо.

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
        Возвращает выбранные значения фильтров для шаблона.
        """
        return {
            "search_query": self.query,
            "selected_category": self.category,
            "selected_brand": self.brand,
            "selected_brand_name": self.get_brand_name(),
            "selected_sort": self.sort,
            "selected_availability": self.availability,
            "selected_availability_label": dict(AVAILABILITY_CHOICES).get(self.availability, self.availability),
            "selected_price_min": self.price_min or "",
            "selected_price_max": self.price_max or "",
            # Новые
            "selected_year_min": self.year_min or "",
            "selected_year_max": self.year_max or "",
            "selected_mileage_min": self.mileage_min or "",
            "selected_mileage_max": self.mileage_max or "",
            "selected_transmission": self.transmission,
            "selected_drive": self.drive,
            "selected_condition": self.condition,
        }