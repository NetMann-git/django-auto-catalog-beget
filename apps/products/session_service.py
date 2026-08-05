# apps/products/session_service.py

"""
Работа с данными каталога, хранящимися в пользовательской сессии.
"""

COMPARISON_KEY = "comparison"
RECENTLY_VIEWED_KEY = "recently_viewed"


class SessionService:
    """
    Сервис для работы с пользовательской сессией.
    """

    @staticmethod
    def get_recently_viewed(request):
        """
        Возвращает список недавно просмотренных товаров.
        """
        return request.session.get(RECENTLY_VIEWED_KEY, [])

    @staticmethod
    def save_recently_viewed(request, product_id, limit):
        """
        Добавляет товар в историю просмотров.
        """

        recently_viewed = SessionService.get_recently_viewed(request)

        if product_id in recently_viewed:
            recently_viewed.remove(product_id)

        recently_viewed.insert(0, product_id)

        request.session[RECENTLY_VIEWED_KEY] = recently_viewed[:limit]

    @staticmethod
    def get_comparison(request):
        """
        Возвращает список товаров для сравнения.
        """
        return request.session.get(COMPARISON_KEY, [])

    @staticmethod
    def save_comparison(request, comparison):
        """
        Сохраняет список товаров для сравнения в сессии.
        """
        request.session[COMPARISON_KEY] = comparison
        request.session.modified = True

    @staticmethod
    def add_to_comparison(request, product_id):
        """
        Добавляет товар в список сравнения.
        """
        comparison = SessionService.get_comparison(request)

        if product_id not in comparison:
            comparison.append(product_id)
            SessionService.save_comparison(request, comparison)

        return comparison