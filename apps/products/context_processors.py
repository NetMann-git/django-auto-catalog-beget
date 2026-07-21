
# apps/products/context_processors.py

def comparison_ids(request):
    """
    Передаёт в шаблоны список ID товаров, добавленных в сравнение.
    """
    ids = request.session.get('comparison', [])
    return {'comparison_ids': ids}


def recently_viewed_ids(request):
    """
    Передаёт в шаблоны список ID товаров, просмотренных в текущей сессии.
    """
    ids = request.session.get('recently_viewed', [])
    return {'recently_viewed_ids': ids}