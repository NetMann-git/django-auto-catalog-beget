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
        Поддерживает как QuerySet, так и список товаров.
        """
        now = timezone.now()

        # Приводим просмотренные товары к множеству ID (поддержка QuerySet и list)
        if viewed_products is None:
            viewed_ids = set()
        elif hasattr(viewed_products, 'values_list'):
            # QuerySet → множество id
            viewed_ids = set(viewed_products.values_list('id', flat=True))
        else:
            # list → множество id из объектов
            viewed_ids = {p.id for p in viewed_products}

        # 1. Ручные рекомендации для заданной страницы
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
            if pp.product.is_active and pp.product.id not in viewed_ids and pp.product.id not in promoted_ids:
                promoted_products.append(pp.product)
                promoted_ids.add(pp.product.id)

        # 2. Добиваем автоматическими рекомендациями
        remaining = limit - len(promoted_products)
        auto_products = []
        if remaining > 0:
            exclude_ids = set(viewed_ids)
            exclude_ids.update(promoted_ids)

            # По категориям просмотренных товаров
            if viewed_ids:
                # Получаем категории просмотренных товаров (работает и для QuerySet, и для list)
                if hasattr(viewed_products, 'values_list'):
                    category_ids = Product.objects.filter(
                        id__in=viewed_ids
                    ).values_list('category_id', flat=True).distinct()
                else:
                    category_ids = {p.category_id for p in viewed_products if p.category_id}

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