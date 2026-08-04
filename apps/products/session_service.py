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