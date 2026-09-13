from django.contrib import admin

from .models import ClientShowcase


@admin.register(ClientShowcase)
class ClientShowcaseAdmin(admin.ModelAdmin):
    list_display = ("name", "vehicle", "sort_order", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("name", "vehicle")
    list_editable = ("sort_order", "is_published")
