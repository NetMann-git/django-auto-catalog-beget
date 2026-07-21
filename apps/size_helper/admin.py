# apps/size_helper/admin.py

from django.contrib import admin
from .models import SizeTable, SizeRecommendation


@admin.register(SizeTable)
class SizeTableAdmin(admin.ModelAdmin):
    list_display = ('size', 'chest', 'waist', 'hips', 'height_min', 'height_max', 'sort_order')
    list_editable = ('chest', 'waist', 'hips', 'height_min', 'height_max', 'sort_order')
    search_fields = ('size',)


@admin.register(SizeRecommendation)
class SizeRecommendationAdmin(admin.ModelAdmin):
    list_display = ('size', 'height_min', 'height_max', 'bust_min', 'bust_max', 'waist_min', 'waist_max', 'hips_min', 'hips_max')
    search_fields = ('size',)