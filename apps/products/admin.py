# apps/products/admin.py

from django.contrib import admin
from django.utils.html import format_html
from easy_thumbnails.files import get_thumbnailer

from .models import (
    Product,
    ProductGalleryImage,
    ProductAttribute,
    Badge,
    Category,
)


from .models import AttributeType
from .models import AttributeValue

from .models import Brand

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "country")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "country")
    fieldsets = (
        (None, {"fields": ("name", "slug", "logo", "description", "country")}),
        ("SEO", {"fields": ("meta_title", "meta_description")}),
    )


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ("value", "sort_order")
    ordering = ("sort_order",)

@admin.register(AttributeType)
class AttributeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "data_type")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AttributeValueInline]


class ProductGalleryInline(admin.TabularInline):
    model = ProductGalleryImage
    extra = 1
    fields = ("image", "alt", "sort_order")
    ordering = ("sort_order",)


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    fields = ("attribute_type", "attribute_value", "sort_order")
    ordering = ("sort_order",)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "title",
        "article",
        "category",
        "price",
        "availability_status",
        "is_featured",
        "is_active",
        "image_tag",
    )
    list_filter = (
        "category",
        "brand",
        "availability_status",
        "is_featured",
        "is_active",
    )
    search_fields = (
        "title",
        "article",
        "short_description",
        "description",
    )
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("badges",)
    view_on_site = False

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "title",
                    "slug",
                    "article",
                    "category",
                    "brand",
                    "image",
                )
            },
        ),
        (
            "Описание",
            {
                "fields": (
                    "short_description",
                    "description",
                )
            },
        ),
        (
            "Каталог",
            {
                "fields": (
                    "price",
                    "currency",
                    "badges",
                )
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                )
            },
        ),
        (
            "Публикация",
            {
                "fields": (
                    "is_featured",
                    "is_active",
                    "availability_status",
                )
            },
        ),
    )

    inlines = [
        ProductGalleryInline,
        ProductAttributeInline,
    ]

    def image_tag(self, obj):
        if obj.image:
            thumbnail = get_thumbnailer(obj.image).get_thumbnail({
                'size': (50, 75),
                'crop': True,
            })
            return format_html(
                '<img src="{}" style="width:50px; height:75px; object-fit: cover;" />',
                thumbnail.url
            )
        return format_html('<span style="color: #aaa;">Нет фото</span>')
    image_tag.short_description = "Фото"