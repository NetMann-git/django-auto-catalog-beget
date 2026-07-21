"""
Пользовательские менеджеры моделей.
"""
# apps/products/managers.py
from wagtail.models import PageManager, PageQuerySet


class ProductQuerySet(PageQuerySet):

    def active(self):
        return self.filter(is_active=True)

    def featured(self):
        return self.filter(is_featured=True)


class ProductManager(PageManager):

    def get_queryset(self):
        return ProductQuerySet(
            self.model,
            using=self._db,
        )

    def active(self):
        return self.get_queryset().active()

    def featured(self):
        return self.get_queryset().featured()