from django.contrib import admin
from django.utils.html import format_html
from easy_thumbnails.files import get_thumbnailer
from .models import PromotedProduct

@admin.register(PromotedProduct)
class PromotedProductAdmin(admin.ModelAdmin):
    list_display = ['image_tag', 'product', 'page', 'priority', 'is_active', 'start_date', 'end_date']
    list_editable = ['priority', 'is_active']
    list_filter = ['page', 'is_active']
    search_fields = ['product__title']
    autocomplete_fields = ['product']

    @admin.display(description='Фото')
    def image_tag(self, obj):
        if obj.product.image:
            thumbnail = get_thumbnailer(obj.product.image).get_thumbnail({
                'size': (50, 75),
                'crop': True,
            })
            return format_html('<img src="{}" style="width:50px; height:75px; object-fit: cover;" />', thumbnail.url)
        return format_html('<span style="color: #aaa;">Нет фото</span>')