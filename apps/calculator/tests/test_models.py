"""Тесты моделей версионируемых ставок."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.calculator.models import (
    CalculatorDefinition,
    RateVersion,
    UtilizationRate,
)


class RateModelsTests(TestCase):
    """Проверяет ограничения периодов и диапазонов ставок."""

    def setUp(self) -> None:
        self.calculator = CalculatorDefinition.objects.create(
            slug="util-sbor",
            title="Калькулятор утилизационного сбора",
        )
        self.version = RateVersion.objects.create(
            calculator=self.calculator,
            name="Ставки 2026",
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 12, 31),
            base_rate=Decimal("20000.00"),
        )

    def test_overlapping_active_versions_are_rejected(self) -> None:
        overlapping = RateVersion(
            calculator=self.calculator,
            name="Пересекающаяся версия",
            effective_from=date(2026, 6, 1),
            effective_to=date(2027, 1, 1),
            base_rate=Decimal("20000.00"),
        )

        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_invalid_power_range_is_rejected(self) -> None:
        rate = UtilizationRate(
            rate_version=self.version,
            powertrain=UtilizationRate.Powertrain.COMBUSTION,
            usage_mode=UtilizationRate.UsageMode.STANDARD,
            age_group=UtilizationRate.AgeGroup.NEW,
            power_kw_min=Decimal("120.00"),
            power_kw_max=Decimal("100.00"),
            coefficient=Decimal("40.0400"),
        )

        with self.assertRaises(ValidationError):
            rate.full_clean()

    def test_electric_rate_rejects_engine_capacity(self) -> None:
        rate = UtilizationRate(
            rate_version=self.version,
            powertrain=UtilizationRate.Powertrain.ELECTRIC,
            usage_mode=UtilizationRate.UsageMode.STANDARD,
            age_group=UtilizationRate.AgeGroup.NEW,
            engine_capacity_max=3000,
            coefficient=Decimal("40.0400"),
        )

        with self.assertRaises(ValidationError):
            rate.full_clean()
