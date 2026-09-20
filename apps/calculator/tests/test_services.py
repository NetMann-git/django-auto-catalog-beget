"""Тесты сервиса утилизационного сбора."""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.calculator.models import (
    CalculatorDefinition,
    RateVersion,
    UtilizationRate,
)
from apps.calculator.services import (
    RateConfigurationError,
    UtilizationCalculationInput,
    UtilizationFeeCalculator,
    calculate_fee,
    horsepower_to_kw,
)


class UtilizationFeeCalculatorTests(TestCase):
    """Проверяет формулу и подбор диапазона."""

    @classmethod
    def setUpTestData(cls) -> None:
        calculator = CalculatorDefinition.objects.create(
            slug="util-sbor",
            title="Утилизационный сбор",
        )
        version = RateVersion.objects.create(
            calculator=calculator,
            name="Тестовые ставки",
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 12, 31),
            base_rate=Decimal("20000"),
        )
        UtilizationRate.objects.create(
            rate_version=version,
            powertrain=UtilizationRate.Powertrain.COMBUSTION,
            usage_mode=UtilizationRate.UsageMode.PERSONAL,
            age_group=UtilizationRate.AgeGroup.NEW,
            engine_capacity_min=1001,
            engine_capacity_max=2000,
            power_kw_min=Decimal("95.62"),
            power_kw_max=Decimal("117.68"),
            coefficient=Decimal("0.17"),
        )

    def test_horsepower_conversion_keeps_160_hp_in_preferential_band(self) -> None:
        self.assertLessEqual(
            horsepower_to_kw(Decimal("160")),
            Decimal("117.68"),
        )

    def test_calculate_fee(self) -> None:
        self.assertEqual(
            calculate_fee(Decimal("20000"), Decimal("0.17")),
            Decimal("3400.00"),
        )

    def test_calculate_selects_matching_rate(self) -> None:
        result = UtilizationFeeCalculator.calculate(
            UtilizationCalculationInput(
                powertrain=UtilizationRate.Powertrain.COMBUSTION,
                age_group=UtilizationRate.AgeGroup.NEW,
                engine_capacity=1500,
                power_kw=horsepower_to_kw(Decimal("150")),
            ),
            calculation_date=date(2026, 6, 1),
        )

        self.assertEqual(result.coefficient, Decimal("0.1700"))
        self.assertEqual(result.amount, Decimal("3400.00"))

    def test_missing_rate_raises_configuration_error(self) -> None:
        with self.assertRaises(RateConfigurationError):
            UtilizationFeeCalculator.calculate(
                UtilizationCalculationInput(
                    powertrain=UtilizationRate.Powertrain.COMBUSTION,
                    age_group=UtilizationRate.AgeGroup.NEW,
                    engine_capacity=2500,
                    power_kw=Decimal("100"),
                ),
                calculation_date=date(2026, 6, 1),
            )
