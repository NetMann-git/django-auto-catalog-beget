from django.db import models
from django.utils import timezone
from apps.products.models import Product
from .models import PromotedProduct

class RecommendationService:
    """Сервис для получения рекомендаций товаров с учётом ручного продвижения."""

    @staticmethod
    def get_similar_products(viewed_products, page='recently_viewed', limit=4):
        """
        Возвращает список товаров для блока «Рекомендуем».
        Сначала берутся активные ручные рекомендации для указанной страницы,
        затем добираются автоматические (по категориям просмотренных товаров).
        Исключаются уже просмотренные товары.
        """
        # 1. Ручные рекомендации для заданной страницы
        now = timezone.now()
        promoted_qs = PromotedProduct.objects.filter(
            page=page,
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        ).select_related('product').order_by('-priority')[:limit]

        promoted_products = []
        promoted_ids = set()
        for pp in promoted_qs:
            if pp.product.is_active and pp.product.id not in promoted_ids:
                # Исключаем уже просмотренные
                if viewed_products and pp.product.id in viewed_products.values_list('id', flat=True):
                    continue
                promoted_products.append(pp.product)
                promoted_ids.add(pp.product.id)

        # 2. Добиваем автоматическими рекомендациями
        remaining = limit - len(promoted_products)
        auto_products = []
        if remaining > 0:
            # Исключаем просмотренные и уже добавленные ручные
            exclude_ids = set()
            if viewed_products:
                exclude_ids.update(viewed_products.values_list('id', flat=True))
            exclude_ids.update(promoted_ids)

            # По категориям просмотренных
            if viewed_products and viewed_products.exists():
                category_ids = viewed_products.values_list('category_id', flat=True).distinct()
                auto_qs = Product.objects.filter(
                    is_active=True,
                    category_id__in=category_ids
                ).exclude(id__in=exclude_ids).distinct()[:remaining]
                auto_products = list(auto_qs)
                remaining -= len(auto_products)

            # Если всё ещё не хватает — добиваем featured
            if remaining > 0:
                featured_qs = Product.objects.filter(
                    is_active=True,
                    is_featured=True
                ).exclude(id__in=exclude_ids.union({p.id for p in auto_products}))[:remaining]
                auto_products += list(featured_qs)

        # 3. Объединяем: сначала ручные, потом автоматические
        result = promoted_products + auto_products
        return result[:limit]