# apps/wishlist/admin.py

from django.contrib import admin
from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("user", "product")
    search_fields = ("user__username", "product__title")
