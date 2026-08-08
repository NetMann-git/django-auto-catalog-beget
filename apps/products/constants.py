# apps/products/constants.py
"""
Константы для товаров.
"""

ITEMS_PER_PAGE = 4
MAX_COMPARISON_ITEMS = 4
MAX_RECENTLY_VIEWED = 5

CURRENCY_CHOICES = [
    ('USD', 'USD $'),
    ('EUR', 'EUR €'),
    ('RUB', 'RUB ₽'),
]

AVAILABILITY_IN_STOCK = "in_stock"
AVAILABILITY_UNDER_ORDER = "under_order"
AVAILABILITY_LAST_SIZE = "last_size"
AVAILABILITY_OUT_OF_STOCK = "out_of_stock"

AVAILABILITY_CHOICES = [
    (AVAILABILITY_IN_STOCK, "В наличии"),
    (AVAILABILITY_UNDER_ORDER, "Под заказ"),
    (AVAILABILITY_LAST_SIZE, "Последний размер"),
    (AVAILABILITY_OUT_OF_STOCK, "Нет в наличии"),
]

ATTRIBUTE_COLLECTION = "collection"
ATTRIBUTE_SILHOUETTE = "silhouette"
