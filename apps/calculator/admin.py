"""Администрирование калькуляторов и ставок."""

from django.contrib import admin

from .models import (
    CalculatorDefinition,
    CurrencyRate,
    CustomsClearanceFeeRate,
    CustomsDutyRate,
    RateVersion,
    UtilizationRate,
)


@admin.register(CalculatorDefinition)
class CalculatorDefinitionAdmin(admin.ModelAdmin):
    """Настройки доступных калькуляторов."""

    list_display = ("title", "slug", "is_active", "sort_order", "updated_at")
    list_editable = ("is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")


@admin.register(RateVersion)
class RateVersionAdmin(admin.ModelAdmin):
    """Версии нормативных ставок."""

    list_display = (
        "name",
        "calculator",
        "effective_from",
        "effective_to",
        "base_rate",
        "is_active",
    )
    list_filter = ("calculator", "is_active", "effective_from")
    search_fields = ("name", "source_name")
    autocomplete_fields = ("calculator",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-effective_from",)


@admin.register(UtilizationRate)
class UtilizationRateAdmin(admin.ModelAdmin):
    """Коэффициенты утилизационного сбора."""

    list_display = (
        "rate_version",
        "powertrain",
        "usage_mode",
        "age_group",
        "engine_capacity_min",
        "engine_capacity_max",
        "power_kw_min",
        "power_kw_max",
        "coefficient",
    )
    list_filter = (
        "rate_version",
        "powertrain",
        "usage_mode",
        "age_group",
    )
    search_fields = ("rate_version__name", "notes")
    autocomplete_fields = ("rate_version",)
    ordering = (
        "rate_version",
        "powertrain",
        "usage_mode",
        "engine_capacity_min",
        "power_kw_min",
    )


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    """Курсы валют, используемые калькуляторами."""

    list_display = (
        "code",
        "nominal",
        "rate_to_rub",
        "effective_date",
        "updated_at",
    )
    list_filter = ("code", "effective_date")
    search_fields = ("code",)
    ordering = ("-effective_date", "code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CustomsDutyRate)
class CustomsDutyRateAdmin(admin.ModelAdmin):
    """Ставки пошлины для автомобилей физических лиц."""

    list_display = (
        "rate_version",
        "age_group",
        "value_eur_min",
        "value_eur_max",
        "engine_capacity_min",
        "engine_capacity_max",
        "value_percentage",
        "minimum_eur_per_cc",
        "fixed_eur_per_cc",
    )
    list_filter = ("rate_version", "age_group")
    search_fields = ("rate_version__name", "notes")
    autocomplete_fields = ("rate_version",)
    ordering = ("rate_version", "age_group", "sort_order")


@admin.register(CustomsClearanceFeeRate)
class CustomsClearanceFeeRateAdmin(admin.ModelAdmin):
    """Ставки сборов за таможенные операции."""

    list_display = (
        "rate_version",
        "customs_value_rub_min",
        "customs_value_rub_max",
        "fee_rub",
    )
    list_filter = ("rate_version",)
    search_fields = ("rate_version__name", "notes")
    autocomplete_fields = ("rate_version",)
    ordering = ("rate_version", "sort_order")
