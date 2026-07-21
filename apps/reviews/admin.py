# apps/reviews/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import Review, ReviewReply, ReviewImage

from .models import ReviewVote


class ReviewReplyInline(admin.StackedInline):
    model = ReviewReply
    extra = 1
    max_num = 1


class ReviewImageInline(admin.TabularInline):  # ← добавляем
    model = ReviewImage
    extra = 1
    fields = ("image", "sort_order")
    ordering = ("sort_order",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "author_name",
        "rating",
        "is_published",
        "is_verified",
        "has_images",
        "created_at",
        "short_text",
    )
    list_filter = (
        "product",
        "rating",
        "is_published",
        "is_verified",
        "created_at",
    )
    search_fields = ("title", "text", "guest_name", "user__username")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_published", "is_verified")

    fieldsets = (
        (None, {"fields": ("product", "user", "guest_name", "rating", "title", "text")}),
        ("Статус", {"fields": ("is_published", "is_verified", "created_at", "updated_at")}),
    )

    inlines = [ReviewReplyInline, ReviewImageInline]  # ← теперь определён

    def author_name(self, obj):
        return obj.get_author_name()
    author_name.short_description = "Автор"

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Текст"

    def has_images(self, obj):
        return obj.images.exists()
    has_images.boolean = True
    has_images.short_description = "Фото"


@admin.register(ReviewReply)
class ReviewReplyAdmin(admin.ModelAdmin):
    list_display = ("review", "created_at", "short_text")
    search_fields = ("text",)
    readonly_fields = ("created_at", "updated_at")

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Текст"

@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ("review", "user", "session_key", "is_helpful")
    list_filter = ("is_helpful",)
