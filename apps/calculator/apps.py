"""Конфигурация приложения калькуляторов."""

from django.apps import AppConfig


class CalculatorConfig(AppConfig):
    """Конфигурация универсального раздела калькуляторов."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.calculator"
    verbose_name = "Калькуляторы"
