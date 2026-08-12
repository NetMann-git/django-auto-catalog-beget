from django.contrib import admin
from .models import PromotedProduct

@admin.register(PromotedProduct)
class PromotedProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'page', 'priority', 'is_active', 'start_date', 'end_date']
    list_editable = ['priority', 'is_active']
    list_filter = ['page', 'is_active']
    search_fields = ['product__title']
    autocomplete_fields = ['product']  # удобный поиск товара по названию