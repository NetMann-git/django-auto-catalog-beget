# apps/products/admin.py

from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']  # теперь ищем title
    prepopulated_fields = {'slug': ('title',)}  # авто-заполнение
    search_fields = ['title']  # поиск по title

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    list_filter = ['created_at']



# from django.utils.html import format_html

# from .models import (
#     Product,
#     ProductGalleryImage,
#     ProductAttribute,
#     Badge,
#     Category,
# )


# from .models import AttributeType
# from .models import AttributeValue

# from .models import Brand

# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ("name", "slug", "country")
#     prepopulated_fields = {"slug": ("name",)}
#     search_fields = ("name", "country")
#     fieldsets = (
#         (None, {"fields": ("name", "slug", "logo", "description", "country")}),
#         ("SEO", {"fields": ("meta_title", "meta_description")}),
#     )


# class AttributeValueInline(admin.TabularInline):
#     model = AttributeValue
#     extra = 1
#     fields = ("value", "sort_order")
#     ordering = ("sort_order",)

# @admin.register(AttributeType)
# class AttributeTypeAdmin(admin.ModelAdmin):
#     list_display = ("name", "slug", "data_type")
#     prepopulated_fields = {"slug": ("name",)}
#     inlines = [AttributeValueInline]


# class ProductGalleryInline(admin.TabularInline):
#     model = ProductGalleryImage
#     extra = 1
#     fields = ("image", "alt", "sort_order")
#     ordering = ("sort_order",)


# class ProductAttributeInline(admin.TabularInline):
#     model = ProductAttribute
#     extra = 1
#     fields = ("attribute_type", "attribute_value", "sort_order")
#     ordering = ("sort_order",)


# @admin.register(Badge)
# class BadgeAdmin(admin.ModelAdmin):
#     list_display = ("title", "slug")
#     prepopulated_fields = {"slug": ("title",)}


# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ("title", "slug")
#     prepopulated_fields = {"slug": ("title",)}


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     save_on_top = True  # <-- добавьте эту строку
#     list_display = (
#         "title",
#         "article",
#         "category",
#         "price",
#         "availability_status",
#         "is_featured",
#         "is_active",
#         "image_tag",
#     )
#     list_filter = (
#         "category",
#         "brand",
#         "availability_status",
#         "is_featured",
#         "is_active",
#     )
#     search_fields = (
#         "title",
#         "article",
#         "short_description",
#         "description",
#     )
#     prepopulated_fields = {"slug": ("title",)}
#     filter_horizontal = ("badges",)
#     view_on_site = False

#     fieldsets = (
#         (
#             "Основное",
#             {
#                 "fields": (
#                     "title",
#                     "slug",
#                     "article",
#                     "category",
#                     "brand",
#                     "image",
#                 )
#             },
#         ),
#         (
#             "Описание",
#             {
#                 "fields": (
#                     "short_description",
#                     "description",
#                 )
#             },
#         ),
#         (
#             "Каталог",
#             {
#                 "fields": (
#                     "price",
#                     "currency",
#                     "badges",
#                 )
#             },
#         ),
#         (
#             "SEO",
#             {
#                 "fields": (
#                     "meta_title",
#                     "meta_description",
#                 )
#             },
#         ),
#         (
#             "Публикация",
#             {
#                 "fields": (
#                     "is_featured",
#                     "is_active",
#                     "availability_status",
#                 )
#             },
#         ),
#     )

#     inlines = [
#         ProductGalleryInline,
#         ProductAttributeInline,
#     ]

#     def image_tag(self, obj):
#         if obj.image:
#             return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
#         return "-"
#     image_tag.short_description = "Фото"