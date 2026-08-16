# apps/recommendations/context_processors.py
from .models import PromotedProduct

def promoted_products(request):
    """
    Добавляет в контекст список ID товаров, которые вручную продвигаются.
    """
    promoted_ids = list(
        PromotedProduct.objects.filter(is_active=True)
        .values_list('product_id', flat=True)
        .distinct()
    )
    return {'promoted_product_ids': promoted_ids}