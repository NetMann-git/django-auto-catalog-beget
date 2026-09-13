from django.contrib import admin

from .models import ClientShowcase


@admin.register(ClientShowcase)
class ClientShowcaseAdmin(admin.ModelAdmin):
    list_display = ("name", "vehicle", "has_video_review", "sort_order", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("name", "vehicle", "rutube_url")

    @admin.display(boolean=True, description="Видеоотзыв")
    def has_video_review(self, obj):
        return bool(obj.rutube_url)
    list_editable = ("sort_order", "is_published")
